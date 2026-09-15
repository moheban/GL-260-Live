# Combined axis generalization ? validation

Date: 2026-09-15. Application version remains **v4.18.0**.

## Changes verified

- Either right axis accepts **None**; any existing dataset group can occupy the left axis.
- Multiple temperature traces render without pressure data. Existing y1/y3 and Z/Z2 companion grouping is retained unless a companion is explicitly assigned elsewhere.
- Shared preparation validates active groups, calculates their ranges, and suppresses pressure analysis and stale cycle overlays when pressure is absent from the plot.
- Separate axes of the same data family receive independent automatic ranges. Manual settings retain the existing semantic-family controls.
- Worker cache keys include axis/group selection. Refresh now retains the newly rebuilt figure cache rather than overwriting it with old state.
- Automatic reduced-axis layouts fit visible artists; custom profile margins remain explicit.
- Display, preview, synchronous export, and refresh share the selected-group behavior. Time samples remain unchanged.

## Results

| Check | Result |
| --- | --- |
| Two grouped temperatures, no pressure, display and export | Passed |
| One/two/three physical axes; either right slot disabled | Passed |
| Moving temperature and pressure between positions | Passed |
| Group labels, styles, gaps, and temperature limits | Passed |
| Missing group and all-invalid data guidance | Passed |
| Independent automatic temperature ranges | Passed |
| Single-axis generation entry without y1 | Passed |
| Warm figure reuse and subsequent topology switches | Passed |
| Derivative zero reference on the left axis | Passed |
| SVG and PDF artifact generation | Passed |
| Automatic single-axis X-tick clearance | Passed; image also inspected |
| 100,000-sample worker preparation and cache hit | Passed |
| Export preserved all 100,000 samples | Passed |
| Native and forced-Python decimation preserved gaps/endpoints | Passed |
| Patched-function syntax and docstring presence | Passed, 24 function/class regions |
| Patched-statement lint, format, import hygiene | Passed, 114 extracted blocks |
| Local-symbol checks on modified functions | Passed |
| Full-entry-file F821 check | Passed |

Representative measurements, not a statistical performance guarantee:

- Warm 100,000-sample temperature preparation: **4.4 ms**, display-cache hit.
- Matched synthetic legacy triple-axis figure build: **5.565 s before**, **5.572 s after**.
- The native decimator remained active (`rust_envelope`). A forced unavailable native result exercised the existing Python fallback and preserved all ten NaN gap samples.

The focused permanent regression is registered in Developer Tools as **Combined temperature-only grouped axes**. Existing grouped-pressure legend, optional-third-axis, exclusion-coordinate, native required-index wrapper, selector, and selected-plot dispatch regressions also passed.

## Validation scope and commands

`$validationRoot` was `C:/Users/mmoheban/AppData/Local/Temp/gl260_combined_ubu3iey5`. Its helper scripts and extracted snippets were temporary and were removed after validation. `$patchFiles` contained the extracted modified functions/classes listed in the extraction manifest.

Commands actually run (historical validation record):

- `.\.venv-314t\Scripts\python.exe "$validationRoot/check.py"` ? initial headless render and wrapper checks.
- `.\.venv-314t\Scripts\python.exe "$validationRoot/verify_more.py"` ? loaded the application once; ran focused regressions plus worker, reuse, and final export checks in that interpreter.
- `.\.venv-314t\Scripts\python.exe "$validationRoot/extract_fast.py"` ? extracted modified functions, compiled each snippet, and checked function docstring presence.
- `.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821,F706,F702,F704 --output-format concise "$validationRoot/blocks"`
- `.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check "$validationRoot/blocks"`
- `.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 "$validationRoot/blocks"`
- `.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F --ignore F821 @patchFiles`
- `.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 "GL-260 Data Analysis and Plotter.py"`

Statement fragments lack their enclosing function/loop and external names, so fragment-only F706/F702/F704 and F821 were excluded. Complete modified-function syntax/local checks and the required whole-file F821 check covered those contextual concerns. No general full-file/repository lint or formatter was run.

Patched areas: axis-group resolution and validation; full figure construction; selector normalization, choices and zero-line state; Combined settings/help; generation/refresh entry gates; shared range preparation; worker snapshots/cache keys/decimation; synchronous export and report preflight; in-place refresh/cache bookkeeping; the two focused regression functions, and the new registry entry. Source UTF-8 BOM and CRLF line endings were preserved.

## Rust and limits

- `Get-Command cargo` resolved to `C:/Users/mmoheban/.cargo/bin/cargo.exe`.
- `Test-Path "$env:USERPROFILE/.cargo/bin/cargo.exe"` returned True.
- `cargo --version` returned `cargo 1.93.1 (083ac5135 2025-12-15)`.
- No Rust source/API change was required: the existing array-based decimation kernels accept the selected groups. Native extension checks and forced fallback checks ran; no Cargo rebuild or full Rust suite was necessary.
- Validation used synthetic data and headless Matplotlib figures. A live Tk session with the user's synthesis workbook was not exercised.
- The broad regression suite was not run. Two older checks were investigated without changing their production behavior: the generation-reuse fixture expects obsolete validation/callback hooks, and the standalone authoritative-bottom-margin check reports **expected 0.31, got 0.44** on the original code as well. The latter uses the unchanged layout manager. Focused generation, actual figure reuse, and reduced-axis geometry checks passed.

Suggested commit message: `Generalized Combined plotting to support optional axes and temperature-only traces.`
