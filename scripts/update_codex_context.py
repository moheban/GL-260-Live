#!/usr/bin/env python3
"""Build and refresh the repo-scoped Codex context snapshot.

This script generates a compact, deterministic context file that reduces repeated
repo re-discovery after chat compaction. The snapshot is intentionally scoped to
this repository and is designed for task-start priming and milestone updates.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

MANUAL_NOTES_START = "<!-- MANUAL_NOTES_START -->"
MANUAL_NOTES_END = "<!-- MANUAL_NOTES_END -->"

PROJECT_MAP_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("GL-260 Data Analysis and Plotter.py", "Primary Python application entry point."),
    ("rust_ext/src/lib.rs", "Rust acceleration core for compute-heavy paths."),
    ("scripts/validate_rust_backend.py", "Rust/Python backend validation utility."),
    ("settings.json", "Primary runtime configuration/state file."),
    ("AGENTS.md", "Repository operating constraints for Codex runs."),
    ("README.md", "Release notes and implementation history."),
    ("docs/user-manual.md", "End-user workflow documentation."),
)

INVARIANT_SECTIONS: tuple[str, ...] = (
    "RUST CORE + PYTHON FALLBACK INTEGRATION STANDARD",
    "PATCH VALIDATION: LINT / STATIC CHECKS (NON-NEGOTIABLE)",
    "TEMPORARY LINT ARTIFACT CLEANUP (NON-NEGOTIABLE)",
    "NON-BREAKAGE GUARANTEE",
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for snapshot regeneration.

    Purpose:
    - Require a milestone note so each refresh records explicit intent.
    Why:
    - Milestone anchoring keeps snapshot updates meaningful and auditable.
    Inputs:
    - CLI flags from `sys.argv`.
    Outputs:
    - Parsed namespace with `milestone` and optional `focus`.
    Side effects:
    - None.
    Exceptions:
    - `SystemExit` when argument validation fails.
    """

    parser = argparse.ArgumentParser(
        description="Update docs/codex-context.md using repo-local facts."
    )
    parser.add_argument(
        "--milestone",
        required=True,
        help="Required milestone note describing what changed.",
    )
    parser.add_argument(
        "--focus",
        default="",
        help="Optional subsystem focus for the current milestone.",
    )
    return parser.parse_args()


def resolve_repo_root() -> Path:
    """Resolve the repository root from this script path.

    Purpose:
    - Compute a stable root path regardless of current working directory.
    Why:
    - Snapshot generation should not depend on where the command is launched.
    Inputs:
    - None.
    Outputs:
    - Absolute `Path` to repository root.
    Side effects:
    - None.
    Exceptions:
    - `RuntimeError` when the script is not located under a `scripts/` folder.
    """

    script_path = Path(__file__).resolve()
    if script_path.parent.name != "scripts":
        raise RuntimeError(
            "Expected update_codex_context.py to be located inside the scripts "
            "directory."
        )
    return script_path.parent.parent


def read_text_file(path: Path) -> str:
    """Read UTF-8 text content when a file exists.

    Purpose:
    - Centralize file reads for snapshot assembly.
    Why:
    - Missing files should degrade gracefully without special-case branches.
    Inputs:
    - `path`: filesystem path to read.
    Outputs:
    - File text or an empty string when the file is absent.
    Side effects:
    - None.
    Exceptions:
    - `UnicodeDecodeError` for invalid UTF-8 file contents.
    - `OSError` for unreadable paths.
    """

    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_marked_block(text: str, start_marker: str, end_marker: str) -> str:
    """Extract a marker-delimited block from existing snapshot text.

    Purpose:
    - Preserve operator-maintained notes across automated regenerations.
    Why:
    - Human-curated context should survive scripted rewrites.
    Inputs:
    - `text`: full snapshot content.
    - `start_marker`: opening marker token.
    - `end_marker`: closing marker token.
    Outputs:
    - Marker body without surrounding markers, or empty string if not found.
    Side effects:
    - None.
    Exceptions:
    - None; malformed marker layout returns an empty string.
    """

    if not text:
        return ""
    start_index = text.find(start_marker)
    if start_index < 0:
        return ""
    body_start = start_index + len(start_marker)
    end_index = text.find(end_marker, body_start)
    if end_index < 0:
        return ""
    return text[body_start:end_index].strip("\n")


