from __future__ import annotations

from pathlib import Path

from tools.code_metrics import (
    FileMetrics,
    add_metrics,
    measure_file,
    metrics_dict,
    reduction_dict,
    zero_metrics,
)

BENCHMARK_LABELS = {
    "01_new_design": "new design document",
    "02_circle_sketch": "circle sketch",
    "03_rectangle_sketch": "rectangle sketch",
    "04_simple_extrude": "simple extrude",
    "05_builder_extrude": "builder extrude",
}

def measure_sparsity(
    repo_root: str | Path | None = None,
    *,
    baselines_dir: str | Path | None = None,
    compact_dir: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, object]:
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent
    baselines = Path(baselines_dir).resolve() if baselines_dir else root / "benchmarks" / "baselines"
    compact = Path(compact_dir).resolve() if compact_dir else root / "benchmarks" / "compact"
    report_path = Path(output_path).resolve() if output_path else root / "build" / "reports" / "sparsity_report.md"

    baseline_files = _python_files_by_relative_path(baselines)
    compact_files = _python_files_by_relative_path(compact)
    if not baseline_files:
        raise RuntimeError(f"No benchmark scripts found in {baselines}")
    if set(baseline_files) != set(compact_files):
        raise RuntimeError("Baseline and compact benchmark sets do not match.")

    pairs = []
    total_baseline = zero_metrics()
    total_compact = zero_metrics()
    for relative_path in sorted(baseline_files):
        baseline_metrics = measure_file(baseline_files[relative_path])
        compact_metrics = measure_file(compact_files[relative_path])
        total_baseline = add_metrics(total_baseline, baseline_metrics)
        total_compact = add_metrics(total_compact, compact_metrics)
        benchmark_id = relative_path.with_suffix("").as_posix()
        pairs.append(
            {
                "id": benchmark_id,
                "label": BENCHMARK_LABELS.get(benchmark_id, benchmark_id.replace("_", " ")),
                "baseline_path": str(baseline_files[relative_path]),
                "compact_path": str(compact_files[relative_path]),
                "baseline": metrics_dict(baseline_metrics),
                "compact": metrics_dict(compact_metrics),
                "reduction": reduction_dict(baseline_metrics, compact_metrics),
            }
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(pairs, total_baseline, total_compact), encoding="utf-8")
    return {
        "pair_count": len(pairs),
        "pairs": pairs,
        "baseline_totals": metrics_dict(total_baseline),
        "compact_totals": metrics_dict(total_compact),
        "reduction_totals": reduction_dict(total_baseline, total_compact),
        "report_path": str(report_path),
    }


def _python_files_by_relative_path(directory: Path) -> dict[Path, Path]:
    return {path.relative_to(directory): path for path in directory.rglob("*.py")}


def _render_report(pairs: list[dict[str, object]], baseline_total: FileMetrics, compact_total: FileMetrics) -> str:
    total_reduction = reduction_dict(baseline_total, compact_total)
    lines = [
        "# Sparsity Report",
        "",
        "Generated benchmark comparison between raw Autodesk call chains and FusionSparse compact equivalents.",
        "",
        "## Totals",
        "",
        "| Metric | Baseline | Compact | Reduction |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key, label in (
        ("chars", "Characters"),
        ("lines", "Lines"),
        ("tokens", "Tokens"),
        ("adsk_refs", "`adsk.` refs"),
    ):
        lines.append(
            f"| {label} | `{getattr(baseline_total, key)}` | `{getattr(compact_total, key)}` | "
            f"`{total_reduction[key + '_pct']:.1f}%` |"
        )

    lines.extend(["", "## Benchmark Pairs", "", "| Benchmark | Baseline chars | Compact chars | Char reduction | Baseline tokens | Compact tokens | Token reduction | Baseline `adsk.` | Compact `adsk.` |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for pair in pairs:
        baseline = pair["baseline"]
        compact = pair["compact"]
        reduction = pair["reduction"]
        lines.append(
            f"| {pair['label']} | `{baseline['chars']}` | `{compact['chars']}` | `{reduction['chars_pct']:.1f}%` | "
            f"`{baseline['tokens']}` | `{compact['tokens']}` | `{reduction['tokens_pct']:.1f}%` | "
            f"`{baseline['adsk_refs']}` | `{compact['adsk_refs']}` |"
        )

    lines.extend(["", "## Notes", "", "- Token counts are estimated using a deterministic regex tokenizer so comparisons remain stable without extra dependencies.", "- Lower counts are better for coding-agent legibility and context efficiency.", ""])
    return "\n".join(lines)
