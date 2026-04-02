"""Regression coverage for scripts/update_codex_context.py continuity features."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from argparse import Namespace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType

import pytest


def load_updater_module() -> ModuleType:
    """Load the context updater script module for direct function-level testing.

    Purpose:
    - Import script-local helpers without requiring package installation.
    Why:
    - The updater is a standalone script under `scripts/`, not a package module.
    Inputs:
    - None.
    Outputs:
    - Loaded updater module object.
    Side effects:
    - Imports and executes module top-level code.
    Exceptions:
    - `RuntimeError` when module spec/loader resolution fails.
    """

    module_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "update_codex_context.py"
    )
    spec = importlib.util.spec_from_file_location("update_codex_context", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load update_codex_context module spec.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_session_jsonl(path: Path, records: list[dict]) -> None:
    """Write session records to a JSONL file with UTF-8 encoding.

    Purpose:
    - Build deterministic session fixtures for updater regression tests.
    Why:
    - Session parsing behavior depends on raw JSONL event layouts.
    Inputs:
    - `path`: destination JSONL path.
    - `records`: ordered event record mappings.
    Outputs:
    - None.
    Side effects:
    - Creates parent directory and writes session file content.
    Exceptions:
    - `OSError` for directory or file write failures.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_session_fixture(
    repo_root: Path,
    session_root: Path,
) -> tuple[Path, Path]:
    """Create two same-repo sessions used for continuity tests.

    Purpose:
    - Produce a newest/previous session pair with realistic event patterns.
    Why:
    - Compaction continuity behavior is validated through multi-session merges.
    Inputs:
    - `repo_root`: repository path encoded into session metadata `cwd`.
    - `session_root`: root directory where session JSONL files are created.
    Outputs:
    - Tuple of `(new_session_path, old_session_path)`.
    Side effects:
    - Writes two JSONL files under the supplied session root.
    Exceptions:
    - `OSError` for fixture file writes.
    """

    old_session = session_root / "2026" / "04" / "01" / "old-session.jsonl"
    new_session = session_root / "2026" / "04" / "02" / "new-session.jsonl"
    old_records = [
        {
            "timestamp": "2026-04-01T12:00:00Z",
            "type": "session_meta",
            "payload": {
                "id": "old-session-id",
                "timestamp": "2026-04-01T11:59:59Z",
                "cwd": str(repo_root),
            },
        },
        {
            "timestamp": "2026-04-01T12:00:10Z",
            "type": "event_msg",
            "payload": {
                "type": "user_message",
                "message": "Need continuity across compaction.",
            },
        },
        {
            "timestamp": "2026-04-01T12:00:20Z",
            "type": "event_msg",
            "payload": {
                "type": "agent_message",
                "phase": "commentary",
                "message": "Checkpoint the in-progress plan before compaction.",
            },
        },
    ]
    new_records = [
        {
            "timestamp": "2026-04-02T12:00:00Z",
            "type": "session_meta",
            "payload": {
                "id": "new-session-id",
                "timestamp": "2026-04-02T11:59:59Z",
                "cwd": str(repo_root),
            },
        },
        {
            "timestamp": "2026-04-02T12:00:01Z",
            "type": "event_msg",
            "payload": {
                "type": "task_started",
                "collaboration_mode_kind": "plan",
            },
        },
        {
            "timestamp": "2026-04-02T12:00:30Z",
            "type": "event_msg",
            "payload": {
                "type": "user_message",
                "message": "Continue from previous checkpoint.",
            },
        },
    ]
    write_session_jsonl(old_session, old_records)
    write_session_jsonl(new_session, new_records)
    old_time = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    new_time = datetime(2026, 4, 2, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    old_session.touch()
    new_session.touch()
    os.utime(old_session, (old_time, old_time))
    os.utime(new_session, (new_time, new_time))
    return new_session, old_session


def test_session_scope_merge_backfills_previous_session(tmp_path: Path) -> None:
    """Ensure merged context backfills turns from the previous same-repo session.

    Purpose:
    - Verify two-session continuity behavior around compaction boundaries.
    Why:
    - New sessions may start with limited turns and need historical backfill.
    Inputs:
    - `tmp_path`: pytest-provided temporary workspace path.
    Outputs:
    - None.
    Side effects:
    - Creates temporary session fixture files.
    Exceptions:
    - Raises assertions when merge/backfill behavior regresses.
    """

    updater = load_updater_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    session_root = tmp_path / "sessions"
    build_session_fixture(repo_root, session_root)
    updater.SESSION_ROOT = session_root

    selected = updater.select_session_files(
        repo_root, session_override="", session_scope=2
    )
    context = updater.load_session_context(selected, turn_limit=3)

    assert context.session_id == "new-session-id"
    assert context.session_chain_ids == ["old-session-id", "new-session-id"]
    texts = [turn.text for turn in context.turns]
    assert "Checkpoint the in-progress plan before compaction." in texts
    assert "Continue from previous checkpoint." in texts


def test_session_scope_one_uses_newest_only(tmp_path: Path) -> None:
    """Ensure single-session scope preserves newest-session-only behavior.

    Purpose:
    - Validate backward-compatible selection when `--session-scope` is 1.
    Why:
    - Operators may intentionally limit context reconstruction scope.
    Inputs:
    - `tmp_path`: pytest-provided temporary workspace path.
    Outputs:
    - None.
    Side effects:
    - Creates temporary session fixture files.
    Exceptions:
    - Raises assertions when scope filtering regresses.
    """

    updater = load_updater_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    session_root = tmp_path / "sessions"
    build_session_fixture(repo_root, session_root)
    updater.SESSION_ROOT = session_root

    selected = updater.select_session_files(
        repo_root, session_override="", session_scope=1
    )
    context = updater.load_session_context(selected, turn_limit=3)

    assert context.session_chain_ids == ["new-session-id"]
    texts = [turn.text for turn in context.turns]
    assert "Checkpoint the in-progress plan before compaction." not in texts
    assert "Continue from previous checkpoint." in texts


def test_fingerprint_changes_when_session_chain_changes() -> None:
    """Ensure turn fingerprint payload includes session-chain provenance.

    Purpose:
    - Confirm dedupe keys differ when session chain differs.
    Why:
    - Identical turns from different continuity chains should remain distinguishable.
    Inputs:
    - None.
    Outputs:
    - None.
    Side effects:
    - None.
    Exceptions:
    - Raises assertions when fingerprint chain sensitivity regresses.
    """

    updater = load_updater_module()
    turns = [updater.TurnEntry(role="assistant", phase="commentary", text="resume")]
    fp_a = updater.build_turn_fingerprint(
        session_id="session-new",
        collaboration_mode="plan",
        turn_limit=5,
        turns=turns,
        session_chain_ids=["session-old", "session-new"],
    )
    fp_b = updater.build_turn_fingerprint(
        session_id="session-new",
        collaboration_mode="plan",
        turn_limit=5,
        turns=turns,
        session_chain_ids=["session-new"],
    )
    assert fp_a != fp_b


def test_watch_trigger_threshold_crossing_and_cooldown() -> None:
    """Validate threshold-crossing and cooldown gating for watch auto-checkpoints.

    Purpose:
    - Verify trigger dedupe behavior under repeated high token usage.
    Why:
    - Watch mode should avoid repeated writes while above threshold.
    Inputs:
    - None.
    Outputs:
    - None.
    Side effects:
    - None.
    Exceptions:
    - Raises assertions when trigger gating semantics regress.
    """

    updater = load_updater_module()
    now_utc = datetime(2026, 4, 2, 12, 0, 0, tzinfo=timezone.utc)
    base_state = {
        "last_session_id": "session-a",
        "last_ratio": 0.79,
        "last_trigger_utc": "",
        "last_observed_utc": "",
    }
    assert updater.should_trigger_watch_checkpoint(
        state=base_state,
        session_id="session-a",
        ratio=0.81,
        threshold=0.80,
        now_utc=now_utc,
    )

    cooldown_state = dict(base_state)
    cooldown_state["last_trigger_utc"] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert not updater.should_trigger_watch_checkpoint(
        state=cooldown_state,
        session_id="session-a",
        ratio=0.81,
        threshold=0.80,
        now_utc=now_utc + timedelta(seconds=10),
    )

    assert updater.should_trigger_watch_checkpoint(
        state=cooldown_state,
        session_id="session-a",
        ratio=0.81,
        threshold=0.80,
        now_utc=now_utc + timedelta(seconds=updater.WATCH_COOLDOWN_SECONDS + 1),
    )


def test_resume_brief_outputs_required_fields(tmp_path: Path) -> None:
    """Ensure resume brief includes required checkpoint and context summary fields.

    Purpose:
    - Validate deterministic resume output contract for task-start usage.
    Why:
    - Post-compaction continuation depends on reliable brief formatting/content.
    Inputs:
    - `tmp_path`: pytest-provided temporary workspace path.
    Outputs:
    - None.
    Side effects:
    - Writes temporary snapshot and companion markdown files.
    Exceptions:
    - Raises assertions when resume output contract regresses.
    """

    updater = load_updater_module()
    repo_root = tmp_path / "repo"
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    updated_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fingerprint = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    snapshot_text = "\n".join(
        [
            "# Codex Context Snapshot",
            "",
            "## Open Work / Next Actions",
            "- Active checkpoint anchor: Continue context continuity implementation",
            "",
            "## Snapshot Metadata",
            f"- Last updated (UTC): {updated_utc}",
            "- Last checkpoint label: Context continuity hardening",
            "- Last collaboration mode: plan",
            "- Last focus area: continuity",
            "- Last session checkpoint id: CHK-TEST-1234",
            "",
        ]
    )
    companion_text = "\n".join(
        [
            "# Codex Session Context",
            "",
            "## Checkpoint Log",
            "",
            "### Checkpoint `CHK-TEST-1234`",
            f"- Fingerprint: `{fingerprint}`",
            "",
            "#### Excerpts",
            "1. [assistant][phase=commentary]",
            "<<<",
            "Resume from this exact implementation checkpoint.",
            ">>>",
            "",
        ]
    )
    (docs_dir / "codex-context.md").write_text(snapshot_text, encoding="utf-8")
    (docs_dir / "codex-session-context.md").write_text(companion_text, encoding="utf-8")

    brief = updater.build_resume_brief(repo_root)
    assert "Last checkpoint id: CHK-TEST-1234" in brief
    assert "Open-work anchor: Continue context continuity implementation" in brief
    assert (
        "Latest assistant excerpt: Resume from this exact implementation checkpoint."
        in brief
    )


def test_resume_brief_fails_on_stale_snapshot(tmp_path: Path) -> None:
    """Ensure stale snapshot detection fails with explicit refresh guidance.

    Purpose:
    - Enforce stale snapshot safeguards before resume workflows proceed.
    Why:
    - Old snapshots risk replaying incorrect task continuity context.
    Inputs:
    - `tmp_path`: pytest-provided temporary workspace path.
    Outputs:
    - None.
    Side effects:
    - Writes temporary stale snapshot markdown file.
    Exceptions:
    - Raises assertions when stale-snapshot guard behavior regresses.
    """

    updater = load_updater_module()
    repo_root = tmp_path / "repo"
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    stale_time = datetime.now(timezone.utc) - timedelta(days=2)
    snapshot_text = "\n".join(
        [
            "# Codex Context Snapshot",
            "",
            "## Snapshot Metadata",
            f"- Last updated (UTC): {stale_time.strftime('%Y-%m-%dT%H:%M:%SZ')}",
            "- Last checkpoint label: stale snapshot",
            "",
        ]
    )
    (docs_dir / "codex-context.md").write_text(snapshot_text, encoding="utf-8")
    (docs_dir / "codex-session-context.md").write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError) as err:
        updater.build_resume_brief(repo_root)
    assert "snapshot is stale" in str(err.value)
    assert "python scripts/update_codex_context.py --milestone" in str(err.value)


