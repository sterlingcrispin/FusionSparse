from __future__ import annotations

from pathlib import Path

import yaml

from .errors import SampleConversionError


def load_sample_pair_rules(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SampleConversionError(f"Sample-pair rules file not found: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict) or not isinstance(loaded.get("pairs"), list):
        raise SampleConversionError(f"{path} must contain a top-level 'pairs' list.")
    for index, pair in enumerate(loaded["pairs"]):
        if not isinstance(pair, dict):
            raise SampleConversionError(f"sample_pairs pair #{index} must be a mapping.")
        for key in ("id", "title", "source_page"):
            value = pair.get(key)
            if not isinstance(value, str) or not value:
                raise SampleConversionError(f"sample_pairs pair #{index} is missing a valid '{key}'.")
        has_official_script = isinstance(pair.get("official_script"), str) and bool(pair.get("official_script"))
        official_generation = pair.get("official_generation")
        if has_official_script == bool(official_generation):
            raise SampleConversionError(
                f"sample_pairs pair #{index} must define exactly one of 'official_script' or 'official_generation'."
            )
        if official_generation is not None:
            if not isinstance(official_generation, dict):
                raise SampleConversionError(f"sample_pairs pair #{index} official_generation must be a mapping.")
            mode = official_generation.get("mode")
            if mode not in {"doc_run", "doc_demo_sketch"}:
                raise SampleConversionError(
                    f"sample_pairs pair #{index} official_generation.mode must be 'doc_run' or 'doc_demo_sketch'."
                )
    return loaded


def path_for_manifest(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
