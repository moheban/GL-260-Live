from typing import Any, Dict, List, Mapping, Optional, Tuple
import copy
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.transforms import Bbox

# Stubs to satisfy references used by snippet-only lint/syntax checks.
COMPARE_COMBINED_TK_OVERRIDE_BINDINGS = ()
COMPARE_PLOT_PRESET_KEYS = ()
DEFAULT_COMPARE_PLOT_PRESET_NAME = "Balanced"


def _resolve_compare_plot_preset_values(*args, **kwargs):
    return {}


def _normalize_compare_layout_overrides(value):
    return {}


def _normalize_compare_tab_settings(value):
    return {}


def _normalize_compare_plot_editor_margins_by_pair(value):
    return {}


def layout_health_autofix(*args, **kwargs):
    return {"issues": []}


class UnifiedApp:
    pass


settings = {}


def _regression_test_compare_combined_tk_override_bindings_complete() -> None:
    """Validate Compare combined Tk-var override bindings cover all preset keys.

    Purpose:
        Ensure Compare render applies every preset-driven Tk variable consumed by
        `_combined_plot_config`, including font and legend controls.
    Why:
        Missing bindings let stale main-tab Tk values leak into Compare renders,
        causing whitespace drift and title/legend regressions.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        None.
    Exceptions:
        Raises AssertionError when bindings are incomplete or malformed.
    """
    mapping = tuple(COMPARE_COMBINED_TK_OVERRIDE_BINDINGS)
    if not mapping:
        raise AssertionError(
            "Expected Compare Tk override binding mapping to be non-empty."
        )
    key_set = {str(key) for key, _attr in mapping}
    attr_set = {str(attr) for _key, attr in mapping}
    if len(key_set) != len(mapping):
        raise AssertionError("Compare Tk override binding keys must be unique.")
    if len(attr_set) != len(mapping):
        raise AssertionError("Compare Tk override binding attrs must be unique.")
    expected_keys = set(COMPARE_PLOT_PRESET_KEYS)
    if key_set != expected_keys:
        raise AssertionError(
            "Compare Tk override binding keys must match compare preset keys exactly."
        )
    required_keys = {
        "combined_title_fontsize",
        "combined_suptitle_fontsize",
        "combined_label_fontsize",
        "combined_tick_fontsize",
        "combined_export_pad_pts",
        "combined_legend_rows",
        "combined_legend_alignment",
        "combined_legend_wrap",
    }
    missing = sorted(required_keys.difference(key_set))
    if missing:
        raise AssertionError(f"Missing required Compare Tk override keys: {missing!r}")


