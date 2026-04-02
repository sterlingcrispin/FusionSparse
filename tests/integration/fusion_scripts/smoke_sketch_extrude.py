from __future__ import annotations

from tests.integration.fusion_scripts._bootstrap import class_label, load_fusion_sparse


def run(context=None) -> dict[str, object]:
    fx, _ = load_fusion_sparse(__file__)
    design = fx.new_design()
    root = design.root
    sketch = root.sketch("xy")
    sketch.circle((0, 0), "20 mm")
    feature = root.extrude(sketch.profile(), "10 mm", op="new_body")
    return {
        "name": "smoke_sketch_extrude",
        "sketch": class_label(sketch),
        "feature": class_label(feature),
    }
