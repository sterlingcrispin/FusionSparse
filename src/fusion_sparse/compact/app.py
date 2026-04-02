"""Compact top-level helpers backed by the runtime context."""

from __future__ import annotations

from fusion_sparse.runtime.context import FusionContext
from fusion_sparse.runtime.adapter import wrap
from fusion_sparse.runtime.context import app as raw_app
from fusion_sparse.runtime.context import ctx as raw_ctx
from fusion_sparse.runtime.context import new_design as raw_new_design
from fusion_sparse.runtime.context import new_or_active_design as raw_new_or_active_design
from fusion_sparse.runtime.context import ui as raw_ui


def app():
    return wrap(raw_app())


def ui():
    return wrap(raw_ui())


def ctx(strict: bool = True) -> FusionContext:
    raw_context = raw_ctx(strict=strict)
    return FusionContext(
        app=wrap(raw_context.app),
        ui=wrap(raw_context.ui),
        product=wrap(raw_context.product),
        design=wrap(raw_context.design),
        doc=wrap(raw_context.doc),
        root=wrap(raw_context.root),
    )


def new_design(visible: bool = True, options=None):
    return wrap(raw_new_design(visible=visible, options=options))


def new_or_active_design():
    return wrap(raw_new_or_active_design())


__all__ = ["app", "ctx", "new_design", "new_or_active_design", "ui"]