def _regression_test_compare_render_applies_complete_tk_override_set() -> None:
    """Validate Compare render applies and restores complete Tk-var overrides.

    Purpose:
        Verify `_compare_render_profile_side` applies compare preset/override values
        to all bound combined-plot Tk vars during render.
    Why:
        Prior partial override coverage caused Compare-only whitespace/title drift
        while main-tab values leaked into compare rendering.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Executes one compare render call against a local harness.
    Exceptions:
        Raises AssertionError when override application or snapshot restore regresses.
    """

    class _VarStub:
        """Minimal Tk-var stub used for deterministic get/set assertions."""

        def __init__(self, value: Any) -> None:
            self._value = value

        def get(self) -> Any:
            """Return current stub value."""
            return self._value

        def set(self, value: Any) -> None:
            """Assign new stub value."""
            self._value = value

    class _CanvasStub:
        """Canvas stub allowing figure attribute assignment."""

        def __init__(self) -> None:
            self.figure = None

    class _Harness:
        """Harness that records Tk-var values during compare-side render."""

        def __init__(self) -> None:
            self.compare_use_profile_layout_var = _VarStub(False)
            self.compare_plot_preset_var = _VarStub(DEFAULT_COMPARE_PLOT_PRESET_NAME)
            self._compare_custom_plot_presets = {}
            self._compare_layout_overrides = {
                "combined_legend_fontsize": 12.25,
                "combined_cycle_legend_fontsize": 11.75,
                "combined_left_pad_pct": 4.0,
            }
            self._compare_panels = {
                "A": {
                    "canvas": _CanvasStub(),
                    "widget": object(),
                    "bundle": {
                        "profile_name": "Profile A",
                        "dataset_path": "C:/tmp/dataset.xlsx",
                        "args": tuple([""] * 24),
                        "plot_settings": {},
                        "plot_elements": {},
                        "layout_profiles": {},
                        "df_reference": object(),
                    },
                    "cycle_rows": [],
                    "total_drop": None,
                    "cycle_fallback_used": False,
                    "cycle_rows_synthesized": False,
                    "cycle_compute_backend": "",
                    "render_success": False,
                    "render_error_message": "",
                }
            }
            self._combined_plot_state = None
            self._combined_layout_state = None
            self._combined_layout_dirty = False
            self._combined_legend_anchor = None
            self._combined_legend_loc = None
            self.df = None
            self.applied_checks_ok = False
            self._tk_initial_values: Dict[str, Any] = {}
            for key, attr_name in COMPARE_COMBINED_TK_OVERRIDE_BINDINGS:
                if key == "combined_legend_wrap":
                    base_value = True
                elif key == "combined_legend_rows":
                    base_value = 7
                elif key == "combined_legend_alignment":
                    base_value = "center"
                else:
                    base_value = -999.0
                self._tk_initial_values[attr_name] = base_value
                setattr(self, attr_name, _VarStub(base_value))

        @staticmethod
        def _compare_parse_float_entry(_raw: Any) -> Optional[float]:
            """Return no-uptake sentinel for status formatting path."""
            return None

        @staticmethod
        def _compare_resolve_figsize_for_panel(_side: str) -> Tuple[float, float]:
            """Return deterministic render figsize for harness."""
            return (6.0, 3.5)

        @staticmethod
        def _compare_effective_pair_plot_elements_override() -> Dict[str, Any]:
            """Return deterministic non-blank side title payload."""
            return {
                "retain_profile_elements": True,
                "hide_text_family": False,
                "side_overrides": {
                    "A": {"title_text": "Render Title", "suptitle_text": "Render Sup"}
                },
            }

        @staticmethod
        def _compare_profile_title_defaults(
            _side_key: str,
            _bundle: Optional[Mapping[str, Any]],
        ) -> Dict[str, str]:
            """Return fallback titles for blank override resolution path."""
            return {"title_text": "Fallback Title", "suptitle_text": "Fallback Sup"}

        @staticmethod
        def _compare_resolve_side_plot_editor_margins(
            _side_key: str,
        ) -> Dict[str, float]:
            """Return deterministic side margins for compare render."""
            return {"left": 0.12, "right": 0.9, "top": 0.88, "bottom": 0.11}

        @staticmethod
        def _finalize_matplotlib_canvas_layout(**_kwargs: Any) -> None:
            """No-op finalize hook for harness render."""
            return None

        @staticmethod
        def _compare_update_side_status(_side_key: str, _message: str) -> None:
            """No-op side status update hook."""
            return None

        @staticmethod
        def _compare_update_status_chips() -> None:
            """No-op status-chip refresh hook."""
            return None

        @staticmethod
        def _compare_log_render_completion_event(_side_key: str) -> None:
            """No-op render-completion logging hook."""
            return None

        def _build_combined_triple_axis_from_state(self, **_kwargs: Any) -> Figure:
            """Assert bound Tk-var values during compare render and return a figure."""
            preset_values = _resolve_compare_plot_preset_values(
                DEFAULT_COMPARE_PLOT_PRESET_NAME,
                custom_presets={},
            )
            normalized_overrides = _normalize_compare_layout_overrides(
                self._compare_layout_overrides
            )
            for setting_key, attr_name in COMPARE_COMBINED_TK_OVERRIDE_BINDINGS:
                expected = normalized_overrides.get(
                    setting_key,
                    preset_values.get(setting_key),
                )
                actual = getattr(self, attr_name).get()
                if isinstance(expected, float):
                    if abs(float(actual) - float(expected)) > 1e-9:
                        raise AssertionError(
                            f"Expected {attr_name}={expected!r}, got {actual!r}."
                        )
                else:
                    if actual != expected:
                        raise AssertionError(
                            f"Expected {attr_name}={expected!r}, got {actual!r}."
                        )
            self.applied_checks_ok = True
            return Figure(figsize=(4.0, 2.8), dpi=100)

    harness = _Harness()
    UnifiedApp._compare_render_profile_side(
        harness,
        "A",
        reason="regression",
        prepared=({}, [], None, {}),
    )
    if not harness.applied_checks_ok:
        raise AssertionError(
            "Expected compare render to evaluate Tk-var override checks."
        )
    for _setting_key, attr_name in COMPARE_COMBINED_TK_OVERRIDE_BINDINGS:
        actual = getattr(harness, attr_name).get()
        expected = harness._tk_initial_values.get(attr_name)
        if actual != expected:
            raise AssertionError(
                f"Expected Tk-var restore for {attr_name}: {expected!r}, got {actual!r}."
            )


