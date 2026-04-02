from __future__ import annotations

from tests.integration.fusion_scripts._bootstrap import class_label, load_fusion_sparse


def run(context=None) -> dict[str, object]:
    fx, _ = load_fusion_sparse(__file__)
    current = fx.ctx(strict=False)
    design = current.design or fx.new_or_active_design()
    root = design.root
    return {
        "name": "smoke_context",
        "app": class_label(fx.app()),
        "design": class_label(design),
        "root": class_label(root),
    }
