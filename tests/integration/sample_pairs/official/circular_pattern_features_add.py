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
    circles.addByCenterRadius(adsk.core.Point3D.create(10, 0, 0), 3)
    profile = sketch.profiles.item(0)

    bodyFeature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByReal(5),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    selectedBody = bodyFeature.bodies.item(0)

    inputEntities = adsk.core.ObjectCollection.create()
    inputEntities.add(selectedBody)

    circularFeats = rootComp.features.circularPatternFeatures
    yAxis = rootComp.yConstructionAxis
    circularFeatInput = circularFeats.createInput(inputEntities, yAxis)
    circularFeatInput.quantity = adsk.core.ValueInput.createByReal(5)
    circularFeatInput.totalAngle = adsk.core.ValueInput.createByString("180 deg")
    circularFeatInput.isSymmetric = False
    circularFeat = circularFeats.add(circularFeatInput)

    print_design_signature(design)
