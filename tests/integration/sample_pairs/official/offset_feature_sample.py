import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    rootComp = design.rootComponent
    sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(4, 3, 0))
    profile = sketch.profiles.item(0)

    bodyFeature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByReal(1.0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = bodyFeature.bodies.item(0)

    offsetFaces = adsk.core.ObjectCollection.create()
    offsetFaces.add(body.faces.item(0))

    offsetFeatures = rootComp.features.offsetFeatures
    offsetInput = offsetFeatures.createInput(
        offsetFaces,
        adsk.core.ValueInput.createByReal(0.25),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    offsetFeatures.add(offsetInput)

    print_design_signature(design)
