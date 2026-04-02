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
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

MANUAL_NOTES_START = "<!-- MANUAL_NOTES_START -->"
MANUAL_NOTES_END = "<!-- MANUAL_NOTES_END -->"
DEFAULT_TURN_LIMIT = 30
DEFAULT_SESSION_SCOPE = 2
DEFAULT_THRESHOLD = 0.80
DEFAULT_POLL_INTERVAL_SECONDS = 15.0
WATCH_COOLDOWN_SECONDS = 180
SNAPSHOT_STALE_HOURS = 24
CHECKPOINT_HEADER = "# Codex Session Context"
CHECKPOINT_LOG_HEADER = "## Checkpoint Log"
SESSION_ROOT = Path.home() / ".codex" / "sessions"
WATCH_STATE_FILENAME = ".codex_context_watch_state.json"

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
    session_files: list[Path]
    session_id: str
    session_chain_ids: list[str]
    session_chain_timestamps: list[str]
    collaboration_mode: str
    session_timestamp: str
    turns: list[TurnEntry]
    turn_limit: int
    fingerprint: str


@dataclass
class SessionSource:
    """Container for one parsed session source and extracted message turns."""

    session_file: Path
    session_id: str
    session_timestamp: str
    collaboration_mode: str
    turns: list[TurnEntry]


