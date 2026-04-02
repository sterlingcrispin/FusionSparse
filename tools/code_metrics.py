from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


TOKEN_PATTERN = re.compile(r"\w+|[^\s\w]", re.UNICODE)
ADSK_PATTERN = re.compile(r"\badsk\.")


@dataclass(frozen=True)
class FileMetrics:
    chars: int
    lines: int
    tokens: int
    adsk_refs: int


def measure_text(text: str) -> FileMetrics:
    return FileMetrics(
        chars=len(text),
        lines=len(text.splitlines()),
        tokens=len(TOKEN_PATTERN.findall(text)),
        adsk_refs=len(ADSK_PATTERN.findall(text)),
    )


def measure_file(path: str | Path) -> FileMetrics:
    text = Path(path).read_text(encoding="utf-8")
    return measure_text(text)


def zero_metrics() -> FileMetrics:
    return FileMetrics(chars=0, lines=0, tokens=0, adsk_refs=0)


def add_metrics(left: FileMetrics, right: FileMetrics) -> FileMetrics:
    return FileMetrics(
        chars=left.chars + right.chars,
        lines=left.lines + right.lines,
        tokens=left.tokens + right.tokens,
        adsk_refs=left.adsk_refs + right.adsk_refs,
    )


def metrics_dict(metrics: FileMetrics) -> dict[str, int]:
    return {
        "chars": metrics.chars,
        "lines": metrics.lines,
        "tokens": metrics.tokens,
        "adsk_refs": metrics.adsk_refs,
    }


def percent_reduction(baseline: int, compact: int) -> float:
    if baseline <= 0:
        return 0.0
    return round((baseline - compact) / baseline * 100.0, 1)


def reduction_dict(baseline: FileMetrics, compact: FileMetrics) -> dict[str, float]:
    return {
        "chars_pct": percent_reduction(baseline.chars, compact.chars),
        "lines_pct": percent_reduction(baseline.lines, compact.lines),
        "tokens_pct": percent_reduction(baseline.tokens, compact.tokens),
        "adsk_refs_pct": percent_reduction(baseline.adsk_refs, compact.adsk_refs),
    }
