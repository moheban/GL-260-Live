# Measured pH response fix — validation

Date: 2026-10-28. BUG FIX MODE. No version or git changes.

The previous active Analysis path fitted per-cycle uptake multipliers to pH,
then reference-shape/terminal-range repairs could overwrite the fit. Pinning
individual anchor rows afterward did not teach the surrounding predictions.
Planning did not consume this learned pH response. Dashboard guidance could
also supersede the calibrated target with an uncalibrated dose estimate.

Analysis now fits measured-minus-model pH residuals against fixed cumulative
CO2 moles. It interpolates measured pH against cumulative uptake between measurements and
retains the nearest model residual outside their range. All compatibility uptake fields retain the supplied
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


## Verified-run integration follow-up (2026-10-30)

The remaining discrepancy was a disconnected reference/inventory path. Legacy
Planning had 2.25 L while Analysis had 2.51 L, so strict volume matching silently
excluded the learned response. Independent geometry then supplied a different gas
volume. Several mass conversions used 44.0095 g/mol despite the selected 45.002
g/mol isotope. Carbonate solvent synchronization could also overwrite solution
volume using pure-water density.

The confirmed reference preserves the saved charge order 730, 689.3, 664.4, 480.8,
721.6 PSIg, measured total 656.9 g of 13CO2, pH 13.01 after charge 4 and 11.21 after
charge 5. Its pressure/temperature inventory fit gives an effective headspace of
1.316414242359121 L. Raw imported cycle data was not rewritten. The local durable
reference library protects this confirmation from an older running app saving
stale settings on exit.

Completed measured runs are retained independently of the current partial run.
Compatible physical recipe/vessel/isotope references can transfer across workspace
profiles and model choices; explicitly user-confirmed references take priority.
Planning consumes the measured pH-vs-moles curve, effective headspace and recorded
thermal progression, sums each selected pressure-drop dose and solves the final
partial pressure using the same inventory. Analysis retains supplied uptake.
NaOH and solution-volume variables are shared between views; carbonate mode keeps
water mass and measured solution volume independent.

Final targeted validation: **37 tests passed in 67.44 s**. At target pH 11.4:

- Recorded charge-pressure sequence: 639.9871 g, 4.902695 scheduled cycles.
- Saved Planning sequence 730, 689, 663, 638, 613, 588 PSIg: 639.9871 g,
  4.880596 scheduled cycles.

Both use the reference baseline temperature, its learned thermal progression and
the configured Planning trough. Tests verify isotope mass conservation, final
pressure inversion, matching timeline pH/mass, cross-workspace reference reuse,
partial-run retention, and headless Tk input sharing. The target is interpolated
between measured pH anchors; the 656.9 g measured endpoint is pH 11.21, not 11.4.
No graphical app session was run. Restart and recompute Planning to load changes.

Final commands (repository root):

```powershell
.\.venv-314t\Scripts\python.exe -m pytest -q -s tests/test_verified_ph_planning.py tests/test_ph_anchor_response.py tests/test_planning_partial_endpoint.py tests/test_replay_mass_continuation.py tests/test_analysis_pdf_report.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821 .tmp_patch_validation/final ph_anchor_calibration.py tests/test_verified_ph_planning.py tests/test_ph_anchor_response.py
.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check .tmp_patch_validation/final ph_anchor_calibration.py tests/test_verified_ph_planning.py tests/test_ph_anchor_response.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 .tmp_patch_validation/final ph_anchor_calibration.py tests/test_verified_ph_planning.py tests/test_ph_anchor_response.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 'GL-260 Data Analysis and Plotter.py'
```

All final checks passed. An inline Python extraction script used `compile()` and
AST docstring checks on the patched snippets. Full modified helpers checked:
`_predict_planning_ph_for_model`, `_replay_mass_calibrated_payload`,
`_co2_gas_molar_mass`, `_context_with_verified_ph_response`,
`_restore_confirmed_ph_references`, `_fixed_uptake_ph_calibration`,
`_create_persistent_solubility_var`, `_sync_solvent_entries`.
The additional 48 extracted blocks covered timeline inventory/response propagation,
Planning inventory/selection/thermal/endpoint integration, Analysis reference
registration, dashboard mass conversions and startup reference restoration.
Extracted blocks used normalized indentation, moved imports and loop scaffolding
where needed. Initial snippet checks exposed extraction-context errors; corrected
scaffolding passed without weakening production assertions. Temporary snippets
were removed before handoff.

The native interpolation kernel added in the earlier patch also supports direct
measured-pH interpolation (zero baseline); no second native algorithm was needed.
The Cargo/link.exe limitation documented above still applies. Python response
fallback and the available backend paths were exercised by the focused tests.

Commit message: **Connected verified carbonate runs to Planning and shared recipe inputs.**
