# GL-260 Data Analysis and Plotter (v4.8.5)

## Overview
GL-260 Data Analysis and Plotter is a desktop Tkinter + Matplotlib application for GL-260 pressure/temperature analysis, cycle detection and moles calculations, advanced speciation workflows, compare/ledger review, and final report generation.

Latest timeline/preview highlights in `v4.8.5`:
- Cycle Speciation Timeline title editing now commits on Enter/focus-out and no longer triggers full timeline refresh on each keystroke
- Default timeline title now follows Job Information format: `<Job Information> Reaction Simulation`
- Timeline title commit path now uses a lightweight title redraw to avoid tree-selection refresh churn in Analysis mode
- Prior timeline preview legend sync behavior from `v4.8.4` remains in place

The canonical application version is defined in `GL-260 Data Analysis and Plotter.py` as:
- `# Version: v4.8.5`
- `APP_VERSION = "v4.8.5"`

## Canonical User Manual Location
The canonical, continuously updated user manual now lives in `docs/`:
- Source of truth: `docs/user-manual.md`
- Published wiki-style manual: `docs/user-manual.html`

Build/validate commands:
```powershell
python scripts/build_user_manual.py
python scripts/build_user_manual.py --check
```

## Table of Contents
- [Part I - Complete User Manual](#part-i---complete-user-manual)
  - [Program Overview and Philosophy](#program-overview-and-philosophy)
  - [Intended Audience](#intended-audience)
  - [Repository Layout](#repository-layout)
  - [Installation and Requirements](#installation-and-requirements)
    - [Download Repo from GitHub into an Empty Folder](#download-repo-from-github-into-an-empty-folder)
    - [First-Time Setup with install_gl260.py (Recommended)](#first-time-setup-with-install_gl260py-recommended)
  - [Running the Application](#running-the-application)
  - [Architecture and Data Flow](#architecture-and-data-flow)
  - [Quickstart Workflow (Linear)](#quickstart-workflow-linear)
  - [UI and Navigation Guide](#ui-and-navigation-guide)
  - [Plotting Architecture Details](#plotting-architecture-details)
  - [Plot Elements and Annotations System](#plot-elements-and-annotations-system)
  - [Combined Triple-Axis Plot Technical Documentation](#combined-triple-axis-plot-technical-documentation)
  - [Interactive Cycle Analysis - Scientific and Operational Guide](#interactive-cycle-analysis---scientific-and-operational-guide)
  - [Advanced Solubility and Equilibrium Engine](#advanced-solubility-and-equilibrium-engine)
  - [Compare Tab Workflow and Reporting](#compare-tab-workflow-and-reporting)
  - [Final Report System - Export and PDF Assembly](#final-report-system---export-and-pdf-assembly)
  - [Preferences and Configuration System](#preferences-and-configuration-system)
  - [Performance and Developer Tools](#performance-and-developer-tools)
  - [Troubleshooting and FAQ](#troubleshooting-and-faq)
  - [Power User and Advanced Workflows](#power-user-and-advanced-workflows)
- [Known Limitations and Tradeoffs](#known-limitations-and-tradeoffs)
- [License](#license)
- [Part II - Changelog / Ledger](#part-ii---changelog--ledger)

## Part I - Complete User Manual

### Program Overview and Philosophy
GL-260 Data Analysis and Plotter is a desktop Tkinter + Matplotlib workflow for deterministic GL-260 analysis: data import, cycle detection, moles calculations, advanced solubility workflows, compare/ledger review, and final report generation.

Part I for `v4.8.5` is installer-first by design:
- Use `scripts/install_gl260.py` as the default bootstrap path on Windows, macOS, and Linux.
- Keep runtime behavior deterministic by running through explicit virtual-environment interpreter paths.
- Treat Rust acceleration as optional; Python paths remain authoritative fallback.
- Keep plotting/report outputs reproducible through shared settings/profile state.

### Intended Audience
- Process engineers and chemists working with GL-260 pressure/temperature datasets.
- Analysts who need reproducible cycle segmentation, moles accounting, and exportable plots.
- Developers and power users who need controlled environment setup, diagnostics, and optional Rust acceleration.

### Repository Layout
Primary paths in this repository:
- `GL-260 Data Analysis and Plotter.py`: Main application entry script.
- `README.md`: Project overview and release ledger (Part II).
- `docs/user-manual.md` + `docs/user-manual.html`: Canonical detailed user manual source and generated wiki artifact.
- `requirements.txt`: Runtime dependency set installed into local environments.
- `settings.json`: Runtime preferences persisted by the application.
- `scripts/install_gl260.py`: Cross-platform bootstrap installer (primary setup workflow in `v4.8.5`).
- `scripts/validate_rust_backend.py`: Rust backend rebuild/import validator for pinned Windows free-threaded flow.
- `rust_ext/`: Rust extension crate built via `maturin` when Rust backend is enabled.
- `solubility_models/`: Chemistry/speciation package used by advanced solubility workflows.
- `profiles/`: Saved workspace and process profile files.
- `Example Data/`: Sample workbook for quick validation.

### Installation and Requirements
#### Python and runtime expectations
- Minimum Python: `3.10+`.
- Recommended for current free-threaded workflows: `3.14` / `3.14t`.
- Installer target environments:
  - `.venv` (standard runtime)
  - `.venv-314t` (free-threaded runtime, preferred when available)
- Run commands from repository root so local resources are discovered reliably.

#### Dependency classification
Required baseline dependencies for startup and core workflows:
- `matplotlib`
- `numpy`
- `pandas`
- `openpyxl`

Optional or feature-gated dependencies:
- `scipy`: enables SciPy-based peak detection and Van der Waals solve paths.
- `mplcursors`: optional cursor interactivity.
- `great_tables`: required for timeline table export/view flows that depend on it.
- `customtkinter`: optional enhanced styling; app falls back to ttk.
- `pypdf` / `PyPDF2`: PDF merge/export compatibility path.
- `gl260_rust_ext` (built from `rust_ext/`): optional acceleration backend with Python fallback.
- `naoh_co2_pitzer_ph_model.py` + `pitzer.dat`: optional NaOH-CO2 model path.

#### Download Repo from GitHub into an Empty Folder
Use this section when you are starting in a brand-new, empty folder where GL-260 will run.

Workflow 1 (primary): Git clone into the current empty folder
1. Create or open your target folder.
2. Confirm it is empty.
3. Run:
```powershell
git clone https://github.com/moheban/GL-260-Live .
```
4. Important: the trailing `.` clones directly into the current folder, and this command requires that folder to be empty.

Workflow 2 (fallback): GitHub ZIP download
1. Open `https://github.com/moheban/GL-260-Live` in your browser.
2. Select **Code** > **Download ZIP**.
3. Extract the ZIP into your intended app folder.
4. Ensure files are at folder root (avoid an extra nested `GL-260-Live` directory level if your workflow expects flat root execution).

Verification checklist (after clone/extract):
- `README.md` is present in the folder root.
- `GL-260 Data Analysis and Plotter.py` is present in the folder root.
- `scripts/install_gl260.py` is present under the `scripts/` folder.

With the repo now in the target folder, run the installer script: `python scripts/install_gl260.py`.
For the full first-run workflow, see [First-Time Setup with install_gl260.py (Recommended)](#first-time-setup-with-install_gl260py-recommended).

#### First-Time Setup with install_gl260.py (Recommended)
Use this section for first launch on a new machine or fresh clone.

Prerequisites:
1. Open a terminal in repository root.
2. Ensure Python is available (`python --version` or `py --version` on Windows).
3. Keep internet access available for dependency and optional Rust tooling installation.

Step-by-step first run:
1. Optional preview mode (no changes):
```powershell
python scripts/install_gl260.py --dry-run
```
2. Run bootstrap installer:
```powershell
python scripts/install_gl260.py
```
3. Wait for setup summary and review these signals:
   - `[ENV] standard: READY|NOT READY`
   - `[ENV] free-threaded: READY|NOT READY`
   - `[RUST] READY|FALLBACK TO PYTHON|SKIPPED`
   - `RUN COMMAND: ...`
4. Copy/paste the exact printed `RUN COMMAND: ...` line to start the app.

Expected launch contract:
```text
RUN COMMAND: .\.venv-314t\Scripts\python.exe "GL-260 Data Analysis and Plotter.py"
```
(If free-threaded is not ready, installer prints the `.venv` launch command instead.)

When to use installer flags:
- `--python-std <path>`: set the exact interpreter used to create `.venv`.
- `--python-ft <path>`: set the exact free-threaded interpreter used to create `.venv-314t`.
- `--dry-run`: print the setup plan and command sequence without mutating repository environments.

First-run recovery guidance:
- Free-threaded interpreter not found:
  - Installer continues with `.venv`; app remains runnable.
  - Add a valid free-threaded interpreter later and re-run installer with `--python-ft`.
- Rust setup/build/import fails:
  - Installer reports fallback and prints repair commands.
  - Continue running Python backend and remediate Rust later.
- No runnable environment provisioned:
  - Installer exits with an error after summary.
  - Use printed `repair:` commands, then re-run installer.

For manual, non-installer setup, see fallback sections below.

#### One-command VS Code bootstrap installer (Windows/macOS/Linux)
Primary bootstrap command:

```powershell
python scripts/install_gl260.py
```

Behavior summary:
- Detects interpreter candidates automatically, with optional explicit overrides.
- Creates/updates `.venv` and attempts `.venv-314t`.
- Installs `requirements.txt` into each ready environment.
- Attempts user-scope Rust setup/build in the selected primary runtime.
- Preserves app readiness by falling back to Python when Rust is unavailable.
- Prints deterministic copy/paste launcher output as `RUN COMMAND: ...`.

#### Windows native venv setup (standard + free-threaded fallback)
Use when installer cannot be used or when manual control is required.

```powershell
# Standard interpreter env
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Free-threaded interpreter env
py -3.14t -m venv .venv-314t
.\.venv-314t\Scripts\python.exe -m pip install --upgrade pip
.\.venv-314t\Scripts\python.exe -m pip install -r requirements.txt
```

Optional free-threaded fontTools hardening:
```powershell
$env:FONTTOOLS_WITH_CYTHON="0"
.\.venv-314t\Scripts\python.exe -m pip install --force-reinstall --no-binary=fonttools fonttools
```

#### macOS native setup (interpreter-agnostic fallback)
Use explicit interpreter paths from python.org, pyenv, Homebrew, or your internal distribution.

```bash
# Example variables; replace with your real interpreter paths
PY_STD="/path/to/python3.14"
PY_FT="/path/to/python3.14t"

"$PY_STD" -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

"$PY_FT" -m venv .venv-314t
./.venv-314t/bin/python -m pip install --upgrade pip
./.venv-314t/bin/python -m pip install -r requirements.txt
```

If a free-threaded interpreter is unavailable on your macOS stack, use `.venv` only.

#### Windows Without Administrative Privileges
The installer already targets no-admin, user-scope defaults. Manual equivalent rules:
- Use a user-writable project folder.
- Use per-user Python installs or explicit user-level interpreter paths.
- Avoid global `site-packages` and activation-script dependency.
- Launch with explicit venv `python.exe` paths.

If `py` launcher is available:
```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe "GL-260 Data Analysis and Plotter.py"
```

If `py` launcher is not available:
```powershell
# Example path; replace with your actual user-level python.exe
$PY="C:\Users\<you>\AppData\Local\Programs\Python\Python314\python.exe"

& $PY -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe "GL-260 Data Analysis and Plotter.py"
```

#### Rust integration (optional) - Windows and macOS
Rust backend is optional. `v4.8.5` installer attempts Rust setup automatically in the selected primary environment.

Manual Rust workflow (only if needed):
1. Install `rustup`, `rustc`, and `cargo`.
2. Install `maturin` in the same venv used to run GL-260.
3. Build and verify import from that same interpreter.

Windows example:
```powershell
.\.venv-314t\Scripts\python.exe -m pip install "maturin>=1.12,<2.0"
.\.venv-314t\Scripts\python.exe -m maturin develop --manifest-path rust_ext/Cargo.toml
.\.venv-314t\Scripts\python.exe -c "import gl260_rust_ext as m; print(m.__file__)"
```

macOS example:
```bash
xcode-select --install
curl https://sh.rustup.rs -sSf | sh
source "$HOME/.cargo/env"

./.venv-314t/bin/python -m pip install "maturin>=1.12,<2.0"
./.venv-314t/bin/python -m maturin develop --manifest-path rust_ext/Cargo.toml
./.venv-314t/bin/python -c "import gl260_rust_ext as m; print(m.__file__)"
```

#### No-Admin Rust integration on Windows
If policy blocks machine-wide install:
- Keep rustup and toolchains in user scope (`%USERPROFILE%\.cargo`, `%USERPROFILE%\.rustup`).
- Ensure `%USERPROFILE%\.cargo\bin` is on PATH for current session.
- Build with the exact venv interpreter used for app launch.

Session-local PATH example:
```powershell
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
rustup default stable
```

If MSVC tools are unavailable and GNU fallback is required:
```powershell
rustup toolchain install stable-x86_64-pc-windows-gnu
rustup target add x86_64-pc-windows-gnu --toolchain stable-x86_64-pc-windows-gnu
.\.venv-314t\Scripts\python.exe -m maturin develop --manifest-path rust_ext/Cargo.toml --target x86_64-pc-windows-gnu
```

#### Repo-local Rust validator script
`scripts/validate_rust_backend.py` remains pinned to this repository's Windows free-threaded flow.

Run:
```powershell
.\.venv-314t\Scripts\python.exe .\scripts\validate_rust_backend.py
```

### Running the Application
Primary launch flow for `v4.8.5`:
1. Run installer: `python scripts/install_gl260.py`
2. Copy/paste printed `RUN COMMAND: ...`
3. Keep using that same interpreter path for terminal runs and VS Code interpreter selection.

Direct launch commands from repository root:

Windows:
```powershell
.\.venv\Scripts\python.exe "GL-260 Data Analysis and Plotter.py"
.\.venv-314t\Scripts\python.exe "GL-260 Data Analysis and Plotter.py"
```

macOS/Linux:
```bash
./.venv/bin/python "GL-260 Data Analysis and Plotter.py"
./.venv-314t/bin/python "GL-260 Data Analysis and Plotter.py"
```

See [First-Time Setup with install_gl260.py (Recommended)](#first-time-setup-with-install_gl260py-recommended) for first-run procedure and recovery behavior.

#### CLI options
Supported startup flags:
- `--benchmark`
- `--points=<int>`
- `--cycles=<int>`
- `--noise=<float>`
- `--open-profile=<profile_name>` (also supports `--open-profile <profile_name>`)

Example:
```powershell
.\.venv\Scripts\python.exe "GL-260 Data Analysis and Plotter.py" --benchmark --points=800000 --cycles=150 --noise=0.25
```

#### Environment-triggered test modes
Targeted environment-controlled test paths:
- `RUN_SOLUBILITY_REGRESSION=1`
- `RUN_PITZER_TESTS=1`
- `RUN_TIMELINE_TABLE_EXPORT_TEST=1`

Windows example:
```powershell
$env:RUN_SOLUBILITY_REGRESSION="1"
.\.venv\Scripts\python.exe "GL-260 Data Analysis and Plotter.py"
```

### Architecture and Data Flow
High-level pipeline:
1. Import data (Excel or CSV).
2. Map columns and apply selection.
3. Build plot series and axis state.
4. Run cycle analysis (automatic and/or manual marker workflow).
5. Generate combined triple-axis plot and overlays.
6. Run optional advanced solubility/speciation analysis.
7. Review compare and ledger results.
8. Export final reports and artifacts.

Core state is held in application-owned data frames, selected-column mappings, plot/cycle settings, and persisted settings/profile payloads. Optional acceleration layers (SciPy/Rust) are additive and fail closed to baseline Python behavior.

Analysis-mode calibration flow now supports one measured-pH anchor per run/profile: select cycle, enter measured pH, run or recompute calibration, then propagate corrected uptake/pH/speciation to downstream cycles and dashboard/timeline outputs.

### Quickstart Workflow (Linear)
Recommended order:
1. Run installer and launch with printed `RUN COMMAND`.
2. Open workbook on Data tab.
3. Select sheet or multi-sheet workflow.
4. Map required columns on Columns tab.
5. Apply column selection.
6. Configure Plot Settings and range policy.
7. Run cycle detection and manual cleanup as needed.
8. Generate combined plot and overlays.
9. Run advanced solubility workflows when required.
10. Build/export final report outputs.

### UI and Navigation Guide
Primary tabs and purpose:
- Data: import workbook/CSV source and sheet selection.
- Columns: map pressure, temperature, derivative, and optional channels.
- Plot: figure generation, axes settings, overlays, and combined-view controls.
- Cycle: cycle marker detection/editing and moles summary.
- Compare: side-by-side run comparisons.
- Ledger: sortable/filterable cross-run metrics.
- Advanced Solubility: planning/analysis/reprocessing chemistry workflows.
- Final Report: export assembly and report packaging.

### Plotting Architecture Details
- Matplotlib is used for figure generation and Tk embedding.
- Multi-axis and combined triple-axis layouts are supported.
- Refresh/render controls are designed to balance responsiveness and reproducibility.
- Overlay and legend behavior persists through settings/profile state where applicable.

### Plot Elements and Annotations System
- Supports add/edit/remove workflows for common annotation types.
- Annotation state is normalized for persistence and export parity.
- Placement and z-order controls are exposed for readability on dense plots.

### Combined Triple-Axis Plot Technical Documentation
- Combined view aligns pressure, temperature, and derivative-oriented channels with cycle context.
- Axis assignment and legend behavior are configurable.
- Refresh policy can run in single-pass, adaptive, or two-pass modes via runtime settings.

### Interactive Cycle Analysis - Scientific and Operational Guide
- Automatic cycle detection uses configurable peak/trough thresholds.
- Manual marker correction supports post-detection cleanup.
- Cycle summaries include ideal-gas moles and optional Van der Waals paths when SciPy is present.
- Results feed cycle summaries, compare workflows, ledger outputs, and report artifacts.

### Advanced Solubility and Equilibrium Engine
- Includes planning, analysis, and reprocessing pathways.
- Supports optional Rust-accelerated kernels with Python fallback.
- Optional NaOH-CO2 path depends on local model module and `pitzer.dat`.
- Model outputs remain available through fallback paths when optional dependencies are missing.
- Analysis workflow supports measured-pH anchor entry (`Measured pH cycle`, `Measured pH anchor`) with one-anchor overwrite semantics per run/profile.
- Anchor-based calibration updates corrected uptake series and corrected pH/speciation series, and displays corrected values beside original estimates.
- Cycle timeline renders include measured anchor marker, corrected pH trajectory, and corrected cycle uptake traces.
- Analysis dashboard includes a measured-pH anchor speciation tile and reaction completion gauge tied to corrected cumulative uptake vs required CO2 for target pH.

### Compare Tab Workflow and Reporting
- Side-by-side comparison supports selected-cycle and metric-level review.
- Compare outputs are consumable by report and ledger workflows.
- Side-local plot/title/cycle context remains explicit for multi-run clarity.

### Final Report System - Export and PDF Assembly
- Assembles selected plots, summaries, and generated tables into report outputs.
- Uses output sizing and DPI policies from settings.
- PDF merge/export routes through available compatibility backend (`pypdf` or `PyPDF2`).

### Preferences and Configuration System
- Settings persist in `settings.json`.
- Process/workspace profiles persist in `profiles/`.
- Runtime configuration includes startup preferences, render policies, and developer toggles.
- Export presets and sizing policies are reusable across sessions.

### Performance and Developer Tools
Developer tools include:
- logging/debug category control
- runtime/render diagnostics
- concurrency controls
- free-threading diagnostics and dependency audits
- Rust backend status/setup entry points
- measured-pH uptake calibration kernel path: `measured_ph_uptake_calibration_core` with fail-closed Python fallback semantics

Performance notes:
- Large datasets and high-resolution exports can be CPU/memory intensive.
- Validate free-threaded and Rust acceleration behavior in your local environment before relying on them for production workflows.

### Troubleshooting and FAQ
Installer-first issues:
- `RUN COMMAND` not produced as expected: re-run `python scripts/install_gl260.py` from repo root and verify setup summary appears before launch line.
- Free-threaded env is `NOT READY`: continue with `.venv`, then install/provide `3.14t` and rerun installer.
- `[RUST] FALLBACK TO PYTHON`: app remains runnable; follow installer `repair:` commands when you are ready.
- Installer exits with no runnable environment: run printed `repair:` commands, then rerun installer.

Runtime and feature issues:
- ABI mismatch (for example `cp314` vs `cp314t`): recreate environment with intended interpreter and reinstall dependencies.
- SciPy unavailable: fallback detection remains available, but Van der Waals paths are limited.
- `great_tables` missing: timeline-table-specific export/view paths requiring it will fail until installed.
- Rust import/build issues: run build and import verification from the same interpreter used to launch the app.
- Settings corruption: inspect/repair `settings.json` and recover from profile autosaves where applicable.

### Power User and Advanced Workflows
#### Conda alternative (primary non-venv option)
Standard env:
```powershell
conda create -n gl260-py314 python=3.14 -y
conda activate gl260-py314
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python "GL-260 Data Analysis and Plotter.py"
```

Free-threaded env:
- If your conda channel/runtime does not provide free-threaded Python, use native `venv` plus a free-threaded interpreter binary.

#### VS Code workflow
1. Open repository folder in VS Code.
2. Run `python scripts/install_gl260.py` in integrated terminal.
3. Copy/paste the final `RUN COMMAND: ...` line.
4. Select the same interpreter (`.venv` or `.venv-314t`) in VS Code.
5. Keep terminal commands pinned to that interpreter path for reproducible runs.

#### Docker (experimental / non-primary)
- GL-260 is primarily a desktop Tkinter GUI workflow.
- Docker is useful for dependency experiments or CI-style non-interactive checks.
- Full GUI use in Docker requires host GUI forwarding and container GUI libs, which is environment-specific and outside primary support scope.

### Known Limitations and Tradeoffs
- Primary workflow is desktop GUI-first; headless/container usage is limited.
- Optional modules gate specific features (`scipy`, `great_tables`, optional chemistry modules, optional Rust backend).
- Large workbooks and high-resolution exports can be memory/CPU intensive.
- Chemistry/model accuracy depends on correct mappings, units, and configured assumptions.

### License
Apache-2.0. See `LICENSE`.

## Part II - Changelog / Ledger

### v4.8.5 Timeline Title Commit Flow + Job Information Default
- Reworked Cycle Speciation Timeline title persistence to commit on explicit input actions (`Enter` and `FocusOut`) instead of per-keystroke trace writes.
- Removed per-keystroke timeline full-refresh side effects from shared title-variable updates to prevent Analysis-mode refresh/tree-selection loop churn after calibration workflows.
- Added a lightweight cycle timeline title redraw path that updates only plot title text and canvas draw scheduling.
- Updated Cycle Speciation Timeline default title sourcing to use Job Information (`Suptitle (Job Information)`) with canonical format `<Job Information> Reaction Simulation`.
- Updated Cycle Timeline Plot Settings reset-to-auto title behavior to use the Job Information-derived default title format.
- Added targeted regressions covering:
  - Job Information-derived default title precedence and fallback behavior,
  - lightweight commit behavior that persists title updates without heavy `_refresh_cycle_views` calls.
- Synced release metadata references to `v4.8.5`.

### v4.8.4 Cycle Timeline Preview Legend Position Sync
- Added timeline-preview main-legend role tagging/capture helpers so preview close only syncs the consolidated timeline legend (not inset legends).
- Enabled draggable legend behavior for Cycle Speciation Timeline Plot Preview and preserved close-time sync into the displayed timeline legend location.
- Added runtime session legend-location override for timeline display/export parity without introducing persistent settings keys.
- Updated cycle timeline export figure path to honor in-session preview legend placement while preserving existing main-legend visibility gating.
- Added targeted regressions for:
  - preview close-time legend capture/apply to display,
  - preview legend dragability,
  - export legend parity with in-session preview override.
- Synced release metadata references to `v4.8.4`.

### v4.8.3 Analysis Measured-pH Warning Source Alignment
- Added one shared Analysis reaction-guidance measured-pH resolver with deterministic precedence:
  - `reaction_final_ph` first,
  - `reaction_slurry_ph` second,
  - `measured_ph_value` anchor fallback only when enabled and cycle-valid.
- Wired the shared resolver into both warning-producing Analysis paths:
  - solver guidance (`_execute_solubility_job` -> `analyze_bicarbonate_reaction`),
  - cycle simulation guidance context (`_run_cycle_solubility_simulation` -> `solubility_simulate_cycle_timeline`).
- Fixed misleading support warnings so Analysis no longer reports "No measured pH provided; relying on ledger ratios." when anchor pH + anchor cycle are valid and recompute is run.
- Added targeted regressions covering anchor fallback behavior and final/slurry precedence behavior.
- Synced release metadata references to `v4.8.3`.

### v4.8.2 Analysis Anchor Propagation + Corrected Completion UX
- Back-propagated measured-pH anchored correction through Analysis runtime progress/regime text so corrected uptake and corrected pH are now the primary reaction-progress basis.
- Added an Analysis fallback reference-trace path from cycle uptake history + Analysis chemistry inputs so progress/regime no longer depend on Planning-only delta-P/manual CO2-per-cycle controls.
- Extended Analysis dashboard summary payload with corrected contract fields:
  - `corrected_total_uptake_g`, `corrected_total_uptake_mol`
  - `corrected_estimated_product_g`, `corrected_actual_yield_pct`
  - `corrected_planning_completion_pct`, `corrected_equivalence_completion_pct`
  - `co2_required_for_target_ph_g`, `co2_required_for_target_ph_mol`
  - `latest_corrected_ph`
- Updated Completion Meter tile to render adjacent pre-anchor and corrected completion gauges.
- Removed measured-pH anchor gauge canvas usage and kept the Measured pH Anchor tile text/badge focused with corrected speciation + required-CO2 context.
- Updated Reaction Progress + Uptake/Yield displays and manual **Send Dashboard Stats to Ledger** handoff to corrected-primary values while retaining raw baselines as secondary context.
- Added regressions for Analysis fallback reference/progress behavior, anchor-calibration required-CO2/completion outputs, corrected-regime precedence, corrected/raw dashboard summary contract fields, dual-gauge rendering calls, and corrected-primary ledger handoff.
- Synced release metadata references to `v4.8.2`.

### v4.8.1 Timeline Legend + Secondary Axis Layout Repair
- Fixed Advanced Speciation Analysis workflow cycle timeline rendering so the consolidated main legend stays visible and recovers from stale cross-figure legend instances during in-tab refreshes.
- Preserved valid user legend placement while adding best-effort on-canvas safety fallback in timeline display and export/preview paths.
- Centralized cycle timeline lower-panel axis layout application so pH and detached pCO2 spacing use one normalized path in both display and export renderers.
- Fixed detached pCO2 axis label placement so it no longer overlaps with detached-axis tick labels in the lower timeline panel.
- Added targeted regressions for:
  - Analysis export legend on-canvas visibility after layout/profile application,
  - detached-axis label/tick non-overlap in display and export,
  - stale cached timeline legend recovery in display refresh.
- Synced release metadata references to `v4.8.1`.

`v4.8.1` addendum - Measured-pH Anchor + Uptake Recalibration
- Added Analysis input/state support for measured-pH anchored calibration (`Measured pH cycle`, `Measured pH anchor`, anchor enable/overwrite semantics) and explicit `Recompute Calibration`.
- Added Analysis runtime payload extensions for measured anchor and correction outputs: `measured_ph_anchor`, `uptake_correction`, corrected uptake series, measured-pH completion payload, and latest corrected speciation payload.
- Added cycle timeline/table/export visualization updates to show measured anchor marker and corrected pH/uptake series alongside original values.
- Added per-profile calibration persistence so anchor/correction state restores and auto-applies when profile chemistry/model basis matches.
- Added Analysis dashboard measured-pH anchor tile with corrected speciation readout and measured completion gauge.
- Added Rust kernel registration/export for anchor calibration: `measured_ph_uptake_calibration_core`, with strict Python fallback parity behavior.

### v4.8.0 Cross-Platform VS Code Bootstrap Installer
- Added `scripts/install_gl260.py` as a single-command installer for Windows, macOS, and Linux repository bootstrapping.
- Added deterministic interpreter discovery with overrides (`--python-std`, `--python-ft`) and a no-mutation planning mode (`--dry-run`).
- Added dual-environment setup behavior that always attempts `.venv` and attempts `.venv-314t` when free-threaded Python is available.
- Added user-scope/no-admin Rust setup flow in the installer (`rustup` detection/install, `maturin` install, extension build, and runtime import verification).
- Added resilient fallback behavior so app readiness is preserved even when Rust setup fails, with explicit repair commands printed.
- Added final launch-command contract in installer output (`RUN COMMAND: ...`) so VS Code users get an exact terminal command to run.
- Updated README installation/running guidance to prioritize the installer workflow.
- Synced release metadata references to `v4.8.0`.

### v4.7.9 Cycle Timeline Dual-Panel Export + Startup Splash Handoff Repair
- Reworked cycle timeline Plot Preview/Export rendering to use the same two-panel structure as the in-tab timeline view across Planning, Analysis, and Reprocessing workflows:
  - top panel: carbon species timeline,
  - bottom panel: pH timeline + cycle CO2 uptake axis.
- Added a shared `Main Plot Legend` checkbox in Cycle Timeline Plot Settings and wired it to a new canonical persisted key `cycle_plot_prefs.show_main_legend` (default enabled), while mirroring legacy `show_legend` for backward compatibility.
- Gated consolidated timeline legend rendering in both display and export/preview paths so legend visibility is now consistent across workflow input modes.
- Hardened startup splash handoff timing by moving bootstrap handoff until root geometry/title/minsize are stabilized, preventing top-left progress placement and app bleed-through during startup transition.
- Extended bootstrap handoff retry tolerance to reduce premature bootstrap clear on slower startup paths while preserving mapped/paint-ready gating.
- Added targeted regressions for dual-panel timeline export coverage across workflows and main-legend toggle gating for display/export behavior.
- Synced release metadata references to `v4.7.9`.

### v4.7.8 Analysis Workflow Stabilization + Startup Overlay Handoff Hardening
- Hardened startup handoff flow so bootstrap splash clear waits for mapped startup overlay readiness, non-trivial root geometry, and first-paint completion before reveal.
- Added a temporary startup `<Configure>` re-raise monitor so overlay stacking stays stable during notebook/layout geometry churn in early startup.
- Added Rust backend capability/identity auditing around `rust_backend_manifest` and exported-kernel contracts so mismatched or deprecated backend states fail closed.
- Added runtime-aware Rust kernel timeout/session-health guards to avoid repeated unstable kernel calls in a single session.
- Added Rust cycle timeline normalization (`cycle_timeline_normalize_core`) with Python fallback parity checks and fail-closed wrapper behavior.
- Expanded regression coverage for startup handoff gating, configure-monitor teardown, Rust capability mismatches, kernel timeout failover, and cycle timeline normalization parity.
- Synced release metadata references to `v4.7.8`.

### v4.7.7 Advanced Speciation UX + Final Product Yield Overhaul
- Reworked the Advanced Speciation tab around large tile layouts so the full tab, not just workflow inputs, now follows the tile-based UX model.
- Replaced the Plot Settings starting-material-only surface with `Final Product Settings`, including a persistent reaction catalog, built-in carbonate reactions, and user-saveable custom reactions.
- Added shared reaction metadata selection to Final Report and surfaced the selected reaction/final product on the report title page metadata block.
- Moved theoretical yield and estimated product yield onto the shared reaction-basis contract so Analysis, Compare, Ledger handoff, profile persistence, and Final Report all use final-product stoichiometry and molar mass.
- Fixed Analysis forensic KPI population by normalizing timeline pH fields around the canonical `ph` / `actual_ph` values and surfacing Planning pH plus delta-pH values directly in the cycle-comparison workflow.
- Added a dedicated `Cycle Comparison Explorer` for selected-cycle review, simplified the on-screen cycle table to higher-signal columns, and preserved the wider schema for expanded viewing and export.

### v4.7.6 Mojibake Cleanup And Rust Backend Hardening Sync
- Replaced authored mojibake in user-facing UI, guidance, report, and export strings with correct Unicode chemistry/scientific symbols.
- Preserved the existing mojibake repair helpers as runtime safety nets for dynamic text while adding curated regression coverage for authored source blocks.
- Kept the Rust backend hardening work in the active release narrative, including the pinned `rust-toolchain.toml` workflow and the interpreter-pinned `scripts/validate_rust_backend.py` rebuild helper.
- Updated README/manual build guidance to stay aligned with `.\.venv-314t\Scripts\python.exe`.
- Synced the application version metadata to `v4.7.6`.

### v4.7.5 Peak/Trough Detection Upgrade Stabilization
- Added shared cycle marker detection/snap cores in Rust for automatic peak/trough discovery and manual marker placement, with Python fallback preserved as the authoritative safety path.
- Manual marker snapping now uses one context-aware workflow across Cycle Analysis and compare-side editing so sharp peaks/troughs resolve to raw extrema more consistently.
- Added cycle detection controls for smoothing, manual snap radius, and auto refine radius, and persisted them through settings/profile threshold payloads.
- Cycle hover previews and cycle trace styling now share one normalization path, preventing preview-only styling drift and fixing the missing `_normalize_cycle_trace_settings` runtime error.
- Synced the application version metadata to `v4.7.5`.

### v4.7.4 Rust-Accelerated Analysis Dashboard + Tile-Based Workflow Inputs
- Extended Rust integration into the Analysis dashboard comparison path with new kernels:
  - `analysis_interpolate_reference_series_core(...)`
  - `analysis_dashboard_core(...)`
- Added Python/Rust core wrappers and parity helpers for dashboard interpolation/summary assembly with strict fail-closed fallback semantics.
- Wired `auto` backend policy routing for:
  - `analysis_interpolate_reference_series_core`
  - `analysis_dashboard_core`
- Updated Analysis dashboard data generation to use shared core routing while keeping reference-run generation in Python for model-callback compatibility.
- Redesigned Planning, Analysis, and Reprocessing workflow input surfaces into responsive tile cards (`2` columns on wide layouts, `1` column on narrow layouts).
- Converted temperature source sections, workflow action rows, and Analysis KPI blocks into tile-based cards with wraplength-aware label updates to prevent clipping.
- Added regression coverage for:
  - dashboard/interpolation Rust wrapper fallback and sanitization,
  - dashboard/interpolation Rust/Python numeric parity fixtures,
  - expanded kernel auto-policy key persistence coverage,
  - responsive workflow tile breakpoint behavior.
- Updated version metadata to `v4.7.4` in script header, `APP_VERSION`, and README.

### v4.7.3 Analysis Dashboard for Advanced Speciation
- Added a new Analysis Dashboard in the Advanced Speciation `Analysis` workflow with draggable/configurable tiles and persisted tile layout/visibility/pin state.
- Added strict per-cycle dashboard payload generation so each detected cycle contributes one `actual_cycle_series` row with pH/speciation/uptake values.
- Added complete reference-run generation (`reference_cycle_series`) that replays detected per-cycle CO2 doses and repeats the final detected dose until target pH stop.
- Added dual comparison payloads (`comparison_series`) for cycle-aligned and CO2-aligned pH/species deltas with alignment quality flags.
- Added dashboard tiles for completion meter (gauge style), current-cycle snapshot, simulation comparison, uptake/yield, species deltas, and warnings/flags.
- Added quick dashboard actions: latest-cycle jump, equivalence-cycle jump, tile configuration dialog, tile layout reset, and drag-reorder behavior.
- Added manual `Send Dashboard Stats to Ledger` action that prefills cycles, total uptake, theoretical yield, actual yield %, and selected-cycle summary notes into a new Ledger entry dialog.
- Extended structured payload support with `analysis_dashboard` and synchronized runtime updates so dashboard data remains aligned with Analysis cycle simulations.
- Updated version metadata to `v4.7.3` in script header, `APP_VERSION`, and README.

### v4.7.2 Startup Splash Gating for Rust Backend Readiness
- Updated startup splash completion gating so Rust backend preflight is part of startup readiness; splash now stays visible until Rust preflight reaches a terminal completed state.
- Moved startup Rust preflight scheduling into the startup readiness poller and removed post-splash preflight scheduling, eliminating the frozen-looking gap between splash dismissal and Rust checks.
- Added explicit startup splash Rust-stage status/progress messaging during final startup checks (`Loading Rust backend startup checks...` / `Finalizing Rust backend startup checks...`).
- Added regression coverage for startup splash gating to verify splash teardown does not occur before Rust preflight completion.
- Kept existing startup Rust preflight behavior and choices intact (`Install now`, `Not now`, `Disable startup Rust checks`), including the Rust-ready status dialog path.
- Updated version metadata to `v4.7.2` in script header, `APP_VERSION`, and README.

### v4.7.1 Rust Acceleration Expansion for Advanced Speciation and Equilibrium
- Expanded optional Rust acceleration into advanced speciation/equilibrium kernels:
  - carbonate-state core solve for both `closed_carbon` and `fixed_pCO2` paths,
  - forced-pH distribution iterative core,
  - Aqion closed-system root/speciation core,
  - NaOH-CO2 Pitzer planning total-carbon solve core.
- Added new Python Rust-bridge wrappers with strict payload sanitization and fail-closed fallback behavior:
  - `_rust_carbonate_state_core(...)`
  - `_rust_forced_ph_distribution_core(...)`
  - `_rust_aqion_closed_speciation_core(...)`
  - `_rust_pitzer_solve_total_carbon_core(...)`
- Wired advanced-engine call sites to Rust-first execution under existing runtime policy semantics, with authoritative Python fallback on any Rust import/runtime/payload error.
- Added synthetic benchmark payload helpers and per-kernel auto-policy keys for the new chemistry kernels:
  - `speciation_carbonate_state_core`
  - `speciation_forced_ph_distribution_core`
  - `aqion_closed_speciation_core`
  - `pitzer_solve_total_carbon_core`
- Added regression coverage for wrapper fallback/sanitization, representative Rust/Python chemistry parity checks (including NaOH-CO2 Pitzer low-carbon, equivalence, and ~900 g trajectory scenarios), and persisted auto-policy key coverage.
- Updated version metadata to `v4.7.1` in script header, `APP_VERSION`, and README.

### v4.7.0 Process Profile Multi-Window Launch + Analysis Forensics
- Added Process Profiles multi-window launch support with a new `Open Profile in New Program Copy` action that starts a child app process and auto-loads the selected profile via `--open-profile`.
- Added a shared profile restore path (`_load_profile_by_name`) so interactive profile loads and CLI-triggered startup loads reuse one lifecycle for splash, restore, and current-profile tracking behavior.
- Refreshed Advanced Speciation workflow input layout with grouped, compact sections for Planning, Analysis, and Reprocessing tabs.
- Added Analysis forensic comparison extensions:
  - new KPI panel (`Forensic Comparison KPIs`) in Analysis,
  - timeline augmentation fields for cycle-aligned and CO2-aligned pH deltas, gas/species deltas, and alignment quality,
  - timeline table/callout/export/plot overlays updated to show forensic fields and CO2-aligned planning traces.
- Added pressure-context propagation and visualization updates so `peak_pressure_psi` / `trough_pressure_psi` flow from cycle timeline generation into Analysis timeline views and exports.
- Fixed malformed CLI handling for `--open-profile` without a value so subsequent flags are preserved (for example `--benchmark` still runs).
- Fixed Analysis forensic summary behavior for empty timelines so KPI deltas remain unavailable instead of reporting synthetic full-deficit values.
- Updated version metadata to `v4.7.0` in script header, `APP_VERSION`, and README.

### v4.6.9 Compare Side Plot Settings Re-Enable + Compare-Scoped Persistence
- Re-enabled Compare `Plot Settings A...` / `Plot Settings B...` in Profile-Exact mode so each side can open the full Combined Plot Settings popup directly from Compare.
- Side popup defaults now stage profile-native settings plus the current compare-side override payload for that pair+side.
- Compare-side Plot Settings applies now persist only to compare state (`settings.json` under `compare_tab`) and do not mutate profile JSON files.
- Compare side bundles are now refreshed from base profile state + persisted pair+side overrides during both:
  - `Load Profiles` staging, and
  - side Plot Settings apply.
  This keeps side-by-side render behavior bundle-driven while making compare-scoped edits immediately visible.
- Updated Profile-Exact Compare messaging to clarify that `Plot Settings A/B...` is an explicit compare-scoped override surface.
- Added regression coverage for:
  - side-bundle override refresh payload merge,
  - load-stage side override reapply,
  - side Plot Settings apply finalize path (rerender + idle lock-x sync).
- Updated version metadata to `v4.6.9` in script header, `APP_VERSION`, and README.

### v4.6.8 Compare Auto-Title Parity
- Compare now resolves each loaded profile title through the same auto-title pipeline used by Plot Settings (`_resolve_effective_title(..., preview=True)`), so side labels/report title metadata match profile auto-generated title output.
- Compare bundle build now persists `effective_compare_title` and seeds compare render args/default title fallback from that resolved value.
- Compare-side title fallback resolution now prefers `effective_compare_title` before raw `args[12]` fallback paths.
- Added regression coverage for side-B auto-title parity across:
  - compare bundle metadata,
  - compare title defaults,
  - compare side render title metadata.
- Updated version metadata to `v4.6.8` in script header, `APP_VERSION`, and README.

### v4.6.7 Startup Interactivity + Profile-Exact Compare Rendering
- Startup restore policy now supports interactive-first reveal with deferred background restore (`startup_autorestore_mode="background"`), so startup interactivity no longer waits on autosave/workbook restore completion.
- Compare side-by-side rendering is now profile-exact by default:
  - each side uses only that profile's own `plot_settings`, `layout_profiles`, `plot_elements`, title, and suptitle,
  - Compare preset/layout/side override layers are no longer applied at render time.
- Compare controls that imply render-time side/style overrides now show Profile-Exact mode messaging.
- Added Compare-local main legend toggle:
  - persisted as `compare_tab.show_main_legend` (default `True`),
  - wired to side-by-side render context without mutating profile files.
- Fixed Compare legend/xlabel rendering stability:
  - strengthened main-legend visibility guard to recover clipped/off-canvas legends,
  - added compare xlabel placement guard so the x-label remains below the primary axis band.
- Compare button text uses white foreground in `_compare_make_button` for improved readability.
- Updated version metadata to `v4.6.7` in script header, `APP_VERSION`, and README.

### v4.6.6 Compare Rendering + Interactive HTML Unification
- Fixed Compare combined render drift where x-axis labels could be pushed into the plot area under side-by-side/layout-manager edge cases.
- Added compare post-solve legend visibility recovery so off-canvas main legends are re-anchored and remain visible in Compare render contexts.
- Replaced Edit Plot A/B popup preview cloning with deterministic side render rebuilds, resolving detached third-axis offset drift, label-size mismatch, and clipping/cutoff behavior.
- Added side-local quick buttons in Compare:
  - `Plot Settings A...`
  - `Plot Settings B...`
  These open the full Plot Settings surface in compare-only pair+side scope (no profile-global writes).
- Added persisted Compare-side quick settings maps under `compare_tab`:
  - `side_plot_settings_overrides_by_pair`
  - `side_layout_overrides_by_pair`
- Clarified report authority in Compare UI/editor/docs:
  - Comparison report uses the side-by-side Compare panes as the output source.
- Upgraded interactive HTML generation into a shared renderer and applied it to:
  - Compare interactive report output
  - Final Report interactive HTML preview/export
- Final Report generation dialog now supports:
  - `PDF`, `PNG`, `HTML`, `PDF + PNG`, `PDF + HTML`, `PNG + HTML`, `PDF + PNG + HTML`
- Updated version metadata to `v4.6.6` in script header, `APP_VERSION`, and README.

### v4.6.5 Compare Debug Instrumentation + Side Cycle Parity
- Added Compare-focused debug categories to Developer Tools Logging & Debug:
  - `compare.render`
  - `compare.whitespace`
  - `compare.cycle_editor`
- Added Compare debug quick actions in Developer Tools -> Runtime / Advanced:
  - `Dump Compare Snapshot`
  - `Dump Compare Whitespace`
  - `Dump Side Editor State`
- Added Compare-tab `Load Diagnostics` quick actions for rapid iteration:
  - `Debug Snapshot`
  - `Debug Whitespace`
- Added unified Compare debug report emitters that always print structured payloads to terminal (`stderr`) and also emit category-gated `_dbg(...)` entries.
- Added focused Compare diagnostics events at key boundaries:
  - per-side profile load result,
  - per-side render-context cycle extraction output,
  - per-side render completion/error with whitespace metrics,
  - side marker-editor recompute/pull/apply events.
- Updated side Compare marker-assignment window (`Open In Cycle Analysis`) to include a Matplotlib toolbar for manual marker workflow parity.
- Updated side Compare marker-assignment trace rendering to preserve NaN/non-finite separator breaks (no artificial line bridges across discontinuous profile segments).
- Updated version metadata to `v4.6.5` in script header, `APP_VERSION`, and README.

### v4.6.4 Compare Rendering Whitespace + Pair Plot Elements + Side Cycle Windows
- Fixed persistent Compare pane whitespace by correcting compare-context legend/x-label gap auto-fix direction inside `layout_health_autofix(...)`, reducing excess vertical gap above the legend and below x-axis labeling in side-by-side panes.
- Compare now builds per-profile render args from profile state/startup defaults (not live workspace UI), with profile-identity fallbacks when title fields are missing:
  - `title_text` fallback: profile name
  - `suptitle_text` fallback: dataset stem (or profile name)
- Added Compare `Plot Elements...` dialog with pair-scoped A/B controls:
  - Side A/B title and suptitle overrides
  - `Retain saved profile plot elements` toggle
  - `Hide text-family elements (keep spans/masks)` toggle (`text`, `callout`, `arrow`, `point` filtered only)
  - `Reset to Loaded Profile`, `Apply`, and `Apply + Close` actions
- Compare now retains and renders each loaded profile's own combined plot elements by default; suppression/filtering is controlled by the new pair-scoped dialog and persisted under `compare_tab.plot_elements_overrides_by_pair`.
- Updated Compare marker-correction workflow so `Open In Cycle Analysis` opens/focuses a dedicated side-specific Cycle Analysis editor window (`A` or `B`) instead of replacing the current workspace profile.
- `Pull Current Markers` in Compare marker editor now reads side-matched editor state only, then applies/saves through existing Compare override/profile save flows.
- Updated version metadata to `v4.6.4` in script header, `APP_VERSION`, and README.

### v4.6.3 Data Tab Profile Readout + Compare Column-Parity + Yield Visibility
- Added a Data tab `Current Workspace Profile` readout that always shows the active profile name and resolved profile path (`Not set` fallback when no profile is tracked).
- Compare `Per-Cycle Uptake Comparison` now mirrors Ledger-style column workflow controls:
  - `View Mode` selector (`Standard`, `Tight`, `Fit to Content`)
  - `Fit All Visible` action
  - separator double-click single-column auto-fit
  - manual resize persistence and horizontal scrollbar support
- Added Compare cycle-table persistence keys under `compare_tab`:
  - `cycle_table_view_mode`
  - `cycle_table_view_profiles`
- Compare cycle-table manual CSV export now respects the current display-column order while keeping the canonical row payload schema for report compatibility.
- Refactored Compare `Yield Comparison` input layout to responsive stacked fields and added dynamic wraplength updates for yield/diagnostics text, preventing right-pane clipping without shrinking the uptake table pane.
- Updated version metadata to `v4.6.3` in script header, `APP_VERSION`, and README.

### v4.6.2 Compare UX + Layout-Health Engine + Interactive HTML Report
- Added global `layout_health_autofix(fig, plot_id, mode, policy)` correction pass that runs after primary layout solving to detect/fix:
  - excessive legend/x-label whitespace,
  - legend/x-label overlap pressure,
  - off-canvas legend/title/suptitle placement,
  - over-compressed axes area.
- Added persisted layout-health settings keys:
  - `layout_health_autofix_enabled`
  - `layout_health_strict_mode`
  - `layout_health_emit_debug_events`
  - `layout_health_max_passes`
  - `layout_health_min_gap_pts`
  - `layout_health_max_gap_pts`
- Added Developer Tools -> Runtime / Advanced -> Layout Health controls and quick actions for runtime toggling/tuning and manual active-figure checks.
- Compare tab is now fully vertically scrollable (whole tab wrapper), while preserving right-side panel scrolling.
- Hardened Compare split persistence:
  - sash release persistence,
  - deferred settle persistence during geometry stabilization,
  - retry-safe restore with clamped split fraction.
- Added Compare-specific readability button helper and applied it across primary Compare controls and Compare popups to preserve full button-label readability under scaling.
- Replaced Compare HTML scaffold with interactive HTML artifact generation:
  - embedded plot images,
  - KPI cards,
  - client-side cycle-table filtering (all/positive/negative delta),
  - yield table and diagnostics panel.
- Added Compare report preference toggle `compare_tab.report_preferences.include_interactive_html` and `Report Options...` control in Compare tab.
- Updated version metadata to `v4.6.2` in script header, `APP_VERSION`, and README.

### v4.6.1 Compare Responsiveness + Marker Correction + Ledger Ordering Upgrade
- Compare load/apply workflows now use a full in-tab overlay (no popup splash), including async render preparation and stale-request guards to reduce UI freezes.
- Compare Layout Manager now applies deterministic Compare-local overrides for whitespace-sensitive controls (legend gap/margin, xlabel pad) and adds detached-axis spacing controls (`detached_spine_offset`, `detached_labelpad`).
- Compare right-side Yield/Diagnostics region is vertically scrollable so lowering the pane sash no longer cuts off Yield Comparison content.
- Added Compare marker-correction workflow with side-targeted popup actions:
  - open the selected profile in Cycle Analysis for reassignment,
  - pull current markers and apply to Compare,
  - optionally persist manual markers back into the profile (`cycle_markers`).
- Added Compare report generation artifacts (`PDF + CSV pack + HTML scaffold`) and status chips for backend path, marker source precedence, and report readiness.
- Added Rust compare alignment kernel (`compare_aligned_cycle_rows_core`) with strict Python fallback parity for cycle-table aggregation.
- Ledger schema/UI expanded with business identifiers and manual ordering:
  - new columns: `Project #`, `Batch #`, `Item #`,
  - persisted row order key: `display_order`,
  - `Move Up` / `Move Down` actions operate in Manual Order mode and persist across restarts,
  - sort mode now supports both `Manual Order` and `Column Sort` views.
- Updated version metadata to `v4.6.1` in script header, `APP_VERSION`, and README.

### v4.6.0 Compare + Ledger Tabs + Yield Comparison Workflow
- Added a new **Compare** tab with two-profile selection (A/B), profile swap, refresh, and side-by-side Combined Triple Axis rendering.
- Compare-pane rendering reuses the existing combined preview/display rendering path (`_build_combined_triple_axis_from_state`) and canvas finalization resize pipeline (`_finalize_matplotlib_canvas_layout`) to preserve plot elements and avoid overlap regressions during pane resize.
- Added Compare per-cycle uptake table with aligned cycle rows for A/B, per-cycle delta, cumulative delta, totals/stat rows, and CSV export.
- Added Compare yield panel with:
  - isolated mass input per run,
  - auto basis mode (profile `reaction_basis` with app fallback),
  - optional override basis mode,
  - theoretical yield, actual yield %, and A-vs-B deltas.
- Extended profile payload compatibility with optional `reaction_basis` serialization so yield basis remains portable between profiles/sessions.
- Added a new **Ledger** tab for persistent QC tracking with sortable/filterable table and full CRUD:
  - fields: profile, run date, final mass, final pH, cycles, total dP uptake, theoretical yield, actual yield %, notes, updated timestamp,
  - actions: Add, Edit, Delete, Add From Profile, Export CSV.
- Added Ledger persistence in settings via normalized `ledger_entries` schema and startup restore.
- Updated application version metadata to `v4.6.0` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.5.6 Rust Kernel Expansion + Layer-Aware Refresh Routing + Final Report Loader Upgrade
- Expanded optional Rust acceleration with new kernels and Python fallback wrappers for:
  - array signature hashing used by adaptive refresh signatures (`array_signature_core`)
  - Final Report cycle statistics row formatting (`final_report_cycle_stats_rows_core`)
  - Final Report cycle timeline row formatting (`final_report_cycle_timeline_rows_core`)
- Added per-kernel `auto` runtime gate persistence (`rust_kernel_auto_policy`) keyed by interpreter fingerprint, with parity and timing checks before enabling Rust.
- Upgraded manual plot Refresh behavior to adaptive layer routing after initial Generate:
  - data-layer changes route to full async refresh
  - non-data layer changes (`trace`, `layout`, `elements`) use selective in-place layer apply when safe
  - no-change refresh requests use fast reveal/finalize path
- Added hybrid layer-refresh state tracking:
  - in-memory full state (`_plot_layer_refresh_state`)
  - lightweight persisted metadata (`plot_layer_refresh_meta`)
  - per-tab toolbar indicator text showing current layer route/state
- Upgraded Final Report preview splash workflow for both full preview and selected-page preview:
  - determinate staged progress updates
  - elapsed-time heartbeat detail text
  - robust timer cleanup and modal grab release on all return paths
- Updated application version metadata to `v4.5.6` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.5.5 First-Pass Combined Layout Fix + Manual Refresh Full Rebuild + Startup Rust Ready Status
- Fixed combined-tab first-pass generation layout drift by invalidating reusable combined plot/layout cache state whenever a combined tab is removed or cleared before rebuild.
- Preserved combined cycle-legend persistence behavior while ensuring cache invalidation runs after legend-anchor capture and before tab/canvas teardown.
- Updated manual plot-tab `Refresh` button behavior to always route through full rebuild (`force_full_rebuild=True`) with explicit splash/progress messaging.
- Kept internal auto-refresh/adaptive orchestration path unchanged so internal optimization behavior remains available outside manual refresh invocations.
- Updated startup Rust preflight ready path to always show a status dialog when Rust is already ready, including executable, ABI/SOABI, and loaded module path context.
- Added regression coverage for combined tab-removal cache invalidation, forced-refresh fast-path bypass behavior, and startup Rust ready-status prompt behavior.
- Updated application version metadata to `v4.5.5` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.5.4 Rust Startup Preflight + Runtime Fingerprint Persistence
- Added persisted Rust runtime install fingerprint tracking keyed by interpreter identity (`sys.executable`, Python version, SOABI/ABI tag, platform, machine) to avoid repeated reinstall prompts on restart when the runtime is unchanged.
- Added startup Rust backend preflight after splash teardown with a three-way prompt:
  - `Install now`
  - `Not now` (Python fallback for current run)
  - `Disable startup Rust checks` (persists `rust_startup_preflight_enabled=False`)
- Added interpreter-aware startup prompt context when a prior Rust-ready record exists for a different runtime/ABI.
- Hardened install verification by running interpreter-pinned import validation (`sys.executable -c "import gl260_rust_ext as m; print(m.__file__)"`) after successful build; failures now emit explicit runtime/ABI diagnostics and fall back safely.
- Added Rust helper `combined_required_indices(...)` and Python wrapper `_rust_combined_required_indices(...)` for non-finite retention index extraction in combined preview decimation, with strict payload validation and Python fallback parity.
- Reduced combined scatter refresh allocation churn by reusing per-trace offset buffers instead of rebuilding `np.column_stack(...)` arrays on each refresh cycle.
- Added Final Report preview render-byte caching keyed by page/zoom/DPI/figure identity and adjacent-page no-GIL-friendly prefetch with token-gated callback safety.
- Added regression coverage for Rust required-index wrapper sanitization/fallback and Final Report preview cache invalidation behavior.
- Updated application version metadata to `v4.5.4` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.5.3 Adaptive Refresh Layering + Draw-Gated Splash Release
- Added conservative adaptive refresh routing for generated plot tabs (`fig1`, `fig2`, `fig_combined`, `fig_peaks`) with three outcomes: `no_change_fast_reveal`, `in_place_display_apply` (non-combined layout/elements-only), and `full_async_refresh`.
- Added deterministic per-plot refresh signature tracking (data fingerprint, layout/settings context, plot elements signature, and trace-style signature) to detect meaningful refresh changes before scheduling async rebuilds.
- Added `dirty_trace` plot-flag support and wired Data Trace Settings apply paths to mark trace changes explicitly, so trace updates route through the full refresh pipeline.
- Hardened refresh overlay sequencing so fast-path and in-place-path refreshes still run staged progress updates and deterministic final layout draw before any splash clear.
- Kept combined splash release draw-gated for adaptive fast paths by arming draw-ack completion state and deferring overlay clear until post-draw completion guards resolve.
- Added adaptive refresh regression coverage for decision routing and fast-path short-circuit behavior while preserving the existing combined overlay completion guard regression.
- Updated application version metadata to `v4.5.3` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.5.2 No-GIL Rust Compatibility + Startup Enforcement
- Updated Rust extension module declaration to `#[pymodule(gil_used = false)]` so free-threaded imports can remain in no-GIL mode.
- Hardened `_load_rust_backend(...)` to detect `False -> True` GIL transitions during Rust import, mark the backend as no-GIL incompatible for the current process, and fail safely to Python fallback.
- Added startup no-GIL enforcement for free-threaded builds: when startup detects GIL-enabled runtime on `cp314t`, the app re-execs once with `-X gil=0` and `PYTHON_GIL=0`.
- Added prompt-first Rust repair flow when no-GIL incompatibility is detected; one in-environment rebuild attempt is offered, then workflows continue with Python fallback if compatibility is still unresolved.
- Updated startup runtime diagnostics to avoid eager Rust imports and report Rust backend state without forcing import-time side effects.
- Updated application version metadata to `v4.5.2` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.5.1 Combined Splash Gating + Cache Singleflight + Rust Overlay Points
- Fixed combined refresh overlay timing so splash teardown stays draw-gated until final legend/layer passes are complete, preventing early reveal before the last plot layer is applied.
- Added extra combined auto-refresh completion guards to defer generic overlay clear when draw-ack, pending legend apply, or queued legend redraw work still targets the active combined figure.
- Added in-memory render-cache singleflight coordination for prepared payloads, cycle segmentation, and cycle metrics so concurrent misses on the same fingerprint are deduplicated.
- Added singleflight performance counters for wait, wait-hit, dedupe, and deduped waiter counts while retaining existing cache hit/miss counters.
- Added Rust helper kernel `cycle_overlay_points_core(...)` and Python bridge `_rust_cycle_overlay_points_core(...)` for strict-validated peak/trough marker point extraction with Python fallback parity.
- Updated application version metadata to `v4.5.1` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.5.0 Threading Control Enforcement + Render/Startup Throughput
- Enforced developer worker-thread controls across cycle metrics compute paths by introducing exact-target worker policy resolution and propagating `requested_workers` / `parallel_enabled` / runtime no-GIL context through render snapshots.
- Updated cycle metrics execution plumbing so core, combined, and cycle-analysis worker flows use the same deterministic cycle worker policy instead of ad-hoc auto-worker fan-out.
- Added worker-policy payload capture (`worker_policy`) and cycle analysis payload reuse (`analysis_payload`) so core render workflows can reuse precomputed cycle results and avoid duplicate cycle recomputation on the UI thread.
- Extended `analyze_pressure_cycles(...)` with `precomputed_cycle_payload` support and updated core-plot generation to consume worker-prepared cycle payloads when available.
- Added `TkTaskRunner.get_diagnostics()` and surfaced live runtime concurrency diagnostics (configured workers, no-GIL state, queue depth, active/pending tasks, live threads) in Developer Tools -> Performance Diagnostics, even when timing capture is disabled.
- Applied conservative startup optimization by lazy-loading optional `great_tables` only when timeline-table export paths require it, with centralized missing-dependency messaging.
- Deferred non-critical Final Report default font-stack resolution to first-use with cached lazy initialization to reduce eager startup work.
- Updated application version metadata to `v4.5.0` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.4.8 Legacy/Contamination Tab De-Integration + Final Report Split Persistence
- Removed runtime notebook integration for Legacy Speciation and Contamination Calculator tabs; Advanced Speciation remains the only solubility/speciation runtime tab.
- Removed legacy/contamination tab visibility controls from Preferences and Tab Layout, and sanitized persisted `tab_order` to supported tab keys only.
- Added startup settings migration to drop deprecated keys (`show_contamination_tab`, `show_solubility_tab`) and normalize Final Report split state.
- Added shared solubility runtime initialization so Advanced Speciation no longer depends on legacy tab build side effects.
- Updated cycle-to-solubility handoff paths to select the Advanced Speciation tab directly.
- Updated solubility summary update/copy/export paths so they continue working when legacy summary widgets are absent.
- Updated Final Report split-pane defaults to favor `Sections Included` at 60% width (left pane weight 3, right pane weight 2) and persist user sash position via `final_report_split_frac`.
- Updated application version metadata to `v4.4.8` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.3.8 Final Report Timeline Reliability + Preview Splash Integration
- Removed Final Report section exclusions so all Final Report tab sections can be generated when selected, including cycle-analysis and cycle-speciation timeline plot pages.
- Added a shared Final Report timeline data resolver with deterministic fallback order across structured payloads, active workflow results, prior workflow results, and visible timeline table rows.
- Hardened Final Report cycle timeline plot/table numeric handling (`CO2`, `pH`, fractions) to tolerate mixed or partially populated timeline entries without breaking preview/export generation.
- Added a blocking modal splash workflow for `Report Preview` and `Render Selected Page Preview`, including staged progress updates and guaranteed splash teardown on success/failure paths.
- Updated Final Report preview page rendering error handling so failed per-page PNG serialization now clears the canvas safely, preserves navigation responsiveness, and surfaces a user warning.
- Updated application version metadata to `v4.3.8` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.3.7 Advanced Speciation Timeline Plot Preview + Consolidated Legend + Settings Parity
- Updated Advanced Speciation cycle timeline plot behavior to always render a consolidated legend in a shadowbox, and made that legend draggable in interactive timeline views.
- Added new cycle timeline plot settings controls for pH-axis label padding/offset and detached pCO2-axis label padding/offset, while retaining existing range controls and title persistence.
- Added shared cycle timeline title inputs to Planning, Analysis, and Reprocessing workflow input tabs; edits now update one shared timeline title used in display and export.
- Added `Cycle Timeline Plot Settings...` to Preferences for direct access to timeline-specific controls.
- Added cycle timeline action-row buttons for `Plot Preview` and `Add Plot Elements...`.
- Added cycle timeline Plot Preview window (11x8.5 export geometry) with toolbar and loading overlay behavior similar to combined preview.
- Added cycle timeline preview plot-elements controller wiring so element drag edits persist in preview and synchronize back to the main timeline plot when preview closes.
- Added new internal plot id `fig_cycle_timeline` to layout/profile defaults and plot-elements routing so timeline display and preview share a stable annotation target.
- Updated cycle timeline rendering/export paths to apply shared axis-spacing preferences and removed hardcoded export-only labelpad overrides that conflicted with user settings.
- Updated application version metadata to `v4.3.7` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.3.6 Close-Time Apply for Non-Trace Elements + Trace-Only Full Rebuild
- Updated Plot Elements close behavior to conditionally apply pending manual property edits (equivalent to `Apply to Selected`) before closing when Live Update is off.
- Added close-time trace-behavior signature detection so only trace-interacting element changes trigger `_refresh_plot_for_plot_id(... force_full_rebuild=True)`.
- Restricted close-time full rebuild triggers to trace-behavior element changes (`trace_mask` / `trace_start`), regardless of active trace selection.
- Updated non-trace close path to skip the full refresh pipeline and reapply only the plot-elements layer with idle redraw, avoiding unnecessary base-figure rebuilds.
- Added internal helper methods for trace-behavior element classification/signature generation and panel-level pending-apply detection used by close-time gating.
- Updated application version metadata to `v4.3.6` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.3.5 Circle Ring Element + Full-Rebuild Close Refresh + Real-Time Splash Timers
- Added a new `Circle` Plot Element type that uses click-drag ellipse geometry (`x0/y0/x1/y1`) and renders as a transparent-center ring for trend highlighting.
- Added full Circle interaction support across placement, hit-testing, drag/move/resize handles, nudge behavior, and persistence/migration paths.
- Added Circle geometry and appearance editors in Plot Elements Properties, including user-adjustable ring edge color, line width, line style, and alpha.
- Added Circle to Plot Elements Add Element controls, selection labels, canonical type aliases, and style apply/copy/paste/preset key filtering.
- Added `force_full_rebuild` refresh control plumbing through the refresh pipeline; combined render reuse is now explicitly bypassed when requested.
- Updated Plot Elements window close refresh to run with `force_full_rebuild=True`, fixing post-close element placement drift that previously required a manual full rebuild.
- Upgraded plot-tab loading overlays to real-time wall-clock elapsed timers (no pulse text), with higher-frequency updates and elapsed composition into detail/progress status.
- Added real-time elapsed timer updates to Combined Plot Preview loading overlay status/progress text with clean timer teardown on hide/close/terminal states.
- Added real-time elapsed timer updates to the startup splash, including clean timer lifecycle handling across reset/completion/overlay teardown.
- Updated application version metadata to `v4.3.5` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.3.4 General Plotter Launcher + Optional Data Handoff
- Added a new top-level `General Plotter` menu adjacent to `Tools`, including `Open General Plotter...` launcher entry.
- Added a dedicated launcher dialog with checkbox control: `Transfer current Data + Columns to General Plotter`.
- Added persistent checkbox preference storage in `settings.json` (`general_plotter_handoff_enabled`) so handoff behavior remembers the last selection.
- Added optional cross-process handoff pipeline from GL-260 to General Plotter using temporary CSV + JSON payload files.
- Scoped handoff mapping to `x` and `y1` only, with validation against currently loaded Data/Columns state.
- Added `--handoff-json` CLI support in General Plotter to ingest transferred payloads and preselect transferred columns.
- Updated application version metadata to `v4.3.4` in script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.2.4 Immediate Startup Visibility + Bootstrap Splash Handoff
- Added a lightweight bootstrap startup splash that is shown before heavyweight imports, so launches no longer appear blank during pre-UI initialization.
- Added staged bootstrap progress updates across binary compatibility checks and dependency import milestones to keep startup feedback visible.
- Added deterministic bootstrap-to-main handoff cleanup so temporary bootstrap windows are destroyed once the main startup splash is active (and during abnormal exit paths).
- Adjusted startup splash ownership behavior so the startup splash can remain visible even while the main root window is initially withdrawn.
- Updated startup flow to reveal the main window as soon as base UI construction completes, while deferred startup readiness tasks continue under splash progress updates.
- Bumped application version metadata to `v4.2.4` in the script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.2.3 Combined Splash + Timeline Readiness
- Startup now keeps a single visible loading surface by hiding the main window behind the startup splash, then revealing it once startup readiness gating completes.
- Plot-tab loading overlays now support richer stage/detail messaging with heartbeat elapsed-time updates so long renders no longer appear frozen.
- Startup-time plot overlays are deferred while the startup splash is active and replayed safely after splash teardown to prevent duplicate loading bars.
- Advanced Speciation loading now uses a unified multi-phase session model so solver and cycle timeline phases share one overlay lifecycle.
- Cycle timeline overlay teardown is now draw-confirmed (with bounded timeout fallback), so the overlay stays active until timeline table/plot rendering is actually ready.
- Bumped application version metadata to `v4.2.3` in the script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.2.2 Dynamic Render Readiness + Selective Core Generation
- Replaced key fixed-delay render waits with readiness-driven geometry/draw scheduling (`<Configure>`/idle callbacks) and bounded emergency timeout fallbacks.
- Added selective core generation so `main_plotting_function(...)` can build only requested outputs (`fig1`, `fig2`, `fig_peaks`) instead of always rendering all core figures.
- Added core cycle side-effects mode (`auto|always|never`, default `auto`) with Plot Settings UI control and full settings/profile persistence wiring.
- Updated core async snapshot/packet orchestration to carry requested core plot keys and resolved side-effects mode end-to-end.
- Added no-GIL-aware render worker policy scaling and synchronized render-cache access with `threading.RLock` for safer concurrent async compute paths.
- Bumped application version metadata to `v4.2.2` in the script header and `APP_VERSION`, and synchronized README top-level version references.

### v4.2.1 Free-Threaded Cycle Metrics Optimization + Version Sync
- Added a canonical runtime no-GIL detector used to gate free-threaded execution paths safely.
- Added a no-GIL optimized cycle-metrics parallel profile with chunked worker dispatch and deterministic ordered merge.
- Kept the legacy per-cycle threaded path unchanged for GIL-enabled execution to preserve historical behavior/performance.
- Added targeted debug diagnostics for cycle-metrics execution profile, worker count, chunk size, and runtime no-GIL state.
- Kept optimization scope in Python compute paths only; no Rust-extension behavior changes were introduced in this release.
- Because cycle analysis and render precompute both route through `_compute_cycle_statistics`, the runtime optimization now benefits both paths automatically when no-GIL mode is active.
- Bumped application version metadata to `v4.2.1` in the script header and `APP_VERSION`, and synchronized README top-level version references.
- Combined Triple-Axis axis-role swaps now map datasets to inner-right vs outer-right positions correctly in both rebuild and reuse paths.
- Added persisted Combined setting `combined_include_zero_line` with Plot Settings checkbox (`Include y=0 line`) to explicitly control dashed derivative reference-line rendering.
- Advanced Speciation timeline table/plot layout refresh is now forced after scenario completion/startup restore so cycle-speciation visuals are visible without tab switching.
- Predicted pH callouts insertion was fixed so all cycle rows render, and parent-canvas wheel routing now avoids stealing scroll from text/tree widgets.
- Startup restore is now autosave-first with legacy fallback only when autosave is unavailable, and splash completion waits on restore terminal state plus post-restore readiness refresh.

### v4.1.0 Rust Combined Precompute Expansion + CSV Import Profiling
- Expanded optional Rust acceleration into combined triple-axis precompute paths while keeping Matplotlib/Tk rendering in Python.
- Added Rust kernels and Python bridge wiring for:
  - Combined decimation index selection (`combined_decimation_indices`)
  - Cycle segmentation merge/core formation (`cycle_segmentation_core`)
  - Cycle metrics + transfer payload assembly (`cycle_metrics_core`)
- Kept strict per-call fallback behavior: any Rust import/runtime/payload error immediately falls back to existing Python calculations with no workflow interruption.
- Added CSV import stage timing diagnostics (`parse_ms`, `transform_ms`, `write_ms`) in async import completion status/debug output.
- Confirmed CSV Rust acceleration is not integrated in this release because XLSX write time remains the dominant bottleneck.
- Bumped application version metadata to `v4.1.0` in the script header and `APP_VERSION`.

### v4.0.0 Rust Acceleration + In-App Toolchain Setup
- Added optional Rust acceleration for core bicarbonate/speciation heavy math paths with strict runtime fallback to existing Python calculations.
- Added first-use in-app Rust setup prompts for the advanced solubility workflows, including optional interactive install (`winget` + `rustup`) and `maturin develop` build.
- Added runtime preference keys for Rust backend mode and install prompting defaults (`rust_backend_mode`, `rust_prompt_install_on_missing`).
- Added Rust backend setup/repair entrypoint in Developer Tools Runtime tab.
- Updated Rust extension packaging/wiring to build/import as `gl260_rust_ext`.
- Bumped application version metadata to `v4.0.0` in the script header and `APP_VERSION`.
- This release is explicitly declared as the first release under the current `vX.Y.Z` semantics policy used by this phase of the project; `X=4` is chosen for the major Rust acceleration and setup workflow expansion.

### Legacy Change Highlights (v3.x and earlier)
All versions earlier than v4.0.0 are treated as legacy. Highlights are grouped here for reference.

### v3.0.12 Combined Triple-Axis Splash Finalization Hardening
- Hardened combined triple-axis overlay finalization so refresh completion is counted only from draw-confirmed acknowledgements tied to the active refreshed combined figure.
- Added explicit completion-ack state (`_combined_overlay_completion_draw_pending` and `_combined_overlay_completion_fig_id`) and reset paths so stale callbacks cannot clear the splash early.
- Kept strict overlay hold behavior until final combined layout/draw stabilization is complete, including post-refresh acknowledgement and geometry settle checks.
- Increased the combined overlay emergency settle timeout from `2.0s` to `12.0s`, with expanded timeout diagnostics that include completion and pending-state details.
- Bumped application version metadata to `v3.0.12` in the script header and `APP_VERSION`.

### v3.0.11 Combined Draw-Confirmed Refresh + Authoritative Layout Margins
- Moved combined refresh completion accounting to the draw-confirmed callback path so manual refresh, auto-refresh, and Plot Settings apply-triggered refresh keep the splash/overlay active until the final drawn state is actually complete.
- Added authoritative layout-margin behavior so Plot Settings display/export margins are the primary bounds for both combined and core plots, while padding/top-margin controls now act as safety-only corrections.
- Unified export profile application so combined exports and Final Report export builds apply the selected export layout profile before finalization.
- Bumped application version metadata to `v3.0.11` in the script header and `APP_VERSION`.

### v3.0.10 CTk Numeric Entry Callback Hardening
- Hardened CTk entry handling for numeric Tk variables (`DoubleVar` / `IntVar`) by introducing a shared string-proxy bridge in `_ui_entry`, preventing callback crashes when fields are temporarily blank during edits.
- Blank or invalid numeric text now preserves the last committed numeric value instead of attempting to write `""` into numeric Tk variables.
- Routed key CTk local entry wrappers (Data/Columns builders) through `_ui_entry` so numeric-entry safety behavior is applied consistently across those surfaces.
- Bumped application version metadata to `v3.0.10` in the script header and `APP_VERSION`.

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

