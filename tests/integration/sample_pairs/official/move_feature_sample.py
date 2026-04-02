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

    inputEntities = adsk.core.ObjectCollection.create()
    inputEntities.add(body)

    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(2.0, 1.0, 0)

    moveFeatures = rootComp.features.moveFeatures
    moveInput = moveFeatures.createInput2(inputEntities)
    moveInput.defineAsFreeMove(transform)
    moveFeatures.add(moveInput)

    print_design_signature(design)
