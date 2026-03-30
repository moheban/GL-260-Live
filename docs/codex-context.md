# Codex Context Snapshot

## Project Map
- `GL-260 Data Analysis and Plotter.py`: Primary Python application entry point.
- `rust_ext/src/lib.rs`: Rust acceleration core for compute-heavy paths.
- `scripts/validate_rust_backend.py`: Rust/Python backend validation utility.
- `scripts/update_codex_context.py`: Context snapshot/checkpoint updater CLI.
- `settings.json`: Primary runtime configuration/state file.
- `AGENTS.md`: Repository operating constraints for Codex runs.
- `docs/codex-context.md`: Compact task-start context primer.
- `docs/codex-session-context.md`: Append-only session checkpoint excerpts.
- `README.md`: Release notes and implementation history.
- `docs/user-manual.md`: End-user workflow documentation.

## Current Invariants
- Implement or extend Rust core paths where applicable
- Preserve a functional Python fallback path
- Validate Rust/Python parity or consistency where practical
- Fail safely to Python fallback if Rust path is unavailable, incompatible, or unhealthy
- UI-only edits and documentation-only edits do not require Rust-core expansion.
- Modified functions
- Modified classes
- Modified code blocks
- Directly adjacent context required for correctness
- Prefer: ruff check <patched code blocks>
- Else: pyflakes <patched code blocks>
- Prefer: ruff format --check <patched code blocks>
- Else: black --check <patched code blocks>
- Prefer: ruff (F401/F811/etc on patched blocks)
- Else: isort --check-only <patched imports>
- Ruff must not be run against the full file or repository.
- Lint only extracted patched regions.
- If full-file linting creates massive output, that is a scope-control failure.
- If patched-block linting fails:
- Fix only issues in patched blocks
- Re-run checks
- Do not expand lint scope beyond the patch
- Report exact commands run
- Report which patched blocks were checked
- Report pass/fail status
- Root-level temporary patch snippets (for example: .tmp_*patch*.py)
- Temporary patch validation directories and generated contents (for example: .tmp_patch_validation/)
- Any equivalent throwaway files created solely to lint/check patched code blocks
- Cleanup must run before final task completion output.
- Cleanup must run even when lint/static checks fail ("Delete Always" policy).
- If cleanup fails for any target, stop and report cleanup failure as an explicit blocker.
- Do not leave temporary patch-lint artifacts in the working tree at handoff.

## Open Work / Next Actions
- Active checkpoint anchor: Validated v4.12.3 equilibrium-primary pH implementation
- Current focus area: scoped patch validation and docs sync
- Collaboration mode: default
- Source session id: 019d3fb2-2012-70a0-85f2-8011171dbc73
- Turn window used: 30
- Session checkpoint id: CHK-20260330T185654Z-f229f274
- Session checkpoint file: docs/codex-session-context.md
- Release context anchor: v2.0.1 Update Highlights
- Refresh this snapshot at every meaningful checkpoint, including planning-only checkpoints with no code edits.
- Keep Manual Notes updated with blockers, local runbook details, and handoff assumptions.

<!-- MANUAL_NOTES_START -->
- Add local debugging shortcuts, unresolved risks, and handoff notes here.
<!-- MANUAL_NOTES_END -->

## Recent Decisions
- 2026-03-30: Validated v4.12.3 equilibrium-primary pH implementation. Rationale: preserve recoverable user/assistant context across compaction. Mode: default. Focus: scoped patch validation and docs sync.
- 2026-03-30: Implemented v4.12.3 equilibrium-primary pH surfaces and docs sync. Rationale: preserve recoverable user/assistant context across compaction. Mode: default. Focus: advanced speciation timeline contract.
- 2026-03-30: Auto checkpoint (plan): # Context from my IDE setup: ## Active file: .gitignore ## Open tabs: - . Rationale: preserve recoverable user/assistant context across compaction. Mode: plan.
- 2026-03-30: Auto checkpoint (default): # Context from my IDE setup: ## Active file: .gitignore ## Open tabs: - . Rationale: preserve recoverable user/assistant context across compaction. Mode: default.
- 2026-03-30: Auto checkpoint (plan): # Context from my IDE setup: ## Active file: settings.json ## Open tabs:. Rationale: preserve recoverable user/assistant context across compaction. Mode: plan.
- 2026-03-30: codex90. Rationale: preserve recoverable user/assistant context across compaction. Mode: default.
- 2026-03-30: codex87. Rationale: preserve recoverable user/assistant context across compaction. Mode: default.
- 2026-03-30: codex. Rationale: preserve recoverable user/assistant context across compaction. Mode: default.
- 2026-03-30: Milestone refresh verification. Rationale: maintain durable, repo-scoped context after chat compaction. Focus: snapshot refresh test.
- 2026-03-30: Bootstrap repo-scoped context snapshot workflow. Rationale: maintain durable, repo-scoped context after chat compaction. Focus: context retention.

## Session Recovery Anchor
- Last checkpoint id: CHK-20260330T185654Z-f229f274
- Companion context file: `docs/codex-session-context.md`
- Collaboration mode: default
- Source session id: 019d3fb2-2012-70a0-85f2-8011171dbc73
- Source session file: C:\Users\mmoheban\.codex\sessions\2026\03\30\rollout-2026-03-30T13-02-11-019d3fb2-2012-70a0-85f2-8011171dbc73.jsonl
- Turn window used: 30
- Fingerprint: f229f274a404b2f2587436aa47c85d49f2a2ded1f7d7dbcfbd5ccd0cb4961d79

## Validation Commands
- `python scripts/update_codex_context.py [--milestone "<note>"] [--focus "<area>"]`
- `python scripts/update_codex_context.py`
- `python scripts/validate_rust_backend.py`
- `python -m pytest -q`
- `python -m py_compile "GL-260 Data Analysis and Plotter.py"`

## Snapshot Metadata
- Last updated (UTC): 2026-03-30T18:56:54Z
- Owner: Codex + repository maintainers
- Scope: Repository-local context primer
- Primer policy: Load this file at task start before broad exploration
- Refresh cadence: Every meaningful checkpoint
- Stale threshold: 24 hours
- Last checkpoint label: Validated v4.12.3 equilibrium-primary pH implementation
- Last focus area: scoped patch validation and docs sync
- Last collaboration mode: default
- Last source session id: 019d3fb2-2012-70a0-85f2-8011171dbc73
- Last source session file: C:\Users\mmoheban\.codex\sessions\2026\03\30\rollout-2026-03-30T13-02-11-019d3fb2-2012-70a0-85f2-8011171dbc73.jsonl
- Last turn window used: 30
- Last session checkpoint id: CHK-20260330T185654Z-f229f274
- Last session fingerprint: f229f274a404b2f2587436aa47c85d49f2a2ded1f7d7dbcfbd5ccd0cb4961d79
