from __future__ import annotations

from tests.integration.fusion_scripts._bootstrap import load_fusion_sparse


def run(context=None) -> dict[str, object]:
    fx, _ = load_fusion_sparse(__file__)
    root = fx.new_design().root
    raw_sketch = root.raw.sketches.add(root.raw.xYConstructionPlane)
    raw_sketch.sketchCurves.sketchCircles.addByCenterRadius(fx.p(0, 0, 0), 1.0)
    profile_count = getattr(raw_sketch.profiles, "count", None)
    return {
        "name": "smoke_raw_escape_hatch",
        "profile_count": profile_count,
        "raw_plane_attr": "xYConstructionPlane",
    }
