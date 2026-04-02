import fusion_sparse as fx


def run(context):
    root = fx.new_design().root
    sketch = root.sketch("xy")
    sketch.rect((0, 0), (10, 5))
    return sketch