def extract_heading_block(text: str, heading: str) -> str:
    """Return the markdown body for a specific level-2 heading.

    Purpose:
    - Reuse existing section content (for example, decision history).
    Why:
    - Incremental updates should retain prior useful context.
    Inputs:
    - `text`: markdown document.
    - `heading`: heading title without markdown prefix.
    Outputs:
    - Heading body text, stripped of outer blank lines.
    Side effects:
    - None.
    Exceptions:
    - None; absent heading yields an empty string.
    """

    pattern = rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def dedupe_preserve_order(items: list[str]) -> list[str]:
    """De-duplicate lines while preserving first-seen order.

    Purpose:
    - Keep stable output and avoid repetitive entries over time.
    Why:
    - Deterministic snapshots reduce diff noise and token overhead.
    Inputs:
    - `items`: candidate lines in preferred order.
    Outputs:
    - Ordered list with duplicates removed.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def collect_project_map(repo_root: Path) -> list[str]:
    """Assemble the project map section using known critical paths.

    Purpose:
    - Surface high-value files for quick orientation at task start.
    Why:
    - Large repositories benefit from a stable, minimal entrypoint map.
    Inputs:
    - `repo_root`: absolute path to repository root.
    Outputs:
    - Ordered markdown bullet lines for existing critical files.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    lines: list[str] = []
    for relative_path, description in PROJECT_MAP_CANDIDATES:
        if (repo_root / relative_path).exists():
            lines.append(f"- `{relative_path}`: {description}")
    return lines


def extract_section_bullets(agents_text: str, section_header: str) -> list[str]:
    """Extract bullet lines from one AGENTS.md section.

    Purpose:
    - Pull invariant rules directly from authoritative repository policy.
    Why:
    - Snapshot invariants should remain aligned with AGENTS.md without manual copy.
    Inputs:
    - `agents_text`: full AGENTS markdown content.
    - `section_header`: exact section title to extract.
    Outputs:
    - Bullet lines from the target section.
    Side effects:
    - None.
    Exceptions:
    - None; absent sections return an empty list.
    """

    lines = agents_text.splitlines()
    section_index = -1
    for idx, line in enumerate(lines):
        if line.strip() == section_header:
            section_index = idx
            break
    if section_index < 0:
        return []

    start_index = section_index + 1
    if start_index < len(lines) and re.fullmatch(r"-{5,}", lines[start_index].strip()):
        start_index += 1

    collected: list[str] = []
    cursor = start_index
    while cursor < len(lines):
        current = lines[cursor].strip()
        # Stop when the next "header sandwich" starts: dashed line, title, dashed line.
        if (
            re.fullmatch(r"-{5,}", current)
            and cursor + 2 < len(lines)
            and lines[cursor + 1].strip()
            and re.fullmatch(r"-{5,}", lines[cursor + 2].strip())
        ):
            break
        if current.startswith("- "):
            collected.append(current)
        cursor += 1
    return collected


def collect_current_invariants(repo_root: Path) -> list[str]:
    """Build the current invariants section from AGENTS policy text.

    Purpose:
    - Snapshot non-negotiable engineering constraints for quick recall.
    Why:
    - Context compaction should not drop guardrails that prevent regressions.
    Inputs:
    - `repo_root`: absolute path to repository root.
    Outputs:
    - Ordered invariant bullets with duplicates removed.
    Side effects:
    - Reads `AGENTS.md`.
    Exceptions:
    - Propagates file read errors from `read_text_file`.
    """

    agents_text = read_text_file(repo_root / "AGENTS.md")
    if not agents_text:
        return ["- AGENTS.md not found; invariants unavailable."]

    invariant_lines: list[str] = []
    for section_header in INVARIANT_SECTIONS:
        invariant_lines.extend(extract_section_bullets(agents_text, section_header))

    if not invariant_lines:
        return ["- No invariant bullets extracted from AGENTS.md sections."]
    return dedupe_preserve_order(invariant_lines)


def extract_latest_release_heading(repo_root: Path) -> str:
    """Return the latest release heading from README as context anchor.

    Purpose:
    - Include release-oriented context discovered through targeted text search.
    Why:
    - Task planning benefits from recent release trajectory awareness.
    Inputs:
    - `repo_root`: absolute repository path.
    Outputs:
    - Latest markdown release heading or fallback text.
    Side effects:
    - Reads `README.md`.
    Exceptions:
    - Propagates file read errors from `read_text_file`.
    """

    readme_text = read_text_file(repo_root / "README.md")
    headings = re.findall(r"(?m)^###\s+(v[0-9]+\.[0-9]+\.[0-9]+[^\n]*)", readme_text)
    if headings:
        return headings[-1].strip()
    return "No semantic release heading found in README.md."


