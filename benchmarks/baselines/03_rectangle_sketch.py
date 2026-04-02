import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    sketch = root.sketches.add(root.xYConstructionPlane)
    p1 = adsk.core.Point3D.create(0, 0, 0)
    p2 = adsk.core.Point3D.create(10, 5, 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)
    return sketch
