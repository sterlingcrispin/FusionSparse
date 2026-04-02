from __future__ import annotations

from tests.integration.fusion_scripts._bootstrap import class_label, load_fusion_sparse


def run(context=None) -> dict[str, object]:
    fx, _ = load_fusion_sparse(__file__)
    design = fx.new_design()
    return {
        "name": "smoke_new_design",
        "design": class_label(design),
        "root": class_label(design.root),
    }
