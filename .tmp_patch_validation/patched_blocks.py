"""Scoped patch validation for mojibake sanitization and regressions."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover - optional in validation contexts
    tk = None  # type: ignore
    ttk = None  # type: ignore


_MOJIBAKE_TRIGGER_CHARS = ("\u00c2", "\u00c3", "\u00ce", "\u00e2", "\u0081")
_MOJIBAKE_FALLBACK_REPLACEMENTS = {
    "\u00c2\u00b0": "\u00b0",
    "\u00c2\u00b2": "\u00b2",
    "\u00c2\u00b3": "\u00b3",
    "\u00c3\u201a\u00c2\u00b0": "\u00b0",
    "\u00c3\u00bc": "\u00fc",
    "\u00ce\u201d": "\u0394",
    "\u00e2\u20ac\u00a6": "\u2026",
    "\u00e2\u20ac\u00a2": "\u2022",
    "\u00e2\u0153\u201c": "\u2713",
    "\u00e2\u2030\u02c6": "\u2248",
    "\u00e2\u2020\u2019": "\u2192",
    "\u00e2\u20ac\u201c": "\u2013",
    "\u00e2\u20ac\u201d": "\u2014",
    "\u00e2\u201a\u201a": "\u2082",
    "\u00e2\u201a\u0192": "\u2083",
    "\u00e2\u0081\u00bb": "\u207b",
    "\u00e2\u0081\u00ba": "\u207a",
    "\u00e2\u0082\u0081": "\u2081",
    "\u00e2\u0082\u0082": "\u2082",
    "\u00e2\u0082\u0083": "\u2083",
    "\u00e2\u0082\u0084": "\u2084",
    "\u00e2\u0082\u0085": "\u2085",
    "\u00e2\u0082\u0086": "\u2086",
    "\u00e2\u0082\u0087": "\u2087",
    "\u00e2\u0082\u0088": "\u2088",
    "\u00e2\u0082\u0089": "\u2089",
    "A\u00f8C": "\u00b0C",
    "H\u00c3\u00bc": "H\u00fc",
}

_FINAL_REPORT_SUBSCRIPT_MAP = {
    "\u2080": "0",
    "\u2081": "1",
    "\u2082": "2",
    "\u2083": "3",
    "\u2084": "4",
    "\u2085": "5",
    "\u2086": "6",
    "\u2087": "7",
    "\u2088": "8",
    "\u2089": "9",
}
_FINAL_REPORT_SUPERSCRIPT_MAP = {
    "\u2070": "0",
    "\u00b9": "1",
    "\u00b2": "2",
    "\u00b3": "3",
    "\u2074": "4",
    "\u2075": "5",
    "\u2076": "6",
    "\u2077": "7",
    "\u2078": "8",
    "\u2079": "9",
    "\u207a": "+",
    "\u207b": "-",
}
_FINAL_REPORT_SUBSCRIPT_RE = re.compile(r"[\u2080-\u2089]+")
_FINAL_REPORT_SUPERSCRIPT_RE = re.compile(
    r"[\u2070\u00b9\u00b2\u00b3\u2074-\u2079\u207a\u207b]+"
)

SOL_DEFAULT_SIM_MODE = "default"
SOL_MODE_INPUT_GUIDE: Dict[str, List[Dict[str, Any]]] = {
    "default": [{"label": "Basis inputs", "optional": False}],
    "naoh_reaction": [{"label": "Reaction charge", "optional": False}],
}
SOL_WORKFLOW_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "Analysis": {
        "guide_mode": "naoh_reaction",
        "mode_key": "naoh_reaction",
        "label": "Analysis",
    }
}
SOL_SIMULATION_MODES: Dict[str, Dict[str, Any]] = {
    "naoh_reaction": {"label": "Advanced Solubility"}
}


def _mojibake_marker_count(text: str) -> int:
    """Count likely mojibake markers in one text payload."""
    count = 0
    for ch in text:
        if ch in _MOJIBAKE_TRIGGER_CHARS:
            count += 1
            continue
        code_point = ord(ch)
        if 0x80 <= code_point <= 0x9F:
            count += 1
    return count


def _repair_mojibake_text(value: Any) -> str:
    """Repair likely mojibake text using guarded legacy-codec round-trips."""
    text = "" if value is None else str(value)
    if not text:
        return text
    baseline_score = _mojibake_marker_count(text)
    if baseline_score <= 0:
        return text
    repaired = text
    best_score = baseline_score
    for source_encoding in ("cp1252", "latin-1"):
        try:
            candidate = text.encode(source_encoding, errors="strict").decode(
                "utf-8", errors="strict"
            )
        except UnicodeError:
            continue
        candidate_score = _mojibake_marker_count(candidate)
        if candidate_score < best_score:
            repaired = candidate
            best_score = candidate_score
    for bad_text, good_text in _MOJIBAKE_FALLBACK_REPLACEMENTS.items():
        repaired = repaired.replace(bad_text, good_text)
    return repaired


def _set_stringvar_repaired(target_var: Any, value: Any) -> None:
    """Set a Tk variable using mojibake-repaired display text."""
    setter = getattr(target_var, "set", None)
    if not callable(setter):
        return
    setter(_repair_mojibake_text(value))


def _sanitize_widget_text_tree(root_widget: Any) -> None:
    """Recursively repair widget text and Treeview item content."""

    if ttk is None:
        return

    def _repair_widget_text(widget: Any) -> None:
        try:
            current_text = widget.cget("text")
        except Exception:
            return
        repaired_text = _repair_mojibake_text(current_text)
        if repaired_text != current_text:
            try:
                widget.configure(text=repaired_text)
            except Exception:
                return

    def _repair_tree_item(tree: ttk.Treeview, item_id: str) -> None:
        try:
            row_data = tree.item(item_id)
        except Exception:
            return
        text_value = row_data.get("text")
        values = row_data.get("values", ())
        repaired_text = _repair_mojibake_text(text_value)
        repaired_values = tuple(_repair_mojibake_text(value) for value in values)
        if repaired_text != text_value or repaired_values != tuple(values):
            try:
                tree.item(item_id, text=repaired_text, values=repaired_values)
            except Exception:
                return
        for child_id in tree.get_children(item_id):
            _repair_tree_item(tree, child_id)

    queue: List[Any] = [root_widget]
    while queue:
        widget = queue.pop(0)
        if widget is None:
            continue
        _repair_widget_text(widget)
        if isinstance(widget, ttk.Treeview):
            columns = ["#0", *list(widget["columns"])]
            for column in columns:
                heading = widget.heading(column)
                repaired = _repair_mojibake_text(heading.get("text", ""))
                widget.heading(column, text=repaired)
            for item_id in widget.get_children(""):
                _repair_tree_item(widget, item_id)
        try:
            queue.extend(list(widget.winfo_children()))
        except Exception:
            continue


def _sanitize_figure_text_artists(fig: Any) -> None:
    """Repair mojibake across text artists in one Matplotlib figure."""
    if fig is None:
        return

    def _repair_text_artist(text_artist: Any) -> None:
        getter = getattr(text_artist, "get_text", None)
        setter = getattr(text_artist, "set_text", None)
        if not callable(getter) or not callable(setter):
            return
        source_text = getter()
        repaired_text = _repair_mojibake_text(source_text)
        if repaired_text != source_text:
            setter(repaired_text)

    for figure_text in list(getattr(fig, "texts", []) or []):
        _repair_text_artist(figure_text)
    _repair_text_artist(getattr(fig, "_suptitle", None))
    for figure_legend in list(getattr(fig, "legends", []) or []):
        for legend_text in list(figure_legend.get_texts() or []):
            _repair_text_artist(legend_text)
    for axis in list(getattr(fig, "axes", []) or []):
        _repair_text_artist(getattr(axis, "title", None))
        _repair_text_artist(getattr(getattr(axis, "xaxis", None), "label", None))
        _repair_text_artist(getattr(getattr(axis, "yaxis", None), "label", None))
        for axis_text in list(getattr(axis, "texts", []) or []):
            _repair_text_artist(axis_text)
        legend = axis.get_legend()
        if legend is not None:
            for legend_text in list(legend.get_texts() or []):
                _repair_text_artist(legend_text)
            _repair_text_artist(legend.get_title())
        for table in list(getattr(axis, "tables", []) or []):
            cell_map = table.get_celld()
            if not isinstance(cell_map, Mapping):
                continue
            for cell in cell_map.values():
                _repair_text_artist(cell.get_text())


def _export_text_summary_png_core(
    text: str,
    path: str,
    metadata: Optional[List[str]] = None,
) -> None:
    """Validation core for text-summary export sanitization behavior."""
    if metadata:
        text = f"{text.rstrip()}\n\n---\n" + "\n".join(metadata)
    text = _repair_mojibake_text(text)
    lines = text.splitlines() or [""]
    max_chars = max(len(line) for line in lines) or 1
    fig_width = max(6.0, min(16.0, 0.12 * max_chars))
    fig_height = max(2.5, min(20.0, 0.38 * len(lines) + 0.5))
    fig = Figure(figsize=(fig_width, fig_height), dpi=150)
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.set_position([0, 0, 1, 1])
    text_artist = ax.text(
        0.0,
        1.0,
        text,
        ha="left",
        va="top",
        fontsize=12,
        family="monospace",
        linespacing=1.35,
        transform=ax.transAxes,
    )
    canvas.draw()
    renderer = canvas.get_renderer()
    bbox = text_artist.get_window_extent(renderer=renderer)
    if bbox.width <= 0 or bbox.height <= 0:
        _sanitize_figure_text_artists(fig)
        fig.savefig(
            path,
            dpi=150,
            bbox_inches="tight",
            pad_inches=0.0,
            facecolor="white",
        )
        return
    pad_x = max(3.0, 0.02 * bbox.width)
    pad_y = max(3.0, 0.02 * bbox.height)
    cropped_bbox = Bbox.from_extents(
        bbox.x0 - pad_x,
        bbox.y0 - pad_y,
        bbox.x1 + pad_x,
        bbox.y1 + pad_y,
    )
    bbox_inches = cropped_bbox.transformed(fig.dpi_scale_trans.inverted())
    _sanitize_figure_text_artists(fig)
    fig.savefig(
        path,
        dpi=150,
        bbox_inches=bbox_inches,
        pad_inches=0.0,
        facecolor="white",
    )


class UnifiedApp:
    """Validation harness for methods changed in the production module."""

    def _update_sol_helper_contents(self) -> None:
        """Validation copy of helper-content refresh with repaired StringVar output."""
        summary_var = getattr(self, "_sol_helper_summary_var", None)
        steps_var = getattr(self, "_sol_helper_steps_var", None)
        if summary_var is None or steps_var is None:
            return
        workflow_key = self._current_solubility_workflow()
        workflow_meta = SOL_WORKFLOW_TEMPLATES.get(workflow_key, {})
        guide_key = workflow_meta.get("guide_mode", SOL_DEFAULT_SIM_MODE)
        guide = SOL_MODE_INPUT_GUIDE.get(guide_key, SOL_MODE_INPUT_GUIDE["default"])
        meta_key = workflow_meta.get("mode_key", guide_key)
        meta = SOL_SIMULATION_MODES.get(meta_key, {})
        completed = 0
        required = 0
        lines: List[str] = []
        next_spec: Optional[Dict[str, Any]] = None
        for spec in guide:
            label = spec.get("label", "Field")
            if spec.get("optional"):
                label = f"{label} (optional)"
            spec_complete = self._helper_spec_complete(spec)
            if spec_complete and not spec.get("optional"):
                completed += 1
            if not spec.get("optional"):
                required += 1
            prefix = "\u2713" if spec_complete else "\u2022"
            lines.append(f"{prefix} {label}")
            if not spec_complete and next_spec is None and not spec.get("optional"):
                next_spec = spec
        if required == 0:
            required = len(guide)
        workflow_label = workflow_meta.get("label") or meta.get(
            "label", "Advanced Solubility"
        )
        _set_stringvar_repaired(
            summary_var,
            f"{workflow_label}: {completed}/{required} required steps complete.",
        )
        _set_stringvar_repaired(
            steps_var,
            "\n".join(lines) if lines else "No guided steps available.",
        )
        self._sol_helper_next_spec = next_spec
        extra_tips: List[str] = []
        if workflow_key == "Analysis":
            extra_tips.append(
                "Import validated cycles or enter CO\u00e2\u201a\u201a totals so "
                "the per-cycle speciation plot reflects real data."
            )
        if extra_tips:
            _set_stringvar_repaired(
                steps_var,
                steps_var.get()
                + "\n"
                + "\n".join(f"\u2022 {tip}" for tip in extra_tips),
            )

    def _final_report_sanitize_text(self, text: str) -> str:
        """Validation copy of Final Report sanitize behavior."""
        if not text:
            return text

        def _sub_replace(match: re.Match[str]) -> str:
            digits = "".join(
                _FINAL_REPORT_SUBSCRIPT_MAP.get(ch, "") for ch in match.group(0)
            )
            return f"$_{digits}$" if digits else match.group(0)

        def _sup_replace(match: re.Match[str]) -> str:
            digits = "".join(
                _FINAL_REPORT_SUPERSCRIPT_MAP.get(ch, "") for ch in match.group(0)
            )
            return f"$^{digits}$" if digits else match.group(0)

        repaired = _repair_mojibake_text(text)
        value = _FINAL_REPORT_SUBSCRIPT_RE.sub(_sub_replace, repaired)
        return _FINAL_REPORT_SUPERSCRIPT_RE.sub(_sup_replace, value)


def _regression_test_solubility_guidance_text_repair() -> None:
    """Validate Advanced Speciation guidance text normalization in helper paths."""
    if tk is None:
        return

    class _Harness(UnifiedApp):
        """Minimal harness covering helper-guidance dependencies."""

        def __init__(self) -> None:
            tk_root = tk.Tcl()
            self._sol_helper_summary_var = tk.StringVar(master=tk_root, value="")
            self._sol_helper_steps_var = tk.StringVar(master=tk_root, value="")

        @staticmethod
        def _current_solubility_workflow() -> str:
            """Return one workflow key that triggers Analysis helper hints."""
            return "Analysis"

        @staticmethod
        def _helper_spec_complete(_spec: Dict[str, Any]) -> bool:
            """Return deterministic incomplete state for helper checklist rows."""
            return False

    harness = _Harness()
    UnifiedApp._update_sol_helper_contents(harness)
    summary_text = harness._sol_helper_summary_var.get()
    steps_text = harness._sol_helper_steps_var.get()
    if "CO\u00e2\u201a\u201a" in steps_text:
        raise AssertionError(
            "Advanced helper steps should not contain mojibake CO2 text."
        )
    if "CO\u2082" not in steps_text:
        raise AssertionError("Advanced helper steps should include repaired CO2 text.")
    if (
        _mojibake_marker_count(summary_text) != 0
        or _mojibake_marker_count(steps_text) != 0
    ):
        raise AssertionError("Advanced helper summary/steps should be mojibake-free.")


def _regression_test_final_report_text_sanitization_path() -> None:
    """Validate Final Report text sanitation applies mojibake repair first."""
    harness = UnifiedApp()
    raw = (
        "GL-260 Final Report \u00e2\u20ac\u201c Page 3 | "
        "CO\u00e2\u201a\u201a and CO\u00e2\u201a\u0192\u00c2\u00b2\u00e2\u0081\u00bb"
    )
    sanitized = UnifiedApp._final_report_sanitize_text(harness, raw)
    if "\u00e2" in sanitized or "\u00c2" in sanitized:
        raise AssertionError(
            f"Final Report sanitize should remove mojibake markers: {sanitized!r}"
        )
    if "\u2013" not in sanitized:
        raise AssertionError(
            f"Final Report sanitize should preserve an en dash: {sanitized!r}"
        )
    if "CO$_2$" not in sanitized:
        raise AssertionError(
            "Final Report sanitize should preserve repaired/subscripted CO2 text: "
            f"{sanitized!r}"
        )


def _regression_test_figure_text_artist_export_sanitization() -> None:
    """Validate figure-level text artist sanitization for export paths."""
    fig = Figure(figsize=(4, 3), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot([0, 1], [0, 1], label="\u00ce\u201dP")
    ax.set_title("pH \u00e2\u2030\u02c6 8")
    ax.set_xlabel("Temperature (\u00c2\u00b0C)")
    ax.set_ylabel("CO\u00e2\u201a\u201a loading")
    ax.text(0.5, 0.5, "NaHCO\u00e2\u201a\u0192", transform=ax.transAxes)
    fig.text(0.5, 0.02, "State \u00e2\u20ac\u201d clean", ha="center")
    legend = ax.legend(loc="upper left")
    if legend is not None:
        legend.set_title("Legend \u00e2\u20ac\u00a2 symbols")
    _sanitize_figure_text_artists(fig)
    if "\u00e2" in ax.get_title():
        raise AssertionError("Axis title should be repaired by figure text sanitizer.")
    if "\u00b0C" not in ax.get_xlabel():
        raise AssertionError("Axis xlabel should contain repaired degree symbol.")
    if "CO\u2082" not in ax.get_ylabel():
        raise AssertionError("Axis ylabel should contain repaired CO2 symbol.")
    if "NaHCO\u2083" not in ax.texts[0].get_text():
        raise AssertionError("Axis annotation should contain repaired NaHCO3 symbol.")
    if "State \u2014 clean" not in fig.texts[0].get_text():
        raise AssertionError("Figure text should contain repaired em dash.")
    legend_texts = [text.get_text() for text in (legend.get_texts() if legend else [])]
    if not legend_texts or "\u0394P" not in legend_texts[0]:
        raise AssertionError("Legend labels should contain repaired delta symbol.")
    plt.close(fig)


REGRESSION_TESTS: List[Tuple[str, Any]] = [
    ("Advanced guidance text repair", _regression_test_solubility_guidance_text_repair),
    (
        "Final report text sanitization path",
        _regression_test_final_report_text_sanitization_path,
    ),
    (
        "Figure text export sanitization",
        _regression_test_figure_text_artist_export_sanitization,
    ),
]
