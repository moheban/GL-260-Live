"""Profile startup import cost and persist a repeatable summary artifact.

Purpose:
    Run the GL-260 entry script under Python import-time tracing and emit
    top import bottlenecks as JSON.
Why:
    Startup optimization work needs deterministic import baseline snapshots.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_IMPORTTIME_PATTERN = re.compile(
    r"^import time:\s+(?P<self_us>\d+)\s+\|\s+(?P<cumulative_us>\d+)\s+\|\s+(?P<module>.+)$"
)


def _parse_importtime(stderr_text: str) -> List[Dict[str, Any]]:
    """Parse Python `-X importtime` stderr output rows.

    Purpose:
        Convert importtime text lines into structured timing records.
    Why:
        JSON artifact generation and sorting require parsed numeric fields.
    Inputs:
        stderr_text: Raw stderr text emitted by Python import-time tracing.
    Outputs:
        Parsed import rows with `module`, `self_us`, and `cumulative_us`.
    Side Effects:
        None.
    Exceptions:
        Malformed lines are skipped.
    """
    rows: List[Dict[str, Any]] = []
    for raw_line in stderr_text.splitlines():
        line = raw_line.strip()
        match = _IMPORTTIME_PATTERN.match(line)
        if not match:
            continue
        module = str(match.group("module") or "").strip()
        if not module:
            continue
        rows.append(
            {
                "module": module,
                "self_us": int(match.group("self_us")),
                "cumulative_us": int(match.group("cumulative_us")),
            }
        )
    return rows


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for startup import profiling artifact generation.

    Purpose:
        Execute the main app under import-time tracing and persist a summary.
    Why:
        Startup import bottlenecks need machine-readable baseline artifacts.
    Inputs:
        argv: Optional CLI argument list override.
    Outputs:
        Process exit code.
    Side Effects:
        Spawns one traced subprocess and writes JSON/log artifacts.
    Exceptions:
        Returns non-zero on subprocess failure.
    """
    parser = argparse.ArgumentParser(
        description="Run startup import profiling for GL-260."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/perf/startup-import-profile-latest.json"),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--top", type=int, default=25, help="Number of top rows to keep."
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    app_path = repo_root / "GL-260 Data Analysis and Plotter.py"
    env = dict(os.environ)
    env["GL260_DISABLE_BOOTSTRAP_SPLASH"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [
        sys.executable,
        "-X",
        "importtime",
        str(app_path),
        "--benchmark",
        "--points=1000",
        "--cycles=4",
        "--noise=0.2",
    ]

    started_at = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed_ms = (time.perf_counter() - started_at) * 1000.0

    parsed_rows = _parse_importtime(proc.stderr)
    top_rows = sorted(parsed_rows, key=lambda row: row["cumulative_us"], reverse=True)[
        : max(1, int(args.top))
    ]

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "python": sys.version,
        "platform": platform.platform(),
        "command": cmd,
        "returncode": int(proc.returncode),
        "elapsed_ms": float(elapsed_ms),
        "top_imports": top_rows,
        "stdout_excerpt": "\n".join(proc.stdout.splitlines()[:20]),
        "stderr_excerpt": "\n".join(proc.stderr.splitlines()[:40]),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    stderr_log = output_path.with_suffix(".importtime.log")
    stderr_log.write_text(proc.stderr, encoding="utf-8")

    print(f"Startup import profile written: {output_path}")
    if proc.returncode != 0:
        print(f"Profile subprocess failed with return code {proc.returncode}")
        return int(proc.returncode)
    for row in top_rows[:10]:
        print(
            f"  {row['module']}: cumulative={row['cumulative_us']} us "
            f"self={row['self_us']} us"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
