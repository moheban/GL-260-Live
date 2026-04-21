"""Run repeatable microbenchmarks for known GL-260 heavy-tab hotspot kernels.

Purpose:
    Measure representative hotspot kernels for Final Report, Compare, and Ledger
    using deterministic synthetic payloads.
Why:
    Provides repeatable before/after timing summaries that can be archived with
    performance optimization changes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional


def _load_app_module(repo_root: Path) -> Any:
    """Load the main GL-260 application module from the repository root.

    Purpose:
        Import the monolithic application module by file path.
    Why:
        Benchmark scripts need direct access to internal hotspot core functions.
    Inputs:
        repo_root: Repository root path containing the main script.
    Outputs:
        Imported module object.
    Side Effects:
        Executes module import side effects.
    Exceptions:
        Raises RuntimeError when module loading fails.
    """
    module_path = repo_root / "GL-260 Data Analysis and Plotter.py"
    repo_text = str(repo_root)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)
    spec = importlib.util.spec_from_file_location("gl260_app_main", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _time_case(fn: Callable[[], Any], iterations: int, warmup: int) -> Dict[str, float]:
    """Benchmark one callable and return summary timing statistics.

    Purpose:
        Capture deterministic wall-clock timing samples for one hotspot callable.
    Why:
        Consistent summary stats are needed for before/after perf comparisons.
    Inputs:
        fn: Callable benchmark target.
        iterations: Number of measured iterations.
        warmup: Number of warmup iterations to discard.
    Outputs:
        Dict containing mean/median/min/max/p95 timing metrics in milliseconds.
    Side Effects:
        Executes the benchmark callable repeatedly.
    Exceptions:
        Propagates callable exceptions to fail-fast benchmark runs.
    """
    for _ in range(max(0, warmup)):
        fn()
    samples_ms: List[float] = []
    for _ in range(max(1, iterations)):
        start = time.perf_counter()
        fn()
        samples_ms.append((time.perf_counter() - start) * 1000.0)
    ordered = sorted(samples_ms)
    p95_index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95))))
    return {
        "mean_ms": float(statistics.fmean(samples_ms)),
        "median_ms": float(statistics.median(samples_ms)),
        "min_ms": float(min(samples_ms)),
        "max_ms": float(max(samples_ms)),
        "p95_ms": float(ordered[p95_index]),
        "iterations": float(len(samples_ms)),
    }


def _build_cases(module: Any) -> Mapping[str, Callable[[], Any]]:
    """Build the hotspot benchmark case map.

    Purpose:
        Assemble named benchmark callables for heavy-tab kernels.
    Why:
        One shared case map keeps benchmark output stable across runs.
    Inputs:
        module: Imported application module exposing hotspot core helpers.
    Outputs:
        Mapping of case names to zero-argument benchmark callables.
    Side Effects:
        None.
    Exceptions:
        Missing symbols raise AttributeError.
    """
    stats_rows = module._synthetic_final_report_cycle_stats_rows()
    timeline_rows = module._synthetic_final_report_cycle_timeline_rows()
    compare_rows_a = module._synthetic_compare_cycle_rows()
    compare_rows_b = [dict(row) for row in module._synthetic_compare_cycle_rows()]
    for idx, row in enumerate(compare_rows_b, start=1):
        row["selected_mass_g"] = float(row.get("selected_mass_g", 0.0) or 0.0) * (
            1.02 + idx * 0.01
        )
        row["cumulative_co2_mass_g"] = (
            float(row.get("cumulative_co2_mass_g", 0.0) or 0.0) * 1.03
        )
    ledger_rows = module._synthetic_ledger_sort_filter_entries()

    return {
        "final_report_cycle_stats_rows_core_python": lambda: module._python_final_report_cycle_stats_rows_core(
            stats_rows,
            "Duration (days)",
        ),
        "final_report_cycle_timeline_rows_core_python": lambda: module._python_final_report_cycle_timeline_rows_core(
            timeline_rows,
        ),
        "compare_aligned_cycle_rows_core_python": lambda: module._python_compare_aligned_cycle_rows_core(
            compare_rows_a,
            compare_rows_b,
        ),
        "ledger_sort_filter_indices_core_python": lambda: module._python_ledger_sort_filter_indices_core(
            ledger_rows,
            filter_value="All Profiles",
            sort_mode="column",
            sort_key="final_mass_g",
            sort_desc=True,
            sort_column_type="number",
        ),
    }


def _maybe_add_rust_cases(module: Any, cases: Dict[str, Callable[[], Any]]) -> None:
    """Append Rust benchmark cases when backend wrappers return valid payloads.

    Purpose:
        Include optional Rust-path measurements in the same output artifact.
    Why:
        Perf tracking needs side-by-side Python/Rust timing where available.
    Inputs:
        module: Imported application module exposing Rust wrappers.
        cases: Mutable benchmark case mapping.
    Outputs:
        None.
    Side Effects:
        Adds case entries into the provided mapping.
    Exceptions:
        Rust probe failures are swallowed to keep Python benchmarks running.
    """
    try:
        stats_rows = module._synthetic_final_report_cycle_stats_rows()
        timeline_rows = module._synthetic_final_report_cycle_timeline_rows()
        compare_rows_a = module._synthetic_compare_cycle_rows()
        compare_rows_b = module._synthetic_compare_cycle_rows()
        ledger_rows = module._synthetic_ledger_sort_filter_entries()

        rust_stats = module._rust_final_report_cycle_stats_rows_core(
            stats_rows, "Duration (days)"
        )
        if isinstance(rust_stats, list):
            cases["final_report_cycle_stats_rows_core_rust"] = (
                lambda: module._rust_final_report_cycle_stats_rows_core(
                    stats_rows,
                    "Duration (days)",
                )
            )

        rust_timeline = module._rust_final_report_cycle_timeline_rows_core(
            timeline_rows
        )
        if isinstance(rust_timeline, list):
            cases["final_report_cycle_timeline_rows_core_rust"] = (
                lambda: module._rust_final_report_cycle_timeline_rows_core(
                    timeline_rows,
                )
            )

        rust_compare = module._rust_compare_aligned_cycle_rows_core(
            compare_rows_a, compare_rows_b
        )
        if isinstance(rust_compare, list):
            cases["compare_aligned_cycle_rows_core_rust"] = (
                lambda: module._rust_compare_aligned_cycle_rows_core(
                    compare_rows_a,
                    compare_rows_b,
                )
            )

        rust_ledger = module._rust_ledger_sort_filter_indices_core(
            ledger_rows,
            filter_value="All Profiles",
            sort_mode="column",
            sort_key="final_mass_g",
            sort_desc=True,
            sort_column_type="number",
        )
        if isinstance(rust_ledger, list):
            cases["ledger_sort_filter_indices_core_rust"] = (
                lambda: module._rust_ledger_sort_filter_indices_core(
                    ledger_rows,
                    filter_value="All Profiles",
                    sort_mode="column",
                    sort_key="final_mass_g",
                    sort_desc=True,
                    sort_column_type="number",
                )
            )
    except Exception:
        return


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for hotspot microbenchmark execution.

    Purpose:
        Run configured hotspot microbenchmarks and persist JSON summary output.
    Why:
        Perf optimization review needs repeatable machine-readable benchmark data.
    Inputs:
        argv: Optional CLI argument list override.
    Outputs:
        Process exit code.
    Side Effects:
        Reads the main app module and writes benchmark JSON artifacts.
    Exceptions:
        Returns non-zero exit code on fatal runtime errors.
    """
    parser = argparse.ArgumentParser(description="Run GL-260 hotspot microbenchmarks.")
    parser.add_argument(
        "--iterations", type=int, default=20, help="Measured iterations per case."
    )
    parser.add_argument(
        "--warmup", type=int, default=3, help="Warmup iterations per case."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/perf/hotspot-benchmark-latest.json"),
        help="Output JSON path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    module = _load_app_module(repo_root)
    cases: Dict[str, Callable[[], Any]] = dict(_build_cases(module))
    _maybe_add_rust_cases(module, cases)

    summary: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "python": sys.version,
        "platform": platform.platform(),
        "iterations": int(max(1, args.iterations)),
        "warmup": int(max(0, args.warmup)),
        "cases": {},
    }

    for case_name, case_fn in cases.items():
        summary["cases"][case_name] = _time_case(
            case_fn,
            iterations=max(1, args.iterations),
            warmup=max(0, args.warmup),
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Hotspot benchmark complete: {output_path}")
    for case_name in sorted(summary["cases"].keys()):
        row = summary["cases"][case_name]
        print(
            f"  {case_name}: median={row['median_ms']:.2f} ms "
            f"p95={row['p95_ms']:.2f} ms mean={row['mean_ms']:.2f} ms"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
