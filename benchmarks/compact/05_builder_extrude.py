import fusion_sparse as fx


def run(context):
    root = fx.new_design().root
    sketch = root.sketch("xy")
    sketch.circle((0, 0), "20 mm")
    return root.extrude(sketch.profile()).one_side("5 mm").taper("2 deg").build()
