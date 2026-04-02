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
    operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    extrudes = root.features.extrudeFeatures
    extrude_input = extrudes.createInput(profile, operation)
    distance = adsk.core.ValueInput.createByString("5 mm")
    taper = adsk.core.ValueInput.createByString("2 deg")
    extent = adsk.fusion.DistanceExtentDefinition.create(distance)
    extrude_input.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection, taper)
    return extrudes.add(extrude_input)