def _regression_test_compare_render_layout_profile_shape_normalized() -> None:
    """Validate Compare render writes normalized layout profile shape.

    Purpose:
        Ensure compare-side rendering always injects a consumable layout profile
        containing `display` and `export` sections.
    Why:
        Flat malformed profile payloads break combined config resolution and
        contribute to whitespace/title overlap regressions.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Executes one compare render call against a local harness.
    Exceptions:
        Raises AssertionError when compare layout profile shape regresses.
    """

    class _VarStub:
        """Minimal Tk-var stub for compare harness."""

        def __init__(self, value: Any) -> None:
            self._value = value

        def get(self) -> Any:
            """Return stub value."""
            return self._value

        def set(self, value: Any) -> None:
            """Assign stub value."""
            self._value = value

    class _CanvasStub:
        """Canvas stub allowing figure assignment by render path."""

        def __init__(self) -> None:
            self.figure = None

    class _Harness:
        """Harness capturing compare layout profile shape during render."""

        def __init__(self) -> None:
            self.compare_use_profile_layout_var = _VarStub(True)
            self.compare_plot_preset_var = _VarStub(DEFAULT_COMPARE_PLOT_PRESET_NAME)
            self._compare_custom_plot_presets = {}
            self._compare_layout_overrides = {}
            self._compare_panels = {
                "A": {
                    "canvas": _CanvasStub(),
                    "widget": object(),
                    "bundle": {
                        "profile_name": "Profile A",
                        "dataset_path": "C:/tmp/dataset.xlsx",
                        "args": tuple([""] * 24),
                        "plot_settings": {},
                        "plot_elements": {},
                        "layout_profiles": {
                            "fig_combined_triple_axis": {
                                "left": 0.22,
                                "right": 0.78,
                                "top": 0.86,
                                "bottom": 0.18,
                            }
                        },
                        "df_reference": object(),
                    },
                    "cycle_rows": [],
                    "total_drop": None,
                    "cycle_fallback_used": False,
                    "cycle_rows_synthesized": False,
                    "cycle_compute_backend": "",
                    "render_success": False,
                    "render_error_message": "",
                }
            }
            self._combined_plot_state = None
            self._combined_layout_state = None
            self._combined_layout_dirty = False
            self._combined_legend_anchor = None
            self._combined_legend_loc = None
            self.df = None
            self.layout_profile_snapshot: Optional[Dict[str, Any]] = None

        @staticmethod
        def _compare_parse_float_entry(_raw: Any) -> Optional[float]:
            """Return no-uptake sentinel for status formatting path."""
            return None

        @staticmethod
        def _compare_resolve_figsize_for_panel(_side: str) -> Tuple[float, float]:
            """Return deterministic render figsize for harness."""
            return (6.0, 3.5)

        @staticmethod
        def _compare_effective_pair_plot_elements_override() -> Dict[str, Any]:
            """Return deterministic non-blank side title payload."""
            return {
                "retain_profile_elements": True,
                "hide_text_family": False,
                "side_overrides": {
                    "A": {"title_text": "Render Title", "suptitle_text": "Render Sup"}
                },
            }

        @staticmethod
        def _compare_profile_title_defaults(
            _side_key: str,
            _bundle: Optional[Mapping[str, Any]],
        ) -> Dict[str, str]:
            """Return fallback titles for blank override resolution path."""
            return {"title_text": "Fallback Title", "suptitle_text": "Fallback Sup"}

        @staticmethod
        def _compare_resolve_side_plot_editor_margins(
            _side_key: str,
        ) -> Dict[str, float]:
            """Return deterministic side margins that should become display baseline."""
            return {"left": 0.21, "right": 0.83, "top": 0.89, "bottom": 0.16}

        @staticmethod
        def _finalize_matplotlib_canvas_layout(**_kwargs: Any) -> None:
            """No-op finalize hook for harness render."""
            return None

        @staticmethod
        def _compare_update_side_status(_side_key: str, _message: str) -> None:
            """No-op side status update hook."""
            return None

        @staticmethod
        def _compare_update_status_chips() -> None:
            """No-op status-chip refresh hook."""
            return None

        @staticmethod
        def _compare_log_render_completion_event(_side_key: str) -> None:
            """No-op render-completion logging hook."""
            return None

        def _build_combined_triple_axis_from_state(self, **_kwargs: Any) -> Figure:
            """Capture compare layout profile payload used during render."""
            profile = dict(
                (settings.get("layout_profiles") or {}).get("fig_combined_triple_axis")
                or {}
            )
            self.layout_profile_snapshot = copy.deepcopy(profile)
            return Figure(figsize=(4.0, 2.8), dpi=100)

    harness = _Harness()
    UnifiedApp._compare_render_profile_side(
        harness,
        "A",
        reason="regression_layout_profile",
        prepared=({}, [], None, {}),
    )
    snapshot = harness.layout_profile_snapshot
    if not isinstance(snapshot, Mapping):
        raise AssertionError(
            "Expected compare render to capture a layout profile snapshot."
        )
    display_section = snapshot.get("display")
    export_section = snapshot.get("export")
    if not isinstance(display_section, Mapping) or not isinstance(
        export_section, Mapping
    ):
        raise AssertionError(
            "Compare layout profile must expose display/export sections."
        )
    display_margins = display_section.get("margins")
    if not isinstance(display_margins, Mapping):
        raise AssertionError(
            "Compare display layout profile must include margins mapping."
        )
    expected_margins = {"left": 0.21, "right": 0.83, "top": 0.89, "bottom": 0.16}
    for key, expected in expected_margins.items():
        actual = float(display_margins.get(key))
        if abs(actual - expected) > 1e-9:
            raise AssertionError(
                f"Expected compare display margin {key}={expected}, got {actual}."
            )


