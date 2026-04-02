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
    profile = sketch.profiles.item(0)
    distance = adsk.core.ValueInput.createByString("10 mm")
    operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    return root.features.extrudeFeatures.addSimple(profile, distance, operation)
