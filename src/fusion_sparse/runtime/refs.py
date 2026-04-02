"""Base wrapper for raw Autodesk objects."""

from __future__ import annotations

from fusion_sparse.runtime._adsk import class_type_name, is_valid_flag, object_type_name


class Ref:
    """Thin wrapper that preserves direct raw Autodesk access."""

    __slots__ = ("raw",)

    def __init__(self, raw: object):
        self.raw = raw

    @property
    def object_type(self) -> str | None:
        return object_type_name(self.raw)

    @property
    def class_type(self) -> str | None:
        return class_type_name(self.raw)

    @property
    def is_valid(self) -> bool:
        return is_valid_flag(self.raw)

    def __getattr__(self, name: str):
        attr = getattr(self.raw, name)
        from fusion_sparse.runtime.adapter import wrap, wrap_callable

        if callable(attr):
            return wrap_callable(attr)
        return wrap(attr)

    def __repr__(self) -> str:
        type_name = self.class_type or self.object_type or type(self.raw).__name__
        return f"Ref({type_name})"

    def __eq__(self, other: object) -> bool:
        other_raw = other.raw if isinstance(other, Ref) else other
        return self.raw == other_raw

    def __hash__(self) -> int:
        try:
            return hash(self.raw)
        except TypeError:
            return hash(id(self.raw))
