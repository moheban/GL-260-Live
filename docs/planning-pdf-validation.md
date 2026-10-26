# Planning PDF report validation

The Planning action row now exports a frozen completed sodium carbonate scenario through the existing Reaction Dashboard renderer and PDF writer. No chemistry kernels or Rust dispatch changed. The first page preserves full-charge count, final pressure, target pH, guard verification, and warnings. Supporting sections are optional. TrueType font embedding in the shared writer preserves searchable report text.

## Targeted validation

Passed: 5 cases covering saved nonlinear pressure setpoints, snapshot independence, optional sections, integer-cycle and mass-dose plans, unavailable or inconsistent schedules, both page orientations, text fitting within table cells, PDF metadata/text/page numbering, and Planning-only action availability.

Commands (repository root):

```powershell
.\.venv-314t\Scripts\python.exe -m pytest -q tests/test_planning_pdf_report.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821 .tmp_planning_pdf_validation tests/test_planning_pdf_report.py
.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check .tmp_planning_pdf_validation tests/test_planning_pdf_report.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 .tmp_planning_pdf_validation tests/test_planning_pdf_report.py
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 "GL-260 Data Analysis and Plotter.py"
```

All listed checks passed. Extracted patched blocks also passed Python `compile` and an AST docstring audit. Snippet scope: `_build_planning_pdf_report`, `_render_planning_pdf_report`, `_write_reaction_dashboard_cycle_pdf`, `_publish_planning_comparison_baseline`, `_set_timeline_action_state`, `_update_planning_pdf_action_state`, `_open_planning_pdf_report_options`, `_run_planning_scenario`, the Planning action-button block, and `PLANNING_PDF_REPORT_SECTIONS`. Temporary snippets were removed after validation.

Interactive Tk save-dialog testing and broader application regressions were not run; automated checks exercised the real report renderer/writer and the action-state method. Rust rebuilding is not applicable to this report/UI change.

Visual inspection of the saved Planning scenario confirmed the first-page charge cards, wrapped instruction table, and footer render without clipping.

## Always-landscape plot page

The plot renderer now uses 11 x 8.5 inch pages independently of table-page preferences. The existing portrait/landscape PDF checks verify the actual saved PDF page dimensions: plot pages remain landscape and every table page follows the selected orientation. No chemistry or Rust paths changed.

Scoped checks cover only `_render_planning_pdf_report` and `test_pdf_pages_and_metadata`; syntax compilation and the docstring audit passed. Exact commands:

```powershell
.\.venv-314t\Scripts\python.exe -m pytest -q tests/test_planning_pdf_report.py -k pdf_pages_and_metadata
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --ignore F821 .tmp_landscape_validation
.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check .tmp_landscape_validation
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 .tmp_landscape_validation
.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 "GL-260 Data Analysis and Plotter.py"
```

All static checks passed after wrapping the updated docstring and formatting the two patched functions. Temporary snippets were removed after validation.
`pdf_pages_and_metadata`: 2 passed, 3 deselected; both saved PDF orientations verified.
