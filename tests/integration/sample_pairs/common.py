from __future__ import annotations

import json


def print_design_signature(design) -> None:
    components = list(_collection_items(design.allComponents))
    axis_records = []
    body_boxes = []
    plane_records = []
    point_records = []
    total_body_count = 0
    sketch_records = []
    for component in components:
        bodies = list(_collection_items(component.bRepBodies))
        total_body_count += len(bodies)
        for body in bodies:
            box = body.boundingBox
            edges = getattr(body, "edges", None)
            faces = getattr(body, "faces", None)
            body_boxes.append(
                {
                    "component": getattr(component, "name", ""),
                    "edge_count": getattr(edges, "count", 0),
                    "face_count": getattr(faces, "count", 0),
                    "min": _point_tuple(box.minPoint),
                    "max": _point_tuple(box.maxPoint),
                    "volume": _number_or_none(getattr(body, "volume", None)),
                }
            )
        sketches = _collection_items(getattr(component, "sketches", []))
        for sketch in sketches:
            sketch_records.append(
                {
                    "component": getattr(component, "name", ""),
                    "profile_count": getattr(getattr(sketch, "profiles", None), "count", 0),
                    "arcs": _arc_records(sketch),
                    "lines": _line_records(sketch),
                    "circles": _circle_records(sketch),
                    "points": _sketch_point_records(sketch),
                    "ellipses": _ellipse_records(sketch),
                    "splines": _spline_records(sketch),
                    "texts": _text_records(sketch),
                }
            )
        for plane in _collection_items(getattr(component, "constructionPlanes", [])):
            geometry = getattr(plane, "geometry", None)
            if geometry is not None:
                plane_records.append(
                    {
                        "component": getattr(component, "name", ""),
                        "normal": _vector_tuple(getattr(geometry, "normal", None)),
                        "origin": _point_tuple(getattr(geometry, "origin", None)),
                    }
                )
        for axis in _collection_items(getattr(component, "constructionAxes", [])):
            geometry = getattr(axis, "geometry", None)
            if geometry is not None:
                axis_records.append(
                    {
                        "component": getattr(component, "name", ""),
                        "direction": _vector_tuple(getattr(geometry, "direction", None)),
                        "origin": _point_tuple(getattr(geometry, "origin", None)),
                    }
                )
        for point in _collection_items(getattr(component, "constructionPoints", [])):
            geometry = getattr(point, "geometry", None)
            if geometry is not None:
                point_records.append(
                    {
                        "component": getattr(component, "name", ""),
                        "point": _point_tuple(geometry),
                    }
                )
    signature = {
        "axis_count": len(axis_records),
        "component_count": len(components),
        "plane_count": len(plane_records),
        "point_count": len(point_records),
        "root_occurrence_count": getattr(design.rootComponent.occurrences, "count", 0),
        "total_body_count": total_body_count,
        "sketch_count": len(sketch_records),
        "axes": sorted(axis_records, key=lambda item: (item["component"], item["origin"], item["direction"])),
        "planes": sorted(plane_records, key=lambda item: (item["component"], item["origin"], item["normal"])),
        "points": sorted(point_records, key=lambda item: (item["component"], item["point"])),
        "sketches": sorted(
            sketch_records,
            key=lambda item: (
                item["component"],
                item["profile_count"],
                len(item["arcs"]),
                len(item["lines"]),
                len(item["circles"]),
                len(item["points"]),
                len(item["ellipses"]),
                len(item["splines"]),
                len(item["texts"]),
                json.dumps(item["arcs"], sort_keys=True),
                json.dumps(item["lines"], sort_keys=True),
                json.dumps(item["circles"], sort_keys=True),
                json.dumps(item["points"], sort_keys=True),
                json.dumps(item["ellipses"], sort_keys=True),
                json.dumps(item["splines"], sort_keys=True),
                json.dumps(item["texts"], sort_keys=True),
            ),
        ),
        "body_boxes": sorted(
            body_boxes,
            key=lambda item: (item["min"], item["max"], item["component"], item["face_count"], item["edge_count"], item["volume"]),
        ),
    }
    print(json.dumps(signature, sort_keys=True))


def _collection_items(collection):
    count = getattr(collection, "count", None)
    item = getattr(collection, "item", None)
    if isinstance(count, int) and callable(item):
        return [item(index) for index in range(count)]
    try:
        return list(collection)
    except TypeError:
        return []


def _point_tuple(point):
    if point is None:
        return None
    return tuple(round(float(value), 6) for value in (point.x, point.y, point.z))


