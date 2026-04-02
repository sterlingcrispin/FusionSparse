"""Generic executor for generated compact surface metadata."""

from __future__ import annotations

from fusion_sparse.compact._helpers import point_collection, point_like, sketch_length_cm
from fusion_sparse.generated.compact_policy import PLANE_ALIASES
from fusion_sparse.generated.compact_surface import COMPACT_METHODS, COMPACT_PROPERTIES
from fusion_sparse.runtime.adapter import unwrap, wrap


def resolve_generated_property(raw_obj, property_id: str):
    spec = COMPACT_PROPERTIES[property_id]
    return wrap(_resolve_attr_path(raw_obj, spec["attr_path"]))


def invoke_generated_method(raw_obj, method_id: str, *args):
    spec = COMPACT_METHODS[method_id]
    kind = spec["kind"]
    if kind == "call":
        target = _resolve_attr_path(raw_obj, spec["target_attrs"])
        method = getattr(target, spec["method"])
        coerced_args = [
            _coerce_argument(raw_obj, coercer, value)
            for coercer, value in zip(spec["coercers"], args, strict=True)
        ]
        return wrap(method(*coerced_args))
    if kind == "collection_list":
        return [wrap(item) for item in _collection_items(_resolve_attr_path(raw_obj, spec["attr_path"]))]
    if kind == "collection_item":
        index = args[0] if args else spec.get("default_index", 0)
        items = _collection_items(_resolve_attr_path(raw_obj, spec["attr_path"]))
        return wrap(items[index])
    raise ValueError(f"Unsupported compact surface method kind: {kind}")


def _resolve_attr_path(raw_obj, attr_path):
    value = raw_obj
    for attr_name in attr_path:
        value = getattr(value, attr_name)
    return value


def _coerce_argument(context_raw, coercer: str, value):
    if coercer == "identity":
        return unwrap(value)
    if coercer == "point":
        return point_like(value)
    if coercer == "point_collection":
        return point_collection(value)
    if coercer == "length_cm":
        return sketch_length_cm(value)
    if coercer == "plane":
        return _resolve_plane(context_raw, value)
    raise ValueError(f"Unsupported compact coercer: {coercer}")


def _resolve_plane(component_raw, plane):
    raw_plane = unwrap(plane)
    if isinstance(raw_plane, str):
        attr_name = PLANE_ALIASES.get(raw_plane.strip().lower())
        if attr_name is None:
            raise ValueError(f"Unsupported sketch plane alias: {plane}")
        return getattr(component_raw, attr_name)
    return raw_plane


def _collection_items(collection):
    raw = unwrap(collection)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, tuple):
        return list(raw)
    count = getattr(raw, "count", None)
    item = getattr(raw, "item", None)
    if isinstance(count, int) and callable(item):
        return [item(index) for index in range(count)]
    try:
        return list(raw)
    except TypeError:
        return []
