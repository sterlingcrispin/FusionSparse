import fusion_sparse as fx


def run(context):
    root = fx.new_design().root
    sketch = root.sketch("xy")
    sketch.circle((0, 0), "20 mm")
    return sketch
