"""Compact hole helpers."""

from __future__ import annotations

from fusion_sparse.runtime.adapter import unwrap, wrap
from fusion_sparse.runtime.enums import hole_pos
from fusion_sparse.runtime.values import v

from fusion_sparse.compact._helpers import flatten_object_collection, point_like


class HoleBuilder:
    __slots__ = ("_depth", "_diameter", "_family", "_features", "_position", "_variant", "_variant_args")

    def __init__(self, features, diameter, depth, family: dict[str, object]):
        self._depth = depth
        self._diameter = diameter
        self._family = family
        self._features = features
        self._position = None
        self._variant = "simple"
        self._variant_args = ()

    def counterbore(self, counterbore_diameter, counterbore_depth):
        self._variant = "counterbore"
        self._variant_args = (counterbore_diameter, counterbore_depth)
        return self

    def countersink(self, countersink_diameter, countersink_angle):
        self._variant = "countersink"
        self._variant_args = (countersink_diameter, countersink_angle)
        return self

    def depth(self, value):
        self._depth = value
        return self

    def by_offsets(self, face, point, edge1, offset1, edge2, offset2):
        self._position = (
            "by_offsets",
            (unwrap(face), point_like(point), unwrap(edge1), v(offset1), unwrap(edge2), v(offset2)),
        )
        return self

    def on_edge(self, face, edge, position="mid"):
        self._position = ("on_edge", (unwrap(face), unwrap(edge), _hole_position(position)))
        return self

    def at_center(self, face, circular_edge):
        self._position = ("at_center", (unwrap(face), unwrap(circular_edge)))
        return self

    def by_points(self, *points):
        self._position = ("by_points", (flatten_object_collection(*points),))
        return self

    def build(self):
        input_obj = self._create_input()
        if self._depth is not None:
            getattr(input_obj, self._family["input_methods"]["depth"])(v(self._depth))
        if self._position is None:
            raise ValueError("HoleBuilder requires a positioning method before build().")
        position_name, args = self._position
        getattr(input_obj, self._family["input_methods"][position_name])(*args)
        return wrap(getattr(self._features, self._family["builder_terminal"])(input_obj))

    def _create_input(self):
        create_method = getattr(self._features, self._family["create_methods"][self._variant])
        if self._variant == "simple":
            return create_method(v(self._diameter))
        return create_method(v(self._diameter), *(v(value) for value in self._variant_args))


def _hole_position(position):
    raw_position = unwrap(position)
    if isinstance(raw_position, str):
        normalized = raw_position.strip().lower().replace("-", "_")
        return getattr(hole_pos, normalized)
    return raw_position


__all__ = ["HoleBuilder"]
