import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    sketch = root.sketches.add(root.xYConstructionPlane)
    center = adsk.core.Point3D.create(0, 0, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, 2.0)
    return sketch
