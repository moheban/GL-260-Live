# Endpoint calibration fix validation

Scope: Reaction Dashboard model changes, stoichiometric completion, repeated
charge-cycle calibration, and sodium carbonate pH endpoint guidance. No version
change or Git operation was performed.

## Behavior checked

- Non-unit stoichiometry produces 0%, 50%, and 100% completion at the corresponding
  product capacity, with consistent Python and native-wrapper/fallback results.
- Four pressure decays accumulate 25%, 50%, 75%, and 100%; recharge gaps preserve
  the preceding consumption instead of resetting it. Overlapping cycles fail.
- Current live Cycle Analysis markers define the calibration interval.
- Changing charge updates calibrated demand/headspace. An equal-sum trace edit
  invalidates the cache. A failed trace read clears the old calibration.
- Changing reaction models clears both calibration and dashboard result caches.
- The real NaOH/CO2 Pitzer model supplies the carbonate forecast. Doubling
  headspace halves predicted cycles. A batch configured to reach the target at
  4.5 cycles agrees with the observed 4–5-cycle range; that range is not imposed.
- The suggested dose reproduces target pH 11.4 within 0.002 pH units. Invalid
  volume inputs make the forecast unavailable. Original endpoint/source-isolation
  regressions remain covered.

The numerical forecast tests use synthetic, explicit batch conditions, not a
reconstruction of the user's previous batch. No interactive Tk session or actual
batch pressure file was used to validate measured pH attainment.

## Commands and scope

All Python commands use `.\.venv-314t\Scripts\python.exe`.

The targeted test command is:

```powershell
.\.venv-314t\Scripts\python.exe -m pytest -q -s tests/test_reaction_endpoint_calibration.py
```

Result: **10 passed in 52.63 seconds**.

Syntax was checked with `compile(block, snippet_path, "exec")` on extracted
patched functions, source-control assignments, and the new test file. Function
docstrings were inspected with `ast.get_docstring` on those extracted regions.

Exact static-check commands:

```powershell
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821 .tmp_patch_validation tests/test_reaction_endpoint_calibration.py
.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check .tmp_patch_validation tests/test_reaction_endpoint_calibration.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 .tmp_patch_validation tests/test_reaction_endpoint_calibration.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 "GL-260 Data Analysis and Plotter.py"
```

All four checks passed. F821 was excluded from isolated snippets and run against
the whole application, as required by repository policy. Other whole-file or
repository-wide lint was not run. Formatting used `ruff format --target-version
py312` on the same extracted regions and the new test file before checking them.

Extracted functions: `_python_reaction_dashboard_core`,
`_rust_reaction_dashboard_core`, `_carbonate_target_endpoint_from_timeline`,
`_reaction_endpoint_cumulative_drop`, `_reaction_carbonate_endpoint_guidance`,
`_python_reaction_endpoint_calibration_core`,
`_rust_reaction_endpoint_calibration_core`,
`_run_reaction_endpoint_calibration_core`, `_on_reaction_template_selected`,
`_refresh_reaction_endpoint_calibration`, `_reaction_dashboard_endpoint_guidance`,
`_suggest_reaction_endpoint_calibration`, `_confirm_suggested_reaction_endpoint`,
`_reaction_dashboard_calibrated_cycle_payload`, and
`_reaction_dashboard_resolve_gas_uptake`. The changed `_reaction_source_vars` and
`source_specs` assignments were checked separately from the surrounding UI builder.

## Rust validation limitation

Preflight resolved Cargo to `C:\Users\mmoheban\.cargo\bin\cargo.exe` and confirmed
`cargo 1.93.1`. The GNU toolchain's executable also resolved through `rustup which
--toolchain stable-x86_64-pc-windows-gnu cargo`, and `cargo
+stable-x86_64-pc-windows-gnu --version` returned 1.93.1.

`cargo check --manifest-path rust_ext/Cargo.toml` failed because the default MSVC
toolchain could not find `link.exe`. The repository-supported alternative,
`.\.venv-314t\Scripts\python.exe scripts/validate_rust_backend.py`, found the
installed GNU toolchain and MinGW, but Windows denied execution of generated
dependency build helpers (`Access is denied`, OS error 5). No extension was rebuilt
or installed. This leaves compiled validation of the changed Rust kernels pending.

Both modified Rust functions were extracted and passed syntax/format checks:

```powershell
rustfmt --edition 2024 --check .tmp_patch_validation/reaction_dashboard_core.rs .tmp_patch_validation/reaction_endpoint_calibration_core.rs
```

The Python wrappers reject the old completion contract and unsupported endpoint
arguments and retain Python fallback. Targeted tests exercised that routing
against the installed extension. Broader regressions were not run because the
focused checks directly exercise the affected paths. Temporary validation snippets
are removed at handoff.
