# CSV import acceleration investigation

Date: 2026-10-30. Includes the original investigation and completed implementation.

## Implementation follow-up (2026-10-30)

The requested implementation is now integrated. The original investigation below
is retained as baseline evidence. No application or crate version was changed.

- `rust_ext/src/csv_io.rs`, registered through `rust_ext/src/lib.rs`, provides
  `csv_table_core`, `write_csv_workbook_core` and `validate_csv_worksheet_core`.
  The CSV kernel uses decoded text and preserves the existing Python metadata
  rules. Preview remains bounded/streaming in Python. The worksheet kernel accepts
  numeric column buffers and text columns, writes buffered XML, and raw-copies
  unrelated compressed ZIP members.
- `gl260_csv_io.py` edits only necessary workbook metadata, appends a date style
  without renumbering existing styles, and handles 1900/1904 date epochs. It checks
  CRCs, unrelated member identities, metadata XML, readable headers, dimensions,
  worksheet XML closure and consecutive row numbers. Native validation avoids
  creating millions of Python XML objects. Text serialization matches the
  installed openpyxl serializer's carriage-return behavior.
- Both native and Python writers operate on a temporary sibling, flush the
  candidate with a writable handle (required on Windows), check for intervening
  destination changes, and use `os.replace` only after validation. Temporary
  candidates are removed on success and failure. A locked destination propagates
  an error without changing the original.
- Python-only mode, older/missing kernels and unhealthy backends remain supported.
  Native execution/validation failures trigger Python retry and health reporting.
  Known unsupported cases (signed packages, calculation chains, complex worksheet
  overwrites with relationships/names, case-insensitive name collisions and mixed
  object columns) use the established Python writer transactionally. Raw ZIP-part
  identity preservation applies to the native path; the fallback retains
  openpyxl's existing serialization behavior.

### Measured results

The saved real CSV contains **66,885 data rows**. Full parsing took **0.239 s in
Python** and **0.119 s in Rust**, with identical headers, rows and channel metadata.

A 100,000-row, 31-column numeric/date worksheet took **6.420 s** to write, validate
and commit into a nearly empty workbook. The investigation's Python write baseline
was **55.934 s** for the same row/column counts (different generated values and
separate runs). This is approximately an 8.7x reduction versus that baseline,
not a guarantee for every file. The native transaction took **8.108 s** when
appending to a copy of the actual 42.5 MB master workbook. SHA-256 comparisons
confirmed all **12 unrelated ZIP entries** retained identical content. The user's
original workbook was never modified by these checks.

The first native prototype took 24.874 s on the empty workbook and 29.180 s on
the master copy. Buffering XML fragments before compression and moving full-sheet
XML validation to Rust removed much of that remaining overhead. Validation still
reads the existing archive for CRC checks, so cost is not independent of size.

### Validation and exact command record

All 15 focused tests passed against both the release DLL and the installed
extension (15 passed in 51.04 s for the installed run). They cover date epochs,
formulas/errors/booleans/missing values, styles/merged cells, unrelated package
contents, overwrite/autosuffix/error modes, native failure fallback, validation
rejection, locked-destination failure, incomplete XML, encoding parity, streaming
preview, randomized quoted/multiline CSV and Python-only parser routing.

Commands were run from the repository root. Build commands used
`PYO3_PYTHON` pointing at `.venv-314t/Scripts/python.exe`,
`CARGO_TARGET_DIR=%LOCALAPPDATA%/gl260-csv-rust-target`, and the user's
`mingw64/bin` prepended to PATH. Packaging additionally set
`RUSTUP_TOOLCHAIN=stable-x86_64-pc-windows-gnu`.

- `Get-Command cargo -All`; `cargo --version`;
  `Test-Path "$env:USERPROFILE/.cargo/bin/cargo.exe"`;
  `& "$env:USERPROFILE/.cargo/bin/cargo.exe" +stable-x86_64-pc-windows-gnu --version`.
  Usable rustup Cargo 1.93.1 was confirmed; the Python shim was not used.
