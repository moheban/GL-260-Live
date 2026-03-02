# Scoped patch validation for GL-260 unicode + toolbar compactness patch.

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Sequence

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover - optional in validation contexts
    tk = None  # type: ignore
    ttk = None  # type: ignore

try:
    import customtkinter as ctk  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    ctk = None


_MOJIBAKE_TRIGGER_CHARS = ("\u00c2", "\u00c3", "\u00ce", "\u00e2", "\u0081")
_MOJIBAKE_FALLBACK_REPLACEMENTS = {
    "\u00c2\u00b0": "\u00b0",
    "\u00c2\u00b2": "\u00b2",
    "\u00c2\u00b3": "\u00b3",
    "\u00c3\u201a\u00c2\u00b0": "\u00b0",
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
    "A\u00f8C": "\u00b0C",
}


def _mojibake_marker_count(text: str) -> int:
    """Count likely mojibake markers in one text payload.

    Purpose:
        Provide a lightweight quality metric to compare repaired text candidates.
    Why:
        UTF-8 text that was decoded with the wrong codec often contains a small
        set of marker glyphs (`Â`, `Ã`, `Î`, `â`) and C1 control characters.
        Counting these markers lets repair logic keep only conversions that
        actually reduce corruption.
    Inputs:
        text: Candidate text to evaluate.
    Outputs:
        Integer count of suspicious marker glyphs/control code points.
    Side Effects:
        None.
    Exceptions:
        None.
    """
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
    """Repair likely mojibake text using guarded legacy-codec round-trips.

    Purpose:
        Normalize UI/display strings that were accidentally persisted or authored
        with broken unicode decoding.
    Why:
        The application renders scientific symbols (`Δ`, `°`, subscripts,
        superscripts) across Tk/Matplotlib surfaces; mojibake (for example
        `Î”P`, `Â°C`, `COâ‚‚`) makes labels unreadable.
    Inputs:
        value: Any display value to normalize; non-string values are stringified.
    Outputs:
        Repaired display string when corruption is detected; otherwise the
        original text representation.
    Side Effects:
        None.
    Exceptions:
        Codec conversion attempts use strict error handling and fall back
        silently when conversion is invalid for the input text.
    """
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


def _compact_layer_status_text(value: Any, *, default_status: str = "clean") -> str:
    """Normalize layer-status labels into a compact, deduplicated display form.

    Purpose:
        Convert verbose or duplicated status text into a short toolbar-safe label.
    Why:
        Plot toolbar status text can be sourced from multiple refresh paths and
        persisted metadata; some paths duplicate prefixes (for example
        `Layer State: Layer State: clean`) and create long strings.
    Inputs:
        value: Raw status text payload from any caller.
        default_status: Fallback status token when payload is empty after cleanup.
    Outputs:
        Compact status string in the canonical `State: ...` format.
    Side Effects:
        None.
    Exceptions:
        None.
    """
    raw_text = _repair_mojibake_text(value)
    normalized = re.sub(r"\s+", " ", raw_text).strip()
    if not normalized:
        normalized = str(default_status or "clean").strip() or "clean"
    normalized = re.sub(
        r"^(?:Layer\s*State\s*:\s*)+",
        "",
        normalized,
        flags=re.IGNORECASE,
    ).strip()
    if not normalized:
        normalized = str(default_status or "clean").strip() or "clean"
    if normalized.lower().startswith("state:"):
        normalized = normalized.split(":", 1)[1].strip() or (
            str(default_status or "clean").strip() or "clean"
        )
    return f"State: {normalized}"


