# Planning endpoint doses and declining cylinder pressure

## Root cause and implementation

Planning previously generated only nominal full-dose cycles, then derived an endpoint recommendation afterward. The downstream timeline consumed those unchanged full doses. The owning `_generate_planning_cycle_payload` path now brackets the target inside the crossing charge, evaluates the selected pH model at trial doses, inverts the gas inventory to a pressure, and verifies the resulting high-to-trough inventory before advancing the ledger. It stops on that endpoint dose. The shared timeline solver consumes the corrected moles and pressure fields; no display-only pH adjustment is used.

An optional persistent Planning input, `planning_charge_pressures_psig`, accepts one available maximum pressure per cycle. For example, `730, 715, 700, 685, 670` represents a 15 PSIg decline per cycle. The configured high pressure minus pressure drop defines the fixed trough. Every full charge uses its own inventory; the final charge is bounded by its available maximum. Exhausting the list leaves an explicit unmet endpoint rather than extrapolating more pressures. Manual mass dosing and a pressure list are mutually exclusive. Carbonate Mode off retains nominal full-dose behavior.

The PDF preserves the actual charge count, full-charge pressure schedule, final pressure, and reduced uptake. Its endpoint plot marker follows the actual final charge row. Plot pages remain landscape. Existing saved runs are not rewritten; rerun Planning to create an updated snapshot.

## Backend consistency

Integration testing exposed different gas constants in the Rust carbonate inventory and Python fallback (0.082057338 versus 0.082057 L atm mol^-1 K^-1). The three Rust carbonate gas-inventory/inverse-pressure paths now use a dedicated constant matching the existing Python contract. Unrelated cycle calculations retain their original constant. Python wrappers compare native inventories and inverse pressures against the Python calculation and reject incompatible older results. Model and ledger evaluation continue through the existing Rust paths with Python fallback.

Cargo preflight resolved `C:\Users\mmoheban\.cargo\bin\cargo.exe`. Both the resolved command and explicit user-profile executable reported `cargo 1.93.1 (083ac5135 2025-12-15)`. The attempted command:

```powershell
cargo check --manifest-path rust_ext/Cargo.toml --offline
```

failed because the MSVC linker `link.exe` was unavailable. No rebuilt extension was installed. Compiled Rust validation remains pending. Extracted Rust syntax/format checks, Python fallback comparisons, and rejection of incompatible native results were used instead.

## Validation commands and scope

```powershell
.\.venv-314t\Scripts\python.exe -m pytest -q tests/test_planning_partial_endpoint.py tests/test_planning_pdf_report.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821 .tmp_partial_endpoint_validation tests/test_planning_partial_endpoint.py
.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check .tmp_partial_endpoint_validation tests/test_planning_partial_endpoint.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 .tmp_partial_endpoint_validation tests/test_planning_partial_endpoint.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 "GL-260 Data Analysis and Plotter.py"
rustfmt --edition 2024 --check .tmp_partial_endpoint_validation/carbonate_inventory.rs .tmp_partial_endpoint_validation/carbonate_constant.rs
```

All scoped static checks passed. Python syntax was checked with `compile` on extracted blocks and the modified test file; AST checks confirmed function docstrings. Scope: `_generate_planning_cycle_payload`, `_parse_planning_charge_pressures`, `_carbonate_pressure_drop_inventory_core`, `_python_carbonate_charge_pressure_setpoint_core`, `_build_planning_pdf_report`, `_render_planning_pdf_report`, the new Planning pressure-list widgets, and their form-payload entry. Rust scope: the carbonate gas constant and three carbonate gas-inventory/inverse-pressure functions.

Checks exercise real Pitzer endpoint generation and the actual timeline consumer, first/whole/partial charge boundaries, nominal behavior with Carbonate Mode off, declining pressures, schedule exhaustion, invalid lists, manual-dose conflicts, incompatible native results, Python fallback consistency, and PDF compilation/page orientation. A separate real-model case verifies a fourth charge of 550-to-0 PSIg after three full charges at 730, 715, and 700 PSIg using a batch whose endpoint is within specification.

Visual inspection and table-cell bounds checks confirmed the portrait report shows separate full-charge pressures and final charge instructions without clipping. The desktop widgets/save-dialog interaction and broader application regression suite were not run; validation focused on the changed chemistry flow, backend boundary and report pipeline.

Final result: 13 targeted tests passed in 60.44 seconds. All temporary patch-validation files were removed after validation.
