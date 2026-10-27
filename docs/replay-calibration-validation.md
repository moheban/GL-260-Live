# Replay calibration validation ? 2026-10-27

Implemented optional measured-net-CO2 headspace fitting after successful real-cycle replay, followed by Analysis recomputation. Added forward pH-anchor inversion using the selected Analysis model, subsequent-cycle uptake subtraction, and full/partial pressure instructions. Original Cycle Analysis payloads and frozen Planning baselines are preserved. Calibration provenance and recommendations are included in saved Analysis report notes.

Validation used three 730-PSIg charges followed by one 481-PSIg charge, each ending at zero PSIg. Covered known-volume recovery, mass and pressure round trips, Python fallback, decline/cancel/accept dialogs through headless UI stubs, source-data refresh, already-reached targets, later cycles, multiple charges, invalid inputs, and frozen report provenance.

## Commands and results

All commands ran from the repository root. Final scoped static checks passed. Temporary snippets were extracted from the new helpers and the modified integration blocks only; they were removed after validation.

```powershell
.\.venv-314t\Scripts\python.exe -m pytest -q tests/test_replay_mass_continuation.py tests/test_planning_partial_endpoint.py tests/test_analysis_pdf_report.py tests/test_reaction_endpoint_calibration.py
```

Result: 32 passed. An earlier report test exposed missing calibration metadata in the frozen snapshot; the snapshot producer was corrected and this final run passed.

```powershell
python .tmp_patch_validation/validate.py
$blocks = @(Get-ChildItem .tmp_patch_validation -Filter *.py | Where-Object Name -ne 'validate.py' | ForEach-Object FullName)
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821 $blocks tests/test_replay_mass_continuation.py
.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check $blocks tests/test_replay_mass_continuation.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 $blocks tests/test_replay_mass_continuation.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 "GL-260 Data Analysis and Plotter.py"
```

Snippet scope: `_replay_mass_calibrated_payload`, `_replay_anchor_continuation`, `_prompt_replay_consumed_mass`; source-refresh comparison; successful-render prompt scheduling; worker and restored-result output propagation; runtime recommendation/calibration rendering; PDF notes and snapshot field; cycle-input/cache signature additions; pending-dialog flags. Syntax was checked with `compile()` on extracted snippets and the new test file. Docstrings were inspected using an AST read with UTF-8 BOM handling. No full-file lint ran except the required F821 check.

Native-toolchain evidence checked:

```powershell
Get-Command cargo | Select-Object Source
cargo --version
Test-Path "$env:USERPROFILE\.cargo\bin\cargo.exe"
```

Cargo resolved to `C:\Users\mmoheban\.cargo\bin\cargo.exe`, reported `cargo 1.93.1 (083ac5135 2025-12-15)`, and the executable existence check returned True. No Rust source or crate changes were needed: the integration reuses existing native/fallback pressure-inventory, inverse-pressure, and chemistry paths. Installed native inventory and inverse-pressure entry points were present; the focused mass test also explicitly disabled native loading and verified matching Python results. No rebuild was required.

A cold sample continuation calculation with a cycle-4 anchor took 0.483 seconds. Chemistry runs in the existing Analysis background worker; the Tk callbacks only collect the optional mass, update inputs, and dispatch recomputation.

## Limits

UI routing was tested with headless stubs; no interactive Tk click-through or physical reactor experiment was performed. The inferred volume assumes net uptake corresponds to the selected pressure drops. Charge instructions are equilibrium-model estimates using the configured temperature and highest observed charge pressure, not a guarantee of a next-day physical pH. The application explains unavailable model states instead of inventing charge instructions. No version changes or Git commands were made.


## Additional legacy runtime probes

Direct calls through `.\.venv-314t\Scripts\python.exe -` passed `_regression_test_analysis_runtime_fallback_reference_without_planning_inputs` and `_regression_test_analysis_runtime_regime_prefers_actual_observed_ph`. The latter is also exercised by the new runtime-publication test.

`_regression_test_analysis_runtime_prefers_cycle_reference_trace_source` still fails: it expects `analysis_cycle`, while the existing frozen-baseline/Analysis-only branch returns `analysis_only_fallback`. This exact failure also reproduced after removing the new runtime recommendation and cache-signature integrations from the method in memory, without changing any repository file. This legacy expectation was left unchanged; it is outside the new calibration/dosing paths.

