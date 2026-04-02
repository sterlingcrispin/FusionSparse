"""Minimal compact workflow: sketch a rectangle and create a new component."""

from __future__ import annotations

import fusion_sparse as fx


def run():
    design = fx.new_design()
    root = design.root
    sketch = root.sketch("xz")
    sketch.rect((0, 0), (10, 5))
    return root.extrude(sketch.profile(), "25 mm", op="new_component")
