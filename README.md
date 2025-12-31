# GL-260 Data Analysis and Plotter (V1.6.0)

## Overview
GL-260 Data Analysis and Plotter is a single-script Tkinter + Matplotlib application for loading Graphtec GL-260 data exported to Excel, mapping columns, generating multi-axis plots, performing cycle analysis with moles calculations, and running solubility/speciation workflows. It also includes a contamination calculator and a configurable final report generator.

The main entry point is `GL-260 Data Analysis and Plotter.py`. The UI title and report metadata are driven by `APP_VERSION` in the script, which currently reports `V1.6.0`.

## Intended Audience
- Chemists, process engineers, and researchers analyzing GL-260 pressure/temperature datasets.
- Advanced data analysts who need reproducible plotting and cycle-by-cycle gas uptake estimates.
- Users who need carbonate speciation, solubility, and contamination workflows tied to cycle data.

## Repository Layout
- `GL-260 Data Analysis and Plotter.py`: Main application script and UI.
- `solubility_models/`: Local package providing speciation constants, models, and the closed-system solver.
- `naoh_co2_pitzer_ph_model.py`: Optional NaOH-CO2 Pitzer/HMW model used by the advanced speciation engine.
- `pitzer.dat`: PHREEQC Pitzer database file used by the optional NaOH-CO2 Pitzer model.
- `settings.json`: Persistent user settings written at runtime (created/updated by the app).
- `assets/`, `data/`, `docs/`, `scripts/`: Supporting project folders (content varies by workflow).
- `requirements.txt` / `pyproject.toml`: Dependency and packaging metadata.

## Installation and Requirements
### Python
- Python 3.10 or newer.

### Required runtime dependencies
These modules are imported unconditionally at startup:
- `matplotlib`
- `numpy`
- `pandas`
- `openpyxl` (Excel reader for pandas)
- `great_tables` (used for timeline table export rendering)

### Optional or feature-gated dependencies
- `scipy`: Enables SciPy peak detection and Van der Waals moles calculations. The app falls back to a built-in peak finder and disables VDW if SciPy is missing.
- `mplcursors`: The app attempts to import it; if missing, it continues without it.

### Setup (typical)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If `great_tables` is not installed by your requirements workflow, install it separately so the app can start.

## Running the Application
From the repository root:
```powershell
python "GL-260 Data Analysis and Plotter.py"
```
The app reads and writes `settings.json` in the current working directory. Run from the repo root so the bundled `pitzer.dat` is discoverable by the NaOH-CO2 Pitzer model.

## Architecture and Data Flow
The application is a single Tkinter process with background workers for long-running steps. Core data flow is:

1. **Load data** on the Data tab (single sheet or stitched multi-sheet).
2. **Map columns** on the Columns tab.
3. **Apply columns** (build numeric series, compute auto ranges, prime cycle state).
4. **Generate plots** (Figure 1, Figure 2, Figure 3 cycle analysis, combined triple-axis).
5. **Cycle analysis** (detect peaks/troughs, compute moles, produce summary and figure).
6. **Solubility/speciation workflows** (legacy and advanced tabs).
7. **Final report** (compile selected figures, tables, and narratives into PDF/PNG).

Internally, the app stores the active data in:
- `self.df`: Active pandas DataFrame (single sheet or stitched).
- `self.sheet_dfs`: Per-sheet DataFrames in multi-sheet mode.
- Global series used by the plotting functions: `x`, `y1`, `y2`, `y3`, `z`, `z2`, plus `selected_columns`.

## User Interface Guide (by Tab)

### Data Tab
Purpose: load Excel workbooks and select one or multiple sheets.

Key controls:
- **Excel file** entry, **Browse...**, and **Rescan File**.
- **Mode**: Single Sheet or Multiple Sheets.
- **Single Sheet**: select a sheet from a combo box and click **Load Sheet Data**.
- **Multiple Sheets**:
  - "Available Sheets" list and "Included Sheets (ordered)" list.
  - **Add >>**, **<< Remove**, **Move Up**, **Move Down** to control the stitched sequence.
  - **Load Selected Sheets** loads and stitches.

