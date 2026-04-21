"""Generate flamegraph artifacts for GL-260 performance workflows.

Purpose:
    Provide one command to regenerate flamegraph artifacts for startup and
    hotspot benchmark workflows.
Why:
    Flamegraphs are used to confirm and prioritize optimization targets.
"""

from __future__ import annotations

import argparse
import os
import pstats
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


def _build_command(target: str, repo_root: Path) -> List[str]:
    """Build the profiled command for one flamegraph target.

    Purpose:
        Resolve the subprocess command corresponding to the requested target.
    Why:
        Startup and hotspot profiling use different entry points.
    Inputs:
        target: Profiling target token (`startup` or `hotspots`).
        repo_root: Repository root path.
    Outputs:
        Subprocess command list.
    Side Effects:
        None.
    Exceptions:
        Raises ValueError for unsupported targets.
    """
    if target == "startup":
        return [
            sys.executable,
            str(repo_root / "GL-260 Data Analysis and Plotter.py"),
            "--benchmark",
            "--points=2000",
            "--cycles=8",
            "--noise=0.25",
        ]
    if target == "hotspots":
        return [
            sys.executable,
            str(repo_root / "scripts/perf/run_hotspot_bench.py"),
            "--iterations=30",
            "--warmup=5",
            "--output=docs/perf/hotspot-benchmark-latest.json",
        ]
    raise ValueError(f"Unsupported target: {target}")


def _fallback_cprofile(
    command: List[str], output_svg: Path, repo_root: Path, env: Optional[dict] = None
) -> int:
    """Run cProfile fallback when `py-spy` is unavailable.

    Purpose:
        Provide a profiling artifact path even when py-spy is missing.
    Why:
        Some environments do not have py-spy installed.
    Inputs:
        command: Target command to profile.
        output_svg: Requested flamegraph SVG path.
        repo_root: Repository root path.
    Outputs:
        Process exit code.
    Side Effects:
        Writes `.prof` and `.txt` summary artifacts near requested output path.
    Exceptions:
        Returns non-zero exit code when profiled command fails.
    """
    profile_path = output_svg.with_suffix(".cprofile.prof")
    summary_path = output_svg.with_suffix(".cprofile.txt")
    target_command = list(command)
    if target_command:
        head = str(target_command[0]).strip().lower()
        if head.endswith("python") or head.endswith("python.exe"):
            target_command = target_command[1:]
    wrapped = [
        sys.executable,
        "-m",
        "cProfile",
        "-o",
        str(profile_path),
    ] + target_command
    proc = subprocess.run(wrapped, cwd=str(repo_root), env=env, check=False)
    if proc.returncode != 0:
        return int(proc.returncode)
    stats = pstats.Stats(str(profile_path))
    stats.sort_stats("cumulative")
    with summary_path.open("w", encoding="utf-8") as handle:
        stats.stream = handle
        stats.print_stats(80)
    print(
        "py-spy not found; generated cProfile artifacts:",
        profile_path,
        summary_path,
    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for flamegraph artifact generation.

    Purpose:
        Generate flamegraph (py-spy) or cProfile fallback artifacts.
    Why:
        Keeps profiling command surface standardized for docs and CI workflows.
    Inputs:
        argv: Optional CLI argument list override.
    Outputs:
        Process exit code.
    Side Effects:
        Spawns profiling subprocesses and writes artifacts under `docs/perf/`.
    Exceptions:
        Returns non-zero exit code on subprocess failure.
    """
    parser = argparse.ArgumentParser(
        description="Generate GL-260 flamegraph artifacts."
    )
    parser.add_argument(
        "--target",
        choices=["startup", "hotspots"],
        default="hotspots",
        help="Profile target.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/perf/flamegraph-latest.svg"),
        help="Flamegraph SVG output path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    command = _build_command(args.target, repo_root)
    output_svg = Path(args.output)
    output_svg.parent.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["GL260_DISABLE_BOOTSTRAP_SPLASH"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    py_spy = shutil.which("py-spy")
    if py_spy:
        started_at = time.perf_counter()
        proc = subprocess.run(
            [
                py_spy,
                "record",
                "--format",
                "flamegraph",
                "-o",
                str(output_svg),
                "--",
            ]
            + command,
            cwd=str(repo_root),
            env=env,
            check=False,
        )
        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        if proc.returncode != 0:
            return int(proc.returncode)
        print(f"Flamegraph generated: {output_svg} ({elapsed_ms:.0f} ms)")
        return 0

    return _fallback_cprofile(command, output_svg, repo_root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
