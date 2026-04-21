# Performance Harness (v4.15.0)

This directory stores repeatable performance artifacts and regeneration commands.

## Commands

Run startup import profiling:

```powershell
python scripts/perf/run_startup_import_profile.py --output docs/perf/startup-import-profile-latest.json
```

Run hotspot microbenchmarks (Final Report / Compare / Ledger cores):

```powershell
python scripts/perf/run_hotspot_bench.py --iterations 20 --warmup 3 --output docs/perf/hotspot-benchmark-latest.json
```

Generate flamegraph artifacts (py-spy preferred, cProfile fallback):

```powershell
python scripts/perf/generate_flamegraph.py --target hotspots --output docs/perf/flamegraph-hotspots-latest.svg
python scripts/perf/generate_flamegraph.py --target startup --output docs/perf/flamegraph-startup-latest.svg
```

## Artifact Notes

- `startup-import-profile-latest.json`: Top import bottlenecks from Python `-X importtime`.
- `hotspot-benchmark-latest.json`: Median/p95 timing summaries for hotspot kernels.
- `flamegraph-*.svg`: py-spy flamegraph output when available.
- `*.cprofile.prof` + `*.cprofile.txt`: fallback artifacts when py-spy is unavailable.

## Targeted Hotspots

- `final_report_cycle_stats_rows_core`
- `final_report_cycle_timeline_rows_core`
- `compare_aligned_cycle_rows_core`
- `ledger_sort_filter_indices_core`
