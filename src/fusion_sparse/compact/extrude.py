"""Compact extrude helpers."""

from __future__ import annotations

from fusion_sparse.generated.compact_policy import EXTRUDE_POLICY
from fusion_sparse.runtime._adsk import import_adsk_module
from fusion_sparse.runtime.adapter import unwrap, wrap
from fusion_sparse.runtime.enums import dir
from fusion_sparse.runtime.refs import Ref
from fusion_sparse.runtime.values import v


class ExtrudeBuilder(Ref):
    """Builder wrapper around ExtrudeFeatureInput."""

    __slots__ = ("_direction", "_distance", "_extent_kind", "_extrude_features", "_family", "_symmetric_full_length", "_taper")

    def __init__(self, extrude_features, profile, operation, family: dict[str, str]):
        builder_input = getattr(extrude_features, family["builder_input"])
        super().__init__(builder_input(profile, operation))
        self._direction = "positive"
        self._distance = None
        self._extent_kind = None
        self._extrude_features = extrude_features
        self._family = family
        self._symmetric_full_length = True
        self._taper = None

    def one_side(self, distance, direction="positive"):
        self._distance = distance
        self._direction = direction
        self._extent_kind = "one_side"
        self._apply_extent()
        return self

    def symmetric(self, distance, full_length=True):
        self._distance = distance
        self._extent_kind = "symmetric"
        self._symmetric_full_length = bool(full_length)
        self._apply_extent()
        return self

    def through_all(self, direction="positive"):
        self._distance = None
        self._direction = direction
        self._extent_kind = "through_all"
        self._apply_extent()
        return self

    def solid(self, flag=True):
        setattr(self.raw, EXTRUDE_POLICY["input_attrs"]["solid"], bool(flag))
        return self

    def surface(self):
        return self.solid(False)

    def taper(self, angle):
        self._taper = angle
        if self._extent_kind is not None:
            self._apply_extent()
        return self

    def participant_bodies(self, *bodies):
        setattr(self.raw, EXTRUDE_POLICY["input_attrs"]["participant_bodies"], [unwrap(body) for body in bodies])
        return self

    def build(self):
        if self._extent_kind is None:
            raise ValueError("ExtrudeBuilder requires one_side(...), symmetric(...), or through_all(...) before build().")
        terminal = getattr(self._extrude_features, self._family["builder_terminal"])
        return wrap(terminal(self.raw))

    def _apply_extent(self):
        taper = v(self._taper) if self._taper is not None else None
        if self._extent_kind == "one_side":
            fusion = import_adsk_module("adsk.fusion")
            extent_type = getattr(fusion, EXTRUDE_POLICY["extent_types"]["distance"])
            extent = extent_type.create(v(self._distance))
            direction = _extent_direction(self._direction)
            getattr(self.raw, EXTRUDE_POLICY["input_methods"]["one_side"])(extent, direction, taper)
            return
        if self._extent_kind == "symmetric":
            getattr(self.raw, EXTRUDE_POLICY["input_methods"]["symmetric"])(
                v(self._distance),
                self._symmetric_full_length,
                taper,
            )
            return
        if self._extent_kind == "through_all":
            fusion = import_adsk_module("adsk.fusion")
            extent_type = getattr(fusion, EXTRUDE_POLICY["extent_types"]["through_all"])
            extent = extent_type.create()
            direction = _extent_direction(self._direction)
            getattr(self.raw, EXTRUDE_POLICY["input_methods"]["one_side"])(extent, direction, taper)
            return
        raise ValueError(f"Unsupported extrude extent kind: {self._extent_kind}")


def _extent_direction(direction):
    raw_direction = unwrap(direction)
    if isinstance(raw_direction, str):
        normalized = raw_direction.strip().lower().replace("-", "_")
        return getattr(dir, normalized)
    return raw_direction


__all__ = ["ExtrudeBuilder"]