def _ui_button(parent, *args, **kwargs):
    """Create a button using CTk when available, else ttk.

    Purpose:
        Provide one compatibility constructor for push-button controls.
    Why:
        Stage-wise CTk migration requires preserving existing callbacks and layout
        code while avoiding repeated availability checks in each UI builder.
    Inputs:
        parent: Parent widget that owns the button.
        *args: Positional arguments accepted by ttk/CTk constructors.
        **kwargs: Keyword arguments such as text, command, width, and state.
    Outputs:
        Widget instance (`ctk.CTkButton` or `ttk.Button`).
    Side Effects:
        None beyond widget construction.
    Exceptions:
        Unsupported CTk-only/ttk-only kwargs are ignored on the CTk branch.
    """
    normalized_kwargs = dict(kwargs)
    if "text" in normalized_kwargs:
        normalized_kwargs["text"] = _repair_mojibake_text(normalized_kwargs.get("text"))
    if ctk is None:
        return ttk.Button(parent, *args, **normalized_kwargs)
    ctk_kwargs = dict(normalized_kwargs)
    ctk_kwargs.pop("style", None)
    ctk_kwargs.pop("padding", None)
    return ctk.CTkButton(parent, *args, **ctk_kwargs)


def _ui_checkbutton(parent, *args, **kwargs):
    """Create a checkbutton using CTk when available, else ttk.

    Purpose:
        Normalize checkbutton creation across ttk and CTk toolkits.
    Why:
        CTk migration should not force callback/business-logic rewrites.
    Inputs:
        parent: Parent widget that owns the checkbutton.
        *args: Positional constructor args.
        **kwargs: Keyword args including text, variable, command, and state.
    Outputs:
        Widget instance (`ctk.CTkCheckBox` or `ttk.Checkbutton`).
    Side Effects:
        None beyond widget construction.
    Exceptions:
        ttk-specific style kwargs are ignored on the CTk branch.
    """
    normalized_kwargs = dict(kwargs)
    if "text" in normalized_kwargs:
        normalized_kwargs["text"] = _repair_mojibake_text(normalized_kwargs.get("text"))
    if ctk is None:
        return ttk.Checkbutton(parent, *args, **normalized_kwargs)
    ctk_kwargs = dict(normalized_kwargs)
    ctk_kwargs.pop("style", None)
    ctk_kwargs.pop("padding", None)
    return ctk.CTkCheckBox(parent, *args, **ctk_kwargs)


def _ui_radiobutton(parent, *args, **kwargs):
    """Create a radio button using CTk when available, else ttk.

    Purpose:
        Provide one constructor for mutually-exclusive choice controls.
    Why:
        Reduces repetitive conditional widget creation in migrated dialogs/tabs.
    Inputs:
        parent: Parent widget for the radiobutton.
        *args: Positional constructor args.
        **kwargs: Keyword args such as text, value, variable, and command.
    Outputs:
        Widget instance (`ctk.CTkRadioButton` or `ttk.Radiobutton`).
    Side Effects:
        None beyond widget construction.
    Exceptions:
        ttk-only style kwargs are ignored on the CTk branch.
    """
    normalized_kwargs = dict(kwargs)
    if "text" in normalized_kwargs:
        normalized_kwargs["text"] = _repair_mojibake_text(normalized_kwargs.get("text"))
    if ctk is None:
        return ttk.Radiobutton(parent, *args, **normalized_kwargs)
    ctk_kwargs = dict(normalized_kwargs)
    ctk_kwargs.pop("style", None)
    ctk_kwargs.pop("padding", None)
    return ctk.CTkRadioButton(parent, *args, **ctk_kwargs)


def _svg_safe_text(value: Any) -> str:
    """Sanitize free-form labels for safe SVG/text rendering.

    Purpose:
        Convert arbitrary display text into a stable form for SVG export and
        Matplotlib text artists.
    Why:
        Export paths receive mixed UI/data strings that may include mojibake and
        reserved symbols.
    Inputs:
        value: Raw label payload from UI state, data labels, or generated text.
    Outputs:
        Sanitized text with reserved characters expanded/removed and whitespace
        collapsed.
    Side Effects:
        None.
    Exceptions:
        None.
    """
    text = _repair_mojibake_text(value)
    replacements = {
        "&": "and",
        "<": "less than",
        ">": "greater than",
        '"': "",
        "'": "",
    }
    sanitized_parts: List[str] = []
    for ch in text:
        sanitized_parts.append(replacements.get(ch, ch))
    sanitized = "".join(sanitized_parts)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized


def _format_axis_label(label: Any) -> str:
    """Format one axis label for on-screen display and export.

    Purpose:
        Produce a consistent, human-readable axis label from a raw source token.
    Why:
        Labels can arrive from workbook headers/settings with underscores and
        occasional mojibake artifacts.
    Inputs:
        label: Raw axis label value.
    Outputs:
        Cleaned axis label string with repaired unicode and normalized spacing.
    Side Effects:
        None.
    Exceptions:
        None.
    """
    normalized = _repair_mojibake_text(label).replace("_", " ")
    normalized = normalized.replace(" (\u00c3\u201a\u00c2\u00b0C)", "")
    normalized = normalized.replace(" (\u00c2\u00b0C)", " (\u00b0C)")
    return normalized


class UnifiedApp:
    """Minimal validation harness for patched status helpers."""

    def _plot_tab_frame_for_plot_id(self, _plot_id: Optional[str]):
        return getattr(self, "_frame", None)

    def _ensure_plot_dirty_flags(self, _plot_id: Optional[str]) -> Dict[str, bool]:
        return getattr(
            self,
            "_flags",
            {
                "dirty_data": False,
                "dirty_layout": False,
                "dirty_elements": False,
                "dirty_trace": False,
            },
        )

    def _layer_status_text_from_flags(
        self,
        *,
        dirty_data: bool,
        dirty_layout: bool,
        dirty_elements: bool,
        dirty_trace: bool,
    ) -> str:
        """Return a compact layer-status summary string from dirty flags."""
        if dirty_data:
            return _compact_layer_status_text("Data pending")
        layers: List[str] = []
        if dirty_trace:
            layers.append("trace")
        if dirty_layout:
            layers.append("layout")
        if dirty_elements:
            layers.append("elements")
        if not layers:
            return _compact_layer_status_text("clean")
        return _compact_layer_status_text("+".join(layers))

    def _update_plot_layer_status_indicator(
        self,
        plot_id: Optional[str],
        *,
        route: Optional[str] = None,
        changed_layers: Optional[Sequence[str]] = None,
    ) -> None:
        """Update one plot tab's layer-status indicator text."""
        frame = self._plot_tab_frame_for_plot_id(plot_id)
        if frame is None:
            return
        status_var = getattr(frame, "_plot_layer_status_var", None)
        if status_var is None:
            return
        flags = self._ensure_plot_dirty_flags(plot_id) or {}
        text = self._layer_status_text_from_flags(
            dirty_data=bool(flags.get("dirty_data", False)),
            dirty_layout=bool(flags.get("dirty_layout", False)),
            dirty_elements=bool(flags.get("dirty_elements", False)),
            dirty_trace=bool(flags.get("dirty_trace", False)),
        )
        route_text = str(route or "").strip().lower()
        if route_text in {
            "full_async_refresh",
            "in_place_layer_refresh",
            "in_place_display_apply",
        }:
            changed = list(changed_layers or [])
            if changed:
                text = f"{route_text} ({'+'.join(changed)})"
            else:
                text = route_text
        status_var.set(_compact_layer_status_text(text))