def _regression_test_compare_blank_title_fallback_resolution() -> None:
    """Validate Compare-side blank title/suptitle overrides fall back to defaults.

    Purpose:
        Ensure compare rendering auto-fills blank persisted title fields from
        profile identity defaults before drawing.
    Why:
        Blank overrides previously produced invisible titles and overlap artifacts.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Executes one compare render call against a local harness.
    Exceptions:
        Raises AssertionError when title fallback behavior regresses.
    """

    class _VarStub:
        """Minimal Tk-var stub for compare harness."""

        def __init__(self, value: Any) -> None:
            self._value = value

        def get(self) -> Any:
            """Return stub value."""
            return self._value

        def set(self, value: Any) -> None:
            """Assign stub value."""
            self._value = value

    class _CanvasStub:
        """Canvas stub allowing figure assignment by render path."""

        def __init__(self) -> None:
            self.figure = None

    class _Harness:
        """Harness capturing render args for title fallback assertions."""

        def __init__(self) -> None:
            self.compare_use_profile_layout_var = _VarStub(False)
            self.compare_plot_preset_var = _VarStub(DEFAULT_COMPARE_PLOT_PRESET_NAME)
            self._compare_custom_plot_presets = {}
            self._compare_layout_overrides = {}
            self._compare_panels = {
                "A": {
                    "canvas": _CanvasStub(),
                    "widget": object(),
                    "bundle": {
                        "profile_name": "Profile A",
                        "dataset_path": "C:/tmp/dataset.xlsx",
                        "args": tuple([""] * 24),
                        "plot_settings": {},
                        "plot_elements": {},
                        "layout_profiles": {},
                        "df_reference": object(),
                    },
                    "cycle_rows": [],
                    "total_drop": None,
                    "cycle_fallback_used": False,
                    "cycle_rows_synthesized": False,
                    "cycle_compute_backend": "",
                    "render_success": False,
                    "render_error_message": "",
                }
            }
            self._combined_plot_state = None
            self._combined_layout_state = None
            self._combined_layout_dirty = False
            self._combined_legend_anchor = None
            self._combined_legend_loc = None
            self.df = None
            self.captured_render_args: Tuple[Any, ...] = tuple()

        @staticmethod
        def _compare_parse_float_entry(_raw: Any) -> Optional[float]:
            """Return no-uptake sentinel for status formatting path."""
            return None

        @staticmethod
        def _compare_resolve_figsize_for_panel(_side: str) -> Tuple[float, float]:
            """Return deterministic render figsize for harness."""
            return (6.0, 3.5)

        @staticmethod
        def _compare_effective_pair_plot_elements_override() -> Dict[str, Any]:
            """Return blank side title payload to trigger fallback behavior."""
            return {
                "retain_profile_elements": True,
                "hide_text_family": False,
                "side_overrides": {"A": {"title_text": "", "suptitle_text": "  "}},
            }

        @staticmethod
        def _compare_profile_title_defaults(
            _side_key: str,
            _bundle: Optional[Mapping[str, Any]],
        ) -> Dict[str, str]:
            """Return deterministic fallback titles for compare-side rendering."""
            return {
                "title_text": "Fallback Profile Title",
                "suptitle_text": "Fallback Dataset SupTitle",
            }

        @staticmethod
        def _compare_resolve_side_plot_editor_margins(
            _side_key: str,
        ) -> Dict[str, float]:
            """Return deterministic side margins for compare render."""
            return {"left": 0.12, "right": 0.9, "top": 0.88, "bottom": 0.11}

        @staticmethod
        def _finalize_matplotlib_canvas_layout(**_kwargs: Any) -> None:
            """No-op finalize hook for harness render."""
            return None

        @staticmethod
        def _compare_update_side_status(_side_key: str, _message: str) -> None:
            """No-op side status update hook."""
            return None

        @staticmethod
        def _compare_update_status_chips() -> None:
            """No-op status-chip refresh hook."""
            return None

        @staticmethod
        def _compare_log_render_completion_event(_side_key: str) -> None:
            """No-op render-completion logging hook."""
            return None

        def _build_combined_triple_axis_from_state(self, **kwargs: Any) -> Figure:
            """Capture final render args used by compare-side render."""
            self.captured_render_args = tuple(kwargs.get("args") or ())
            return Figure(figsize=(4.0, 2.8), dpi=100)

    harness = _Harness()
    UnifiedApp._compare_render_profile_side(
        harness,
        "A",
        reason="regression_title_fallback",
        prepared=({}, [], None, {}),
    )
    if len(harness.captured_render_args) < 14:
        raise AssertionError(
            "Expected compare render args tuple to include title fields."
        )
    if str(harness.captured_render_args[12]) != "Fallback Profile Title":
        raise AssertionError("Expected compare render title to use fallback default.")
    if str(harness.captured_render_args[13]) != "Fallback Dataset SupTitle":
        raise AssertionError(
            "Expected compare render suptitle to use fallback default."
        )


