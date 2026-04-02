"""Shared helpers for compact feature wrappers."""

from __future__ import annotations

import re

from fusion_sparse.generated.compact_policy import SKETCH_LENGTH_PATTERN, SKETCH_LENGTH_UNITS_CM
from fusion_sparse.runtime._adsk import looks_like_type
from fusion_sparse.runtime.adapter import unwrap
from fusion_sparse.runtime.geom import oc, p
from fusion_sparse.runtime.refs import Ref
from fusion_sparse.runtime.enums import loft_align, op, pattern_dist, shell_type, sweep_scale
from fusion_sparse.runtime.values import Expression


_LENGTH_PATTERN = re.compile(SKETCH_LENGTH_PATTERN, re.IGNORECASE)


def feature_operation(operation):
    raw_operation = unwrap(operation)
    if isinstance(raw_operation, str):
        normalized = raw_operation.strip().lower().replace("-", "_")
        return getattr(op, normalized)
    return raw_operation


def point_like(value):
    raw = unwrap(value)
    if isinstance(raw, (tuple, list)) and len(raw) in {2, 3}:
        return p(raw)
    return raw


def point_collection(value):
    raw = unwrap(value)
    if looks_like_type(raw, "ObjectCollection"):
        return raw
    if _is_multi_value(raw):
        return oc(*(point_like(item) for item in raw))
    return oc(point_like(raw))


def pattern_distance_type(value):
    raw = unwrap(value)
    if isinstance(raw, str):
        normalized = raw.strip().lower().replace("-", "_")
        return getattr(pattern_dist, normalized)
    return raw


def sweep_profile_scaling(value):
    raw = unwrap(value)
    if isinstance(raw, str):
        normalized = raw.strip().lower().replace("-", "_")
        return getattr(sweep_scale, normalized)
    return raw


def loft_edge_alignment(value):
    raw = unwrap(value)
    if isinstance(raw, str):
        normalized = raw.strip().lower().replace("-", "_")
        return getattr(loft_align, normalized)
    return raw


def shell_type_value(value):
    raw = unwrap(value)
    if isinstance(raw, str):
        normalized = raw.strip().lower().replace("-", "_")
        return getattr(shell_type, normalized)
    return raw


def object_collection(value):
    raw = unwrap(value)
    if _is_multi_value(raw):
        return oc(*raw)
    return oc(raw)


def first_raw(value):
    raw = unwrap(value)
    if _is_multi_value(raw):
        for item in raw:
            return unwrap(item)
        return None
    return raw


def single_or_collection(value):
    raw = unwrap(value)
    if _is_multi_value(raw):
        return oc(*raw)
    return raw


def raw_list(value):
    raw = unwrap(value)
    if _is_multi_value(raw):
        return [unwrap(item) for item in raw]
    return [raw]


def sketch_length_cm(value) -> float:
    raw = unwrap(value)
    if isinstance(raw, bool):
        raise TypeError("Sketch lengths cannot be boolean values.")
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(value, Expression):
        raw = value.text
    if isinstance(raw, str):
        match = _LENGTH_PATTERN.match(raw)
        if not match:
            raise TypeError(f"Unsupported sketch length expression: {raw}")
        magnitude = float(match.group("value"))
        unit = match.group("unit").lower()
        return magnitude * SKETCH_LENGTH_UNITS_CM[unit]
    for attr_name in ("realValue", "value"):
        candidate = getattr(raw, attr_name, None)
        if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
            return float(candidate)
    raise TypeError(f"Unsupported sketch length value: {type(value).__name__}")


def feature_path(features, value, *, chain=True):
    raw = unwrap(value)
    if looks_like_type(raw, "Path"):
        return raw
    return features.createPath(raw, bool(chain))


def flatten_object_collection(*values):
    items = []
    for value in values:
        raw = unwrap(value)
        if _is_multi_value(raw):
            items.extend(raw)
        else:
            items.append(raw)
    return oc(*items)


def plane_or_entity(component, value, plane_aliases=None):
    raw = unwrap(value)
    if isinstance(raw, str):
        attr_name = (plane_aliases or _default_plane_aliases()).get(raw.strip().lower())
        if attr_name is not None:
            return getattr(component, attr_name)
    return raw


def _default_plane_aliases():
    return {
        "xy": "xYConstructionPlane",
        "xz": "xZConstructionPlane",
        "yz": "yZConstructionPlane",
    }


def _is_multi_value(value):
    return isinstance(value, (list, tuple, set, frozenset))


__all__ = [
    "feature_operation",
    "feature_path",
    "first_raw",
    "flatten_object_collection",
    "loft_edge_alignment",
    "object_collection",
    "pattern_distance_type",
    "plane_or_entity",
    "point_collection",
    "point_like",
    "raw_list",
    "shell_type_value",
    "sketch_length_cm",
    "single_or_collection",
    "sweep_profile_scaling",
]
