"""Compact modification-feature helpers."""

from __future__ import annotations

from fusion_sparse.compact._helpers import (
    feature_operation,
    first_raw,
    object_collection,
    plane_or_entity,
    point_like,
    single_or_collection,
)
from fusion_sparse.runtime._adsk import import_adsk_module
from fusion_sparse.runtime.adapter import unwrap, wrap
from fusion_sparse.runtime.geom import mat_identity, vec
from fusion_sparse.runtime.values import v


def move_entities(component, family: dict[str, object], entities, *, translation=None, transform=None):
    if (translation is None) == (transform is None):
        raise ValueError("move requires exactly one of translation= or transform=.")
    moves = component.features.moveFeatures
    input_obj = getattr(moves, family["builder_input"])(object_collection(entities))
    getattr(input_obj, family["input_methods"]["free_move"])(_move_transform(translation=translation, transform=transform))
    return wrap(getattr(moves, family["builder_terminal"])(input_obj))


def offset_entities(component, family: dict[str, object], entities, distance, *, op="new_body", chain=True):
    offsets = component.features.offsetFeatures
    input_obj = getattr(offsets, family["builder_input"])(
        object_collection(entities),
        v(distance),
        feature_operation(op),
        bool(chain),
    )
    return wrap(getattr(offsets, family["builder_terminal"])(input_obj))


def replace_faces(component, family: dict[str, object], source_faces, target, *, tangent_chain=False):
    replace_features = component.features.replaceFaceFeatures
    input_obj = getattr(replace_features, family["builder_input"])(
        object_collection(source_faces),
        bool(tangent_chain),
        plane_or_entity(component, target),
    )
    return wrap(getattr(replace_features, family["builder_terminal"])(input_obj))


def scale_entities(component, family: dict[str, object], entities, origin, factor, *, xyz=None):
    scales = component.features.scaleFeatures
    input_obj = getattr(scales, family["builder_input"])(
        object_collection(entities),
        point_like(origin),
        v(factor),
    )
    if xyz is not None:
        if not isinstance(xyz, (tuple, list)) or len(xyz) != 3:
            raise ValueError("scale xyz= expects a 3-item tuple or list.")
        getattr(input_obj, family["input_methods"]["non_uniform"])(*(v(value) for value in xyz))
    return wrap(getattr(scales, family["builder_terminal"])(input_obj))


def split_bodies(component, family: dict[str, object], bodies, tool, *, extend=True):
    split_features = component.features.splitBodyFeatures
    input_obj = getattr(split_features, family["builder_input"])(
        single_or_collection(bodies),
        plane_or_entity(component, tool),
        bool(extend),
    )
    return wrap(getattr(split_features, family["builder_terminal"])(input_obj))


def thread_faces(
    component,
    family: dict[str, object],
    faces,
    *,
    internal=False,
    length=None,
    thread_type=None,
    designation=None,
    thread_class=None,
):
    thread_features = component.features.threadFeatures
    face_collection = object_collection(faces)
    if thread_type is None or designation is None or thread_class is None:
        thread_type, designation, thread_class = _resolve_thread_spec(
            thread_features,
            first_raw(faces),
            internal=internal,
            thread_type=thread_type,
            designation=designation,
            thread_class=thread_class,
        )
    fusion = import_adsk_module("adsk.fusion")
    thread_info = fusion.ThreadInfo.create(
        False,
        bool(internal),
        str(thread_type),
        str(designation),
        str(thread_class),
        True,
    )
    input_obj = getattr(thread_features, family["builder_input"])(face_collection, thread_info)
    if length is not None:
        setattr(input_obj, family["input_attrs"]["full_length"], False)
        setattr(input_obj, family["input_attrs"]["length"], v(length))
    return wrap(getattr(thread_features, family["builder_terminal"])(input_obj))


def trim_tool(component, family: dict[str, object], tool, *, cell=0):
    trim_features = component.features.trimFeatures
    input_obj = getattr(trim_features, family["builder_input"])(unwrap(tool))
    cells = getattr(input_obj, family["input_attrs"]["cells"])
    getattr(cells, family["input_methods"]["item"])(int(cell)).isSelected = True
    return wrap(getattr(trim_features, family["builder_terminal"])(input_obj))


def _move_transform(*, translation=None, transform=None):
    if transform is not None:
        return unwrap(transform)
    matrix = mat_identity()
    matrix.translation = vec(translation)
    return matrix


def _resolve_thread_spec(
    thread_features,
    face,
    *,
    internal: bool,
    thread_type,
    designation,
    thread_class,
):
    query = thread_features.threadDataQuery
    resolved_type = thread_type or getattr(query, "defaultMetricThreadType", None) or _first_item(getattr(query, "allThreadTypes", []))
    if resolved_type is None:
        raise ValueError("Could not resolve a default thread type for thread().")
    resolved_designation = designation
    resolved_class = thread_class
    diameter = _thread_diameter(face)
    if (resolved_designation is None or resolved_class is None) and diameter is not None:
        recommended = query.recommendThreadData(float(diameter), bool(internal), str(resolved_type))
        if isinstance(recommended, (tuple, list)) and len(recommended) >= 3 and recommended[0]:
            resolved_designation = resolved_designation or recommended[1]
            resolved_class = resolved_class or recommended[2]
    if resolved_designation is None or resolved_class is None:
        size = _first_item(query.allSizes(str(resolved_type)))
        if size is None:
            raise ValueError("Could not resolve a thread size for thread().")
        resolved_designation = resolved_designation or _first_item(query.allDesignations(str(resolved_type), size))
        if resolved_designation is None:
            raise ValueError("Could not resolve a thread designation for thread().")
        resolved_class = resolved_class or _first_item(query.allClasses(bool(internal), str(resolved_type), str(resolved_designation)))
    if resolved_class is None:
        raise ValueError("Could not resolve a thread class for thread().")
    return resolved_type, resolved_designation, resolved_class


def _thread_diameter(face):
    geometry = getattr(face, "geometry", None)
    radius = getattr(geometry, "radius", None)
    if radius is None:
        return None
    try:
        return float(radius) * 2.0
    except (TypeError, ValueError):
        return None


def _first_item(value):
    if hasattr(value, "count") and hasattr(value, "item"):
        count = getattr(value, "count", 0)
        if count:
            return value.item(0)
        return None
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


__all__ = [
    "move_entities",
    "offset_entities",
    "replace_faces",
    "scale_entities",
    "split_bodies",
    "thread_faces",
    "trim_tool",
]