def _build_topbar_button(
    parent: Any,
    *,
    text: str,
    command: Callable[[], None],
    scale_length_cb: Callable[[int], int],
    ctk_width: int = 130,
    ttk_width: int = 12,
) -> Any:
    """Create one compact plot-tab toolbar button with deterministic sizing.

    Purpose:
        Build topbar action buttons that remain stable as plots refresh.
    Why:
        The plot tab keeps Matplotlib navigation tools and several action
        buttons in one row; explicit button sizing prevents overlap/jitter.
    Inputs:
        parent: Container frame for the button.
        text: Button label text.
        command: Callback invoked on button press.
        scale_length_cb: Scaling callback that converts logical lengths to pixels.
        ctk_width: Width in pixels when CTk buttons are active.
        ttk_width: Width in character units when ttk buttons are active.
    Outputs:
        Constructed button widget instance.
    Side Effects:
        Instantiates one Tk/CTk button widget.
    Exceptions:
        None; delegates widget-construction failures to caller context.
    """
    if ctk is None:
        return _ui_button(
            parent,
            text=text,
            command=command,
            width=max(6, int(ttk_width)),
        )
    return _ui_button(
        parent,
        text=text,
        command=command,
        width=max(96, int(ctk_width)),
        height=max(24, int(scale_length_cb(28))),
    )


def _regression_test_mojibake_text_repair_samples() -> None:
    """Validate mojibake repair for representative scientific/UI symbol payloads."""
    samples = [
        ("Total \u00ce\u201dP", "Total \u0394P"),
        ("Temperature (\u00c2\u00b0C)", "Temperature (\u00b0C)"),
        ("CO\u00e2\u201a\u201a", "CO\u2082"),
        ("CO\u00e2\u201a\u0192\u00c2\u00b2\u00e2\u0081\u00bb", "CO\u2083\u00b2\u207b"),
        ("Loading\u00e2\u20ac\u00a6", "Loading\u2026"),
        ("\u00e2\u20ac\u00a2 item", "\u2022 item"),
        ("\u00e2\u0153\u201c done", "\u2713 done"),
        ("x \u00e2\u2030\u02c6 y", "x \u2248 y"),
        ("a \u00e2\u2020\u2019 b", "a \u2192 b"),
    ]
    for raw_value, expected in samples:
        actual = _repair_mojibake_text(raw_value)
        if actual != expected:
            raise AssertionError(
                "Mojibake repair mismatch for "
                f"{raw_value!r}: got={actual!r}, expected={expected!r}"
            )
    ascii_text = "Pressure (PSI)"
    ascii_repaired = _repair_mojibake_text(ascii_text)
    if ascii_repaired != ascii_text:
        raise AssertionError("ASCII text should remain unchanged by repair helper.")


def _regression_test_layer_status_text_compaction() -> None:
    """Validate compact layer-status formatting and duplicate-prefix cleanup."""
    deduped = _compact_layer_status_text("Layer State: Layer State: clean")
    if deduped != "State: clean":
        raise AssertionError(f"Layer-status dedupe mismatch: {deduped!r}")
    mojibake_status = _compact_layer_status_text(
        "Layer State: CO\u00e2\u201a\u201a ready"
    )
    if mojibake_status != "State: CO\u2082 ready":
        raise AssertionError(
            f"Layer-status mojibake repair mismatch: {mojibake_status!r}"
        )

    clean_status = UnifiedApp()._layer_status_text_from_flags(
        dirty_data=False,
        dirty_layout=False,
        dirty_elements=False,
        dirty_trace=False,
    )
    if clean_status != "State: clean":
        raise AssertionError(f"Clean status mismatch: {clean_status!r}")
    dirty_status = UnifiedApp()._layer_status_text_from_flags(
        dirty_data=False,
        dirty_layout=True,
        dirty_elements=True,
        dirty_trace=False,
    )
    if dirty_status != "State: layout+elements":
        raise AssertionError(f"Dirty-layer status mismatch: {dirty_status!r}")
    data_pending_status = UnifiedApp()._layer_status_text_from_flags(
        dirty_data=True,
        dirty_layout=False,
        dirty_elements=False,
        dirty_trace=False,
    )
    if data_pending_status != "State: Data pending":
        raise AssertionError(f"Data-pending status mismatch: {data_pending_status!r}")