- `cargo +stable-x86_64-pc-windows-gnu check --manifest-path rust_ext/Cargo.toml --target x86_64-pc-windows-gnu`.
  The initial check caught a ZIP API type mismatch, corrected before the release build.
- `cargo +stable-x86_64-pc-windows-gnu build --release --manifest-path rust_ext/Cargo.toml --target x86_64-pc-windows-gnu`.
  Passed; emitted ten existing warnings in unrelated numerical code.
- `.\.venv-314t\Scripts\python.exe -X utf8 -m maturin build --release --manifest-path rust_ext/Cargo.toml --target x86_64-pc-windows-gnu --interpreter .\.venv-314t\Scripts\python.exe --out "$env:LOCALAPPDATA\gl260-csv-rust-target\wheels"`.
  Passed and produced the CPython 3.14t wheel.
- `.\.venv-314t\Scripts\python.exe -X utf8 -m pip install --force-reinstall --no-deps "$env:LOCALAPPDATA\gl260-csv-rust-target\wheels\gl260_rust_ext-0.1.0-cp314-cp314t-win_amd64.whl"`.
  Installed successfully; new processes expose all three kernels. An already-running
  application must restart to use the replacement DLL.
  Pip retained an old binary in `site-packages/~0860_rust_ext`; automatic approval
  review rejected its cleanup with "blocked by policy", so that backup was left
  in place. It is not the active installed module.
- `.\.venv-314t\Scripts\python.exe -X utf8 -m pytest tests/test_csv_native_io.py -q --tb=short`.
  Native build tests used `GL260_TEST_RUST_PATH` pointing at the release DLL;
  the installed-backend run omits that override.
- `.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E4,E7,E9,F --ignore F821 .tmp_patch_validation`.
- `.\.venv-314t\Scripts\python.exe -m ruff format --target-version py312 --check .tmp_patch_validation`.
- `.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select E9,F401,F811 .tmp_patch_validation`.
- `.\.venv-314t\Scripts\python.exe -m ruff check --target-version py312 --select F821 "GL-260 Data Analysis and Plotter.py"`.
- `& "$env:USERPROFILE/.cargo/bin/rustfmt.exe" --edition 2024 --check rust_ext/src/csv_io.rs`.

Scoped Python checks use copies of the new module/test code plus only the modified
entry-file functions: `_parse_gl260_csv_table_with_metadata`,
`_csv_import_native_backend`, `_write_gl260_output_sheet`, and
`_write_gl260_output_sheet_python`. Syntax was checked with Python `compile` on
these regions, and their docstrings were verified using AST. Lint, formatting,
import hygiene and full-entry-file F821 checks passed. Main-file UTF-8 BOM and CRLF
encoding were preserved. Temporary patch snippets are removed at handoff.
Broader unrelated application tests were not run; validation targets CSV import,
native integration and the transaction failure paths changed here.

