# Measured pH response fix — validation

Date: 2026-10-28. BUG FIX MODE. No version or git changes.

The previous active Analysis path fitted per-cycle uptake multipliers to pH,
then reference-shape/terminal-range repairs could overwrite the fit. Pinning
individual anchor rows afterward did not teach the surrounding predictions.
Planning did not consume this learned pH response. Dashboard guidance could
also supersede the calibrated target with an uncalibrated dose estimate.

Analysis now fits measured-minus-model pH residuals against fixed cumulative
CO2 moles. It interpolates residuals between measurements and retains the nearest
residual outside their range. All compatibility uptake fields retain the supplied
inventory; no pH fitting changes gas mass. Calculated chemistry is retained as a
separate diagnostic, and calibrated fractions are explicitly pH-based estimates.
The same learned response determines the target dose and dashboard remaining dose.

The latest response is saved for Planning when learning is enabled. Reuse requires
matching model, NaOH mass, liquid volume and temperature. Planning uses the response
inside its endpoint solve, including partial charges, and carries it into timeline
replay. Resetting the owning profile's learning clears its response. No-anchor and
unrelated chemistry workflows retain their existing model behavior.

## Results

- 33 focused tests passed, covering response interpolation/extrapolation, fixed
  uptake, real Pitzer anchor fitting and target inversion, Analysis row integration,
  Planning endpoint integration, dashboard target precedence, existing replay,
  pressure/partial-charge behavior and Analysis PDF reporting.
- Python patched-block syntax, docstrings, lint, formatting and import hygiene
  passed. The required full-main-file F821 check passed.
- Rust response kernel and export were added. Scoped rustfmt passed.
- Native build could not complete: `Get-Command cargo` resolved to
  `C:\Users\mmoheban\.cargo\bin\cargo.exe`; `cargo --version` returned
  `cargo 1.93.1 (083ac5135 2025-12-15)`; the user Cargo executable exists.
  `cargo check` failed because MSVC `link.exe` is unavailable. The new native
  kernel was therefore not executed. Existing installed chemistry and Python
  response fallback were tested, including rejection of an unhealthy native result.
- No broad regression suite or GUI session was run. Anchor agreement verifies
  calibration, not independently measured accuracy beyond the observations.

## Commands and scope

Commands were run from the repository root. Temporary snippets were removed
after validation. F821 was excluded from snippets and run on the whole main file
as required. The partial Analysis-function snippet included a return scaffold for
variables consumed by unchanged downstream code.

```powershell
.\.venv-314t\Scripts\python.exe -m pytest -q tests/test_ph_anchor_response.py tests/test_planning_partial_endpoint.py tests/test_replay_mass_continuation.py tests/test_analysis_pdf_report.py
.\.venv-314t\Scripts\python.exe .tmp_patch_validation/check_syntax.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821 .tmp_patch_validation ph_anchor_calibration.py tests/test_ph_anchor_response.py
.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check .tmp_patch_validation ph_anchor_calibration.py tests/test_ph_anchor_response.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 .tmp_patch_validation ph_anchor_calibration.py tests/test_ph_anchor_response.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 'GL-260 Data Analysis and Plotter.py'
cargo check --manifest-path rust_ext/Cargo.toml
rustfmt --edition 2024 --check .tmp_patch_validation/ph_anchor_response_core.rs
```

Extracted main-file scope: `_predict_planning_ph_for_model`,
`_fixed_uptake_ph_calibration`, replaced `_apply_analysis_measured_ph_calibration`
prefix, Planning response selection, response reset, target precedence,
timeline response fields and changed UI string literals. The two new Python
files were checked in full. Rust formatting was restricted to the new kernel.

Commit message: **Fixed pH anchor learning while preserving measured uptake.**