Runtime behavior:
- Sheet names are read via `openpyxl` (read-only) with a pandas fallback.
- The selected file path and last sheet are persisted to `settings.json`.

### Multi-Sheet Stitching (Data + Columns)
When multi-sheet mode is enabled:
- A **Date & Time** column (selected on the Columns tab) is required.
- Each sheet is loaded into a working DataFrame and gets:
  - `__GL260_DATETIME__`: parsed datetime values.
  - `__GL260_ELAPSED_DAYS_STITCHED__`: elapsed time from the earliest timestamp.
  - `__GL260_ELAPSED_HMS__`: elapsed time formatted as `HH:MM:SS` (or `D HH:MM:SS`).
- Sheets are concatenated with a NaN separator row between them.
- The X column is automatically set to `__GL260_ELAPSED_DAYS_STITCHED__`.
- If any sheet lacks the Date & Time column, a warning is shown and those rows are NaN.

Elapsed time units (days/hours/minutes/seconds) are configurable in **File -> Preferences -> Data & Columns...**.

### Columns Tab
Purpose: map DataFrame columns to plotting and cycle-analysis roles.

Required:
- **X-Axis (Elapsed Time, <unit>)**
- **Primary Y (Reactor, PSI)**

Optional:
- **Primary Y (Manifold, PSI)** (y3)
- **Secondary Y (Derivative)** (y2)
- **Temperature Trace (Internal)** (z)
- **Temperature Trace 2 (External)** (z2)
- **Date & Time** (dt) required only for multi-sheet stitching

Per-series styling (for scatter/line plots):
- Size, Color, and Line Style controls appear for series that support scatter overrides.

Actions:
- **Apply Column Selection** triggers background series building and auto-range updates.
- **Per-Sheet Column Mapping...** opens a dialog to override the global column mapping per sheet (multi-sheet only).

### Plot Settings Tab
Purpose: control plot ranges, axes, style, cycle detection parameters, and combined-plot settings.

Sections and key fields:

**Titles**
- Suptitle and Title text fields.

**Ranges**
- Time min/max, Pressure Y min/max, Temp Y min/max, Derivative Y min/max.

**Axes**
- Enable Temperature Axis (right axis on Figure 1).
- Enable Derivative Axis (right axis on Figure 2).
- Combined derivative axis offset (moves the third axis spine on the combined plot).
- Axis padding percent and a **Refresh Axis Ranges** button.

**Gas Model (Van der Waals)**
- Preset selection (editable/custom).
- Vessel volume (L).
- VDW `a` and `b` constants.
- Gas molar mass (g/mol).
- **Apply VDW** updates the constants used in cycle moles calculations.

**Starting Material Settings**
- Starting material molar mass and mass (used in reaction completion summaries).

**Peak & Trough Detection**
- Prominence (PSI), minimum distance (samples), minimum delta-P for a valid cycle, and minimum width (samples).

**Cycle Integration**
- Show cycle markers on core plots.
- Show cycle legend on core plots.
- Include moles summary in core plot legends.

**Combined Triple-Axis Settings**
- Choose the dataset for inner left, inner right, and outer right axes.
- Combined Axis Settings (Preferences) control label text, label padding, axis spacing, legend wrap rows, legend alignment, legend spacing, title/suptitle spacing, font sizes, and per-mode margins/export padding for this figure.

**Ticks**
- Auto/manual ticks for time, pressure, temperature, derivative.

**Plot Actions**
- Apply Column Selection.
- Generate Figures 1 & 2.
- Generate Figure 1 only.
- Generate Figure 2 only.
- Generate Combined Triple-Axis Plot.

### Plot Tabs (Figures 1/2/3/Combined)
After plotting, each figure appears as a new tab in the main notebook.

Common controls:
- Matplotlib toolbar (pan, zoom, save, etc.).
- **Save As** (PNG/PDF/SVG, multi-select).
- **Refresh Plot** (forces resize and redraw).
- **Close Plot**.

Per-plot annotations:
- **Add Plot Elements...** on Figure 1/2/3.
- **Plot Elements...** and **Clear Elements** on the combined plot.

