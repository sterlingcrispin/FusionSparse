"""Transient geometry helpers."""

from __future__ import annotations

from fusion_sparse.runtime._adsk import import_adsk_module, looks_like_type
from fusion_sparse.runtime.adapter import unwrap


def p(x, y=None, z=0):
    raw = unwrap(x)
    if y is None and looks_like_type(raw, "Point3D"):
        return raw
    if y is None:
        geometry = getattr(raw, "geometry", None)
        if looks_like_type(geometry, "Point3D"):
            return geometry
    px, py, pz = _coerce_xyz(x, y, z)
    core = import_adsk_module("adsk.core")
    return core.Point3D.create(px, py, pz)


def vec(x, y=None, z=0):
    raw = unwrap(x)
    if y is None and looks_like_type(raw, "Vector3D"):
        return raw
    vx, vy, vz = _coerce_xyz(x, y, z)
    core = import_adsk_module("adsk.core")
    return core.Vector3D.create(vx, vy, vz)


def mat_identity():
    core = import_adsk_module("adsk.core")
    matrix = core.Matrix3D.create()
    if hasattr(matrix, "setToIdentity"):
        matrix.setToIdentity()
    return matrix


def oc(*items):
    core = import_adsk_module("adsk.core")
    collection = core.ObjectCollection.create()
    for item in items:
        raw = unwrap(item)
        if raw is None:
            continue
        collection.add(raw)
    return collection


def _coerce_xyz(x, y=None, z=0):
    if y is None:
        if not isinstance(x, (tuple, list)):
            raise TypeError("Expected an Autodesk point/vector or a 2- or 3-item coordinate tuple.")
        if len(x) == 2:
            return x[0], x[1], 0
        if len(x) == 3:
            return x[0], x[1], x[2]
        raise TypeError("Coordinate tuples must have length 2 or 3.")
    return x, y, z