@dataclass
class TokenUsageSnapshot:
    """Container for latest token usage values from a session file."""

    total_tokens: int
    model_context_window: int
    ratio: float
    observed_utc: str


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for snapshot regeneration.

    Purpose:
    - Support manual refresh, watch automation, and task-start resume workflows.
    Why:
    - One script should handle continuity checkpointing and deterministic resume reads.
    Inputs:
    - CLI flags from `sys.argv`.
    Outputs:
    - Parsed namespace containing mode, scope, and update behavior options.
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
    parser.add_argument(
        "--session-scope",
        type=int,
        default=DEFAULT_SESSION_SCOPE,
        help="Number of same-repo sessions to merge for recovery continuity.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Token window ratio that triggers automatic checkpointing in watch mode.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Seconds between token-window checks in watch mode.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--watch",
        action="store_true",
        help="Continuously monitor token usage and auto-checkpoint on threshold crossings.",
    )
    mode_group.add_argument(
        "--resume-brief",
        action="store_true",
        help="Print deterministic resume context from snapshot and checkpoint files.",
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


def select_session_files(
    repo_root: Path, session_override: str, session_scope: int
) -> list[Path]:
    """Select same-repo session files used for continuity recovery.

    Purpose:
    - Resolve a deterministic session chain for compacted-context recovery.
    Why:
    - New compacted sessions can initially miss in-progress turns.
    Inputs:
    - `repo_root`: current repository root path.
    - `session_override`: optional explicit session file path.
    - `session_scope`: max number of session files to include.
    Outputs:
    - Ordered list (newest-first) of session files used for context reconstruction.
    Side effects:
    - Reads session directory and minimal session metadata.
    Exceptions:
    - `FileNotFoundError` when an explicit override path does not exist.
    """

    safe_scope = max(1, int(session_scope))
    if session_override.strip():
        override_path = Path(session_override).expanduser().resolve()
        if not override_path.exists():
            raise FileNotFoundError(f"Session override not found: {override_path}")
        return [override_path]

    session_files = iter_session_files()
    if not session_files:
        return []

    normalized_repo_root = normalize_path(repo_root)
    matching_files: list[Path] = []
    for session_file in session_files:
        meta = read_session_meta(session_file)
        session_cwd = str(meta.get("cwd") or "")
        if session_cwd and normalize_path(session_cwd) == normalized_repo_root:
            matching_files.append(session_file)
    if matching_files:
        return matching_files[:safe_scope]
    return session_files[:safe_scope]


def build_turn_fingerprint(
    session_id: str,
    collaboration_mode: str,
    turn_limit: int,
    turns: list[TurnEntry],
    session_chain_ids: list[str],
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
    - `session_chain_ids`: ordered session-id chain used to build `turns`.
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
        "session_chain_ids": [str(value) for value in session_chain_ids],
        "turns": [
            {"role": turn.role, "phase": turn.phase, "text": turn.text}
            for turn in turns
        ],
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def parse_session_source(session_file: Path) -> SessionSource:
    """Parse one session file into reusable metadata and turn excerpts.

    Purpose:
    - Normalize one session source for multi-session continuity merges.
    Why:
    - Compaction boundaries can split in-progress context across sessions.
    Inputs:
    - `session_file`: source session jsonl path.
    Outputs:
    - Parsed `SessionSource` containing metadata and normalized turns.
    Side effects:
    - Reads session jsonl content.
    Exceptions:
    - `OSError` or `UnicodeDecodeError` for unreadable files.
    """

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

    return SessionSource(
        session_file=session_file,
        session_id=session_id,
        session_timestamp=session_timestamp,
        collaboration_mode=collaboration_mode,
        turns=deduped_turns,
    )


def load_session_context(session_files: list[Path], turn_limit: int) -> SessionContext:
    """Load metadata and merged turn excerpts from one or more session files.

    Purpose:
    - Recover compacted conversation context without rescanning repo state.
    Why:
    - Planning and editing checkpoints both need durable turn-level context.
    Inputs:
    - `session_files`: selected source session logs (newest-first list).
    - `turn_limit`: number of recent turns to retain.
    Outputs:
    - `SessionContext` with mode, session chain ids, turns, and fingerprint.
    Side effects:
    - Reads session jsonl content.
    Exceptions:
    - `OSError` or `UnicodeDecodeError` for unreadable files.
    """

    safe_turn_limit = max(1, int(turn_limit))
    if not session_files:
        empty_fingerprint = build_turn_fingerprint(
            "unknown",
            "unknown",
            safe_turn_limit,
            [],
            ["unknown"],
        )
        return SessionContext(
            session_file=None,
            session_files=[],
            session_id="unknown",
            session_chain_ids=["unknown"],
            session_chain_timestamps=[],
            collaboration_mode="unknown",
            session_timestamp="",
            turns=[],
            turn_limit=safe_turn_limit,
            fingerprint=empty_fingerprint,
        )

    ordered_files = sorted(session_files, key=lambda path: path.stat().st_mtime)
    parsed_sources = [parse_session_source(path) for path in ordered_files]
    primary_source = parsed_sources[-1]

    merged_turns: list[TurnEntry] = []
    seen: set[tuple[str, str, str]] = set()
    for source in parsed_sources:
        for turn in source.turns:
            dedupe_key = (turn.role, turn.phase, turn.text)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            merged_turns.append(turn)

    windowed_turns = merged_turns[-safe_turn_limit:]
    session_chain_ids = [
        source.session_id.strip() or "unknown" for source in parsed_sources
    ]
    session_chain_timestamps = [
        source.session_timestamp.strip() for source in parsed_sources
    ]
    fingerprint = build_turn_fingerprint(
        session_id=primary_source.session_id,
        collaboration_mode=primary_source.collaboration_mode,
        turn_limit=safe_turn_limit,
        turns=windowed_turns,
        session_chain_ids=session_chain_ids,
    )
    return SessionContext(
        session_file=primary_source.session_file,
        session_files=ordered_files,
        session_id=primary_source.session_id,
        session_chain_ids=session_chain_ids,
        session_chain_timestamps=session_chain_timestamps,
        collaboration_mode=primary_source.collaboration_mode,
        session_timestamp=primary_source.session_timestamp,
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
    trigger_reason: str,
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
    - `trigger_reason`: reason checkpoint refresh was initiated.
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
    session_chain_ids_text = ", ".join(session_context.session_chain_ids)
    focus_value = focus_area.strip() if focus_area.strip() else "Not specified"

    block_lines = [
        f"### Checkpoint `{checkpoint_id}`",
        f"- Captured (UTC): {captured_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Collaboration mode: `{session_context.collaboration_mode}`",
        f"- Source session id: `{session_context.session_id}`",
        f"- Source session file: `{session_file_text}`",
        f"- Source session chain ids: `{session_chain_ids_text}`",
        (
            "- Source session timestamp: "
            f"`{session_context.session_timestamp or 'unknown'}`"
        ),
        f"- Turn window used: `{session_context.turn_limit}`",
        f"- Fingerprint: `{session_context.fingerprint}`",
        f"- Checkpoint label: {checkpoint_label}",
        f"- Focus area: {focus_value}",
        f"- Trigger reason: {trigger_reason.strip() or 'manual'}",
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
    trigger_reason: str,
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
    - `trigger_reason`: reason checkpoint refresh was initiated.
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
        "- `python scripts/update_codex_context.py --resume-brief`",
        "- `python scripts/update_codex_context.py --watch`",
        "- `python scripts/validate_rust_backend.py`",
        "- `python -m pytest -q`",
        '- `python -m py_compile "GL-260 Data Analysis and Plotter.py"`',
    ]
    session_chain_ids_text = ", ".join(session_context.session_chain_ids)

    open_work_lines = [
        f"- Active checkpoint anchor: {checkpoint_label}",
        f"- Current focus area: {focus_value}",
        f"- Collaboration mode: {session_context.collaboration_mode}",
        f"- Source session id: {session_context.session_id}",
        f"- Source session chain ids: {session_chain_ids_text}",
        f"- Turn window used: {session_context.turn_limit}",
        f"- Session checkpoint id: {checkpoint_id}",
        f"- Session checkpoint file: {companion_rel_path}",
        f"- Last checkpoint trigger reason: {trigger_reason.strip() or 'manual'}",
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
        f"- Source session chain ids: {session_chain_ids_text}",
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
        f"- Last source session chain ids: {session_chain_ids_text}",
        f"- Last source session file: {session_context.session_file or 'unavailable'}",
        f"- Last turn window used: {session_context.turn_limit}",
        f"- Last trigger reason: {trigger_reason.strip() or 'manual'}",
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


def parse_utc_iso8601(value: str) -> datetime | None:
    """Parse UTC timestamp strings used in snapshot and watcher state documents.

    Purpose:
    - Convert persisted ISO strings into timezone-aware datetimes safely.
    Why:
    - Resume staleness and watcher cooldown checks require robust UTC parsing.
    Inputs:
    - `value`: ISO-8601 timestamp string, expected with a trailing `Z`.
    Outputs:
    - Parsed UTC datetime or `None` when parsing fails.
    Side effects:
    - None.
    Exceptions:
    - None; malformed timestamps return `None`.
    """

    cleaned = str(value or "").strip()
    if not cleaned:
        return None
    normalized = cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def extract_snapshot_metadata_value(snapshot_text: str, label: str) -> str:
    """Extract one metadata value line from the snapshot markdown.

    Purpose:
    - Read specific metadata fields without reparsing the full document structure.
    Why:
    - Resume output requires deterministic extraction of key recovery fields.
    Inputs:
    - `snapshot_text`: full `docs/codex-context.md` text.
    - `label`: metadata label text after `- ` and before `:`.
    Outputs:
    - Field value string or empty string when not found.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    pattern = rf"(?m)^- {re.escape(label)}: (.+)$"
    match = re.search(pattern, snapshot_text)
    return str(match.group(1)).strip() if match else ""


def extract_latest_assistant_excerpt(companion_text: str) -> str:
    """Extract the latest assistant excerpt from the newest checkpoint block.

    Purpose:
    - Surface actionable assistant context for deterministic post-compaction resume.
    Why:
    - Resume brief should expose immediate continuation context, not just metadata.
    Inputs:
    - `companion_text`: full `docs/codex-session-context.md` content.
    Outputs:
    - Normalized excerpt string, truncated for compact display.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    checkpoint_pattern = (
        r"(?ms)^### Checkpoint `(?P<id>[^`]+)`\n"
        r"(?P<body>.*?)(?=^### Checkpoint `|\Z)"
    )
    checkpoint_matches = list(re.finditer(checkpoint_pattern, companion_text))
    if not checkpoint_matches:
        return "No assistant excerpt captured in checkpoint companion."
    newest_body = str(checkpoint_matches[-1].group("body") or "")
    assistant_pattern = r"(?ms)^\d+\. \[assistant\]\[phase=[^\]]+\]\n<<<\n(.*?)\n>>>"
    assistant_matches = list(re.finditer(assistant_pattern, newest_body))
    if not assistant_matches:
        return "No assistant excerpt captured in latest checkpoint."
    excerpt_text = normalize_whitespace(str(assistant_matches[-1].group(1) or ""))
    if len(excerpt_text) <= 280:
        return excerpt_text
    return f"{excerpt_text[:277]}..."


def build_resume_brief(repo_root: Path) -> str:
    """Build a deterministic resume brief from snapshot and companion files.

    Purpose:
    - Provide a compact recovery summary for post-compaction task continuation.
    Why:
    - Explicit resume reads prevent unnecessary context re-discovery work.
    Inputs:
    - `repo_root`: absolute repository root path.
    Outputs:
    - Multi-line text summary for terminal display.
    Side effects:
    - Reads snapshot and companion context documents.
    Exceptions:
    - `RuntimeError` when snapshot is missing or stale.
    """

    snapshot_path = repo_root / "docs" / "codex-context.md"
    companion_path = repo_root / "docs" / "codex-session-context.md"
    refresh_hint = (
        'python scripts/update_codex_context.py --milestone "<note>" --focus "<area>"'
    )
    if not snapshot_path.exists():
        raise RuntimeError(
            "Resume brief unavailable: docs/codex-context.md is missing. "
            f"Run: {refresh_hint}"
        )

    snapshot_text = read_text_file(snapshot_path)
    updated_at_text = extract_snapshot_metadata_value(snapshot_text, "Last updated (UTC)")
    updated_at = parse_utc_iso8601(updated_at_text)
    if updated_at is None:
        raise RuntimeError(
            "Resume brief unavailable: snapshot metadata is missing a valid UTC timestamp. "
            f"Run: {refresh_hint}"
        )
    stale_cutoff = datetime.now(timezone.utc) - timedelta(hours=SNAPSHOT_STALE_HOURS)
    if updated_at < stale_cutoff:
        raise RuntimeError(
            "Resume brief unavailable: snapshot is stale (>24h). "
            f"Last updated: {updated_at_text}. Run: {refresh_hint}"
        )

    companion_text = read_text_file(companion_path)
    open_work_anchor = extract_snapshot_metadata_value(
        snapshot_text, "Active checkpoint anchor"
    )
    checkpoint_id = extract_snapshot_metadata_value(
        snapshot_text, "Last session checkpoint id"
    )
    checkpoint_label = extract_snapshot_metadata_value(
        snapshot_text, "Last checkpoint label"
    )
    collaboration_mode = extract_snapshot_metadata_value(
        snapshot_text, "Last collaboration mode"
    )
    focus_area = extract_snapshot_metadata_value(snapshot_text, "Last focus area")
    assistant_excerpt = extract_latest_assistant_excerpt(companion_text)

    lines = [
        "Resume Brief",
        f"- Last checkpoint id: {checkpoint_id or 'unknown'}",
        f"- Last checkpoint label: {checkpoint_label or 'unknown'}",
        f"- Last collaboration mode: {collaboration_mode or 'unknown'}",
        f"- Last focus area: {focus_area or 'Not specified'}",
        f"- Open-work anchor: {open_work_anchor or 'unknown'}",
        f"- Latest assistant excerpt: {assistant_excerpt}",
    ]
    return "\n".join(lines)


def print_resume_brief(repo_root: Path) -> None:
    """Print deterministic resume context details for task-start recovery.

    Purpose:
    - Emit a required terminal-visible recovery summary before broad exploration.
    Why:
    - Visibility confirms resume context was actually loaded after compaction.
    Inputs:
    - `repo_root`: absolute repository root path.
    Outputs:
    - None.
    Side effects:
    - Prints resume lines to stdout.
    Exceptions:
    - Propagates `RuntimeError` from `build_resume_brief(...)`.
    """

    print(build_resume_brief(repo_root))


def read_latest_token_usage(session_file: Path) -> TokenUsageSnapshot | None:
    """Read the most recent token usage sample from a session log file.

    Purpose:
    - Monitor model context-window pressure for pre-compaction checkpoint triggers.
    Why:
    - Watch mode relies on local token telemetry emitted in session logs.
    Inputs:
    - `session_file`: source session jsonl path.
    Outputs:
    - Latest `TokenUsageSnapshot`, or `None` when unavailable.
    Side effects:
    - Reads session jsonl file contents.
    Exceptions:
    - `OSError` for unreadable files.
    """

    latest_snapshot: TokenUsageSnapshot | None = None
    with session_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(record.get("type") or "") != "event_msg":
                continue
            payload_value = record.get("payload")
            payload = payload_value if isinstance(payload_value, dict) else {}
            if str(payload.get("type") or "") != "token_count":
                continue
            info_value = payload.get("info")
            info = info_value if isinstance(info_value, dict) else {}
            last_usage_value = info.get("last_token_usage")
            last_usage = (
                last_usage_value if isinstance(last_usage_value, dict) else {}
            )
            total_tokens = int(last_usage.get("total_tokens") or 0)
            model_context_window = int(info.get("model_context_window") or 0)
            if total_tokens <= 0 or model_context_window <= 0:
                continue
            ratio = float(total_tokens) / float(model_context_window)
            latest_snapshot = TokenUsageSnapshot(
                total_tokens=total_tokens,
                model_context_window=model_context_window,
                ratio=ratio,
                observed_utc=str(record.get("timestamp") or ""),
            )
    return latest_snapshot


def load_watch_state(state_path: Path) -> dict[str, Any]:
    """Load watcher cooldown and threshold state from local state storage.

    Purpose:
    - Persist threshold-crossing bookkeeping across watch process restarts.
    Why:
    - Cooldown behavior must survive watcher restarts to avoid checkpoint spam.
    Inputs:
    - `state_path`: filesystem path for watcher state file.
    Outputs:
    - State mapping with normalized keys and defaults.
    Side effects:
    - Reads state file when it exists.
    Exceptions:
    - `OSError` for unreadable state files.
    """

    default_state: dict[str, Any] = {
        "last_session_id": "",
        "last_ratio": 0.0,
        "last_trigger_utc": "",
        "last_observed_utc": "",
    }
    if not state_path.exists():
        return default_state
    try:
        raw_state = json.loads(read_text_file(state_path))
    except json.JSONDecodeError:
        return default_state
    if not isinstance(raw_state, dict):
        return default_state
    normalized = dict(default_state)
    normalized["last_session_id"] = str(raw_state.get("last_session_id") or "")
    normalized["last_ratio"] = float(raw_state.get("last_ratio") or 0.0)
    normalized["last_trigger_utc"] = str(raw_state.get("last_trigger_utc") or "")
    normalized["last_observed_utc"] = str(raw_state.get("last_observed_utc") or "")
    return normalized


def save_watch_state(state_path: Path, state: dict[str, Any]) -> None:
    """Persist watcher cooldown and threshold state to a local file.

    Purpose:
    - Keep watch trigger state deterministic across invocations.
    Why:
    - Cross-process continuity avoids repetitive threshold-triggered writes.
    Inputs:
    - `state_path`: filesystem path for watcher state file.
    - `state`: normalized watcher state mapping.
    Outputs:
    - None.
    Side effects:
    - Writes local watcher state file.
    Exceptions:
    - `OSError` for directory creation or write failures.
    """

    state_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
    write_text_file(state_path, serialized + "\n")


def should_trigger_watch_checkpoint(
    state: dict[str, Any],
    session_id: str,
    ratio: float,
    threshold: float,
    now_utc: datetime,
) -> bool:
    """Decide whether watch mode should trigger a new checkpoint update.

    Purpose:
    - Gate automatic checkpoint writes to threshold crossings with cooldown.
    Why:
    - Prevent repetitive writes when token usage remains above threshold.
    Inputs:
    - `state`: persisted watcher state mapping.
    - `session_id`: active session identifier.
    - `ratio`: current token usage ratio (`last_tokens / context_window`).
    - `threshold`: configured watch trigger threshold.
    - `now_utc`: current UTC timestamp.
    Outputs:
    - `True` when update should trigger, else `False`.
    Side effects:
    - None.
    Exceptions:
    - None.
    """

    effective_threshold = max(0.01, min(float(threshold), 0.99))
    previous_ratio = float(state.get("last_ratio") or 0.0)
    if str(state.get("last_session_id") or "") != str(session_id):
        previous_ratio = 0.0
    crossed_threshold = ratio >= effective_threshold and previous_ratio < effective_threshold
    if not crossed_threshold:
        return False
    last_trigger = parse_utc_iso8601(str(state.get("last_trigger_utc") or ""))
    if last_trigger is None:
        return True
    return (now_utc - last_trigger).total_seconds() >= WATCH_COOLDOWN_SECONDS


def run_snapshot_update(
    args: argparse.Namespace,
    repo_root: Path,
    *,
    trigger_reason: str,
) -> tuple[str, bool]:
    """Run one snapshot/checkpoint update cycle with explicit trigger reason.

    Purpose:
    - Reuse one deterministic update workflow across default and watch modes.
    Why:
    - Shared path keeps metadata and checkpoint outputs consistent.
    Inputs:
    - `args`: parsed CLI options.
    - `repo_root`: absolute repository root path.
    - `trigger_reason`: reason checkpoint refresh was initiated.
    Outputs:
    - Tuple `(checkpoint_id, appended)` for update status reporting.
    Side effects:
    - Reads session/snapshot files and writes snapshot/companion files.
    Exceptions:
    - Propagates file and parsing exceptions from helper functions.
    """

    captured_utc = datetime.now(timezone.utc)
    snapshot_path = repo_root / "docs" / "codex-context.md"
    companion_path = repo_root / "docs" / "codex-session-context.md"
    companion_rel_path = str(companion_path.relative_to(repo_root)).replace("\\", "/")
    session_files = select_session_files(
        repo_root,
        args.session_file,
        int(args.session_scope),
    )
    session_context = load_session_context(session_files, args.turn_limit)
    checkpoint_label = build_checkpoint_label(
        args.milestone,
        session_context,
        captured_utc,
    )
    checkpoint_id, appended = append_session_checkpoint(
        companion_path=companion_path,
        session_context=session_context,
        checkpoint_label=checkpoint_label,
        focus_area=args.focus,
        trigger_reason=trigger_reason,
        captured_utc=captured_utc,
    )
    existing_snapshot = read_text_file(snapshot_path)
    rendered = render_snapshot(
        checkpoint_label=checkpoint_label,
        focus_area=args.focus,
        trigger_reason=trigger_reason,
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
    print(f"Session chain ids: {', '.join(session_context.session_chain_ids)}")
    print(f"Trigger reason: {trigger_reason}")
    return checkpoint_id, appended


def run_watch_loop(args: argparse.Namespace, repo_root: Path) -> None:
    """Run continuous token-window monitoring with threshold-triggered updates.

    Purpose:
    - Trigger automatic pre-compaction checkpoints from local session telemetry.
    Why:
    - Hybrid automation removes manual timing dependence near compaction.
    Inputs:
    - `args`: parsed CLI options.
    - `repo_root`: absolute repository root path.
    Outputs:
    - None.
    Side effects:
    - Polls session logs, writes watcher state, and may update snapshot/checkpoint files.
    Exceptions:
    - Propagates file/parsing exceptions from helper functions.
    """

    threshold = max(0.01, min(float(args.threshold), 0.99))
    poll_interval = max(1.0, float(args.poll_interval))
    state_path = repo_root / WATCH_STATE_FILENAME
    state = load_watch_state(state_path)
    print(
        "Watch mode started: "
        f"threshold={threshold:.2f}, poll_interval={poll_interval:.1f}s, "
        f"session_scope={max(1, int(args.session_scope))}"
    )
    try:
        while True:
            now_utc = datetime.now(timezone.utc)
            session_files = select_session_files(
                repo_root,
                args.session_file,
                int(args.session_scope),
            )
            if not session_files:
                print("Watch heartbeat: no session files detected.")
                time.sleep(poll_interval)
                continue

            primary_file = sorted(
                session_files,
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )[0]
            session_meta = read_session_meta(primary_file)
            session_id = str(session_meta.get("id") or "unknown")
            token_snapshot = read_latest_token_usage(primary_file)
            if token_snapshot is None:
                print(
                    "Watch heartbeat: token usage unavailable; waiting for token_count events."
                )
                time.sleep(poll_interval)
                continue

            if should_trigger_watch_checkpoint(
                state=state,
                session_id=session_id,
                ratio=token_snapshot.ratio,
                threshold=threshold,
                now_utc=now_utc,
            ):
                trigger_reason = (
                    "pre-compaction threshold crossing "
                    f"({token_snapshot.ratio:.3f} >= {threshold:.2f})"
                )
                run_snapshot_update(args, repo_root, trigger_reason=trigger_reason)
                state["last_trigger_utc"] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

            state["last_session_id"] = session_id
            state["last_ratio"] = token_snapshot.ratio
            state["last_observed_utc"] = token_snapshot.observed_utc
            save_watch_state(state_path, state)
            print(
                "Watch heartbeat: "
                f"session={session_id}, ratio={token_snapshot.ratio:.3f}, "
                f"tokens={token_snapshot.total_tokens}/{token_snapshot.model_context_window}"
            )
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        save_watch_state(state_path, state)
        print("Watch mode stopped.")


def main() -> None:
    """Run CLI workflow for snapshot update, watch mode, or resume brief output.

    Purpose:
    - Tie argument parsing and mode dispatch into one entrypoint command.
    Why:
    - Operator workflows should use one script for manual, automated, and resume actions.
    Inputs:
    - CLI options parsed by `parse_args()`.
    Outputs:
    - Prints update/resume/watch status messages.
    Side effects:
    - Reads session files, reads/writes snapshot files, and may write watch state.
    Exceptions:
    - Raises `SystemExit` with non-zero status for invalid runtime prerequisites.
    """

    args = parse_args()
    repo_root = resolve_repo_root()
    try:
        if args.resume_brief:
            print_resume_brief(repo_root)
            return
        if args.watch:
            run_watch_loop(args, repo_root)
            return
        run_snapshot_update(args, repo_root, trigger_reason="manual")
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
