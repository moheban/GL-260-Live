# Codex Context Snapshot

## Project Map
- `GL-260 Data Analysis and Plotter.py`: Primary Python application entry point.
- `rust_ext/src/lib.rs`: Rust acceleration core for compute-heavy paths.
- `scripts/validate_rust_backend.py`: Rust/Python backend validation utility.
- `settings.json`: Primary runtime configuration/state file.
- `AGENTS.md`: Repository operating constraints for Codex runs.
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
- Active milestone anchor: Milestone refresh verification
- Current focus area: snapshot refresh test
- Release context anchor: v2.0.1 Update Highlights
- Refresh this snapshot after each major milestone, not after every minor edit.
- Keep Manual Notes updated with current blockers and local runbook details.

<!-- MANUAL_NOTES_START -->
- Add local debugging shortcuts, unresolved risks, and handoff notes here.
<!-- MANUAL_NOTES_END -->

## Recent Decisions
- 2026-03-30: Milestone refresh verification. Rationale: maintain durable, repo-scoped context after chat compaction. Focus: snapshot refresh test.
- 2026-03-30: Bootstrap repo-scoped context snapshot workflow. Rationale: maintain durable, repo-scoped context after chat compaction. Focus: context retention.

## Validation Commands
- `python scripts/update_codex_context.py --milestone "<note>" [--focus "<area>"]`
- `python scripts/validate_rust_backend.py`
- `python -m pytest -q`
- `python -m py_compile "GL-260 Data Analysis and Plotter.py"`

## Snapshot Metadata
- Last updated (UTC): 2026-03-30T14:37:17Z
- Owner: Codex + repository maintainers
- Scope: Repository-local context primer
- Primer policy: Load this file at task start before broad exploration
- Refresh cadence: Per major milestone
- Stale threshold: 24 hours
- Last milestone note: Milestone refresh verification
- Last focus area: snapshot refresh test