Suggested commit message: `Integrated replay CO2 headspace calibration and pH-anchor charge guidance`.

## Follow-up fixes: negative gauge, carbonate saturation and parallel uptake cases

The saved run contains a 689.3 to −1.9 PSIg cycle. Replay previously passed its
691.2 psi drop through Planning's drop-at-most-high-gauge validation. Both Python
and Rust inventory/inverse-pressure implementations now have an explicit measured
subatmospheric option. Planning defaults are preserved. Replay retains the actual
reading and rejects endpoints at or below absolute vacuum.

The focused NaOH–CO2 Pitzer Analysis path previously reused its inherited generic
bicarbonate dissolution solver. That solver treated sodium-equivalent bookkeeping
mass as charged NaHCO3 and applied an incompatible open-gas-boundary calculation.
Focused Analysis now builds diagnostics from its calculated finite Pitzer species,
retaining native/fallback sodium and hydrogen molalities. Nahcolite Q/K uses the
selected PHREEQC database phase reaction and constant; database reads are cached
by path and modification timestamp. Both UTF-8 and Windows-1252 database files
are supported. Salt-specific solid estimates are identified separately; this is
not a full precipitation-equilibrium calculation or a temperature-dependent
nahcolite phase model.

VDW and corrected uptake now have independent consumption, model pH and speciation
results in adjacent timeline columns, the Analysis summary and frozen PDF notes.
The existing raw solve is reused, with at most one extra corrected timeline solve
in the worker. Missing corrections remain unavailable. Explicit model evaluations
are exempt from the renderer's legacy artificial pH-descent adjustment.

Validation covered the actual negative-pressure bounds, mass round trips, default
Planning restrictions, vacuum rejection, carbonate-rich finite speciation, a true
nahcolite supersaturation case, Python/native consistency, independent VDW and
corrected inventories, normalization, visible table values and unchanged model pH
through rendering. The final suite, including the renderer check, passed all
38 tests in 123.78 seconds.

```powershell
.\.venv-314t\Scripts\python.exe -m pytest -q tests/test_carbonate_analysis_saturation.py tests/test_replay_mass_continuation.py tests/test_planning_partial_endpoint.py tests/test_analysis_pdf_report.py tests/test_reaction_endpoint_calibration.py
$blocks = @(Get-ChildItem .tmp_patch_validation -Filter *.py | ForEach-Object FullName)
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821 $blocks tests/test_carbonate_analysis_saturation.py tests/test_replay_mass_continuation.py
.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check $blocks tests/test_carbonate_analysis_saturation.py tests/test_replay_mass_continuation.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 $blocks tests/test_carbonate_analysis_saturation.py tests/test_replay_mass_continuation.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 "GL-260 Data Analysis and Plotter.py"
rustfmt --check --edition 2021 .tmp_patch_validation/carbonate_pressure_drop_inventory_core.rs .tmp_patch_validation/carbonate_charge_pressure_setpoint_core.rs
```

Patched-block syntax used `compile()` on extracted snippets. Scoped lint,
formatting, import hygiene, full-main-file F821 and Rust snippet formatting passed.
Snippet scope: the two pressure helpers; replay mass/continuation helpers; focused
Pitzer predictor and new phase/speciation helpers; finite-state dispatch, salt
accounting, fractions, row/summary dictionaries and assumptions; new paired-case
helpers; runtime/restore/worker integration; PDF comparison notes; table rendering
and model-value preservation; and the solids summary. No broad lint was run.

The Cargo preflight again resolved `C:\Users\mmoheban\.cargo\bin\cargo.exe`,
reported `cargo 1.93.1 (083ac5135 2025-12-15)`, and found the executable. Running
`.\.venv-314t\Scripts\python.exe scripts/validate_rust_backend.py` failed because
Windows denied execution of
`rust_ext\target\debug\build\pyo3-build-config-62be4903ca2e12db\build-script-build`.
The new native source could not be compiled or tested. The installed extension
and explicit Python fallback were exercised instead; an older extension rejecting
the new optional keyword safely routes to Python. No replacement extension was
installed, no versions were changed, and no Git actions were performed.

Suggested commit message: `Fixed replay pressure calibration and added parallel uptake chemistry diagnostics`.
