"""Construction helper namespaces for components."""

from __future__ import annotations

from fusion_sparse.runtime.adapter import unwrap, wrap
from fusion_sparse.runtime.values import v

from fusion_sparse.compact._helpers import plane_or_entity, point_like


class PlaneHelper:
    __slots__ = ("_component", "_family", "_policy")

    def __init__(self, component, family, policy: dict[str, object]):
        self._component = component
        self._family = family
        self._policy = policy

    def offset(self, reference, distance):
        return self._create("offset", plane_or_entity(self._component, reference), v(distance))

    def angle(self, line_or_axis, angle, reference_plane):
        return self._create("angle", unwrap(line_or_axis), v(angle), plane_or_entity(self._component, reference_plane))

    def between(self, plane_a, plane_b):
        return self._create(
            "between",
            plane_or_entity(self._component, plane_a),
            plane_or_entity(self._component, plane_b),
        )

    def tangent(self, face, angle, reference_plane):
        return self._create("tangent", unwrap(face), v(angle), plane_or_entity(self._component, reference_plane))

    def edges(self, edge_a, edge_b):
        return self._create("edges", unwrap(edge_a), unwrap(edge_b))

    def three_points(self, a, b, c):
        return self._create("three_points", point_like(a), point_like(b), point_like(c))

    def tangent_at(self, face, point):
        return self._create("tangent_at", unwrap(face), point_like(point))

    def on_path(self, path, distance):
        return self._create("on_path", unwrap(path), v(distance))

    def _create(self, method_key: str, *args):
        input_obj = getattr(self._family, self._policy["builder_input"])()
        getattr(input_obj, self._policy["methods"][method_key])(*args)
        return wrap(getattr(self._family, self._policy["builder_terminal"])(input_obj))


class AxisHelper:
    __slots__ = ("_component", "_family", "_policy")

    def __init__(self, component, family, policy: dict[str, object]):
        self._component = component
        self._family = family
        self._policy = policy

    def circular_face(self, face):
        return self._create("circular_face", unwrap(face))

    def perpendicular(self, face, point):
        return self._create("perpendicular", unwrap(face), point_like(point))

    def between_planes(self, plane_a, plane_b):
        return self._create(
            "between_planes",
            plane_or_entity(self._component, plane_a),
            plane_or_entity(self._component, plane_b),
        )

    def between_points(self, a, b):
        return self._create("between_points", point_like(a), point_like(b))

    def edge(self, edge_or_curve):
        return self._create("edge", unwrap(edge_or_curve))

    def normal(self, face, point):
        return self._create("normal", unwrap(face), point_like(point))

    def _create(self, method_key: str, *args):
        input_obj = getattr(self._family, self._policy["builder_input"])()
        getattr(input_obj, self._policy["methods"][method_key])(*args)
        return wrap(getattr(self._family, self._policy["builder_terminal"])(input_obj))


class PointHelper:
    __slots__ = ("_component", "_family", "_policy")

    def __init__(self, component, family, policy: dict[str, object]):
        self._component = component
        self._family = family
        self._policy = policy

    def edges(self, edge_a, edge_b):
        return self._create("edges", unwrap(edge_a), unwrap(edge_b))

    def planes(self, plane_a, plane_b, plane_c):
        return self._create(
            "planes",
            plane_or_entity(self._component, plane_a),
            plane_or_entity(self._component, plane_b),
            plane_or_entity(self._component, plane_c),
        )

    def edge_plane(self, edge_or_axis, plane):
        return self._create("edge_plane", unwrap(edge_or_axis), plane_or_entity(self._component, plane))

    def center(self, entity):
        return self._create("center", unwrap(entity))

    def at(self, entity):
        return self._create("at", unwrap(entity))

    def _create(self, method_key: str, *args):
        input_obj = getattr(self._family, self._policy["builder_input"])()
        getattr(input_obj, self._policy["methods"][method_key])(*args)
        return wrap(getattr(self._family, self._policy["builder_terminal"])(input_obj))

__all__ = ["AxisHelper", "PlaneHelper", "PointHelper"]
