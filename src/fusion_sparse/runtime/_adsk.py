"""Internal helpers for working with lazy Autodesk imports."""

from __future__ import annotations

import importlib
import inspect


_ADSK_HINT = (
    "Autodesk Fusion's embedded Python environment is required for this operation "
    "because the `adsk` modules are not available."
)


def import_adsk_module(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        missing_root = (exc.name or "").split(".", 1)[0]
        if missing_root != "adsk":
            raise
        raise ModuleNotFoundError(_ADSK_HINT) from exc


def read_member(value: object, name: str):
    attr = getattr(value, name)
    if callable(attr):
        try:
            return attr()
        except TypeError:
            return attr
    return attr


def object_type_name(value: object) -> str | None:
    candidate = _member_value(value, "objectType")
    return str(candidate) if candidate is not None else None


def class_type_name(value: object) -> str | None:
    class_attr = getattr(type(value), "classType", None)
    if class_attr is not None:
        try:
            resolved = class_attr()
        except TypeError:
            resolved = class_attr
        if isinstance(resolved, str):
            return resolved

    instance_attr = getattr(value, "classType", None)
    if instance_attr is not None:
        try:
            resolved = instance_attr()
        except TypeError:
            resolved = instance_attr
        if isinstance(resolved, str):
            return resolved

    return None


def is_valid_flag(value: object) -> bool:
    candidate = _member_value(value, "isValid")
    if isinstance(candidate, bool):
        return candidate
    return True


def is_adsk_object(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, bytes, bytearray, int, float, complex, bool, list, tuple, dict, set, frozenset)):
        return False
    if inspect.isclass(value) or inspect.ismodule(value) or inspect.isroutine(value):
        return False

    module_name = getattr(type(value), "__module__", "")
    if module_name.startswith("adsk"):
        return True

    return any(
        hasattr(value, attr) or hasattr(type(value), attr)
        for attr in ("objectType", "classType", "isValid")
    )


def looks_like_type(value: object, type_name: str) -> bool:
    object_type = object_type_name(value) or ""
    class_type = class_type_name(value) or ""
    return object_type.endswith(type_name) or class_type.endswith(type_name)


def _member_value(value: object, name: str):
    try:
        return read_member(value, name)
    except AttributeError:
        return None