def _vector_tuple(vector):
    if vector is None:
        return None
    return tuple(round(float(value), 6) for value in (vector.x, vector.y, vector.z))


def _number_or_none(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _line_records(sketch):
    lines = getattr(getattr(sketch, "sketchCurves", None), "sketchLines", None)
    records = []
    for line in _collection_items(lines):
        start = _sketch_point_tuple(getattr(line, "startSketchPoint", None))
        end = _sketch_point_tuple(getattr(line, "endSketchPoint", None))
        if start is not None and end is not None:
            records.append({"start": start, "end": end})
    return sorted(records, key=lambda item: (item["start"], item["end"]))


def _circle_records(sketch):
    circles = getattr(getattr(sketch, "sketchCurves", None), "sketchCircles", None)
    records = []
    for circle in _collection_items(circles):
        center = _sketch_point_tuple(getattr(circle, "centerSketchPoint", None))
        radius = _number_or_none(getattr(circle, "radius", None))
        if center is not None and radius is not None:
            records.append({"center": center, "radius": radius})
    return sorted(records, key=lambda item: (item["center"], item["radius"]))


def _arc_records(sketch):
    arcs = getattr(getattr(sketch, "sketchCurves", None), "sketchArcs", None)
    records = []
    for arc in _collection_items(arcs):
        center = _sketch_point_tuple(getattr(arc, "centerSketchPoint", None))
        start = _sketch_point_tuple(getattr(arc, "startSketchPoint", None))
        end = _sketch_point_tuple(getattr(arc, "endSketchPoint", None))
        radius = _number_or_none(getattr(arc, "radius", None))
        if center is not None and start is not None and end is not None:
            records.append({"center": center, "end": end, "radius": radius, "start": start})
    return sorted(records, key=lambda item: (item["center"], item["start"], item["end"], item["radius"]))


def _sketch_point_records(sketch):
    records = []
    for point in _collection_items(getattr(sketch, "sketchPoints", [])):
        point_tuple = _sketch_point_tuple(point)
        if point_tuple is not None:
            records.append({"point": point_tuple})
    return sorted(records, key=lambda item: item["point"])


def _ellipse_records(sketch):
    ellipses = getattr(getattr(sketch, "sketchCurves", None), "sketchEllipses", None)
    records = []
    for ellipse in _collection_items(ellipses):
        center = _sketch_point_tuple(getattr(ellipse, "centerSketchPoint", None))
        major_axis = _vector_tuple(getattr(ellipse, "majorAxis", None))
        major_radius = _number_or_none(getattr(ellipse, "majorAxisRadius", None))
        minor_radius = _number_or_none(getattr(ellipse, "minorAxisRadius", None))
        if center is not None:
            records.append(
                {
                    "center": center,
                    "major_axis": major_axis,
                    "major_radius": major_radius,
                    "minor_radius": minor_radius,
                }
            )
    return sorted(
        records,
        key=lambda item: (item["center"], item["major_axis"], item["major_radius"], item["minor_radius"]),
    )


def _spline_records(sketch):
    splines = getattr(getattr(sketch, "sketchCurves", None), "sketchFittedSplines", None)
    records = []
    for spline in _collection_items(splines):
        fit_points = [
            _sketch_point_tuple(point)
            for point in _collection_items(getattr(spline, "fitPoints", []))
            if _sketch_point_tuple(point) is not None
        ]
        if fit_points:
            records.append({"fit_points": fit_points, "length": _number_or_none(getattr(spline, "length", None))})
    return sorted(records, key=lambda item: (item["fit_points"], item["length"]))


def _text_records(sketch):
    texts = getattr(sketch, "sketchTexts", None)
    records = []
    for text in _collection_items(texts):
        box = getattr(text, "boundingBox", None)
        records.append(
            {
                "text": getattr(text, "text", None),
                "font": getattr(text, "fontName", None),
                "height": _number_or_none(getattr(text, "height", None)),
                "min": _point_tuple(getattr(box, "minPoint", None)) if box is not None else None,
                "max": _point_tuple(getattr(box, "maxPoint", None)) if box is not None else None,
            }
        )
    return sorted(records, key=lambda item: (item["text"], item["font"], item["height"], item["min"], item["max"]))


def _sketch_point_tuple(point):
    geometry = getattr(point, "geometry", None)
    if geometry is None:
        return None
    try:
        return _point_tuple(geometry)
    except AttributeError:
        return None
