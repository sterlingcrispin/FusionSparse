import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    rootComp = design.rootComponent
    sketch = rootComp.sketches.add(rootComp.xZConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 3)
    profile = sketch.profiles.item(0)

    bodyFeature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByReal(5.0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = bodyFeature.bodies.item(0)

    splitBodyFeatures = rootComp.features.splitBodyFeatures
    splitInput = splitBodyFeatures.createInput(body, rootComp.yZConstructionPlane, True)
    splitBodyFeatures.add(splitInput)

    print_design_signature(design)
