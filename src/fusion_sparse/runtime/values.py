"""Unit-safe value creation for Fusion ValueInput objects."""

from __future__ import annotations

from dataclasses import dataclass
import numbers

from fusion_sparse.runtime._adsk import import_adsk_module, is_adsk_object, looks_like_type
from fusion_sparse.runtime.adapter import unwrap
from fusion_sparse.runtime.errors import UnitCoercionError
from fusion_sparse.runtime.refs import Ref


@dataclass(frozen=True)
class Expression:
    text: str

    def __str__(self) -> str:
        return self.text


class Units:
    def mm(self, value) -> Expression:
        return Expression(f"{_format_number(value)} mm")

    def cm(self, value) -> Expression:
        return Expression(f"{_format_number(value)} cm")

    def m(self, value) -> Expression:
        return Expression(f"{_format_number(value)} m")

    def inch(self, value) -> Expression:
        return Expression(f"{_format_number(value)} in")

    def in_(self, value) -> Expression:
        return self.inch(value)

    def deg(self, value) -> Expression:
        return Expression(f"{_format_number(value)} deg")

    def rad(self, value) -> Expression:
        return Expression(f"{_format_number(value)} rad")

    def expr(self, text: str) -> Expression:
        return Expression(str(text))


u = Units()


def v(value):
    """Coerce numbers, expressions, refs, and raw Autodesk values into ValueInput."""
    core = import_adsk_module("adsk.core")
    value_input_cls = getattr(core, "ValueInput", None)
    if value_input_cls is None:
        raise UnitCoercionError("adsk.core.ValueInput is not available.")

    raw = unwrap(value)
    if raw is None:
        raise UnitCoercionError("Cannot coerce None into a ValueInput.")
    if looks_like_type(raw, "ValueInput"):
        return raw
    if isinstance(value, Expression):
        return value_input_cls.createByString(value.text)
    if isinstance(raw, str):
        return value_input_cls.createByString(raw)
    if isinstance(raw, bool):
        return value_input_cls.createByBoolean(raw)
    if isinstance(raw, numbers.Real):
        return value_input_cls.createByReal(float(raw))
    if isinstance(value, Ref) and looks_like_type(raw, "ValueInput"):
        return raw
    if is_adsk_object(raw):
        return value_input_cls.createByObject(raw)
    raise UnitCoercionError(f"Unsupported value input type: {type(value).__name__}")


def _format_number(value) -> str:
    if not isinstance(value, numbers.Real) or isinstance(value, bool):
        raise UnitCoercionError("Explicit unit helpers require a numeric value.")
    if float(value).is_integer():
        return str(int(value))
    return f"{float(value):g}"
