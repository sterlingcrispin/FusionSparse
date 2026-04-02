import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    rootComp = design.rootComponent
    sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(adsk.core.Point3D.create(10, 0, 0), 3)
    profile = sketch.profiles.item(0)

    bodyFeature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByString("5 mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = bodyFeature.bodies.item(0)

    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)

    mirrorFeatures = rootComp.features.mirrorFeatures
    mirrorPlane = rootComp.xYConstructionPlane
    mirrorInput = mirrorFeatures.createInput(bodies, mirrorPlane)
    mirrorFeature = mirrorFeatures.add(mirrorInput)

    print_design_signature(design)
