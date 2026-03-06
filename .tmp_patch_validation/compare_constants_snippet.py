from typing import Dict, Tuple

COMPARE_PLOT_PRESET_KEYS = ()
COMPARE_PLOT_EDITOR_MARGIN_KEYS: Tuple[str, ...] = ("left", "right", "top", "bottom")
COMPARE_COMBINED_TK_OVERRIDE_BINDINGS: Tuple[Tuple[str, str], ...] = (
    ("combined_legend_gap_pts", "combined_legend_label_gap"),
    ("combined_legend_bottom_margin_pts", "combined_legend_bottom_margin"),
    ("combined_xlabel_tick_gap_pts", "combined_xlabel_tick_gap"),
    ("combined_left_pad_pct", "combined_left_padding_pct"),
    ("combined_right_pad_pct", "combined_right_padding_pct"),
    ("combined_top_margin_pct", "combined_top_margin_pct"),
    ("combined_title_pad_pts", "combined_title_pad_pts"),
    ("combined_suptitle_pad_pts", "combined_suptitle_pad_pts"),
    ("combined_suptitle_y", "combined_suptitle_y"),
    ("combined_suptitle_fontsize", "combined_suptitle_fontsize"),
    ("combined_title_fontsize", "combined_title_fontsize"),
    ("combined_label_fontsize", "combined_label_fontsize"),
    ("combined_tick_fontsize", "combined_tick_fontsize"),
    ("combined_legend_fontsize", "combined_legend_fontsize"),
    ("combined_cycle_legend_fontsize", "combined_cycle_legend_fontsize"),
    ("combined_export_pad_pts", "combined_export_pad_pts"),
    ("combined_legend_wrap", "combined_legend_wrap"),
    ("combined_legend_rows", "combined_legend_rows"),
    ("combined_legend_alignment", "combined_legend_alignment"),
)
COMPARE_LAYOUT_PROFILE_SECTION_KEYS: Tuple[str, ...] = (
    "xlabel_pad_pts",
    "detached_spine_offset",
    "detached_labelpad",
)
COMPARE_LAYOUT_ANCHOR_KEYS: Tuple[str, ...] = (
    "combined_legend_anchor",
    "combined_legend_loc",
    "combined_cycle_legend_anchor",
    "combined_cycle_legend_loc",
    "combined_cycle_legend_anchor_space",
    "combined_cycle_legend_anchor_mode",
    "combined_cycle_legend_ref_dx_px",
    "combined_cycle_legend_ref_dy_px",
)
COMPARE_CYCLE_TABLE_VIEW_MODE_TOKENS: Tuple[str, ...] = ("standard", "tight", "fit")
COMPARE_CYCLE_TABLE_VIEW_MODE_LABELS: Dict[str, str] = {
    "standard": "Standard",
    "tight": "Tight",
    "fit": "Fit to Content",
}