Per-plot layout:
- **Layout Editor...** for per-plot layout tweaks (title/suptitle positions, legend anchors/loc, axis label padding); apply to preview and/or export.

Export behavior:
- Export DPI is controlled via **Preferences -> Saved Output Options...**.
- Export size can be controlled per output profile (see "Output Size Profiles").

### Cycle Analysis Tab
Purpose: interactive cycle detection, manual correction, and moles summaries.

Key actions:
- **Send to Advanced Speciation & Equilibrium Engine**: sends the cycle payload into the advanced workflows.
- **Analyze Selection**: analyze only a dragged selection range on the cycle chart.
- **Analyze Full Range**: clear selection and analyze the whole dataset.
- **Re-detect Peaks/Troughs**: rerun detection with current parameters (manual edits preserved).
- **Clear All Markers**: removes all markers (auto and manual).
- **Reset Manual Marks**: removes manual adds/removals and reverts to auto-detected set.
- **Save Summary PNG**: exports the cycle summary text widget as PNG.
- **Update/Generate Figure 3**: rebuilds the cycle analysis figure tab using current markers.

Interactive marker controls (on the cycle plot):
- Shift + left-click: add a peak.
- Shift + right-click: add a trough.
- Right-click (no shift): remove the nearest marker.

Other controls:
- Automatic peak/trough detection toggle.
- Cycle temperature column selector (used to compute mean temperature between peak and trough).

Outputs:
- Summary text (used by reports and PNG export).
- Cycle statistics table (per-cycle metrics).
- Cycle plot (Figure 3: Cycle Analysis).

### Contamination Calculator Tab (optional)
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
- **Save Summary PNG** for the contamination summary.

### Legacy Speciation Tab (tab label: "Legacy Speciation Tab")
Purpose: run solubility and speciation analysis using Debye-Huckel or related models.

Key elements:
- **Speciation Model** selector (Debye-Huckel, Davies, Pitzer-lite, etc.).
- **Simulation Basis** (mode-specific guidance, assumptions, and steps).
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

### Advanced Speciation & Equilibrium Engine
Purpose: guided workflows for planning, analysis, and reprocessing with cycle integration.

Workflow structure:
- A notebook with **Planning**, **Analysis**, and **Reprocessing** tabs.
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

### Final Report Tab
Purpose: assemble a multi-section report using plots, tables, and text outputs.

Key controls:
- Final report title.
- Combined plot title override (report-only).
- Template management (Save As Template, Update Template, Delete Template).
- Layout mode:
  - `single_page_portrait`
  - `mixed_pages`
  - `plots_landscape_pages`
- Typography: font scale, margins, page numbers, section headers.
- Section selection and ordering.

Report sections (examples):
- Cycle Analysis Plot with peaks/troughs
- Figure 1 / Figure 2
- Combined Triple-Axis Plot
- Cycle Analysis Summary
- Cycle Statistics Table
- Cycle Speciation Timeline Plot/Table
- Predicted pH Callouts
- CO2 Dosing Guidance
- Planner Narrative
- Key Metrics Summary
- Solubility Summary
- Math Details

Export:
- PDF/PNG with export DPI and output size profiles.

### Menus, Preferences, and Tools
**File**
- Open Excel, Rescan File, Save Settings, Font Family..., Exit.

**File -> Preferences**
- Show/hide optional tabs.
- Tab Layout (order and visibility).
- Data & Columns (elapsed time unit).
- Show solubility input helper.
- Auto-jump to Plot tab after Apply.
- Scatter Plot Settings (marker, size, color, alpha, edge color, line width).
- Cycle Analysis Plot Settings (trace line color/style/width, peak/trough colors, marker size).
- Saved Output Options (export DPI and output size profiles).
- Combined Axis Settings.
- Axis Auto-Range Settings.
- Optimize Layout for Current Display.
- Run Solubility Regression.

**View**
- Zoom in/out/reset.
- Zoom presets.

**Tools -> Developer Tools**
- Free-threading & GIL controls.
- Dependency free-threading audit.
- Concurrency controls for background tasks.
- Validate timeline table export.
- Regression checks.

