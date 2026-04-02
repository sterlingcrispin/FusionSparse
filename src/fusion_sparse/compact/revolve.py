"""Compact revolve helpers."""

from __future__ import annotations

from fusion_sparse.runtime.adapter import unwrap, wrap
from fusion_sparse.runtime.refs import Ref
from fusion_sparse.runtime.values import v


class RevolveBuilder(Ref):
    """Builder wrapper around RevolveFeatureInput."""

    __slots__ = ("_angle", "_family", "_revolve_features", "_symmetric")

    def __init__(self, revolve_features, profile, axis, operation, family: dict[str, object]):
        builder_input = getattr(revolve_features, family["builder_input"])
        super().__init__(builder_input(profile, axis, operation))
        self._angle = None
        self._family = family
        self._revolve_features = revolve_features
        self._symmetric = False

    def angle(self, angle, symmetric=False):
        self._angle = angle
        self._symmetric = bool(symmetric)
        return self

    def build(self):
        if self._angle is None:
            raise ValueError("RevolveBuilder requires angle(...) before build().")
        getattr(self.raw, self._family["input_methods"]["angle"])(self._symmetric, v(self._angle))
        return wrap(getattr(self._revolve_features, self._family["builder_terminal"])(self.raw))


__all__ = ["RevolveBuilder"]