def test_default_update_flow_remains_compatible(tmp_path: Path) -> None:
    """Ensure default one-shot update mode still produces snapshot and companion output.

    Purpose:
    - Validate backward compatibility for existing command usage.
    Why:
    - `python scripts/update_codex_context.py` should continue working unchanged.
    Inputs:
    - `tmp_path`: pytest-provided temporary workspace path.
    Outputs:
    - None.
    Side effects:
    - Creates temporary repo/session fixtures and writes output docs.
    Exceptions:
    - Raises assertions when default update behavior regresses.
    """

    updater = load_updater_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    session_root = tmp_path / "sessions"
    build_session_fixture(repo_root, session_root)
    updater.SESSION_ROOT = session_root

    args = Namespace(
        milestone="Compatibility checkpoint",
        focus="continuity",
        turn_limit=30,
        session_file="",
        session_scope=2,
        threshold=0.80,
        poll_interval=15.0,
        watch=False,
        resume_brief=False,
    )
    checkpoint_id, _ = updater.run_snapshot_update(
        args,
        repo_root,
        trigger_reason="manual",
    )
    snapshot_path = repo_root / "docs" / "codex-context.md"
    companion_path = repo_root / "docs" / "codex-session-context.md"
    assert checkpoint_id.startswith("CHK-")
    assert snapshot_path.exists()
    assert companion_path.exists()
    snapshot_text = snapshot_path.read_text(encoding="utf-8")
    assert "Last trigger reason: manual" in snapshot_text
