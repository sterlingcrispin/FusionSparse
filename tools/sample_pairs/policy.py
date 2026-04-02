from __future__ import annotations

from pathlib import Path

from tools.apply_rules import load_rules

from .errors import SampleConversionError


PLANE_ALIASES = {
    "xYConstructionPlane": "xy",
    "xZConstructionPlane": "xz",
    "yZConstructionPlane": "yz",
}

FEATURE_OPERATION_ALIASES = {
    "JoinFeatureOperation": "join",
    "CutFeatureOperation": "cut",
    "IntersectFeatureOperation": "intersect",
    "NewBodyFeatureOperation": "new_body",
    "NewComponentFeatureOperation": "new_component",
}

DIRECTION_ALIASES = {
    "PositiveExtentDirection": "positive",
    "NegativeExtentDirection": "negative",
    "SymmetricExtentDirection": "symmetric",
}


def load_compact_policy(repo_root: str | Path | None) -> dict[str, object]:
    return load_rules(repo_root)["compact_policy"]


def load_sketch_translation_policy(repo_root: str | Path | None) -> dict[tuple[str, str, int], dict[str, object]]:
    sketch = load_compact_policy(repo_root)["sketch"]
    reverse: dict[tuple[str, str, int], dict[str, object]] = {}
    for method_id, raw_method in sketch["methods"].items():
        collection = sketch["collections"].get(method_id)
        coercers = sketch["coercers"].get(method_id)
        if not isinstance(collection, str):
            raise SampleConversionError(f"Missing sketch collection for translation method: {method_id}")
        if not isinstance(coercers, list):
            raise SampleConversionError(f"Missing sketch coercers for translation method: {method_id}")
        reverse[(collection, raw_method, len(coercers))] = {"compact_method": method_id, "coercers": coercers}
    return reverse


def load_construction_translation_policy(repo_root: str | Path | None) -> dict[str, dict[str, object]]:
    construction = load_compact_policy(repo_root)["construction"]
    reverse: dict[str, dict[str, object]] = {}
    for helper_name, section in construction.items():
        reverse[section["family_id"]] = {
            "helper_name": helper_name,
            "builder_input": section["builder_input"],
            "builder_terminal": section["builder_terminal"],
            "reverse_methods": {raw_name: method_name for method_name, raw_name in section["methods"].items()},
        }
    return reverse
