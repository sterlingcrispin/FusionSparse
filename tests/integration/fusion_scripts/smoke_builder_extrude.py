from __future__ import annotations

from tests.integration.fusion_scripts._bootstrap import class_label, load_fusion_sparse


def run(context=None) -> dict[str, object]:
    fx, _ = load_fusion_sparse(__file__)
    design = fx.new_design()
    root = design.root
    sketch = root.sketch("xy")
    sketch.circle((0, 0), "10 mm")
    feature = root.extrude(sketch.profile()).one_side("5 mm").taper("2 deg").build()
    return {
        "name": "smoke_builder_extrude",
        "feature": class_label(feature),
    }
