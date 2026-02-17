# GL-260 Data Analysis and Plotter (v3.0.9)

## Overview
GL-260 Data Analysis and Plotter is a single-script Tkinter + Matplotlib application for loading Graphtec GL-260 data from Excel or direct CSV import (processed into new Excel sheets), mapping columns, generating multi-axis plots, performing cycle analysis with moles calculations, and running solubility/speciation workflows. It also includes a contamination calculator and a configurable final report generator.

The main entry point is `GL-260 Data Analysis and Plotter.py`. The UI title and report metadata are driven by `APP_VERSION`, which reports `v3.0.9`.

## Table of Contents
- [Part I - Complete User Manual](#part-i---complete-user-manual)
  - [Program Overview and Philosophy](#program-overview-and-philosophy)
  - [Intended Audience](#intended-audience)
  - [Repository Layout](#repository-layout)
  - [Installation and Requirements](#installation-and-requirements)
  - [Running the Application](#running-the-application)
  - [Architecture and Data Flow](#architecture-and-data-flow)
  - [Quickstart Workflow (Linear)](#quickstart-workflow-linear)
  - [UI and Navigation Guide](#ui-and-navigation-guide)
  - [Plotting Architecture Details](#plotting-architecture-details)
  - [Plot Elements and Annotations System](#plot-elements-and-annotations-system)
  - [Combined Triple-Axis Plot Technical Documentation](#combined-triple-axis-plot-technical-documentation)
  - [Interactive Cycle Analysis - Scientific and Operational Guide](#interactive-cycle-analysis---scientific-and-operational-guide)
  - [Advanced Solubility and Equilibrium Engine](#advanced-solubility-and-equilibrium-engine)
  - [Final Report System - Export and PDF Assembly](#final-report-system---export-and-pdf-assembly)
  - [Preferences and Configuration System](#preferences-and-configuration-system)
  - [Performance and Developer Tools](#performance-and-developer-tools)
  - [Troubleshooting and FAQ](#troubleshooting-and-faq)
  - [Power User and Advanced Workflows](#power-user-and-advanced-workflows)
- [Known Limitations and Tradeoffs](#known-limitations-and-tradeoffs)
- [License](#license)
- [Part II - Changelog / Ledger](#part-ii---changelog--ledger)
  - [v3.0.9 Import Progress + Preview Element Sync + Shadowbox Color Controls](#v309-import-progress--preview-element-sync--shadowbox-color-controls)
  - [v3.0.8 Developer Tools Dialog Hub](#v308-developer-tools-dialog-hub)
  - [v3.0.7 Developer Tools and Diagnostics Expansion](#v307-developer-tools-and-diagnostics-expansion)
  - [v3.0.3 Process Profiles Plot Settings Retention](#v303-process-profiles-plot-settings-retention)
  - [v3.0.2 Plot Elements Editor Window Sizing Hardening](#v302-plot-elements-editor-window-sizing-hardening)
  - [v3.0.1 Startup Splash + Background Startup Orchestration](#v301-startup-splash--background-startup-orchestration)
  - [v3.0.0 Import CSV Dialog UX Refresh and Major Version Rollforward](#v300-import-csv-dialog-ux-refresh-and-major-version-rollforward)
  - [v2.13.1 Legend Drag Snap Offset Fix](#v2131-legend-drag-snap-offset-fix)
  - [v2.13.0 Plot Elements Close-Triggered Refresh Overlay](#v2130-plot-elements-close-triggered-refresh-overlay)
  - [v2.12.10 Core Overlay Adaptive Pass Targeting](#v21210-core-overlay-adaptive-pass-targeting)
  - [v2.12.9 Core Overlay Completion-Gated Refresh](#v2129-core-overlay-completion-gated-refresh)
  - [v2.12.8 Refresh Overlay Reappearance Across Plot Refreshes](#v2128-refresh-overlay-reappearance-across-plot-refreshes)
  - [v2.12.7 Adaptive Combined Refresh + Data-Tab CSV Shortcut](#v2127-adaptive-combined-refresh--data-tab-csv-shortcut)
  - [v2.12.6 Combined Axes Layering Enforcement](#v2126-combined-axes-layering-enforcement)
  - [v2.12.5 Cycle Marker Top-Layer Z-Order + Data Trace UX Clarity](#v2125-cycle-marker-top-layer-z-order--data-trace-ux-clarity)
  - [v2.12.4 Working Version Rollforward + Docs Sync](#v2124-working-version-rollforward--docs-sync)
  - [v2.12.3 Input Persistence + Async Speciation Overlay](#v2123-input-persistence--async-speciation-overlay)
  - [v2.12.2 Planning Timeline Persistence + Input Stability](#v2122-planning-timeline-persistence--input-stability)
  - [v2.12.0 Data Trace Settings + Combined Splash Hold](#v2120-data-trace-settings--combined-splash-hold)
  - [v2.11.13 Columns Per-Series Line Width Control](#v21113-columns-per-series-line-width-control)
  - [v2.11.12 Combined Splash Refresh Race Hardening](#v21112-combined-splash-refresh-race-hardening)
  - [v2.11.11 Combined Post-Draw Refresh Hook](#v21111-combined-post-draw-refresh-hook)
  - [v2.11.10 Combined Auto Refresh Scheduling Fix](#v21110-combined-auto-refresh-scheduling-fix)
  - [v2.11.9 Combined Auto Refresh Overlay Continuity](#v2119-combined-auto-refresh-overlay-continuity)
  - [v2.11.8 Combined Auto Refresh Second Pass](#v2118-combined-auto-refresh-second-pass)
  - [v2.11.7 Forced Refresh Finalize Before Reveal](#v2117-forced-refresh-finalize-before-reveal)
  - [v2.11.6 Async Display Settings Application](#v2116-async-display-settings-application)
  - [v2.11.5 Async Plot Rendering and Immediate Tabs](#v2115-async-plot-rendering-and-immediate-tabs)
  - [v2.11.4 Plot Tab Auto Refresh Overlay](#v2114-plot-tab-auto-refresh-overlay)
  - [v2.11.2 Combined Plot Auto Refresh Overlay](#v2112-combined-plot-auto-refresh-overlay)
  - [v2.11.1 Plot Preview Combined Legend Tracking Restore](#v2111-plot-preview-combined-legend-tracking-restore)
  - [v2.11.0 New Profile Workflow + Suptitle Label Update](#v2110-new-profile-workflow--suptitle-label-update)
  - [v2.10.2 README Restructure (User Manual First)](#v2102-readme-restructure-user-manual-first)
  - [v2.10.1 Final Report Preview Window Auto-Sizing](#v2101-final-report-preview-window-auto-sizing)
  - [v2.9.12 Combined Single-Pass Render](#v2912-combined-single-pass-render)
  - [v2.9.11 Combined Cycle Legend Anchor Space Persistence](#v2911-combined-cycle-legend-anchor-space-persistence)
  - [v2.9.10 Combined Cycle Legend Refresh Redraw](#v2910-combined-cycle-legend-refresh-redraw)
  - [v2.9.8 Combined Cycle Legend Persistence Apply](#v298-combined-cycle-legend-persistence-apply)
  - [v2.9.6 Combined Cycle Legend Tracking Debug](#v296-combined-cycle-legend-tracking-debug)
  - [v2.9.3 Combined Legend Isolation](#v293-combined-legend-isolation)
  - [v2.9.1 Combined Cycle Legend Controls](#v291-combined-cycle-legend-controls)
  - [v2.9.0 Combined Legend Persistence](#v290-combined-legend-persistence)
  - [v2.6.0 Final Report Tab Scrolling](#v260-final-report-tab-scrolling)
  - [v2.5.0 Final Report Pipeline Hardening](#v250-final-report-pipeline-hardening)
  - [v2.4.0 Performance and Responsiveness](#v240-performance-and-responsiveness)
  - [v2.3.0 Documentation Pass](#v230-documentation-pass)
  - [v2.2.0 Update Highlights](#v220-update-highlights)
  - [v2.1.1 Update Highlights](#v211-update-highlights)
  - [v2.1.0 Update Highlights](#v210-update-highlights)
  - [v2.0.4 Update Highlights](#v204-update-highlights)
  - [v2.0.3 Update Highlights](#v203-update-highlights)
  - [v2.0.2 Update Highlights](#v202-update-highlights)
  - [v2.0.1 Update Highlights](#v201-update-highlights)
  - [Legacy Change Highlights (v1.x and earlier)](#legacy-change-highlights-v1x-and-earlier)

## Part I - Complete User Manual

### Program Overview and Philosophy
GL-260 Data Analysis and Plotter is designed for reproducible, end-to-end analysis of GL-260 pressure and temperature datasets. The application emphasizes:
- Explicit column mapping and deterministic series construction.
- Transparent plot settings and auto-range controls to avoid hidden state.
- Cycle-aware analysis so derived metrics are always traceable to peak/trough markers.
- Consistent export and report pipelines so on-screen previews match final outputs.
- Scientific workflows that connect experimental data to solubility and equilibrium models.

### Intended Audience
- Chemists, process engineers, and researchers analyzing GL-260 pressure/temperature datasets.
- Advanced data analysts who need reproducible plotting and cycle-by-cycle gas uptake estimates.
- Users who need carbonate speciation, solubility, and contamination workflows tied to cycle data.

### Repository Layout
- `GL-260 Data Analysis and Plotter.py`: Main application script and UI.
- `solubility_models/`: Local package providing speciation constants, models, and the closed-system solver.
- `naoh_co2_pitzer_ph_model.py`: Optional NaOH-CO2 Pitzer/HMW model used by the advanced speciation engine.
- `pitzer.dat`: PHREEQC Pitzer database file used by the optional NaOH-CO2 Pitzer model.
- `settings.json`: Persistent user settings written at runtime (created/updated by the app).
- `assets/`, `data/`, `docs/`, `scripts/`: Supporting project folders (content varies by workflow).
- `requirements.txt` / `pyproject.toml`: Dependency and packaging metadata.

### Installation and Requirements
#### Python
- Python 3.10 or newer.

#### Required runtime dependencies
These modules are imported unconditionally at startup:
- `matplotlib`
- `numpy`
- `pandas`
- `openpyxl` (Excel reader for pandas)
- `great_tables` (used for timeline table export rendering)

#### Optional or feature-gated dependencies
- `scipy`: Enables SciPy peak detection and Van der Waals moles calculations. The app falls back to a built-in peak finder and disables VDW if SciPy is missing.
- `mplcursors`: The app attempts to import it; if missing, it continues without it.

#### Setup (typical)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If `great_tables` is not installed by your requirements workflow, install it separately so the app can start.

### Running the Application
From the repository root:
```powershell
python "GL-260 Data Analysis and Plotter.py"
```
The app reads and writes `settings.json` in the current working directory. Run from the repo root so the bundled `pitzer.dat` is discoverable by the NaOH-CO2 Pitzer model.

### Architecture and Data Flow
The application is a single Tkinter process with background workers for long-running steps. Core data flow is:

1. Load data on the Data tab (single sheet or stitched multi-sheet).
2. Map columns on the Columns tab.
3. Apply columns (build numeric series, compute auto ranges, prime cycle state).
4. Generate plots (Figure 1, Figure 2, Figure 3 cycle analysis, combined triple-axis).
5. Cycle analysis (detect peaks/troughs, compute moles, produce summary and figure).
6. Solubility/speciation workflows (legacy and advanced tabs).
7. Final report (compile selected figures, tables, and narratives into PDF/PNG).

Internally, the app stores the active data in:
- `self.df`: Active pandas DataFrame (single sheet or stitched).
- `self.sheet_dfs`: Per-sheet DataFrames in multi-sheet mode.
- Global series used by the plotting functions: `x`, `y1`, `y2`, `y3`, `z`, `z2`, plus `selected_columns`.

### Quickstart Workflow (Linear)
Required operational order (do not reorder):
Apply Columns -> configure auto-range axis settings + advanced automatic plot titling + Plot Settings -> Cycle Analysis (auto detect OR manual peak/trough assignment) -> generate Combined Triple-Axis Plot -> add plot elements/overlays -> export -> final report.

Follow this linear workflow from start to finish:

1. Load an Excel workbook on the Data tab.
2. Select the target sheet (single sheet) or build the included sheet order (multi-sheet).
3. Map columns on the Columns tab for pressure, temperature, derivative, and optional auxiliary channels.
4. Click Apply Column Selection and confirm the applied indicator is green.
5. Configure Plot Settings before any heavy analysis:
   - Open Axis Auto-Range Settings and choose which axes are allowed to update.
   - Set Axis Span Padding percent to add vertical breathing room.
   - Lock or auto-scale axes by updating min/max ranges as needed.
   - Configure plot styling (fonts, scatter settings, legend defaults) and layout preferences.
6. Configure advanced automatic plot titling:
   - Enable Auto-generate Title and review the Auto Title Preview.
   - Choose the Data Type and template placeholders.
   - Decide whether to copy the auto title to the manual title for lock-in.
7. Navigate to the Cycle Analysis tab:
   - Run automatic peak/trough detection with tuned prominence/distance/width.
   - OR use manual peak/trough assignment with the interactive markers.
   - Iterate until the cycle markers match the physical experiment.
8. Verify cycle metrics for consistency:
   - Delta-P per cycle.
   - Uptake moles (ideal and VDW when available).
   - Mean temperature per cycle.
   - Total uptake summary.
9. Generate the Combined Triple-Axis Plot only after cycle analysis is finalized.
10. Add plot elements and overlays (Plot Elements editor, cycle legend, annotations, spans).
11. Export plots using the configured DPI and output size profiles.
12. Generate the Final Report PDF so the report stitches exported figures in order.

Why this order is mandatory:
- Cycle markers feed directly into combined plot overlays and report content. If cycle analysis is not finalized, combined plot overlays and report summaries will be out of sync.

Common mistakes:
- Generating the combined plot before correcting cycle markers.
- Leaving axis auto-range unchecked for a critical axis, which locks a stale range.
- Skipping Apply Column Selection after changing column mappings.

Visual success indicators:
- The Apply Column Selection status indicator shows applied state.
- Auto Title Preview displays a resolved title or a clear fallback reason.
- Cycle markers appear on the cycle plot and update the summary text.
- Combined plot overlays and legends match the cycle markers.

Troubleshooting notes:
- If the combined plot looks clipped, check the Axis Auto-Range Settings and axis padding percent.
- If cycle metrics look inconsistent, rerun detection or manually adjust peak/trough placement.

### UI and Navigation Guide

#### Data Tab
Purpose: load Excel workbooks and select one or multiple sheets.

Key controls:
- Excel file entry, Browse..., and Rescan File.
- Mode: Single Sheet or Multiple Sheets.
- Single Sheet: select a sheet from a combo box, click Load Sheet Data, or click Import GL-260 CSV... to open the CSV import popup directly.
- Multiple Sheets:
  - "Available Sheets" list and "Included Sheets (ordered)" list.
  - Add >>, << Remove, Move Up, Move Down to control the stitched sequence.
  - Load Selected Sheets loads and stitches; Import GL-260 CSV... next to it opens the same CSV import popup.

Runtime behavior:
- Sheet names are read via `openpyxl` (read-only) with a pandas fallback.
- The selected file path and last sheet are persisted to `settings.json`.

#### GL-260 CSV Import (File menu or Data tab Import GL-260 CSV...)
Purpose: convert raw Graphtec GL-260 CSV exports into a new Excel sheet that matches the app's expected schema.

Workflow:
- Choose a raw GL-260 CSV file and a target Excel workbook.
- Provide a new sheet name and choose how to handle name conflicts (error, overwrite, or auto-suffix).
- Preview detected columns and map the GL-260 channels to Reactor/Manifold pressure and Internal/External temperature.
- Configure calculation settings:
  - Derivative source (default: Reactor Pressure).
  - Exponential smoothing dampening factor (default: 0.98).
  - Moving average window (default: 100 points).
- Import writes numeric values only (no Excel formulas) and freezes the header row.

Dialog behavior (`v3.0.0`):
- The settings area is now vertically scrollable to keep all sections reachable on shorter displays.
- `Import` and `Close` stay fixed in the footer and remain visible while scrolling.
- The Ignore columns selector uses a tighter listbox/scrollbar layout to reduce empty gray space and improve readability.
- During import execution, an indeterminate progress bar appears in the footer so long-running CSV imports show active progress feedback.

Output schema (fixed):
- Date & Time
- Elapsed Time (days / hours / minutes / seconds)
- Reactor Pressure (PSI)
- Manifold Pressure (PSI)
- External Reactor Temperature
- Internal Reactor Temperature
- First Derivative (delta-PSI/hour)
- Smoothed First Derivative
- First Derivative Moving Average

Settings persisted:
- Last CSV path and workbook path.
- Last sheet name and sheet conflict handling choice.
- Channel mapping and calculation defaults.

#### Multi-Sheet Stitching (Data + Columns)
When multi-sheet mode is enabled:
- A Date & Time column (selected on the Columns tab) is required.
- Each sheet is loaded into a working DataFrame and gets:
  - `__GL260_DATETIME__`: parsed datetime values.
  - `__GL260_ELAPSED_DAYS_STITCHED__`: elapsed time from the earliest timestamp.
  - `__GL260_ELAPSED_HMS__`: elapsed time formatted as `HH:MM:SS` (or `D HH:MM:SS`).
- Sheets are concatenated with a NaN separator row between them.
- The X column is automatically set to `__GL260_ELAPSED_DAYS_STITCHED__`.
- If any sheet lacks the Date & Time column, a warning is shown and those rows are NaN.

Elapsed time units (days/hours/minutes/seconds) are configurable in File -> Preferences -> Data & Columns....

#### Columns Tab
Purpose: map DataFrame columns to plotting and cycle-analysis roles.

Required:
- X-Axis (Elapsed Time, <unit>)
- Primary Y (Reactor, PSI)

Optional:
- Primary Y (Manifold, PSI) (y3)
- Secondary Y (Derivative) (y2)
- Temperature Trace (Internal) (z)
- Temperature Trace 2 (External) (z2)
- Date & Time (dt) required only for multi-sheet stitching

Per-series styling (for scatter/line plots):
- Size, Line Width (pt), Color, and Line Style controls appear for series that support scatter overrides.

Actions:
- Apply Column Selection (Columns tab + bottom action bar) triggers background series building and auto-range updates.
- Per-Sheet Column Mapping... opens a dialog to override the global column mapping per sheet (multi-sheet only).

#### Plot Settings Tab
Purpose: control plot ranges, axes, style, cycle detection parameters, and combined-plot settings.

Titles
- Suptitle (Job Information) (manual) and Title (manual) text fields.
- Auto-generate Title toggle:
  - When ON, manual Title is ignored during rendering; Suptitle (Job Information) remains manual.
  - Use Copy Auto Title -> Manual Title to explicitly overwrite the manual Title.
- Data Type combobox with Manage Types...:
  - Add/rename/delete/reorder types; no empty names or duplicates (case-insensitive).
  - At least one type is always preserved (fallback: "Reaction").
- Template string (default: `{type} Day {day_start}-{day_end} {date_start}-{date_end}`) with Edit... dialog and validation.
  - Supported placeholders: `{type}`, `{day_start}`, `{day_end}`, `{date_start}`, `{date_end}`, `{start_dt_iso}`, `{end_dt_iso}`, `{start_year}`, `{end_year}`.
- Auto Title uses:
  - Full dataset (Columns tab): uses the loaded dataset date range (NaT rows ignored in stitched data).
  - Current view range: attempts to map the visible x-range to datetime; if mapping is not possible, it falls back to full-dataset tokens.
- Day count mode:
  - Date diff (end-start): 1/13 -> 1/19 yields Day 1-6.
  - Inclusive (end-start+1): 1/13 -> 1/19 yields Day 1-7.
- Auto Title Preview shows the computed title (and notes when a fallback is used).

Ranges
- Time min/max, Pressure Y min/max, Temp Y min/max, Derivative Y min/max.

Axes
- Enable Temperature Axis (right axis on Figure 1).
- Enable Derivative Axis (right axis on Figure 2).
- Combined derivative axis offset (moves the detached derivative spine to avoid label collisions).

Axis Auto-Range Settings
- Auto-Axis Settings... (next to Refresh Axis Ranges) opens this dialog without applying new ranges.
- Open Axis Auto-Range Settings... to choose which axes auto-range tools update.
- Unchecked axes keep manual min/max values, even when Refresh Axis Ranges is used.
- Span Padding (%) expands Y ranges as a percentage of data span.

Cycle Analysis Parameters
- Automatic peak/trough detection toggle.
- Prominence, minimum distance, width, and minimum delta-P controls.
- Cycle temperature column selector (used to compute mean temperature between peak and trough).

Combined Plot Layout
- Combined Plot Layout Tuner controls margins, label padding, and combined axis spacing.
- Layout profiles are saved for display vs export to keep previews consistent with exports.

#### Data Trace Settings Dialog
Purpose: configure per-trace styling overrides that apply to all core plots, combined previews, and exports.

Where to find it:
- Open any generated plot tab and click Data Trace Settings... next to Plot Settings....

Controls (per trace):
- Color (picker + Clear)
- Marker style (combobox + Clear)
- Marker size (pt^2) (entry + Clear)
- Line style (combobox + Clear)
- Line width (pt) (entry + Clear)
- Z-order priority (Background / Normal / Foreground / Hero)
- Z-order numeric override (optional; supersedes Priority)
- Effective Z (read-only; live resolved z-order shown per row)

Inheritance behavior:
- Blank fields inherit existing defaults with no behavior change.
- Priority set to Inherit leaves the trace at its existing z-order.
- In the Combined Triple-Axis plot, cycle peak/trough markers are rendered on a dedicated overlay axis that is always above all data axes; Data Trace Settings z-order controls apply to traces only.

#### Combined Triple-Axis Plot Tab
Purpose: preview the combined plot, manage overlays, and export the triple-axis figure.

Key controls:
- Generate Plot and Refresh actions (from the bottom action bar).
- Generated plot tabs switch immediately and show a loading overlay with a determinate progress bar while background computation runs; the UI-thread render finishes the stabilized layout.
- Refresh operations now re-show the loading overlay and progress bar, and the refreshed plot is revealed only after refresh finalization completes.
- Close Plot removes the generated figure tab and returns focus to Plot Settings.
- Plot Elements editor for adding annotations and overlays.
- Export controls (PNG/SVG/PDF) with output size profiles and DPI.

Stabilization note:
Combined plots use adaptive refresh stabilization. A second pass is run only when pass-1 signals show material data/layout/plot-element changes plus geometry drift, while ambiguous signals fail closed to a second pass. The loading overlay remains visible until required passes complete and stabilization is confirmed, and the splash progress bar advances by render milestones until completion.

#### Cycle Analysis Tab
Purpose: detect cycles, compute moles, and interactively edit peak/trough markers.

Key actions:
- Automatic detection with SciPy (if available) or built-in fallback.
- Manual editing: Shift + left-click to add a peak, Shift + right-click to add a trough, right-click to remove nearest marker.
- Undo/redo, marker import/export, summary copy, and per-cycle CSV export.

Outputs:
- Summary text (inputs used, gas model inputs, gas uptake totals, per-cycle metrics).
- Cycle statistics table (per-cycle metrics).
- Cycle plot (Figure 3: Cycle Analysis).

#### Contamination Calculator Tab (optional)
Purpose: estimate Na2CO3 contamination and CO2 required to reach target pH.

Core inputs:
- Sample pH, NaOH pellet mass, NaOH purity, temperature, final volume, pKa2.
- Optional CoA carbonate (Na2CO3 wt%).

Equilibrium options (optional):
- Slurry pH override.
- pKa1, Henry constant, pCO2.
- Solubility caps for HCO3- and CO3^2-.
- Iteration limits and tolerance.

Outputs:
- Carbonate speciation and Na2CO3 contamination mass.
- CO2 required to reach target pH.
- Optional SLE and CO2 diagnostics.

Export:
- Save Summary PNG for the contamination summary.

#### Legacy Speciation Tab (tab label: "Legacy Speciation Tab")
Purpose: run solubility and speciation analysis using Debye-Huckel or related models.

Key elements:
- Speciation Model selector (Debye-Huckel, Davies, Pitzer-lite, etc.).
- Simulation Basis (mode-specific guidance, assumptions, and steps).
- Input helpers and checklists for required fields.
- pH sweep settings.
- Run and export controls:
  - Run Solubility Analysis
  - Export Summary PNG
  - Copy Summary
  - Export CSV
  - Export JSON
  - Send to Contamination

Outputs and panels:
- Highlights and narrative summary.
- Species table (concentrations, moles, fractional carbon).
- Saturation indices and ionic strength.
- Sensitivity analysis table.
- pH sweep table and plot.
- Math and glossary viewers.

#### Advanced Speciation and Equilibrium Engine
Purpose: guided workflows for planning, analysis, and reprocessing with cycle integration.

Workflow structure:
- A notebook with Planning, Analysis, and Reprocessing tabs.
- Each workflow has its own input form, guidance text, and output summary.
- Workflow state (inputs and cycle payloads) is persisted per workflow.

Cycle integration:
- Cycle payloads can be imported from the Cycle Analysis tab.
- Manual CO2 or NaOH inputs can be used if no cycle data exists.
- Cycle payloads are stored per workflow so planning and analysis runs remain independent.

Outputs:
- Structured highlights, warnings, and assumptions.
- Species tables, saturation tables, sensitivity analysis, and pH sweep plots.
- Cycle speciation timeline (per-cycle pH and speciation results).
- Timeline plot and timeline table with export options.

Exports:
- CSV and JSON outputs for species and timeline data.
- Planner narrative, CO2 guidance, and math preview exported as PNG.
- Timeline table export (PDF/PNG) with orientation and ACS-quality options.
  - Uses `great_tables` for PDF/PNG rendering.
  - Includes a fallback path when table rendering fails.

#### Final Report Tab
Purpose: assemble a multi-section report using plots, tables, and text outputs.

Key controls:
- Final report title.
- Combined plot title override (report-only).
- Template management (Save As Template, Update Template, Delete Template).
- Generate Final Report... (always visible) prompts for PDF/PNG/Both and uses the existing report generators.
- Layout mode:
  - `single_page_portrait`
  - `mixed_pages`
  - `plots_landscape_pages`
- Fit mode:
  - Preserve Export Layout (default)
  - Report Layout (legacy)
- Safe margins preset: Normal / Extra-Safe.
- Typography: font scale, margins, page numbers, section headers.
- Table style preset: Compact / Normal / Large.
- Per-section toggles: Include Section Header, Include Caption, Caption Placement (Same Page / Next Page).
- Section selection and ordering.
- Preview actions: Open Preview Window, Render Selected Page Preview, Update Layout Preview.

Report sections (examples):
- Figure 1 / Figure 2
- Combined Triple-Axis Plot (Preserve Export Layout reuses export rendering; Report Layout uses report layout fit)
- Cycle Analysis Summary
- Cycle Statistics Table
- Cycle Speciation Timeline Table
- Predicted pH Callouts
- CO2 Dosing Guidance
- Planner Narrative
- Key Metrics Summary
- Solubility Summary
- Math Details

Combined Triple-Axis Plot is included by default; older settings are auto-migrated to include it in selected sections.
Cycle Analysis plot and Cycle Speciation Timeline plot are interactive-only and excluded from Final Report exports.

Export:
- PDF/PNG with export DPI and output size profiles.
- PDF output stitches exported PDF artifacts per section in the selected order (deterministic).
- Fit Mode controls how complex plots are rendered:
  - Preserve Export Layout embeds the export render into the report page.
  - Report Layout uses the report layout solver and axes-fit placement.
- Combined Triple-Axis Plot failures block generation unless you opt into a degraded report.
- Final Report generation requires applied columns; pending column application blocks export.
- Captions can render on the same page or a dedicated caption page; figure/table numbers are independent of page numbers.
- Tables are centered, wrapped, and styled with presets to prevent overlap or clipping.

Settings keys (settings.json):
- `final_report.fit_mode`: "Preserve Export Layout" (default) or "Report Layout (legacy)".
- `final_report.safe_margin_preset`: "Normal" (default) or "Extra-Safe".
- `final_report.table_style_preset`: "Normal" (default), "Compact", or "Large".
- `final_report.section_header_enabled`: per-section header toggle map.
- `final_report.section_caption_enabled`: per-section caption toggle map.
- `final_report.section_caption_placement`: per-section caption placement map ("Same Page" / "Next Page").

#### Menus, Preferences, and Tools
File
- Open Excel, Rescan File, Import GL-260 CSV, Save Settings, Font Family..., Exit.

File -> Preferences
- Show/hide optional tabs.
- Tab Layout (order and visibility).
- Data & Columns (elapsed time unit).
- Show solubility input helper.
- Auto-jump to Plot tab after Apply.
- Scatter Plot Settings (marker, size, color, alpha, edge color, line width).
- Cycle Analysis Plot Settings (trace line color/style/width, peak/trough colors, marker shapes, marker size in pts^2).
- Saved Output Options (export DPI and output size profiles).
- Combined Axis Settings.
- Axis Auto-Range Settings.
- Optimize Layout for Current Display.
- Run Solubility Regression.

View
- Zoom in/out/reset.
- Zoom presets.

Tools -> Developer Tools...
- Unified dialog hub for debug logging/category controls and performance diagnostics.
- Free-threading & GIL controls (separate dialog launched from hub).
- Dependency free-threading audit (separate dialog launched from hub).
- Concurrency controls for background tasks (inline in hub Runtime/Advanced tab).
- Validate timeline table export and regression checks (launched from hub).

### Plotting Architecture Details

#### Figures
- Figure 1: Pressure (y1/y3) vs time, optional temperature axis (z/z2) on the right.
- Figure 2: Pressure (y1/y3) vs time, optional derivative axis (y2) on the right.
- Figure 3: Cycle analysis plot with peaks/troughs.
- Combined Triple-Axis: Single figure with three Y axes (inner left, inner right, outer right).

#### Axis and title handling
- Axis ranges are applied from Plot Settings or auto-refresh.
- Tick locations can be automatic or manual per axis.
- Titles and suptitles are centered on the union of visible axes so multi-axis plots stay aligned.
- Axis labels are derived from the selected column names and normalized (underscores removed for display).
- Plot fonts use a preferred Matplotlib serif stack (defaulting to `STIXGeneral` when available) with fallbacks; the optional Font Family... setting overrides the plot font family.

#### Scatter vs line rendering
- Global scatter settings live in the Scatter Plot Settings dialog.
- Per-series overrides (size, line width, color, line style) are set on the Columns tab.
- Scatter settings apply to Figures 1/2/3 and the combined plot.

#### Legend handling
- Legends are created per figure and are draggable when enabled in Plot Settings.
- Legends omit datasets that are set to None in the Columns tab.
- Cycle legends can be added to core plots when enabled.
- Combined triple-axis cycle legend anchors persist across refresh/regeneration (when enabled) and are reused for export preview and final exports; main legends re-center on rebuild.
- Center Plot Legend affects only the main legend; cycle legend placement is independent and is never captured by main-legend logic.
- Manual main-legend drags (when enabled) are session-only and do not disable Center Plot Legend.
- Plot Settings -> Cycle Legend (Combined Plot) provides Enable Dragging, Lock Position, Persist Position, Reset Position, and Clamp-on-capture controls.

#### Combined cycle legend placement
- The combined triple-axis cycle legend supports axis-relative placement with fixed pixel offsets.
- A reference axis (main/right/deriv) and reference corner define where the offsets are measured from.
- Placement is preserved across the main window, export preview, and final exports when persistence is enabled.
- Anchor space (figure vs axes) is preserved when reapplying user-dragged cycle legend positions.
- Workflow: Enable Cycle Legend Dragging -> drag the legend -> keep Persist Cycle Legend Position ON to retain placement across Refresh/Rebuild; Lock Cycle Legend Position disables dragging without hiding the legend; Reset Cycle Legend Position clears stored offsets and returns to defaults.
- Clamp Cycle Legend Inside Axes on Capture keeps stored positions within the visible axes bounds.
- Legacy combined cycle legend anchors are automatically migrated to the axis-offset model on first render.

#### Combined cycle legend persistence debug verification
Use the terminal debug output to confirm that drag-release capture and persistence are wired correctly:
- Generate the Combined Triple-Axis plot and confirm:
  - `DEBUG: legend tracking canvas type=FigureCanvasTkAgg id=...`
  - `DEBUG: connect button_release_event cid=...`
- Click anywhere in the plot and confirm:
  - `DEBUG: button_release_event fired fig_id=... x=... y=... inaxes=...`
- Drag the cycle legend and release; confirm:
  - `DEBUG: button_release_event fired fig_id=...`
  - `DEBUG: Combined cycle legend capture source=drag ...`
- Click Refresh, then click in the plot again; confirm the canvas identity and cids are re-printed and the button-release debug line fires.
- With Persist Cycle Legend Position enabled and stored offsets present, `source=auto` capture should not appear; only `source=drag` commits new offsets.

### Plot Elements and Annotations System
Plot annotations are stored per plot in `settings.json` and rendered on top of figures.

Supported element types:
- Text
- Callout
- Arrow
- Point
- X-span
- Span + Label
- Box Region (rectangle)
- Reference Line (vertical or horizontal)
- Ink (freehand line)

Key behaviors:
- Each element has an ID, name, visibility flag, lock flag, z-order, style, and geometry.
- Elements can be attached to data coordinates (move with pan/zoom) or axes coordinates (fixed to plot frame).
- Elements can target the primary, right, or third axis in multi-axis plots.
- Axis-based legacy elements are automatically migrated into data coordinates.
- Elements are applied both to on-screen figures and to exported PNG/PDF/SVG outputs.
- Plot Elements controllers are rebound on figure swaps (Refresh, preview/export) so selection/dragging remains active.
- Closing the Plot Elements window triggers a one-shot plot refresh through the shared Refresh pipeline, including the loading splash and determinate progress bar until refresh completion.
- Persisted Plot Elements editor geometry is normalized on open so restored size/position stay on-screen after monitor or layout changes.
- Plot Elements editor pane sizing defaults are hardened to keep controls visible and reduce cramped split-pane states on smaller displays.
- Element placement uses a dedicated Plot Elements editor with:
  - Add Element controls (type, axis, coordinate space) with explicit Place on Plot arming and status hints.
  - Color, transparency, and label presets.
  - Live update toggle for immediate redraw plus apply/revert/undo/redo for edits.

Persistence:
- `settings["plot_elements"]` stores element lists per plot ID.
- `settings["annotations_ui"]` stores per-plot UI state (collapsed state, last mode, add defaults, live update).

### Combined Triple-Axis Plot Technical Documentation

#### 1) Conceptual Overview
The combined triple-axis plot unifies pressure, temperature, and derivative or auxiliary traces in a single figure. It exists to show cycle context, pressure changes, temperature response, and derived behavior in one aligned timeline, enabling direct interpretation of cycle structure and thermal response without cross-plot alignment errors.

Rendering Behavior:
- Display renders for the combined plot defer until the canvas reports stable geometry so the first visible draw uses final DPI/size and persisted legend anchors.
- Auto-refresh runs two forced refresh passes (using the Refresh path) before the loading overlay is cleared to fully settle margins and layout.
- A loading cursor is shown and render controls are disabled while the combined plot finalizes.

#### 2) Axis Architecture
- X axis: elapsed time (stitched when multi-sheet mode is enabled).
- Left Y axis: primary pressure (y1) and optional manifold pressure (y3).
- Right Y axis: temperature traces (z/z2).
- Detached right Y axis: derivative or auxiliary channel (y2) with configurable offset.
- Combined layering is enforced at the Axes level from active trace priorities: left/right/third axis z-order is resolved dynamically, a dedicated top overlay axis carries cycle markers, and the derivative `y=0` dashed line is rendered on the overlay layer so it stays above X-span elements.

#### 3) Axis Range Control System
- Auto-range tools pull min/max from current data only for the axes enabled in Axis Auto-Range Settings.
- Unchecked axes keep the manual min/max you enter, which effectively locks that axis.
- Span Padding (%) expands Y ranges around the data span to prevent clipping.
- Refresh Axis Ranges applies the current auto-range settings without altering manual ranges for locked axes.

#### 4) Interactive Plot Elements
- Cycle markers and trough markers are drawn from the Cycle Analysis state.
- Region shading and annotations are layered with configurable z-order so overlays do not hide data.
- Legends (main and cycle) are draggable and persist across preview and export.
- Plot Elements provide additional overlays (text, callouts, spans, reference lines, and freehand marks).

#### 5) Automatic Title Generation System
- Titles can be auto-generated at render time using the Auto Title system in Plot Settings.
- Metadata inputs: Data Type, dataset date range (full dataset or current view range), and day-count mode.
- Formatting rules: template placeholders are resolved to dates, day spans, and ISO strings.
- Overrides: Copy Auto Title -> Manual Title captures the computed title for manual edits.
- Example outputs:
  - Reaction Day 1-6 2026-01-13 - 2026-01-19
  - Reaction Day 3-5 2026-02-10 - 2026-02-12

#### 6) Export and Layout Pipeline
- Preview rendering favors responsiveness, while export rendering rebuilds figures for deterministic output.
- Plot Preview supports drag edits for existing Plot Elements on the Combined plot; committed positions are synced back to the display plot when preview closes, while Combined legend drag behavior remains unchanged.
- Output DPI and size profiles are applied uniformly across plot exports.
- Combined plot exports are reused by the Final Report when Preserve Export Layout is selected.
- Layout profiles ensure consistent margins and legend placement across preview and export.

### Interactive Cycle Analysis - Scientific and Operational Guide

#### 1) Physical Meaning of Cycles
A cycle is defined as a pressure peak followed by a trough, representing a gas uptake event. Cycle metrics map directly to uptake and conversion estimates, so accurate peak/trough placement is required for valid downstream analysis and reporting.

#### 2) Automatic Detection Algorithm
- Peak/trough detection uses `scipy.signal.find_peaks` when SciPy is available.
- A built-in peak finder is used when SciPy is missing.
- Key parameters:
  - Prominence: suppresses noise-driven peaks.
  - Minimum distance: enforces spacing between cycles.
  - Width: avoids narrow spikes.
  - Minimum delta-P threshold: filters low-amplitude cycles.

#### 3) Manual Editing System (Manual Peak/Trough Assignment)
Manual editing is an integral workflow and is required when automatic detection is insufficient.

Manual assignment workflow:
- Shift + left-click: add a peak marker.
- Shift + right-click: add a trough marker.
- Right-click (no shift): remove the nearest marker.
- Disable automatic detection to operate in manual-only mode.
- Use undo/redo to step through marker edits.
- Import/export marker sets to reuse curated cycles across sessions.

Edge cases and guidance:
- Overlapping cycles: delete extra markers and reassign peak/trough pairs in order.
- Noisy derivatives: increase prominence or switch to manual-only placement.
- Temperature drift segments: use manual placement to avoid false cycles.

Refresh and verification:
- After marker edits, refresh the Cycle Analysis summary to recompute metrics.
- Confirm that delta-P and uptake totals match expected experimental trends.

#### 4) Cycle Analytics Outputs
- Delta-P per cycle (PSI to atm conversion is applied for moles calculations).
- Uptake moles (ideal gas and Van der Waals when SciPy is available).
- Mean temperature per cycle from the selected cycle temperature column.
- Total uptake and optional conversion estimates when starting material inputs are configured.

#### 5) Cycle Visualization (Figure 3)
- The Cycle Analysis plot shows pressure with peak/trough markers and per-cycle overlays.
- Marker and legend styling is configured in Cycle Analysis Plot Settings.
- The Cycle Analysis plot is interactive-only and is excluded from Final Report exports.

### Advanced Solubility and Equilibrium Engine

#### 1) Purpose
The Advanced Solubility and Equilibrium Engine models CO2 dissolution, carbonate/bicarbonate speciation, and pH evolution with cycle-aware inputs. It is designed to connect experimental uptake cycles to equilibrium outputs and planning scenarios.

#### 2) Physical and Chemical Models
- Ideal gas and Van der Waals models for uptake calculations.
- Henry's law for CO2 dissolution into solution.
- Carbonate and bicarbonate equilibria with charge balance.
- Stoichiometric progression models for reaction planning and projection.
- Optional NaOH-CO2 Pitzer (HMW/PHREEQC-style) model when `naoh_co2_pitzer_ph_model.py` and `pitzer.dat` are available.

#### 3) Computational Workflow
- Choose a workflow tab: Planning, Analysis, or Reprocessing.
- Provide solution inputs (mass, volume, temperature, pH targets, headspace conditions).
- Import cycle payloads or manually enter CO2/NaOH inputs.
- Run the solver to generate speciation, pH, and saturation metrics.
- As of `v2.12.3`, manual Analysis CO2 charged values are preserved, Planning NaOH inputs persist after runs, and heavy solver work is executed asynchronously.

#### 4) Visualization Outputs
- Species concentration plots and saturation summaries.
- pH sweep curves and speciation tables.
- Cycle speciation timeline plots and tables.
- Planning workflow timeline plots include a draggable legend that retains its placement across redraws and exports.
- Planning workflow inputs persist after each run; NaOH mass and related fields remain unchanged.
- Analysis workflow preserves manual CO2 charged entries; cycle auto-fill occurs only when the field is blank.
- Speciation solver runs asynchronously with a loading overlay so the tab remains responsive.
- Headspace/solution partitioning summaries for CO2 uptake.

#### 5) Experimental Use Cases
- Compare cycle-derived uptake to predicted dissolved CO2 capacity.
- Validate pH trajectory against expected equilibrium states.
- Generate planning guidance for dosing or reaction completion targets.

### Final Report System - Export and PDF Assembly
The Final Report system assembles a multi-section report using exported plot artifacts and configured tables.

Report pipeline:
- Uses export-grade plots and tables for deterministic output.
- Stitches PDF artifacts per section in the selected order.
- Reuses the combined plot export when Preserve Export Layout is selected.
- Live Final Report preview uses preview-only DPI scaling and opens at a page-sized, screen-clamped centered window for faster visual review.

Section ordering and inclusion:
- Section selection and ordering are state-driven and persisted in settings.
- Each section can independently enable headers and captions, with Same Page or Next Page caption placement.
- Combined Triple-Axis Plot is always appended when generation succeeds.

PDF assembly behavior:
- Layout mode controls page orientation and plot placement.
- Fit mode chooses between Preserve Export Layout and legacy Report Layout.
- Tables are centered and wrapped with style presets to prevent overlap.

### Preferences and Configuration System

#### Preferences
Use File -> Preferences to configure:
- Optional tab visibility and tab order.
- Data and column defaults (elapsed time units).
- Scatter plot styling and cycle plot marker styling.
- Output DPI and size profiles for exports.
- Combined axis settings, axis auto-range settings, and layout tuning.
- UI scaling and Optimize Layout for Current Display.

#### Settings Persistence and Restoration
The app persists state to `settings.json` in the working directory.

Load behavior:
- If `settings.json` is missing, defaults are used.
- If the file is corrupt, it is moved to `settings.json.corrupt-<timestamp>` and defaults are used.

Save behavior:
- Uses a temporary file and atomic replace for durability.

Key persisted categories:
- Data loading: `last_file_path`, `last_sheet_name`, multi-sheet selection.
- Column mapping: global column map, per-sheet overrides.
- Plot settings: ranges, ticks, axis toggles, titles.
- Scatter settings and per-series overrides.
- Cycle analysis settings and manual marker edits.
- Combined axis labels, offsets, and layout spacing.
- Layout profiles (per-plot display/export margins, title/suptitle positions, legend anchors/loc, axis label padding).
- Output profiles, export DPI, and final report settings.
- Plot elements and annotation UI state.
- Tab visibility and tab order.
- Window geometry and UI font scaling.

#### Process Profiles
Process Profiles store and restore full workspace snapshots, including dataset selection (optional), sheet selection, column mappings, plot settings/elements, layout tuning, and final report configuration. Access the manager via Profiles -> Manage Profiles....

Profiles are stored in `profiles/` as `profiles/<profile_name>.json`. The manager supports Save Current As..., Load, Overwrite, Rename, Delete, Export, and Import. Export writes the selected profile to a JSON file; Import brings a JSON profile into the `profiles/` folder.

Use New Profile to start a clean workspace without inheriting prior dataset or plot state. New Profile clears the workspace to startup defaults, then opens a single configuration dialog that captures:
- Profile name
- Suptitle (Job Information)
- Gas Model preset (VDW)
- Vessel volume
- VDW a and b
- Gas molar mass
- Starting material preset
- Starting material molar mass
- Starting material mass
- Stoichiometric ratio

New Profile also supports an optional `Keep plot settings for New Profile` flow (enabled by default in Process Profiles). When enabled, New Profile still resets to a clean workspace baseline, then reapplies retained plot settings and layout profiles.

Retained scope for `Keep plot settings for New Profile`:
- Plot settings
- Layout profiles

Not retained scope for `Keep plot settings for New Profile`:
- Plot elements
- Annotation UI state

The Include dataset file path option determines whether the Excel path is saved with the profile. If a profile does not include a path (or the file is missing), the app prompts you to relink the dataset before loading. This option is independent from `Keep plot settings for New Profile`. New Profile saves a dataset-optional profile that loads without a relink prompt. The current workspace is auto-backed up to `profiles/_autosave_last_workspace.json` before a profile load.

#### Saved Output Profiles and Export Sizes
Export functions are unified by shared output size profiles and DPI settings.

Output sizes are controlled by Preferences -> Saved Output Options.... Profiles support:
- Auto sizing (inherit figure size).
- Fixed sizes (inches or pixels).
- Aspect-ratio constrained sizes.

Default output profiles include (keys shown as stored in `settings.json`):
- `plot_export`: General Plot Exports
- `cycle_summary_png`: Cycle Analysis Summary PNG
- `solubility_summary_png`: Advanced Solubility Summary PNG
- `sol_planner_narrative_png`: Planner Narrative PNG
- `sol_co2_guidance_png`: CO2 Guidance PNG
- `sol_math_preview_png`: Math Preview PNG
- `sol_math_detail_export`: Detailed Math Viewer Export
- `final_report_png`: Final Report PNG
- `contamination_summary_png`: Contamination Summary PNG

### Performance and Developer Tools
The app keeps the UI responsive with a dedicated task runner:

- `TkTaskRunner` owns a thread pool and enforces "latest task wins" per task name.
- Results and errors are marshaled back to the Tk event loop via `after`.
- Used for column application, cycle analysis, solubility solver runs, and diagnostics.

Developer tools (Tools -> Developer Tools...) provide:
- Logging & Debug tab with global toggles and immediate-apply behavior.
- Debug category search/filter plus bulk actions (`Enable All`, `Disable All`).
- Dump Debug Settings, Clear Debug Once-Guards, and Dump Performance Stats actions.
- Performance Diagnostics tab with stage-level timings (data prep, cycle context, combined render, embed).
- Runtime / Advanced tab for concurrency controls and advanced tool launch buttons.
- Free-threading & GIL controls, dependency free-threading audit, regression checks, and timeline table export validation via dedicated dialogs/actions launched from the hub.

#### Debug Logging and Performance Stats
The debug/logging framework is centralized and off by default. Use the following workflow:

1) Open Tools -> Developer Tools..., then enable `Enable Debug Logging`.
2) In Logging & Debug, use category filter and `Enable All`/`Disable All` or per-category toggles.
3) Optional: Enable `Enable Debug File Logging` to capture logs in `gl260_debug.log`.
4) Use Dump Debug Settings to verify active categories, and Clear Debug Once-Guards to re-emit one-shot logs.
5) Use Dump Performance Stats to view aggregated timing/counter metrics.

Initial debug categories:
- Core/Infrastructure: `ui.events`, `cache.render`, `perf.timing`
- Plotting: `plotting.render`, `plotting.layout`, `plotting.legends`
- Cycle Analysis: `cycle.analysis`, `cycle.interaction`
- Final Report: `report.build`, `report.figures`, `report.export`
- Speciation Engine: `speciation.engine`, `speciation.solver`, `speciation.chemistry`, `speciation.results`
- IO: `io.excel`, `io.files`

Performance stats are aggregated (count/total/min/max/last) and gated behind `perf.timing` (or the relevant subsystem category). These include combined plot build/refresh, render cache hits/misses, cycle analysis compute, final report build/export, and speciation solver timing.

Warnings:
- Free-threading and concurrency tuning are expert tools. Changing defaults can impact stability or responsiveness and should be tested on representative datasets.

### Troubleshooting and FAQ
- Symptom: Plots look clipped or axes do not update. Cause: Axis auto-range is disabled for that axis or padding is too small. Fix: Review Axis Auto-Range Settings and Span Padding (%) in Plot Settings.
- Symptom: Combined plot is missing cycle overlays. Cause: Cycle analysis has not been finalized or automatic detection is disabled without manual markers. Fix: Run cycle detection or manually assign peaks/troughs, then regenerate the combined plot.
- Symptom: Combined X-span highlight appears to cover reference guides. Cause: The derivative `y=0` dashed line now renders on the combined overlay layer by design. Fix: Adjust span opacity/color if visual contrast is needed; the `y=0` line should remain above spans.
- Symptom: Cycle detection is noisy or misses cycles. Cause: Prominence/distance/width thresholds are too low or data is noisy. Fix: Adjust detection settings or switch to manual-only placement.
- Symptom: Final Report generation fails. Cause: Combined plot export failed or columns are not applied. Fix: Apply columns, regenerate combined plot export, then rerun the report.
- Symptom: VDW moles are not shown. Cause: SciPy is not installed. Fix: Install SciPy or rely on ideal gas metrics.
- Symptom: Timeline table export fails. Cause: `great_tables` not installed or rendering error. Fix: Install `great_tables` and retry; use fallback output if prompted.
- Symptom: Settings reset unexpectedly. Cause: `settings.json` is corrupt. Fix: Check for `settings.json.corrupt-*` and reconfigure settings.

### Power User and Advanced Workflows
- Multi-sheet stitching for long experiments: ensure Date & Time is mapped consistently and use per-sheet column mapping when schemas vary.
- Long-run analysis: use auto-range settings carefully and consider manual axis locks when comparing segments.
- Batch export: configure output profiles and export DPI once, then export multiple plots in sequence.
- Automated reporting: export plots first, then run Final Report generation to reuse export renders.
- Cycle analysis curation: auto-detect, manually correct peaks/troughs, validate metrics, then lock in combined plot overlays.
- Profile-based workflows: use Process Profiles to capture and reuse full analysis setups across datasets.

### Known Limitations and Tradeoffs
- Excel workbooks remain the canonical data source; raw Graphtec GL-260 CSV imports are supported via the dedicated import dialog only.
- Multi-sheet stitching inserts NaN separator rows, which can affect downstream calculations if not accounted for.
- Cycle detection quality depends on user-defined prominence/distance/width parameters.
- Van der Waals moles require SciPy; without it, only ideal gas totals are computed.
- The NaOH-CO2 Pitzer model is optional and requires a valid `pitzer.dat`.
- Large datasets are loaded fully into memory.

### License
Apache-2.0. See `LICENSE`.

## Part II - Changelog / Ledger

### v3.0.9 Import Progress + Preview Element Sync + Shadowbox Color Controls
- Added an indeterminate progress bar to the `Import GL-260 CSV` dialog footer so imports show active work instead of appearing frozen.
- Combined `Plot Preview` now supports dragging existing Plot Elements, and committed preview positions are synchronized back to the live Combined display plot when preview closes.
- Extended Plot Elements text-style controls with color pickers for `BBox Edge` (shadowbox outline) and `Shadow Color` (`bbox_shadow_color`) used by `BBox Shadow`.
- Bumped application version metadata to `v3.0.9` in the script header and `APP_VERSION`.

### v3.0.8 Developer Tools Dialog Hub
- Reworked Developer Tools into a unified dialog hub to avoid one-by-one menu toggling.
- Added category bulk actions (`Enable All`, `Disable All`) and category search/filter for faster debug setup.
- Moved Performance Diagnostics UI into the Developer Tools hub while preserving existing data capture behavior.
- Kept unrelated/heavier tools in dedicated dialogs, launched from hub controls (Free-Threading, Dependency Audit, Regression Checks).
- Bumped application version metadata to `v3.0.8` in the script header and `APP_VERSION`.

### v3.0.7 Developer Tools and Diagnostics Expansion
- Added centralized Developer Tools controls for debug logging/category gating, file logging toggle, and startup tab-cycling preference.
- Added performance diagnostics capture/reporting pipeline and performance stats dump tooling.
- Added advanced runtime utilities: Free-Threading & GIL controls, dependency free-threading audit, concurrency controls, and regression check dialog entrypoints.
- Bumped application version metadata to `v3.0.7` in the script header and `APP_VERSION`.

### v3.0.3 Process Profiles Plot Settings Retention
- Added a Process Profiles option: `Keep plot settings for New Profile` (enabled by default).
- New Profile can preserve current plot settings and layout profiles while still creating a clean, dataset-optional profile.
- Preserve/restore ordering is reset-first then restore plot/layout so plot elements and annotation UI state do not carry over.
- Bumped application version metadata to `v3.0.3` in the script header and `APP_VERSION`.

### v3.0.2 Plot Elements Editor Window Sizing Hardening
- Plot Elements editor now applies screen-safe geometry restoration so persisted window sizes/positions are clamped on open with sane fallback sizing and centered defaults.
- Reorganized the Plot Elements editor control-row layout to improve action-button usability and reduce crowding.
- Adjusted split-pane sash bounds/defaults to keep both panes visible on smaller displays.
- Bumped application version metadata to `v3.0.2` in the script header and `APP_VERSION`.

### v3.0.1 Startup Splash + Background Startup Orchestration
- Added a startup splash window with a determinate loading bar so launch progress is visible immediately and remains visible until startup completion gates are satisfied.
- Added startup orchestration gates that hold splash teardown until the main UI build, deferred Plot Settings stage-two build, deferred Cycle Analysis stage-four build, and startup restore state all report complete.
- Switched initial Cycle Analysis tab construction from synchronous mode to deferred staged mode to reduce launch-time UI blocking.
- Kept workbook/session restore on the existing background worker path and integrated restore status milestones with startup splash progress messaging.
- Guarded initial Data-tab warm-up selection while the startup splash is active to avoid competing tab-switch churn during launch.
- Added a Developer Tools preference (`Disable Startup Tab Cycling During Splash`) so startup can skip tab cycling while splash is visible.
- When that preference is enabled, splash teardown now waits for visible startup tabs to report interaction readiness before the loading UI is removed.
- Bumped application version metadata to `v3.0.1` in the script header and `APP_VERSION`.

### v3.0.0 Import CSV Dialog UX Refresh and Major Version Rollforward
- Refreshed the `Import GL-260 CSV` popup layout so the settings body is scrollable while the action footer stays fixed.
- Kept `Import` and `Close` always visible at the bottom of the dialog, including on constrained laptop-height windows.
- Cleaned up the Ignore columns selector layout with tighter listbox/scrollbar alignment and reduced dead space.
- Updated README user-manual content for the revised Import CSV dialog behavior.
- Bumped application version metadata to `v3.0.0` in the script header and `APP_VERSION`.
- This is the first release using explicit `vX.Y.Z` semantics for this project phase; `X=3` was selected for a major UI/UX rollforward milestone, with `Y=0` and `Z=0` reset at the major boundary.

### v2.13.1 Legend Drag Snap Offset Fix
- Fixed the cycle legend drag snap/offset issue by removing manual motion-time legend relocation that rewrote `loc` from absolute cursor coordinates.
- Combined cycle legend dragging now relies on Matplotlib's native draggable movement path, preserving the click grab-point offset during drag.
- Normalized runtime legend draggability enable/disable through `_make_legend_draggable(...)` so combined and non-combined plots use one consistent helper path.
- Preserved existing cycle legend persistence semantics (`combined_cycle_legend_anchor_mode`, `combined_cycle_legend_loc`, `combined_cycle_legend_anchor_space`, and axis-offset keys) without schema changes.
- Bumped application version metadata to `v2.13.1` in the script header and `APP_VERSION`.

### v2.13.0 Plot Elements Close-Triggered Refresh Overlay
- Closing the Plot Elements editor now schedules one idle refresh for the owning plot tab via the shared `Refresh` path.
- The refresh uses the existing `_force_plot_refresh(...)` overlay pipeline, so splash/progress behavior matches manual Refresh and stays visible until finalization.
- Added a close/refresh latch in the editor close handler to prevent duplicate refresh scheduling from repeated close events.
- Bumped application version metadata to `v2.13.0` in the script header and `APP_VERSION`.

### v2.12.10 Core Overlay Adaptive Pass Targeting
- Core plot overlays now capture a layout-signature baseline before pass 1 and adaptively choose a one-pass or two-pass refresh target based on signature change detection.
- Core refresh completion now tracks target-aware progress milestones and finalization messaging to keep determinate splash progress synchronized with pass decisions.
- Overlay release remains completion-gated (`ready_seen` + target passes) with guarded state transitions so splash cleanup remains deterministic.

### v2.12.9 Core Overlay Completion-Gated Refresh
- Added completion-based core overlay orchestration that holds the splash during forced refresh passes and clears only after pass completion and draw readiness.
- Introduced invoked/completed pass counters and scheduled refresh-pass callbacks so core plots follow the same shared refresh command path used by the Refresh button.
- Added fail-closed overlay cleanup paths when frame/canvas/refresh command availability checks fail, preventing stuck overlays during teardown races.

### v2.12.8 Refresh Overlay Reappearance Across Plot Refreshes
- Refresh overlays now reappear at refresh entry across generated plot tabs for both manual and programmatic refresh paths that use the shared refresh pipeline.
- The loading overlay and determinate progress bar remain visible until refresh rendering/finalization completes, and only then is the refreshed figure shown.
- Bumped application version metadata to `v2.12.8` in the script header and `APP_VERSION`.

### v2.12.7 Adaptive Combined Refresh + Data-Tab CSV Shortcut
- Updated Combined Triple-Axis auto-refresh pass targeting to use a decision bundle that tracks data, layout, plot elements, and rendered geometry signatures.
- Combined pass 2 now runs adaptively: unchanged data/layout/elements can complete in one pass, while ambiguous or incomplete decision signals conservatively require pass 2.
- Added debug-only decision diagnostics for combined adaptive refresh logic (change flags, ambiguity flag, and computed pass target).
- Added direct `Import GL-260 CSV...` buttons on the Data tab in both Single Sheet and Multiple Sheets modes, including placement next to `Load Selected Sheets` in Multiple Sheets mode.
- Bumped application version metadata to `v2.12.7` in the script header and `APP_VERSION`.

### v2.12.6 Combined Axes Layering Enforcement
- Enforced deterministic Combined Triple-Axis draw order at the Axes level (left, right, third) so cross-axis layering is stable and predictable.
- Added a dedicated invisible overlay axis for Combined cycle peak/trough markers; markers now render above all traces even when large z-order overrides are used.
- Moved the Combined derivative `y=0` dashed reference line to the overlay layer so it remains above X-span plot elements while preserving marker-top layering.
- Added a determinate splash progress bar for plot-generation overlays (core, combined, and other generated plot tabs), with milestone-based progress through data prep, render, auto-refresh passes, and completion.
- Applied resolved per-trace z-order values to every created trace artist and added plotting.render debug logs that report intended vs actual artist z-order per axis role plus one-time axis z-order snapshots.

### v2.12.5 Cycle Marker Top-Layer Z-Order + Data Trace UX Clarity
- Added dynamic cycle marker overlay z-ordering so peak/trough markers always render above trace layers, including custom trace z-order overrides.
- Replaced hardcoded cycle marker z-order values across cycle and core plotting paths with a computed top-overlay z-order helper.
- Updated Data Trace Settings with explicit overlay guidance, Priority and Z-Order Override tooltips, and a live read-only Effective Z column.

### v2.12.4 Working Version Rollforward + Docs Sync
- Set `v2.12.4` as the active working version (`APP_VERSION` and file header).
- Updated the README user manual wording to explicitly call out the `v2.12.3` input-persistence and async-speciation behavior in the Advanced Solubility workflow.

### v2.12.3 Input Persistence + Async Speciation Overlay
- Analysis workflow now preserves user-entered CO2 charged values; Cycle Analysis auto-fill occurs only when the field is blank.
- Planning workflow no longer overwrites NaOH mass with analysis defaults after a run; user inputs persist.
- Advanced Speciation solver runs in a background worker with a loading overlay to keep the tab responsive.

### v2.12.2 Planning Timeline Persistence + Input Stability
- Planning timeline legends are now created once, remain draggable, and keep their placement across redraws and exports.
- Planning workflow inputs now persist after a run; NaOH mass and related fields no longer reset to defaults.

### v2.12.0 Data Trace Settings + Combined Splash Hold
- Added Data Trace Settings... dialog (accessible from generated plot tabs) to manage per-trace color, marker style/size, line style/width, and z-order overrides.
- Per-trace styling now persists per profile and applies consistently across core plots, combined display, previews, and exports.
- Combined triple-axis loading overlay now waits for the second refresh pass and renderer-ready confirmation before clearing, preventing early reveal of unstable legend/layout states.

### v2.11.13 Columns Per-Series Line Width Control
- Added a per-series Line Width (pt) input on the Columns tab to control line thickness independently of marker size.
- Blank line width values inherit existing defaults and persist with profile settings.

### v2.11.12 Combined Splash Refresh Race Hardening
- Combined post-draw refresh now retries briefly when the refresh callback is not yet wired, keeping the splash overlay visible until the forced auto-refresh actually runs.
- The combined plot refresh command is assigned before any initial draw/draw_idle can fire, reducing timing races on first render.
- Overlay cleanup still fails closed after a bounded retry window to avoid stalls if the tab is torn down mid-refresh.

### v2.11.11 Combined Post-Draw Refresh Hook
- Combined Triple-Axis now invokes the same Refresh callback as the button exactly once after the first draw_event, guaranteeing stable geometry before the refresh.
- The loading overlay stays visible through the initial render, first draw, and the auto-refresh pass, then clears only after the refresh-triggered draw completes.
- Added debug logs for first draw, auto-refresh invocation, and overlay clearing.

### v2.11.10 Combined Auto Refresh Scheduling Fix
- Combined Triple-Axis initial draw now sets the render-complete flag and schedules the auto-refresh pipeline so forced refresh runs automatically.
- Combined forced refresh now applies the same display/layout finalization step as other plots, so margins settle without a manual Refresh.
- Loading overlays clear only after the final auto-refresh pass completes, keeping the splash visible through stabilization passes.
- Added debug logs for combined auto-refresh scheduling and completion.

### v2.11.9 Combined Auto Refresh Overlay Continuity
- Combined Triple-Axis forced refresh now applies the same display/layout finalization step as other plots, ensuring margins/layout settle without a manual Refresh.
- Loading overlays remain visible for all forced refresh passes and clear only after the final pass, eliminating the white-background second refresh.

### v2.11.8 Combined Auto Refresh Second Pass
- Combined Triple-Axis auto-refresh now runs two forced refresh passes (via the Refresh-button path) before clearing the loading overlay.
- The loading splash remains visible until the second pass completes, so margins/layout match a manual Refresh on first reveal.

### v2.11.7 Forced Refresh Finalize Before Reveal
- Combined Triple-Axis forced refresh now runs the same synchronous finalize pass (layout solve + draw) before clearing the loading overlay.
- The first visible frame after the splash screen disappears now matches a manual Refresh, with no intermediate margin or layout state.

### v2.11.6 Async Display Settings Application
- Display layout profiles (including margins), plot elements, and annotation controller bindings are now applied through a single helper during initial tab creation and async figure installs before the forced refresh and overlay clear.
- Async render installs now apply the full display settings stack after attaching the new figure, eliminating first-render margin mismatches across plot types.

### v2.11.5 Async Plot Rendering and Immediate Tabs
- Plot generation now creates and selects new plot tabs immediately, with loading overlays shown right away.
- Plot data preparation runs in background workers; Matplotlib/Tk rendering stays on the UI thread once computation completes.
- Combined, Figure 1/2, and Cycle Analysis generation follow the same compute/render split without changing plot output.

### v2.11.4 Plot Tab Auto Refresh Overlay
- All generated plot tabs (Figure 1, Figure 2, Combined, and Cycle Analysis) now show a loading overlay on first render while a one-time automatic refresh stabilizes layout and sizing.
- The first visible plot render now matches the manual Refresh output across plot types without changing plot math or export behavior.

### v2.11.2 Combined Plot Auto Refresh Overlay
- Combined Triple-Axis first render is hidden behind a loading overlay while an automatic refresh applies the final layout and font scaling.
- The first visible combined plot now matches the manual Refresh output without requiring user action.

### v2.11.1 Plot Preview Combined Legend Tracking Restore
- Plot Preview no longer alters Combined Triple-Axis legend drag callbacks; closing preview restores combined legend interactivity without a manual Refresh.

### v2.11.0 New Profile Workflow + Suptitle Label Update
- Added a New Profile button in the Profiles Manager for creating clean, dataset-optional profiles.
- New Profile resets the workspace to startup defaults and uses a single configuration dialog for gas model, vessel volume, starting material, and suptitle inputs.
- New profiles load without prompting for dataset relinking.
- Plot Settings UI labels now use "Suptitle (Job Information)" for clarity.

### v2.10.2 README Restructure (User Manual First)
- Reordered README so the Complete User Manual appears before the Changelog / Ledger.
- Updated version strings to v2.10.2.

### v2.10.1 Final Report Preview Window Auto-Sizing
- Final Report live preview now uses a preview-only DPI baseline (screen-fit clamped) so 100% preview zoom is display-reasonable and no longer tied to export DPI.
- Opening the Live Final Report Preview now auto-sizes the window to the rendered page image, clamps to screen bounds, and centers once at open.
- Preview auto-sizing is one-time per window open, so user manual resizing remains in control after the initial render.

### v2.9.12 Combined Single-Pass Render
- Combined Triple-Axis Generate/Refresh now defers rendering until canvas geometry is ready, applies saved legend anchors before the first draw, and performs a single draw for the display.
- A loading cursor is shown and render controls are disabled while the combined plot finalizes.

### v2.9.11 Combined Cycle Legend Anchor Space Persistence
- Combined triple-axis cycle legend persistence now captures axes-space anchors in axes coordinates and reapplies them with the reference axis transform to prevent refresh drift.
- Legacy figure-anchored cycle legend positions continue to restore without regression.

### v2.9.10 Combined Cycle Legend Refresh Redraw
- Combined triple-axis cycle legend now renders at the saved dragged location immediately after Refresh/regenerate without requiring a click.

### v2.9.8 Combined Cycle Legend Persistence Apply
- Combined triple-axis cycle legend persistence now applies saved offsets post-draw to ensure stable placement across refresh/regenerate.
- Drag capture explicitly marks persistence and records a debug persist-write line when offsets are saved.

### v2.9.6 Combined Cycle Legend Tracking Debug
- Combined triple-axis legend tracking now logs the active Tk canvas identity and event connection IDs so drag-release wiring can be verified in terminal output.
- Button release events emit a mandatory debug line on every mouse-up, confirming drag releases are detected.
- Auto-capture no longer overwrites persisted cycle legend offsets; stored offsets are reapplied when persistence is enabled.

### v2.9.3 Combined Legend Isolation
- Main and cycle legends in the combined plot are now fully independent; only the cycle legend persists its dragged position across Refresh/Regenerate when persistence is enabled.
- Cycle legend drag capture is gated to explicitly tagged cycle legends and only wired when cycle dragging is enabled, preventing cross-talk with the main legend.
- Cycle legend offsets are reapplied before layout solve; main legend centering is re-applied after layout solve for consistent placement.
- Main legend dragging remains optional and session-only; Center Plot Legend is no longer disabled by drag.

### v2.9.1 Combined Cycle Legend Controls
- Added a Plot Settings -> Cycle Legend (Combined Plot) subsection with drag enable/lock/persist/reset and clamp-on-capture controls.
- Cycle legend drag placement now persists across display refresh/regeneration when persistence is enabled; lock prevents accidental moves.
- Center Plot Legend applies only to the main legend; cycle legend placement remains independent.
- Closing generated plot tabs explicitly returns focus to the Plot Settings tab.

### v2.9.0 Combined Legend Persistence
- Combined triple-axis cycle legend positions persist in the display view across Refresh/regeneration, tab switches, and app restarts.
- Display legend dragging now captures anchors on mouse release, keeping export preview and final exports aligned with the on-screen placement.
- Manual main-legend drags are session-only; Center Plot Legend remains in control of default centering.
- Closing a generated plot tab now returns focus to the Plot Settings tab.

### v2.6.0 Final Report Tab Scrolling
- The entire Final Report tab is now vertically scrollable to keep every control accessible on smaller windows.
- The scroll container wraps the full tab layout without changing report generation, layout order, or export behavior.
- Mousewheel scrolling stays within the Final Report tab while text widgets keep their native scrolling.

### v2.5.0 Final Report Pipeline Hardening
- Final Report layout now reserves header/caption/footer bands before layout, eliminating overlaps with section headers and group labels.
- Combined Triple-Axis report pages skip tight_layout and fit existing axes into the content rect; Preserve Export Layout reuses export rendering for complex plots.
- Added Fit Mode selector: Preserve Export Layout (default) and Report Layout (legacy).
- Added per-section header/caption toggles, caption placement (Same Page / Next Page), and a Render Selected Page Preview action.
- Tables are centered, wrapped, and dynamically sized with style presets (Compact / Normal / Large).
- Safe Margins preset adds extra spacing for tighter layouts.

### v2.4.0 Performance and Responsiveness
- Combined triple-axis plot preview now uses a two-phase render (background data prep + UI-thread figure build) to keep the UI responsive.
- Display renders reuse the combined figure when structure is unchanged; export renders always rebuild for deterministic output.
- Added performance diagnostics in Developer Tools -> Performance Diagnostics... with stage-level timings for prepared data, cycle context, combined render, and embed.
- Combined plot cycle context is skipped when cycle overlays are disabled to avoid unnecessary work.
- Output invariance: plot appearance, export results, and analysis semantics are unchanged by these performance updates.

### v2.3.0 Documentation Pass
- Added a comprehensive commenting system with docstrings on every function and loop-level intent notes.
- Documented high-risk subsystems (combined triple-axis plots, layout editor, plot elements, solubility workflows, caching).
- Improves reviewability, debugging safety, and future change confidence by explaining design rationale and data flow.

### v2.2.0 Update Highlights
- Added Process Profiles (Profiles -> Manage Profiles...) to save, restore, import, and export full workspace snapshots.
- Profiles live in `profiles/` as JSON; dataset paths are optional and trigger a relink prompt when missing.
- Columns tab: Apply Column Selection button + indicator now sit next to Per-Sheet Column Mapping, left-aligned.
- Combined triple-axis plot tab: redundant Clear Elements toolbar button removed (use Plot Elements -> Clear All).
- Final Report tab: Generate Final Report and new Report Preview buttons are left-aligned.

### v2.1.1 Update Highlights
- Final Report PDFs stitch exported PDF artifacts per section in the selected order for deterministic output.
- Final Report section ordering is state-driven; preview and generation respect the reorderable list.
- Final Report generation requires applied columns and blocks (or prompts) if the combined plot export fails.

### v2.1.0 Update Highlights
- Final Report PDF now stitches the Combined Triple-Axis export into the report instead of re-rendering it.
- Combined Triple-Axis Plot is the authoritative report plot and is always appended when generation succeeds.
- Cycle Analysis plot and cycle speciation timeline plot are interactive-only and excluded from Final Report exports.
- Plot generation is unified to the bottom action bar with a single Generate Plot control and a single Apply Column Selection button + status indicator.
- Plot Settings tab no longer includes redundant plot-generation buttons.

### v2.0.4 Update Highlights
- Final Report plot pages are built from the export pipeline (same layout rules, legend sizing, and full-page sizing as manual exports).
- Combined Triple-Axis Plot is included in the default report section order and selected by default.
- Older Final Report settings auto-migrate `selected_sections` to insert `combined_plot` after Figure 2.
- Final Report Preview thumbnails are derived from export-grade figures so preview and output match.

### v2.0.3 Update Highlights
- Final Report plots now use the export-grade pipeline (layout profiles, legend sizing, Agg finalization) for visual parity with manual exports.
- Combined Triple-Axis report pages default to landscape (11x8.5) with preflight validation and descriptive fallback text when data is missing.
- Final Report generation is hardened against invalid state and report text normalizes CO2 subscripts to mathtext to avoid glyph warnings.

### v2.0.2 Update Highlights
- Plot selection defaults to Combined Triple-Axis Plot only on first launch (no saved settings).
- Plot selection checkbox states persist across restarts.

### v2.0.1 Update Highlights
- Added File -> Import GL-260 CSV... for direct ingestion of raw Graphtec CSV exports into a new Excel sheet.
- New modal CSV import dialog provides channel mapping, sheet naming/handling, and preprocessing controls.
- Derived columns (elapsed time, first derivative, smoothed derivative, moving average) are computed in Python and written as values.
- Generated sheets match the existing schema and are immediately usable by Columns, plotting, and cycle analysis.

### Legacy Change Highlights (v1.x and earlier)
All versions earlier than v2.0.0 are treated as legacy. Highlights are grouped here for reference.

#### v1.8.9 Update Highlights
- Bottom action bar now supports selective plot generation with per-plot checkboxes and a single Generate Plot action (no forced full rebuild).
- Cycle Analysis UI is reorganized into Manual Workflow + Advanced/Recompute, with undo/redo, marker import/export, summary copy, and per-cycle CSV export.
- Final Report output fixes: captions render once, figure/table numbers are independent of page numbers, no cropping, and tables auto-fit within margins.

#### v1.8.8 Update Highlights
- Starting Material Settings now include a display name and optional note for the material reacting with the selected gas.
- CO2/13CO2 has been removed from starting-material presets; gas identity lives only in the VDW Gas Model selection.
- Conversion estimates now explicitly report the gas used for uptake and the starting material label from the new field.

#### v1.8.7 Update Highlights
- Cycle Analysis Summary is unified across auto/mixed/manual-only paths with a single builder.
- Summary now verifies the exact gas model inputs used (preset label, V, a, b, MW, SciPy availability).
- Gas uptake mass is always shown; conversion estimates only appear when starting material mass, MW, and stoichiometry are configured.
- New Summary Formatting controls (compact, diagnostics, per-cycle gas mass, conversion estimate readiness) are persisted.
- Starting material defaults are blank to avoid CO2/13CO2 wording unless explicitly configured.

#### v1.8.6 Update Highlights
- Added Auto Title support in Plot Settings -> Titles with render-time resolution for Preview/Refresh/Export.
- Introduced managed Data Type lists (combobox + Manage Types dialog with add/rename/delete/reorder).
- Added template editor with placeholder validation and a day-count mode selector (date diff vs inclusive).
- Auto Title sources include full dataset or current view range, with deterministic fallback to full dataset when mapping is not possible.

#### v1.8.5 Update Highlights
- Combined cycle legend drag placement now persists from the embedded plot or Plot Preview into exports (PNG/SVG/PDF).
- Peak/trough marker size changes propagate to the embedded plot, Plot Preview, and exports without stale cache reuse.
- Main and cycle legend size adjustments now persist in settings across preview open/close and export cycles.

#### v1.8.4 Update Highlights
- Plot Settings closes without a redraw when no values change.
- Combined plot layout tuning is accessed via Plot Settings -> Combined Plot Layout Tuner.
- Save As stays visible in narrow plot tabs by keeping it separate from export checkboxes.
- Main legend anchor/loc is re-applied after sizing for stable placement on refresh/export.
- Refresh button label shortened to Refresh.

#### v1.8.1 Update Highlights
- Added a Cycle Analysis Plot Settings control for Peak / Trough Marker Size (pts^2) to adjust marker area.

#### v1.8.0 Update Highlights
- Unified render pipeline for initial render, Refresh, Plot Preview, and export (no split paths).
- Refresh always builds a new figure while reusing cached prepared data and cycle metrics when the dataset is unchanged.
- Deterministic overlay gating for markers, cycle legend, and moles summary; moles summary appends to the main legend when the cycle legend is off.
- Manual vs auto marker sourcing is enforced (auto off uses manual-only markers; auto on supports manual add/remove overrides).
- Plot Elements controllers are fully rebound on figure swaps so add/select/drag stays reliable after refresh and layout edits.

#### v1.7.4 Update Highlights
- Columns set to None are omitted from plots and legends (combined, core, export).
- Main vs cycle legend sizing is now independent, with plot-aware controls.
- Peak and trough marker shapes are configurable alongside size/color.
- Cycle Analysis reserves top margin to avoid title overlap on refresh/resize.
- Apply VDW now refreshes Cycle Analysis and shows a dirty/applied indicator.

#### v1.7.1 Update Highlights
- Plot elements remain interactive after Refresh on the combined triple-axis tab (placement + drag stay armed).
- Refresh now retargets plot annotations after a deterministic install/draw/finalize pipeline.

#### v1.7.0 Update Highlights
- Plot Elements workflow updated with explicit placement arming and clearer add-status feedback.
- Plot Elements editor keeps add defaults and provides a tighter edit/apply/revert loop.

#### v1.6.8 Update Highlights
- Combined triple-axis plots keep clean breaks between stitched sheets in the display window.
- Plot element placement works across all element types in the combined plot view.
- Span + Label selections respect the configured appearance color immediately and the textbox is draggable.

Additional internal change summaries:
- v1.6.3:
  - Plot Preview/export now reflects manual Cycle Analysis edits correctly.
- v1.6.2:
  - Fixed combined plot xlabel spacing.
  - Fixed cycle legend dragged position persistence across refresh/preview.
- v1.6.0:
  - Added a Layout Editor for per-plot layout adjustments (title/suptitle positions, legend anchors/loc, axis label padding).
  - Added persisted layout profiles (`settings["layout_profiles"]`) for per-plot display/export layout state, including margins and legend anchors.
  - Expanded combined plot layout controls with per-mode margins and legend anchor offsets.
- v1.5.0.4:
  - Plot Elements placement and live update fixes.
  - Restored drag placement for spans and axes routing refresh after plot rebuilds.
- v1.5.0.0:
  - Free-threading readiness helpers and Developer Tools GIL controls.
  - Unified `TkTaskRunner` for background tasks.
  - Dependency audit tooling and session warning.
  - VS Code interpreter prompts for GIL-disabled requests.
- v1.4.0.8:
  - Persisted multi-sheet selected sheets to `settings.json`.
  - Plot Elements opens a dedicated annotations Toplevel per plot.
  - Treeview selection recursion fix in annotations editor.
  - Layout fixes for the annotations Toplevel.
