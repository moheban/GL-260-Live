#!/usr/bin/env python3
"""Build and refresh the repo-scoped Codex context snapshot.

This script generates a compact, deterministic context file that reduces repeated
repo re-discovery after chat compaction. The snapshot is intentionally scoped to
this repository and is designed for task-start priming and milestone updates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANUAL_NOTES_START = "<!-- MANUAL_NOTES_START -->"
MANUAL_NOTES_END = "<!-- MANUAL_NOTES_END -->"
DEFAULT_TURN_LIMIT = 30
CHECKPOINT_HEADER = "# Codex Session Context"
CHECKPOINT_LOG_HEADER = "## Checkpoint Log"
SESSION_ROOT = Path.home() / ".codex" / "sessions"

PROJECT_MAP_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("GL-260 Data Analysis and Plotter.py", "Primary Python application entry point."),
    ("rust_ext/src/lib.rs", "Rust acceleration core for compute-heavy paths."),
    ("scripts/validate_rust_backend.py", "Rust/Python backend validation utility."),
    ("scripts/update_codex_context.py", "Context snapshot/checkpoint updater CLI."),
    ("settings.json", "Primary runtime configuration/state file."),
    ("AGENTS.md", "Repository operating constraints for Codex runs."),
    ("docs/codex-context.md", "Compact task-start context primer."),
    ("docs/codex-session-context.md", "Append-only session checkpoint excerpts."),
    ("README.md", "Release notes and implementation history."),
    ("docs/user-manual.md", "End-user workflow documentation."),
)

INVARIANT_SECTIONS: tuple[str, ...] = (
    "RUST CORE + PYTHON FALLBACK INTEGRATION STANDARD",
    "PATCH VALIDATION: LINT / STATIC CHECKS (NON-NEGOTIABLE)",
    "TEMPORARY LINT ARTIFACT CLEANUP (NON-NEGOTIABLE)",
    "NON-BREAKAGE GUARANTEE",
)


@dataclass
class TurnEntry:
    """Container for one persisted user/assistant turn excerpt."""

    role: str
    phase: str
    text: str


@dataclass
class SessionContext:
    """Container for session metadata and extracted turn excerpts."""

    session_file: Path | None
    session_id: str
    collaboration_mode: str
    session_timestamp: str
    turns: list[TurnEntry]
    turn_limit: int
    fingerprint: str


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
        default="",
        help="Optional milestone note describing what changed.",
    )
    parser.add_argument(
        "--focus",
        default="",
        help="Optional subsystem focus for the current milestone.",
    )
    parser.add_argument(
        "--turn-limit",
        type=int,
        default=DEFAULT_TURN_LIMIT,
        help="Number of recent user/assistant turns to checkpoint.",
    )
    parser.add_argument(
        "--session-file",
        default="",
        help="Optional explicit session jsonl path for debugging.",
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


def write_text_file(path: Path, content: str) -> None:
    """Write UTF-8 text content to disk at the requested path.

    Purpose:
    - Centralize text writes for snapshot and session-checkpoint documents.
    Why:
    - Shared write behavior keeps output encoding and parent-dir handling stable.
    Inputs:
    - `path`: destination file path.
    - `content`: UTF-8 text payload to persist.
    Outputs:
    - None.
    Side effects:
    - Creates parent directories as needed and writes file contents.
    Exceptions:
    - `OSError` for parent creation or file write failures.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def normalize_whitespace(text: str) -> str:
    """Normalize multi-line text to stable single-spacing for dedupe/fingerprints.

    Purpose:
    - Normalize text from multiple event payload formats into a comparable form.
    Why:
    - Session logs can duplicate turns across event channels with tiny spacing diffs.
    Inputs:
    - `text`: raw message text.
    Outputs:
    - Normalized text with collapsed whitespace and trimmed edges.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    return re.sub(r"\s+", " ", text or "").strip()


def normalize_path(path: Path | str) -> str:
    """Normalize filesystem paths for robust path comparisons.

    Purpose:
    - Compare cwd values from session logs with local repo root reliably.
    Why:
    - Windows path casing and separator differences can otherwise miss matches.
    Inputs:
    - `path`: filesystem path object or string.
    Outputs:
    - Normalized lowercase string representation.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    resolved = str(Path(path).resolve())
    return resolved.replace("/", "\\").lower()


