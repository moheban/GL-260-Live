# Analysis PDF reporting validation — 2026-10-26

Implemented the Analysis **Generate PDF Report** action beside **Open Plot in New Tab**, using the existing Planning table layout, section-selection dialog, and PDF writer. Completed Analysis runs capture independent report inputs and cycle provenance. Export reads saved Analysis results, preserves raw and corrected values, and identifies observed pH separately from calculated pH. Legacy results explicitly identify unavailable input provenance. Plot pages always use landscape orientation.

This is report adaptation and UI integration; chemistry calculations and Rust dispatch were unchanged. No Rust build, version update, or git operation was performed.

## Validation results

- `10 passed`: `tests/test_analysis_pdf_report.py` and `tests/test_planning_pdf_report.py`. Covered frozen inputs, measured/calculated distinctions, legacy data, optional content, button gating, searchable PDF content, page numbering, table text fit, and both page orientations with landscape plots.
- Read the saved Analysis result from `settings.json` without changing it; exported its 10 cycles to a 10-page PDF in the system temporary directory. The renderer received normalized export preferences, matching the production dialog.
- Visually inspected generated portrait summary and landscape plot images. Labels, legends, tables, and page footers fit.
- Patched-block syntax, function docstring audit, lint, formatting, import hygiene, and full-main-file undefined-variable checks passed.
- The initial test run had one incorrect expectation that an export with optional sections disabled had only one mandatory section. Production intentionally includes both summary and run notes; the expectation was corrected and the combined suite rerun successfully.
- Interactive Tk save-dialog clicking was not exercised. The actual builders/renderers/writer and mode/pending button logic were exercised. Broader chemistry suites were not rerun because no solver behavior changed.

## Commands and scope

Commands ran from the repository root using `.\.venv-314t\Scripts\python.exe`:

```powershell
.\.venv-314t\Scripts\python.exe -m pytest tests/test_analysis_pdf_report.py tests/test_planning_pdf_report.py -q
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821 .tmp_analysis_pdf_validation tests/test_analysis_pdf_report.py
.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check .tmp_analysis_pdf_validation tests/test_analysis_pdf_report.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 .tmp_analysis_pdf_validation tests/test_analysis_pdf_report.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 "GL-260 Data Analysis and Plotter.py"
```

Temporary snippets contained `_freeze_analysis_pdf_snapshot`, `_build_analysis_pdf_report`, `_render_analysis_pdf_report`, `_open_planning_pdf_report_options`, `_open_analysis_pdf_report_options`, `_open_workflow_pdf_report_options`, `_update_analysis_pdf_action_state`, `_set_timeline_action_state`, the modified `_compute_cycle_result`/`_on_ok`/`_on_err` callbacks, and the new button, pending-state, and section-choice blocks. The new test file was checked in full. No other full-file lint ran.

Python stdin checks used `compile(source, filename, "exec")` on these extracted blocks and the new test file, and `ast.get_docstring` on their function nodes. All passed. Temporary lint snippets were removed before handoff.

Suggested commit message: `Added Analysis PDF reports using saved cycle data and calculations`
