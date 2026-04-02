"""Helpers that bridge raw Autodesk objects and FusionSparse refs."""

from __future__ import annotations

from functools import wraps

from fusion_sparse.runtime.errors import GenerationMismatchError
from fusion_sparse.runtime._adsk import class_type_name, is_adsk_object, object_type_name
from fusion_sparse.runtime.refs import Ref


def unwrap(value):
    """Convert FusionSparse refs back to raw Autodesk objects."""
    if isinstance(value, Ref):
        return value.raw
    if isinstance(value, tuple):
        return tuple(unwrap(item) for item in value)
    if isinstance(value, list):
        return [unwrap(item) for item in value]
    if isinstance(value, dict):
        return {unwrap(key): unwrap(item) for key, item in value.items()}
    if isinstance(value, set):
        return {unwrap(item) for item in value}
    return value


def wrap(value):
    """Wrap raw Autodesk values where useful while leaving primitives untouched."""
    if isinstance(value, Ref):
        return value
    if isinstance(value, tuple):
        return tuple(wrap(item) for item in value)
    if isinstance(value, list):
        return [wrap(item) for item in value]
    if isinstance(value, dict):
        return {wrap(key): wrap(item) for key, item in value.items()}
    if isinstance(value, set):
        return {wrap(item) for item in value}
    if is_adsk_object(value):
        wrapper_cls = _resolve_wrapper_class(value)
        return wrapper_cls(value)
    return value


def wrap_callable(raw_callable):
    """Create a proxy that unwraps args and wraps Autodesk results."""

    @wraps(raw_callable)
    def proxy(*args, **kwargs):
        unwrapped_args = tuple(unwrap(arg) for arg in args)
        unwrapped_kwargs = {key: unwrap(value) for key, value in kwargs.items()}
        return wrap(raw_callable(*unwrapped_args, **unwrapped_kwargs))

    return proxy


def _resolve_wrapper_class(value) -> type[Ref]:
    try:
        from fusion_sparse.generated.wrapper_dispatch import resolve_wrapper_class
    except ImportError as exc:
        raise GenerationMismatchError("fusion_sparse.generated.wrapper_dispatch is required at runtime.") from exc

    if not callable(resolve_wrapper_class):
        keys = tuple(filter(None, (object_type_name(value), class_type_name(value), type(value).__name__)))
        raise GenerationMismatchError(f"Generated wrapper resolver is invalid for runtime dispatch: {keys!r}")
    return resolve_wrapper_class(value)
