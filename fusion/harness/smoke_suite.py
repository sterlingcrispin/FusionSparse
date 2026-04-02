from __future__ import annotations

import traceback


def run_all(context=None) -> dict[str, object]:
    results = []
    failures = []
    smoke_cases = [
        _smoke_context,
        _smoke_new_design,
        _smoke_sketch_extrude,
        _smoke_builder_extrude,
        _smoke_raw_escape_hatch,
    ]
    for smoke_case in smoke_cases:
        try:
            payload = smoke_case(context)
            payload.setdefault("name", smoke_case.__name__.removeprefix("_"))
            payload.setdefault("ok", True)
            results.append(payload)
        except Exception as exc:
            failures.append(
                {
                    "name": smoke_case.__name__.removeprefix("_"),
                    "ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
    return {
        "ok": not failures,
        "results": results,
        "failures": failures,
    }


def format_summary(summary: dict[str, object]) -> str:
    lines = ["FusionSparse smoke results", ""]
    for result in summary["results"]:
        detail_parts = [f"{key}={value}" for key, value in sorted(result.items()) if key not in {"name", "ok"}]
        suffix = f": {', '.join(detail_parts)}" if detail_parts else ""
        lines.append(f"PASS {result['name']}{suffix}")
    for failure in summary["failures"]:
        lines.append(f"FAIL {failure['name']}: {failure['error']}")
    lines.extend(["", f"overall_ok={summary['ok']}"])
    return "\n".join(lines)


def _smoke_context(context=None) -> dict[str, object]:
    import fusion_sparse as fx

    current = fx.ctx(strict=False)
    design = current.design or fx.new_or_active_design()
    root = design.root
    return {
        "name": "smoke_context",
        "app": _class_label(fx.app()),
        "design": _class_label(design),
        "root": _class_label(root),
    }


def _smoke_new_design(context=None) -> dict[str, object]:
    import fusion_sparse as fx

    design = fx.new_design()
    return {
        "name": "smoke_new_design",
        "design": _class_label(design),
        "root": _class_label(design.root),
    }


def _smoke_sketch_extrude(context=None) -> dict[str, object]:
    import fusion_sparse as fx

    design = fx.new_design()
    root = design.root
    sketch = root.sketch("xy")
    sketch.circle((0, 0), "20 mm")
    feature = root.extrude(sketch.profile(), "10 mm", op="new_body")
    return {
        "name": "smoke_sketch_extrude",
        "sketch": _class_label(sketch),
        "feature": _class_label(feature),
    }


def _smoke_builder_extrude(context=None) -> dict[str, object]:
    import fusion_sparse as fx

    design = fx.new_design()
    root = design.root
    sketch = root.sketch("xy")
    sketch.circle((0, 0), "10 mm")
    feature = root.extrude(sketch.profile()).one_side("5 mm").taper("2 deg").build()
    return {
        "name": "smoke_builder_extrude",
        "feature": _class_label(feature),
    }


def _smoke_raw_escape_hatch(context=None) -> dict[str, object]:
    import fusion_sparse as fx

    root = fx.new_design().root
    raw_sketch = root.raw.sketches.add(root.raw.xYConstructionPlane)
    raw_sketch.sketchCurves.sketchCircles.addByCenterRadius(fx.p(0, 0, 0), 1.0)
    profile_count = getattr(raw_sketch.profiles, "count", None)
    return {
        "name": "smoke_raw_escape_hatch",
        "profile_count": profile_count,
        "raw_plane_attr": "xYConstructionPlane",
    }


def _class_label(value) -> str:
    for attr_name in ("class_type", "object_type"):
        candidate = getattr(value, attr_name, None)
        if isinstance(candidate, str) and candidate:
            return candidate
    raw = getattr(value, "raw", None)
    for attr_name in ("classType", "objectType"):
        getter = getattr(raw, attr_name, None)
        if callable(getter):
            try:
                candidate = getter()
            except Exception:
                continue
            if isinstance(candidate, str) and candidate:
                return candidate
    return type(value).__name__
