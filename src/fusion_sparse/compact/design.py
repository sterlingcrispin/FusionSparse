"""Compact design wrappers."""

from __future__ import annotations

from fusion_sparse.compact._surface import resolve_generated_property
from fusion_sparse.runtime.refs import Ref


class DesignRef(Ref):
    """Thin ergonomic view over a Fusion design."""

    @property
    def root(self):
        return resolve_generated_property(self.raw, "DesignRef.root")


__all__ = ["DesignRef"]
