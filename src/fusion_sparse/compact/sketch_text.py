"""Thin helpers for sketch text creation."""

from __future__ import annotations

from fusion_sparse.compact._helpers import point_like, sketch_length_cm
from fusion_sparse.generated.compact_policy import TEXT_POLICY
from fusion_sparse.runtime._adsk import import_adsk_module
from fusion_sparse.runtime.adapter import unwrap, wrap


def add_multiline_text(
    sketch,
    text,
    corner,
    diagonal,
    height,
    *,
    h_align="left",
    v_align="top",
    spacing=0,
    font=None,
    hflip=False,
    vflip=False,
):
    texts, input_obj = _text_input(sketch, text, height)
    _set_text_attrs(input_obj, font=font, hflip=hflip, vflip=vflip)
    horizontal = _horizontal_alignment(h_align)
    vertical = _vertical_alignment(v_align)
    method = getattr(input_obj, TEXT_POLICY["input_methods"]["multiline"])
    method(
        point_like(corner),
        point_like(diagonal),
        horizontal,
        vertical,
        sketch_length_cm(spacing),
    )
    return wrap(getattr(texts, TEXT_POLICY["builder_terminal"])(input_obj))


def add_path_text(
    sketch,
    text,
    path,
    height,
    *,
    above=False,
    align="center",
    spacing=0,
    fit=False,
    font=None,
    hflip=False,
    vflip=False,
):
    texts, input_obj = _text_input(sketch, text, height)
    _set_text_attrs(input_obj, font=font, hflip=hflip, vflip=vflip)
    method_key = "fit_path" if fit else "along_path"
    method = getattr(input_obj, TEXT_POLICY["input_methods"][method_key])
    raw_path = unwrap(path)
    if fit:
        method(raw_path, bool(above))
    else:
        method(raw_path, bool(above), _horizontal_alignment(align), sketch_length_cm(spacing))
    return wrap(getattr(texts, TEXT_POLICY["builder_terminal"])(input_obj))


def _text_input(sketch, text, height):
    sketch_raw = unwrap(sketch)
    texts = getattr(sketch_raw, TEXT_POLICY["collection_attr"])
    create_input = getattr(texts, TEXT_POLICY["builder_input"])
    return texts, create_input(str(text), sketch_length_cm(height))


def _set_text_attrs(input_obj, *, font, hflip, vflip):
    attrs = TEXT_POLICY["input_attrs"]
    setattr(input_obj, attrs["horizontal_flip"], bool(hflip))
    setattr(input_obj, attrs["vertical_flip"], bool(vflip))
    if font:
        setattr(input_obj, attrs["font_name"], str(font))


def _horizontal_alignment(value):
    return _enum_member("HorizontalAlignments", TEXT_POLICY["horizontal_alignments"], value)


def _vertical_alignment(value):
    return _enum_member("VerticalAlignments", TEXT_POLICY["vertical_alignments"], value)


def _enum_member(enum_name, aliases, value):
    raw = unwrap(value)
    if not isinstance(raw, str):
        return raw
    normalized = raw.strip().lower().replace("-", "_")
    member_name = aliases.get(normalized)
    if member_name is None:
        raise ValueError(f"Unsupported sketch text alignment: {value}")
    core = import_adsk_module("adsk.core")
    enum_type = getattr(core, enum_name)
    return getattr(enum_type, member_name)


__all__ = ["add_multiline_text", "add_path_text"]
