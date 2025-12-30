# GL-260 Data Analysis and Plotter

## Overview
GL-260 Data Analysis and Plotter is a script-first application for analyzing GL-260 data, generating plots, and running planning workflows.

## Installation
- `python -m venv .venv`
- `activate` (use the activation command for your shell, e.g. `.\.venv\Scripts\Activate.ps1` on PowerShell)
- `pip install -r requirements.txt`

## Running
- `python "GL-260 Data Analysis and Plotter V1.5.0.5.py"`

## Solubility Models
- `solubility_models` is included as a local package folder.
- The NaOH-CO2 Pitzer/HMW model is included and required (`naoh_co2_pitzer_ph_model.py`).
- `pitzer.dat` is included in the repo root; the app searches the current working directory and the script directory. If you run from the repo root, it will be found automatically. You can also pass `--pitzer <path>` to the model.

## Settings & Outputs
- `settings.json` is generated at runtime in the working directory.
- Exported outputs (png/pdf/csv/svg/etc.) are written to the locations you choose in the UI.

## Changelog / Recent Changes
### V1.5.0.0
- Free-threading readiness helpers and Developer Tools GIL controls.
- Unified TkTaskRunner for thread-safe background tasks.
- Dependency free-threading audit tooling and session warning.
- VS Code interpreter switch prompt for GIL-disabled requests.
- No default behavior changes.

### V1.4.0.8
- Persist multi-sheet selected sheets to settings.json and restore on startup.
- "Plot Elements..." opens a Toplevel annotations editor per plot instead of overlaying.
- Break Treeview selection refresh recursion to stabilize selection and deletion.
- Fix annotations Toplevel layout so all controls stay visible (Delete not cut off).

## License
Apache-2.0. See `LICENSE`.