def _regression_test_layout_health_compare_off_canvas_no_gap_shift() -> None:
    """Validate compare layout-health skips gap-target shifts for off-canvas-only issues.

    Purpose:
        Ensure `layout_health_autofix` only applies gap-target anchor movement when
        explicit gap issues are present in compare context.
    Why:
        Off-canvas-only detections previously drifted legend anchors due coupled
        gap-target logic, worsening compare whitespace behavior.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Temporarily monkeypatches layout-health artist lookup helpers.
    Exceptions:
        Raises AssertionError when compare off-canvas correction regresses.
    """

    class _AnchorStub:
        """Simple bbox-anchor stub exposing x0/y0 coordinates."""

        def __init__(self, x0: float, y0: float) -> None:
            self.x0 = float(x0)
            self.y0 = float(y0)

    class _LegendStub:
        """Legend stub capturing final anchor pair applied by autofix."""

        def __init__(self) -> None:
            self._anchor = _AnchorStub(0.5, -0.03)
            self.applied_anchor: Optional[Tuple[float, float]] = None

        def get_bbox_to_anchor(self) -> _AnchorStub:
            """Return deterministic starting anchor used by autofix."""
            return self._anchor

        def set_bbox_to_anchor(
            self,
            anchor: Tuple[float, float],
            transform: Any = None,
        ) -> None:
            """Capture adjusted anchor pair applied by autofix."""
            _ = transform
            self.applied_anchor = (float(anchor[0]), float(anchor[1]))

    legend_stub = _LegendStub()
    xlabel_stub = object()
    fig = Figure(figsize=(4.0, 4.0), dpi=100)
    FigureCanvasAgg(fig)

    original_primary_legend = globals().get("_layout_health_primary_legend")
    original_primary_xlabel = globals().get("_layout_health_primary_xlabel")
    original_bbox_fn = globals().get("_layout_health_bbox_in_fig")
    try:
        globals()["_layout_health_primary_legend"] = lambda _fig: legend_stub
        globals()["_layout_health_primary_xlabel"] = lambda _fig: xlabel_stub

        def _bbox_stub(
            _fig: Figure,
            artist: Any,
            _renderer: Any,
        ) -> Optional[Bbox]:
            """Return deterministic figure-space bboxes for legend/xlabel stubs."""
            if artist is legend_stub:
                return Bbox.from_extents(0.10, -0.03, 0.90, 0.05)
            if artist is xlabel_stub:
                return Bbox.from_extents(0.20, 0.09, 0.80, 0.12)
            return None

        globals()["_layout_health_bbox_in_fig"] = _bbox_stub
        result = layout_health_autofix(
            fig,
            "fig_combined_triple_axis",
            "display",
            {
                "layout_health_autofix_enabled": True,
                "layout_health_context": "compare",
                "layout_health_max_passes": 1,
            },
        )
    finally:
        if callable(original_primary_legend):
            globals()["_layout_health_primary_legend"] = original_primary_legend
        if callable(original_primary_xlabel):
            globals()["_layout_health_primary_xlabel"] = original_primary_xlabel
        if callable(original_bbox_fn):
            globals()["_layout_health_bbox_in_fig"] = original_bbox_fn

    issues = list(result.get("issues") or [])
    if "legend_off_canvas" not in issues:
        raise AssertionError(
            "Expected off-canvas legend issue in compare layout-health pass."
        )
    if "legend_xlabel_gap_high" in issues or "legend_xlabel_gap_low" in issues:
        raise AssertionError("Off-canvas-only scenario should not include gap issues.")
    if legend_stub.applied_anchor is None:
        raise AssertionError(
            "Expected compare layout-health to apply legend off-canvas correction."
        )
    fig_h_pts = max(float(fig.get_size_inches()[1]) * 72.0, 1.0)
    expected_y = -0.03 + min(0.12, abs(-0.03) + (2.0 / fig_h_pts))
    expected_y = max(-0.02, min(0.28, float(expected_y)))
    actual_y = float(legend_stub.applied_anchor[1])
    if abs(actual_y - expected_y) > 1e-6:
        raise AssertionError(
            f"Expected compare off-canvas correction y={expected_y:.6f}, got {actual_y:.6f}."
        )