def extract_recent_decisions(existing_snapshot: str) -> list[str]:
    """Load prior decision bullets from the existing snapshot.

    Purpose:
    - Preserve recent decision continuity across updates.
    Why:
    - Historical context reduces repeated backtracking during long tasks.
    Inputs:
    - `existing_snapshot`: current snapshot text if available.
    Outputs:
    - Ordered list of decision bullets from `Recent Decisions`.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    block = extract_heading_block(existing_snapshot, "Recent Decisions")
    if not block:
        return []
    return [
        line.strip() for line in block.splitlines() if line.strip().startswith("- ")
    ]


def render_snapshot(
    milestone_note: str, focus_area: str, repo_root: Path, existing_snapshot: str
) -> str:
    """Render the full snapshot markdown in a deterministic section order.

    Purpose:
    - Produce the canonical repo-scoped context snapshot content.
    Why:
    - Stable formatting minimizes diff churn and keeps task-start primers compact.
    Inputs:
    - `milestone_note`: required operator-provided summary of milestone.
    - `focus_area`: optional subsystem emphasis.
    - `repo_root`: repository root path.
    - `existing_snapshot`: prior snapshot text for block preservation.
    Outputs:
    - Full markdown document text.
    Side effects:
    - Reads repo files through helper functions.
    Exceptions:
    - Propagates helper exceptions for invalid file operations.
    """

    now_utc = datetime.now(timezone.utc)
    iso_timestamp = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_stamp = now_utc.date().isoformat()
    focus_value = focus_area.strip() if focus_area.strip() else "Not specified"

    project_map_lines = collect_project_map(repo_root)
    invariants = collect_current_invariants(repo_root)
    release_anchor = extract_latest_release_heading(repo_root)

    decision_line = (
        f"- {date_stamp}: {milestone_note.strip()}. "
        "Rationale: maintain durable, repo-scoped context after chat compaction."
    )
    if focus_area.strip():
        decision_line += f" Focus: {focus_area.strip()}."
    historical_decisions = extract_recent_decisions(existing_snapshot)
    recent_decisions = dedupe_preserve_order([decision_line, *historical_decisions])[
        :12
    ]

    manual_notes_body = extract_marked_block(
        existing_snapshot, MANUAL_NOTES_START, MANUAL_NOTES_END
    )
    if not manual_notes_body.strip():
        manual_notes_body = (
            "- Add local debugging shortcuts, unresolved risks, and handoff notes here."
        )

    validation_commands = [
        (
            '- `python scripts/update_codex_context.py --milestone "<note>" '
            '[--focus "<area>"]`'
        ),
        "- `python scripts/validate_rust_backend.py`",
        "- `python -m pytest -q`",
        '- `python -m py_compile "GL-260 Data Analysis and Plotter.py"`',
    ]

    open_work_lines = [
        f"- Active milestone anchor: {milestone_note.strip()}",
        f"- Current focus area: {focus_value}",
        f"- Release context anchor: {release_anchor}",
        (
            "- Refresh this snapshot after each major milestone, not after every "
            "minor edit."
        ),
        "- Keep Manual Notes updated with current blockers and local runbook details.",
    ]

    rendered_lines = [
        "# Codex Context Snapshot",
        "",
        "## Project Map",
        *project_map_lines,
        "",
        "## Current Invariants",
        *invariants,
        "",
        "## Open Work / Next Actions",
        *open_work_lines,
        "",
        MANUAL_NOTES_START,
        manual_notes_body,
        MANUAL_NOTES_END,
        "",
        "## Recent Decisions",
        *recent_decisions,
        "",
        "## Validation Commands",
        *validation_commands,
        "",
        "## Snapshot Metadata",
        f"- Last updated (UTC): {iso_timestamp}",
        "- Owner: Codex + repository maintainers",
        "- Scope: Repository-local context primer",
        "- Primer policy: Load this file at task start before broad exploration",
        "- Refresh cadence: Per major milestone",
        "- Stale threshold: 24 hours",
        f"- Last milestone note: {milestone_note.strip()}",
        f"- Last focus area: {focus_value}",
        "",
    ]
    return "\n".join(rendered_lines)


def write_snapshot(snapshot_path: Path, content: str) -> None:
    """Persist snapshot content to docs/codex-context.md.

    Purpose:
    - Save generated snapshot content in its canonical repository location.
    Why:
    - Task-start workflows need a stable on-disk primer path.
    Inputs:
    - `snapshot_path`: destination file path.
    - `content`: markdown content to write.
    Outputs:
    - None.
    Side effects:
    - Creates parent directories as needed and writes UTF-8 file content.
    Exceptions:
    - `OSError` for path creation/write failures.
    """

    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(content, encoding="utf-8")


def main() -> None:
    """Run CLI workflow to refresh the repo context snapshot.

    Purpose:
    - Tie argument parsing, snapshot rendering, and file output together.
    Why:
    - Provide a single repeatable command for milestone-based context updates.
    Inputs:
    - CLI options parsed by `parse_args()`.
    Outputs:
    - Prints updated snapshot path on success.
    Side effects:
    - Reads repository files and writes `docs/codex-context.md`.
    Exceptions:
    - Propagates parsing/path/file exceptions with non-zero process exit.
    """

    args = parse_args()
    repo_root = resolve_repo_root()
    snapshot_path = repo_root / "docs" / "codex-context.md"
    existing_snapshot = read_text_file(snapshot_path)
    rendered = render_snapshot(args.milestone, args.focus, repo_root, existing_snapshot)
    write_snapshot(snapshot_path, rendered)
    print(f"Updated snapshot: {snapshot_path}")


if __name__ == "__main__":
    main()