Benchmarks ran as inline stdin harnesses with
`.\.venv-314t\Scripts\python.exe -X utf8 -`, using temporary directories and the
actual production functions. Rust API references:
[raw ZIP copying](https://docs.rs/zip/2.4.2/zip/write/struct.ZipWriter.html#method.raw_copy_file),
[CSV reader configuration](https://docs.rs/csv/latest/csv/struct.ReaderBuilder.html),
and [streaming XML validation](https://docs.rs/quick-xml/latest/quick_xml/reader/struct.Reader.html).

## Finding

Prioritize workbook serialization over CSV parsing. The importer already routes
pressure derivatives, smoothing, and moving averages through the optional Rust
array kernel. CSV parsing and Excel output still run in Python.

The saved CSV has 66,909 physical lines (including metadata). Its destination
workbook is 42,455,121 bytes, with eight worksheet XML parts totaling 246.3 MiB
uncompressed. Only file metadata and ZIP contents were inspected; the user's
workbook and CSV were not modified.

The production `_write_gl260_output_sheet` loads the entire existing workbook,
appends each output row as Python cell objects, and saves the entire workbook.
Import cost therefore depends on existing workbook contents as well as imported
row count. Subsequent sheet loading can add latency outside the import timings.

## Measurement method

Executed production functions extracted through Python AST, without starting the
GUI, using `.venv-314t/Scripts/python.exe -X utf8 -` with an inline stdin harness.
Synthetic inputs contain eight numeric channels and second-resolution timestamps;
six pressure channels produce 31 output columns with all calculations enabled.
Each write targets a temporary workbook initially containing one empty sheet.
These are stage measurements, not timings of the user's complete UI workflow.
The saved mapping uses two pressure channels, so its output width differs.

The 50,000-row run took 0.703 seconds to parse and 4.403 seconds to transform
using the Python derivative fallback. Its **profiled** write took 103.370 seconds.
cProfile attributed 88.633 seconds to workbook saving and 76.282 cumulative
seconds to `openpyxl.cell._writer.etree_write_cell`. Profiling adds overhead;
this write duration must not be compared as a normal throughput benchmark.

The installed Rust array kernel passed comparison against the Python derivative,
smoothed derivative, and moving average arrays at 50,000 rows and six traces,
including matching NaNs (relative tolerance 1e-9, absolute tolerance 1e-8).
Direct kernel times were 0.378 seconds for Rust and 0.963 seconds for Python.
These exclude application backend loading, timeout routing, and health checks.

The **unprofiled** 100,000-row run measured:

| Stage | Seconds |
| --- | ---: |
| CSV parse | 0.447 |
| Dataframe construction and transform (Python derivatives) | 3.279 |
| Excel write | 55.934 |
| Total of measured stages | 59.660 |

Writing accounts for 93.8% of those measured stages. Direct six-trace derivative
timings were 0.874 seconds in Python and 0.299 seconds in Rust (2.93x), with the
same numerical parity checks passing. These are single-run observations;
startup/cache effects and machine load prevent interpreting the different row
counts as a scaling curve. The temporary benchmark directory and workbooks were
removed by the harness on successful completion.

## Recommended implementation order

1. Add a capability-gated Rust worksheet-writing path in `rust_ext/src/lib.rs`.
   Generate worksheet XML from typed column buffers, avoiding Python cell objects.
   Preserve unrelated workbook package parts rather than loading and serializing
   every existing worksheet. Update workbook relationships, content types, styles,
   and sheet metadata consistently. Preserve overwrite/error/autosuffix behavior,
   date formats, missing values, strings, column order, and frozen headers.
2. Write to a temporary sibling file, validate the result, then replace the target
   only after successful completion. Retain the existing openpyxl path for
   unsupported workbook features, missing Rust capabilities, or native failures.
   Package preservation and overwrite references need explicit validation before
   enabling this path for existing user workbooks.
3. Then consider a Rust CSV parser that preserves Graphtec metadata, encoding
   fallback, quoting, header normalization, units-row handling, preview limits,
   and short/long-row behavior. Return typed columns to reduce intermediate lists
   and repeated string conversions. Keep the current parser as the fallback.
4. Validate on a copy of the saved large workbook, checking untouched worksheets,
   formulas, styles, relationships, and the imported data. Measure parse,
   transform, write, and post-import refresh separately. No native writer speedup
   is claimed until such an implementation is benchmarked.

## Environment and validation boundaries

Saved backend setting: `auto`. Installed extension exports
`csv_pressure_derivatives_array_core`. Source locations: Python parser at line
97026, transformer at 97694, writer at 97886, import worker near 112122;
Rust array kernel at line 5445.

Cargo preflight resolved `C:/Users/mmoheban/.cargo/bin/cargo.exe` ahead of the
Python Scripts shim; `cargo --version` returned
`cargo 1.93.1 (083ac5135 2025-12-15)`. The user Cargo executable exists.
No `link.exe` command was visible in the current PATH. No rebuild was needed or
attempted: comparisons used the installed extension. No application code was
patched, so patch lint and broader regression tests were not applicable.

The context resume command required `-X utf8` because the console's default
cp1252 encoding could not print an existing Unicode checkpoint. Context snapshots
were refreshed using the same UTF-8 interpreter option.