def _regression_test_compare_plot_editor_margin_persistence_round_trip() -> None:
    """Validate pair+side Compare plot-editor margin persistence normalization.

    Purpose:
        Ensure `plot_editor_margins_by_pair` survives normalize/persist/load with a
        stable pair+side schema and clamped margin values.
    Why:
        Compare plot editor values must persist per pair without leaking or schema drift.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        None.
    Exceptions:
        Raises AssertionError when margin round-trip normalization regresses.
    """
    raw_state = {
        "plot_editor_margins_by_pair": {
            "Profile A||Profile B": {
                "A": {"left": 0.22, "right": 0.84, "top": 0.91, "bottom": 0.17},
                "B": {"left": "0.18", "right": "0.88", "top": "0.90", "bottom": "0.15"},
                "C": {"left": 0.0, "right": 1.0, "top": 1.0, "bottom": 0.0},
            },
            "bad-pair": {"A": {"left": 0.95, "right": 0.2, "top": 0.1, "bottom": 0.9}},
        }
    }
    normalized = _normalize_compare_tab_settings(raw_state)
    margins_by_pair = normalized.get("plot_editor_margins_by_pair")
    if not isinstance(margins_by_pair, Mapping):
        raise AssertionError(
            "Expected normalized compare state to include margin mapping."
        )
    pair_payload = margins_by_pair.get("Profile A||Profile B")
    if not isinstance(pair_payload, Mapping):
        raise AssertionError(
            "Expected persisted pair payload for Profile A||Profile B."
        )
    if "C" in pair_payload:
        raise AssertionError(
            "Unexpected non-A/B side key retained in normalized margin mapping."
        )
    side_a = pair_payload.get("A")
    side_b = pair_payload.get("B")
    if not isinstance(side_a, Mapping) or not isinstance(side_b, Mapping):
        raise AssertionError(
            "Expected both side A and B margin payloads after normalization."
        )
    if abs(float(side_a.get("left")) - 0.22) > 1e-9:
        raise AssertionError(
            "Expected side A left margin to persist normalized float value."
        )
    if abs(float(side_b.get("right")) - 0.88) > 1e-9:
        raise AssertionError(
            "Expected side B right margin to persist normalized float value."
        )
    round_trip = _normalize_compare_tab_settings(normalized)
    if round_trip.get("plot_editor_margins_by_pair") != margins_by_pair:
        raise AssertionError(
            "Expected compare margin mapping to remain stable on round-trip normalization."
        )