def extract_message_text(content_items: Any) -> str:
    """Extract plain text from message content arrays in session payloads.

    Purpose:
    - Support both user and assistant message payload variants in session logs.
    Why:
    - Different message channels use `text`, `input_text`, or `output_text`.
    Inputs:
    - `content_items`: raw payload content object.
    Outputs:
    - Joined text body (newline-delimited) or empty string.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    if not isinstance(content_items, list):
        return ""
    extracted: list[str] = []
    for item in content_items:
        if not isinstance(item, dict):
            continue
        text_value = (
            item.get("text") or item.get("input_text") or item.get("output_text") or ""
        )
        if isinstance(text_value, str) and text_value.strip():
            extracted.append(text_value.strip())
    return "\n".join(extracted).strip()


def iter_session_files() -> list[Path]:
    """Return known Codex session files sorted by last modified time descending.

    Purpose:
    - Locate candidate session logs for checkpoint extraction.
    Why:
    - Latest matching repo session should be preferred for context recovery.
    Inputs:
    - None.
    Outputs:
    - Sorted list of session file paths.
    Side effects:
    - Reads local filesystem metadata.
    Exceptions:
    - None; missing session root yields empty list.
    """

    if not SESSION_ROOT.exists():
        return []
    return sorted(
        SESSION_ROOT.rglob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def read_session_meta(session_file: Path) -> dict[str, str]:
    """Read minimal metadata from a session file.

    Purpose:
    - Quickly obtain session id/cwd/timestamp for session matching.
    Why:
    - Repo-aware selection should avoid parsing complete files when unnecessary.
    Inputs:
    - `session_file`: path to one jsonl session log.
    Outputs:
    - Dict containing `id`, `cwd`, and `timestamp` when present.
    Side effects:
    - Reads session file lines.
    Exceptions:
    - `OSError` for unreadable files.
    """

    metadata: dict[str, str] = {"id": "", "cwd": "", "timestamp": ""}
    with session_file.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index > 120:
                break
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("type") != "session_meta":
                continue
            meta_payload = payload.get("payload") or {}
            if not isinstance(meta_payload, dict):
                continue
            metadata["id"] = str(meta_payload.get("id") or "")
            metadata["cwd"] = str(meta_payload.get("cwd") or "")
            metadata["timestamp"] = str(meta_payload.get("timestamp") or "")
            break
    return metadata


def select_session_file(repo_root: Path, session_override: str) -> Path | None:
    """Select the best session file to recover context for this repository.

    Purpose:
    - Resolve a deterministic session source for compacted-context recovery.
    Why:
    - Using unrelated sessions introduces wrong context into the snapshot.
    Inputs:
    - `repo_root`: current repository root path.
    - `session_override`: optional explicit session file path.
    Outputs:
    - Selected session file path or `None` when unavailable.
    Side effects:
    - Reads session directory and minimal session metadata.
    Exceptions:
    - `FileNotFoundError` when an explicit override path does not exist.
    """

    if session_override.strip():
        override_path = Path(session_override).expanduser().resolve()
        if not override_path.exists():
            raise FileNotFoundError(f"Session override not found: {override_path}")
        return override_path

    session_files = iter_session_files()
    if not session_files:
        return None

    normalized_repo_root = normalize_path(repo_root)
    for session_file in session_files:
        meta = read_session_meta(session_file)
        session_cwd = str(meta.get("cwd") or "")
        if session_cwd and normalize_path(session_cwd) == normalized_repo_root:
            return session_file
    return session_files[0]


def build_turn_fingerprint(
    session_id: str, collaboration_mode: str, turn_limit: int, turns: list[TurnEntry]
) -> str:
    """Build a stable fingerprint for extracted session turns.

    Purpose:
    - Detect when checkpoint excerpts are unchanged across updater runs.
    Why:
    - Duplicate checkpoint appends should be prevented for idempotent behavior.
    Inputs:
    - `session_id`: source session identifier.
    - `collaboration_mode`: detected mode token (`plan`, `default`, etc.).
    - `turn_limit`: window size used for extraction.
    - `turns`: extracted user/assistant excerpts.
    Outputs:
    - SHA-256 fingerprint hex string.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    payload = {
        "session_id": session_id,
        "collaboration_mode": collaboration_mode,
        "turn_limit": int(turn_limit),
        "turns": [
            {"role": turn.role, "phase": turn.phase, "text": turn.text}
            for turn in turns
        ],
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_session_context(session_file: Path | None, turn_limit: int) -> SessionContext:
    """Load session metadata and recent turn excerpts from a jsonl session file.

    Purpose:
    - Recover compacted conversation context without rescanning repo state.
    Why:
    - Planning and editing checkpoints both need durable turn-level context.
    Inputs:
    - `session_file`: selected source session log (or `None` if unavailable).
    - `turn_limit`: number of recent turns to retain.
    Outputs:
    - `SessionContext` with mode, session ids, turns, and fingerprint.
    Side effects:
    - Reads session jsonl content.
    Exceptions:
    - `OSError` or `UnicodeDecodeError` for unreadable files.
    """

    safe_turn_limit = max(1, int(turn_limit))
    if session_file is None:
        empty_fingerprint = build_turn_fingerprint(
            "unknown", "unknown", safe_turn_limit, []
        )
        return SessionContext(
            session_file=None,
            session_id="unknown",
            collaboration_mode="unknown",
            session_timestamp="",
            turns=[],
            turn_limit=safe_turn_limit,
            fingerprint=empty_fingerprint,
        )

    session_id = "unknown"
    session_timestamp = ""
    collaboration_mode = "unknown"
    raw_turns: list[TurnEntry] = []

    with session_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            record_type = record.get("type")
            payload_value = record.get("payload")
            payload = payload_value if isinstance(payload_value, dict) else {}

            if record_type == "session_meta":
                session_id = str(payload.get("id") or session_id)
                session_timestamp = str(payload.get("timestamp") or session_timestamp)
                continue

            if record_type == "event_msg":
                event_type = str(payload.get("type") or "")
                if event_type == "task_started":
                    collaboration_mode = (
                        str(
                            payload.get("collaboration_mode_kind") or collaboration_mode
                        )
                        .strip()
                        .lower()
                        or "unknown"
                    )
                    continue
                if event_type in {"user_message", "agent_message"}:
                    role = "user" if event_type == "user_message" else "assistant"
                    phase = str(payload.get("phase") or "").strip().lower()
                    text = str(payload.get("message") or "")
                    raw_turns.append(TurnEntry(role=role, phase=phase, text=text))
                    continue

            if record_type == "response_item":
                item_type = str(payload.get("type") or "")
                if item_type != "message":
                    continue
                role = str(payload.get("role") or "").strip().lower()
                if role not in {"user", "assistant"}:
                    continue
                phase = str(payload.get("phase") or "").strip().lower()
                text = extract_message_text(payload.get("content"))
                raw_turns.append(TurnEntry(role=role, phase=phase, text=text))

    deduped_turns: list[TurnEntry] = []
    seen: set[tuple[str, str, str]] = set()
    for turn in raw_turns:
        normalized_text = normalize_whitespace(turn.text)
        if not normalized_text:
            continue
        dedupe_key = (turn.role, turn.phase, normalized_text)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped_turns.append(
            TurnEntry(role=turn.role, phase=turn.phase, text=normalized_text)
        )

    windowed_turns = deduped_turns[-safe_turn_limit:]
    fingerprint = build_turn_fingerprint(
        session_id=session_id,
        collaboration_mode=collaboration_mode,
        turn_limit=safe_turn_limit,
        turns=windowed_turns,
    )
    return SessionContext(
        session_file=session_file,
        session_id=session_id,
        collaboration_mode=collaboration_mode,
        session_timestamp=session_timestamp,
        turns=windowed_turns,
        turn_limit=safe_turn_limit,
        fingerprint=fingerprint,
    )


def build_checkpoint_label(
    milestone_note: str, session_context: SessionContext, now_utc: datetime
) -> str:
    """Resolve a checkpoint label for snapshot decision history.

    Purpose:
    - Produce a stable label for both explicit milestones and no-edit checkpoints.
    Why:
    - Planning checkpoints often need context persistence without code changes.
    Inputs:
    - `milestone_note`: user-supplied milestone text (optional).
    - `session_context`: extracted session data used for auto-labeling.
    - `now_utc`: timestamp used for fallback labels.
    Outputs:
    - Human-readable checkpoint label string.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    stripped_milestone = (milestone_note or "").strip()
    if stripped_milestone:
        return stripped_milestone

    latest_user_turn = ""
    for turn in reversed(session_context.turns):
        if turn.role == "user" and turn.text:
            latest_user_turn = turn.text
            break
    snippet = latest_user_turn[:72]
    if snippet:
        return f"Auto checkpoint ({session_context.collaboration_mode}): {snippet}"
    return (
        "Auto checkpoint "
        f"({session_context.collaboration_mode}) "
        f"{now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )


def parse_companion_checkpoints(companion_text: str) -> dict[str, str]:
    """Parse existing checkpoint fingerprints from companion context document.

    Purpose:
    - Map fingerprints to checkpoint ids for append dedupe checks.
    Why:
    - Repeated updates with unchanged turns should reuse existing checkpoints.
    Inputs:
    - `companion_text`: full companion markdown file content.
    Outputs:
    - Mapping of fingerprint -> checkpoint id.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    mapping: dict[str, str] = {}
    pattern = (
        r"(?ms)^### Checkpoint `(?P<id>[^`]+)`\n"
        r"(?P<body>.*?)(?=^### Checkpoint `|\Z)"
    )
    for match in re.finditer(pattern, companion_text):
        checkpoint_id = str(match.group("id") or "").strip()
        body = str(match.group("body") or "")
        fp_match = re.search(r"(?m)^- Fingerprint: `([a-f0-9]{64})`$", body)
        if not checkpoint_id or not fp_match:
            continue
        mapping[str(fp_match.group(1))] = checkpoint_id
    return mapping


def ensure_companion_header(existing_text: str) -> str:
    """Ensure companion session-context file has canonical headers.

    Purpose:
    - Guarantee stable document structure before checkpoint appends.
    Why:
    - Append logic and parsing rely on consistent checkpoint section headers.
    Inputs:
    - `existing_text`: current companion file text (possibly empty).
    Outputs:
    - Normalized companion text with required header scaffolding.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    if existing_text.strip():
        if (
            CHECKPOINT_HEADER in existing_text
            and CHECKPOINT_LOG_HEADER in existing_text
        ):
            return existing_text
    header = [
        CHECKPOINT_HEADER,
        "",
        (
            "Append-only store of recent user/assistant context excerpts recovered "
            "from local Codex sessions."
        ),
        "",
        CHECKPOINT_LOG_HEADER,
        "",
    ]
    if not existing_text.strip():
        return "\n".join(header)
    return "\n".join(header) + existing_text.strip() + "\n"


def append_session_checkpoint(
    companion_path: Path,
    session_context: SessionContext,
    checkpoint_label: str,
    focus_area: str,
    captured_utc: datetime,
) -> tuple[str, bool]:
    """Append a new checkpoint block unless an identical fingerprint already exists.

    Purpose:
    - Persist raw planning/editing excerpts in an append-only companion file.
    Why:
    - Compacted chat context should remain recoverable without rescanning code.
    Inputs:
    - `companion_path`: destination path for companion session context markdown.
    - `session_context`: current session metadata and excerpt window.
    - `checkpoint_label`: milestone/auto-generated checkpoint label.
    - `focus_area`: optional current focus label.
    - `captured_utc`: UTC timestamp for checkpoint capture.
    Outputs:
    - Tuple `(checkpoint_id, appended)` where `appended` is false when deduped.
    Side effects:
    - Reads and writes companion markdown file.
    Exceptions:
    - `OSError` for read/write failures.
    """

    existing_text = ensure_companion_header(read_text_file(companion_path))
    existing_mapping = parse_companion_checkpoints(existing_text)
    if session_context.fingerprint in existing_mapping:
        checkpoint_id = existing_mapping[session_context.fingerprint]
        write_text_file(companion_path, existing_text)
        return checkpoint_id, False

    checkpoint_id = (
        f"CHK-{captured_utc.strftime('%Y%m%dT%H%M%SZ')}"
        f"-{session_context.fingerprint[:8]}"
    )
    session_file_text = (
        str(session_context.session_file)
        if session_context.session_file
        else "unavailable"
    )
    focus_value = focus_area.strip() if focus_area.strip() else "Not specified"

    block_lines = [
        f"### Checkpoint `{checkpoint_id}`",
        f"- Captured (UTC): {captured_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Collaboration mode: `{session_context.collaboration_mode}`",
        f"- Source session id: `{session_context.session_id}`",
        f"- Source session file: `{session_file_text}`",
        (
            "- Source session timestamp: "
            f"`{session_context.session_timestamp or 'unknown'}`"
        ),
        f"- Turn window used: `{session_context.turn_limit}`",
        f"- Fingerprint: `{session_context.fingerprint}`",
        f"- Checkpoint label: {checkpoint_label}",
        f"- Focus area: {focus_value}",
        "",
        "#### Excerpts",
    ]
    if not session_context.turns:
        block_lines.append("- No user/assistant turn excerpts were captured.")
    else:
        for index, turn in enumerate(session_context.turns, start=1):
            role_label = turn.role
            phase_label = turn.phase if turn.phase else "none"
            block_lines.extend(
                [
                    f"{index}. [{role_label}][phase={phase_label}]",
                    "<<<",
                    turn.text,
                    ">>>",
                    "",
                ]
            )
    block_lines.append("")

    block_text = "\n".join(block_lines)
    updated_text = existing_text
    if not updated_text.endswith("\n"):
        updated_text += "\n"
    updated_text += block_text
    write_text_file(companion_path, updated_text)
    return checkpoint_id, True


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
    checkpoint_label: str,
    focus_area: str,
    repo_root: Path,
    existing_snapshot: str,
    session_context: SessionContext,
    checkpoint_id: str,
    companion_rel_path: str,
    captured_utc: datetime,
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

    iso_timestamp = captured_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_stamp = captured_utc.date().isoformat()
    focus_value = focus_area.strip() if focus_area.strip() else "Not specified"

    project_map_lines = collect_project_map(repo_root)
    invariants = collect_current_invariants(repo_root)
    release_anchor = extract_latest_release_heading(repo_root)

    decision_line = (
        f"- {date_stamp}: {checkpoint_label}. "
        "Rationale: preserve recoverable user/assistant context across compaction."
    )
    decision_line += f" Mode: {session_context.collaboration_mode}."
    if focus_value != "Not specified":
        decision_line += f" Focus: {focus_value}."
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
            '- `python scripts/update_codex_context.py [--milestone "<note>"] '
            '[--focus "<area>"]`'
        ),
        "- `python scripts/update_codex_context.py`",
        "- `python scripts/validate_rust_backend.py`",
        "- `python -m pytest -q`",
        '- `python -m py_compile "GL-260 Data Analysis and Plotter.py"`',
    ]

    open_work_lines = [
        f"- Active checkpoint anchor: {checkpoint_label}",
        f"- Current focus area: {focus_value}",
        f"- Collaboration mode: {session_context.collaboration_mode}",
        f"- Source session id: {session_context.session_id}",
        f"- Turn window used: {session_context.turn_limit}",
        f"- Session checkpoint id: {checkpoint_id}",
        f"- Session checkpoint file: {companion_rel_path}",
        f"- Release context anchor: {release_anchor}",
        (
            "- Refresh this snapshot at every meaningful checkpoint, including "
            "planning-only checkpoints with no code edits."
        ),
        (
            "- Keep Manual Notes updated with blockers, local runbook details, and "
            "handoff assumptions."
        ),
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
        "## Session Recovery Anchor",
        f"- Last checkpoint id: {checkpoint_id}",
        f"- Companion context file: `{companion_rel_path}`",
        f"- Collaboration mode: {session_context.collaboration_mode}",
        f"- Source session id: {session_context.session_id}",
        f"- Source session file: {session_context.session_file or 'unavailable'}",
        f"- Turn window used: {session_context.turn_limit}",
        f"- Fingerprint: {session_context.fingerprint}",
        "",
        "## Validation Commands",
        *validation_commands,
        "",
        "## Snapshot Metadata",
        f"- Last updated (UTC): {iso_timestamp}",
        "- Owner: Codex + repository maintainers",
        "- Scope: Repository-local context primer",
        "- Primer policy: Load this file at task start before broad exploration",
        "- Refresh cadence: Every meaningful checkpoint",
        "- Stale threshold: 24 hours",
        f"- Last checkpoint label: {checkpoint_label}",
        f"- Last focus area: {focus_value}",
        f"- Last collaboration mode: {session_context.collaboration_mode}",
        f"- Last source session id: {session_context.session_id}",
        f"- Last source session file: {session_context.session_file or 'unavailable'}",
        f"- Last turn window used: {session_context.turn_limit}",
        f"- Last session checkpoint id: {checkpoint_id}",
        f"- Last session fingerprint: {session_context.fingerprint}",
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

    write_text_file(snapshot_path, content)


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
    captured_utc = datetime.now(timezone.utc)
    snapshot_path = repo_root / "docs" / "codex-context.md"
    companion_path = repo_root / "docs" / "codex-session-context.md"
    companion_rel_path = str(companion_path.relative_to(repo_root)).replace("\\", "/")
    session_file = select_session_file(repo_root, args.session_file)
    session_context = load_session_context(session_file, args.turn_limit)
    checkpoint_label = build_checkpoint_label(
        args.milestone, session_context, captured_utc
    )
    checkpoint_id, appended = append_session_checkpoint(
        companion_path=companion_path,
        session_context=session_context,
        checkpoint_label=checkpoint_label,
        focus_area=args.focus,
        captured_utc=captured_utc,
    )
    existing_snapshot = read_text_file(snapshot_path)
    rendered = render_snapshot(
        checkpoint_label=checkpoint_label,
        focus_area=args.focus,
        repo_root=repo_root,
        existing_snapshot=existing_snapshot,
        session_context=session_context,
        checkpoint_id=checkpoint_id,
        companion_rel_path=companion_rel_path,
        captured_utc=captured_utc,
    )
    write_snapshot(snapshot_path, rendered)
    status_text = "appended" if appended else "reused_existing"
    print(f"Updated snapshot: {snapshot_path}")
    print(f"Updated session context: {companion_path} ({status_text})")


if __name__ == "__main__":
    main()