## Plotting Architecture Details

### Figures
- **Figure 1**: Pressure (y1/y3) vs time, optional temperature axis (z/z2) on the right.
- **Figure 2**: Pressure (y1/y3) vs time, optional derivative axis (y2) on the right.
- **Figure 3**: Cycle analysis plot with peaks/troughs.
- **Combined Triple-Axis**: Single figure with three Y axes (inner left, inner right, outer right).

### Axis and title handling
- Axis ranges are applied from Plot Settings or auto-refresh.
- Tick locations can be automatic or manual per axis.
- Titles and suptitles are centered on the union of visible axes so multi-axis plots stay aligned.
- Axis labels are derived from the selected column names and normalized (underscores removed for display).
- Plot fonts use a preferred Matplotlib serif stack (defaulting to `STIXGeneral` when available) with fallbacks; the optional **Font Family...** setting overrides the plot font family.

### Scatter vs line rendering
- Global scatter settings live in the Scatter Plot Settings dialog.
- Per-series overrides (size, color, line style) are set on the Columns tab.
- Scatter settings apply to Figures 1/2/3 and the combined plot.

### Legend handling
- Legends are created per figure and are draggable.
- Cycle legends can be added to core plots when enabled.

## Plot Elements / Annotations System
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
- Elements can be attached to **data coordinates** (move with pan/zoom) or **axes coordinates** (fixed to plot frame).
- Elements can target the primary, right, or third axis in multi-axis plots.
- Axis-based legacy elements are automatically migrated into data coordinates.
- Elements are applied both to on-screen figures and to exported PNG/PDF/SVG outputs.
- Element placement uses a dedicated "Plot Elements" Toplevel editor with:
  - Add Element controls and placement hints.
  - Color, transparency, and label presets.
  - Live update toggle for immediate redraw.
  - Undo/redo history.

Persistence:
- `settings["plot_elements"]` stores element lists per plot ID.
- `settings["annotations_ui"]` stores per-plot UI state (collapsed state, last mode, add defaults, live update).

## Cycle Analysis and Moles Calculations
Cycle analysis is based on pressure cycles (peak to trough) with a minimum delta-P threshold.

Detection:
- Uses `scipy.signal.find_peaks` when available.
- Falls back to a lightweight built-in peak finder if SciPy is missing.
- Peaks and troughs are paired as: each peak uses the next trough to its right.

Moles calculations:
- For each cycle, delta-P is converted from PSI to atm.
- Mean temperature is computed from the selected cycle temperature column; default is 25 C if missing.
- Ideal gas moles use delta-P, vessel volume, and temperature.
- Van der Waals moles use `a` and `b` constants and require SciPy's nonlinear solver.
- Total uptake is reported for ideal and VDW (if available).

Reagent metrics:
- Starting material mass and molar mass are used to estimate theoretical moles.
- Completion ratio and percent are reported for ideal and VDW totals.

## Solubility and Speciation Engine (shared)
The solubility system is used by both the legacy and advanced tabs.

Core concepts:
- **SolubilityInputs**: mass of NaHCO3, water mass or solution volume, temperature, pH guess/target, headspace parameters, and speciation mode.
- **Speciation modes**:
  - `fixed_pCO2`: uses headspace CO2 boundary.
  - `closed_carbon`: closed-system carbonate inventory without external CO2 boundary.
- Activity corrections and ionic strength are computed based on the selected model.

Available models (registered at runtime):
- Debye-Huckel (Full)
- Debye-Huckel (Capped)
- Davies (Limited)
- Pitzer (Lite)
- Aqion Closed CO2 (closed system; sodium-free, no saturation)
- NaOH-CO2 Pitzer (HMW / PHREEQC-style) if `naoh_co2_pitzer_ph_model.py` and `pitzer.dat` are available

Closed carbonate system:
- Uses charge balance and alpha fractions to solve pH.
- Bisection is the primary solver; numpy-enabled quartic solving is used when available.