def _regression_test_compare_plot_editor_apply_rerenders_targeted_side_only() -> None:
    """Validate Compare plot-editor apply path rerenders only the targeted side.

    Purpose:
        Ensure `Apply + Rerender` updates one side margin payload and rerenders only
        that side while preserving lock-x synchronization.
    Why:
        Side-local editor actions should not trigger unnecessary rerenders on the
        opposite pane.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Executes `_compare_apply_side_plot_editor_margins` with local harness state.
    Exceptions:
        Raises AssertionError when side routing or rerender triggers regress.
    """

    class _Harness:
        """Harness capturing side-local apply/rerender behavior."""

        def __init__(self) -> None:
            self._compare_plot_editor_margins_by_pair: Dict[str, Any] = {}
            self._compare_panels = {
                "A": {"bundle": {"profile_name": "Profile A"}},
                "B": {"bundle": {"profile_name": "Profile B"}},
            }
            self.render_calls: List[str] = []
            self.lock_calls: List[str] = []
            self.diagnostics_calls = 0
            self.persist_calls = 0

        @staticmethod
        def _compare_default_plot_editor_margins() -> Dict[str, float]:
            """Return deterministic compare default margins for normalization."""
            return {"left": 0.125, "right": 0.9, "top": 0.88, "bottom": 0.11}

        @staticmethod
        def _compare_selected_pair_key() -> str:
            """Return deterministic pair key for harness persistence tests."""
            return "Profile A||Profile B"

        def _compare_persist_state(self) -> None:
            """Count compare persistence calls."""
            self.persist_calls += 1

        def _compare_store_side_plot_editor_margins(
            self,
            side_key: str,
            margins: Mapping[str, Any],
            *,
            persist_state: bool,
        ) -> None:
            """Delegate side margin storage to production helper."""
            UnifiedApp._compare_store_side_plot_editor_margins(
                self,
                side_key,
                margins,
                persist_state=persist_state,
            )

        def _compare_render_profile_side(
            self, side_key: str, *, reason: str = ""
        ) -> None:
            """Capture targeted side rerender invocations."""
            _ = reason
            self.render_calls.append(str(side_key))

        def _compare_apply_locked_x_axis(self, *, redraw_mode: str = "force") -> None:
            """Capture lock-x redraw mode used after targeted rerender."""
            self.lock_calls.append(str(redraw_mode))

        def _compare_refresh_diagnostics_panel(self) -> None:
            """Count diagnostics panel refresh calls."""
            self.diagnostics_calls += 1

    harness = _Harness()
    UnifiedApp._compare_apply_side_plot_editor_margins(
        harness,
        "A",
        {"left": 0.2, "right": 0.86, "top": 0.9, "bottom": 0.14},
        rerender_side=True,
        persist_state=True,
    )
    if harness.render_calls != ["A"]:
        raise AssertionError(
            f"Expected targeted rerender for side A only, got {harness.render_calls!r}."
        )
    if harness.lock_calls != ["idle"]:
        raise AssertionError(
            "Expected side-local apply path to request idle lock-x sync."
        )
    if harness.diagnostics_calls != 1:
        raise AssertionError(
            "Expected one diagnostics refresh after targeted rerender."
        )
    pair_map = _normalize_compare_plot_editor_margins_by_pair(
        harness._compare_plot_editor_margins_by_pair
    )
    pair_payload = pair_map.get("Profile A||Profile B")
    if not isinstance(pair_payload, Mapping):
        raise AssertionError("Expected persisted pair payload after side apply.")
    if "A" not in pair_payload:
        raise AssertionError("Expected targeted side A margins to persist after apply.")
    if "B" in pair_payload:
        raise AssertionError(
            "Unexpected side B margin payload created by side A apply."
        )
    if harness.persist_calls != 1:
        raise AssertionError("Expected one compare state persist call for side apply.")
