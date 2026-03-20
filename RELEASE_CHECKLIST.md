# GL-260 Release Checklist

Use this checklist for every user-facing feature patch, bug fix that changes workflow behavior, and release candidate.

## Documentation Gate (Mandatory)

- [ ] `docs/user-manual.md` reviewed for impact from this release.
- [ ] Any changed workflow has updated sections with:
  - [ ] Purpose
  - [ ] Preconditions
  - [ ] Inputs
  - [ ] Step-by-step actions
  - [ ] Expected outputs
  - [ ] Common errors and recovery
  - [ ] Related exports/artifacts
- [ ] Screenshots in `docs/assets/screenshots/` updated where UI/flow changed.
- [ ] Added/updated alt text and figure captions in `docs/user-manual.md`.
- [ ] Rebuilt docs HTML: `python scripts/build_user_manual.py`.
- [ ] HTML freshness check passed: `python scripts/build_user_manual.py --check`.

## Functional Validation Gate

- [ ] Smoke-test affected workflow paths in app UI.
- [ ] Validate output artifacts for touched workflows (plots/reports/CSV/JSON/PDF/HTML as applicable).
- [ ] Confirm no regression in default path: Data -> Columns -> Plot -> Cycle -> Final Report.

## Release Readiness Gate

- [ ] `README.md` canonical manual notice and links remain correct.
- [ ] Changelog/ledger entry updated for user-visible behavior changes.
- [ ] Dependencies updated when docs/tooling changes introduce new requirements.
- [ ] Final pre-release pass confirms manual and app behavior are aligned.