NaOH-CO2 Pitzer model:
- Reads focused Pitzer parameters from `pitzer.dat`.
- Used for planning pH predictions in high-alkalinity NaOH systems.
- The app searches for `pitzer.dat` in:
  - The module's default path (if valid),
  - The current working directory,
  - The script directory.

## Threading and Background Tasks
The app keeps the UI responsive with a dedicated task runner:

- `TkTaskRunner` owns a thread pool and enforces "latest task wins" per task name.
- Results and errors are marshaled back to the Tk event loop via `after`.
- Used for:
  - Column application and series building,
  - Cycle analysis computations,
  - Solubility solver runs and cycle timeline simulation,
  - Dependency audits and regression checks.

Concurrency controls are available under **Tools -> Developer Tools -> Concurrency Controls...**.

## Settings Persistence and Restoration
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

## Export and Reporting Workflows
Export functions are available throughout the app and are unified by shared output size profiles and DPI:

- **Plot export** (PNG/PDF/SVG) from each plot tab.
- **Cycle summary** PNG export from the Cycle Analysis tab.
- **Solubility outputs**:
  - Summary PNG,
  - CSV and JSON for species and timeline data,
  - Math preview and narrative exports as PNG.
- **Timeline table export** (PDF/PNG) with orientation and ACS-quality options.
- **Final Report** export (PDF/PNG) with configurable sections and layout.

Output sizes are controlled by **Preferences -> Saved Output Options...**. Profiles support:
- Auto sizing (inherit figure size),
- Fixed sizes (inches or pixels),
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

## Known Limitations and Tradeoffs
- Excel workbooks are the only supported data source.
- Multi-sheet stitching inserts NaN separator rows, which can affect downstream calculations if not accounted for.
- Cycle detection quality depends on user-defined prominence/distance/width parameters.
- Van der Waals moles require SciPy; without it, only ideal gas totals are computed.
- The NaOH-CO2 Pitzer model is optional and requires a valid `pitzer.dat`.
- Large datasets are loaded fully into memory.

## Versioning and Change Highlights (V1.6.x and earlier)
The script includes internal change summaries:

- **V1.6.0**:
  - Added a Layout Editor for per-plot layout adjustments (title/suptitle positions, legend anchors/loc, axis label padding, detached axis offsets).
  - Added persisted layout profiles (`settings["layout_profiles"]`) for per-plot display/export layout state, including margins and legend anchors.
  - Expanded combined plot layout controls with per-mode margins and legend anchor offsets.

- **V1.5.0.4**:
  - Plot Elements placement and live update fixes.
  - Restored drag placement for spans and axes routing refresh after plot rebuilds.

- **V1.5.0.0**:
  - Free-threading readiness helpers and Developer Tools GIL controls.
  - Unified `TkTaskRunner` for background tasks.
  - Dependency audit tooling and session warning.
  - VS Code interpreter prompts for GIL-disabled requests.

- **V1.4.0.8**:
  - Persisted multi-sheet selected sheets to `settings.json`.
  - Plot Elements opens a dedicated annotations Toplevel per plot.
  - Treeview selection recursion fix in annotations editor.
  - Layout fixes for the annotations Toplevel.

Note: the UI title uses `APP_VERSION` set to `V1.6.0`.

## Troubleshooting
- **"No Data" or "Missing Columns" errors**: Load a sheet on the Data tab and set required columns on the Columns tab.
- **Multi-sheet load errors**: Ensure a Date & Time column is selected and present in every included sheet.
- **Cycle detection seems wrong**: Adjust prominence, distance, width, and minimum delta-P; disable auto detection to preserve manual markers.
- **VDW moles unavailable**: Install SciPy; otherwise the app will report only ideal-gas totals.
- **NaOH-CO2 Pitzer model missing**: Ensure `naoh_co2_pitzer_ph_model.py` and `pitzer.dat` are in the expected locations.
- **Settings reset unexpectedly**: A corrupt `settings.json` is renamed automatically; check for `settings.json.corrupt-*`.
- **Export errors**: Verify output paths and export DPI; try a different format if one fails.

## License
Apache-2.0. See `LICENSE`.
