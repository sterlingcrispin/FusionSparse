"""Builder workflow: sketch a circle and create a symmetric cut or join-style feature."""

from __future__ import annotations

import fusion_sparse as fx


def run(existing_body=None):
    design = fx.new_design()
    root = design.root
    sketch = root.sketch("xy")
    sketch.circle((0, 0), "10 mm")
    builder = root.extrude(sketch.profile()).symmetric("8 mm")
    if existing_body is not None:
        builder = builder.participant_bodies(existing_body)
    return builder.build()
