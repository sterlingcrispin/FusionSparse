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
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 3)
    profile = sketch.profiles.item(0)

    bodyFeature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByReal(5),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = bodyFeature.bodies.item(0)

    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    quantityOne = adsk.core.ValueInput.createByReal(4)
    distanceOne = adsk.core.ValueInput.createByReal(5)
    quantityTwo = adsk.core.ValueInput.createByReal(3)
    distanceTwo = adsk.core.ValueInput.createByReal(4)

    rectangularPatterns = rootComp.features.rectangularPatternFeatures
    input = rectangularPatterns.createInput(
        bodies,
        rootComp.xConstructionAxis,
        quantityOne,
        distanceOne,
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )
    input.setDirectionTwo(rootComp.yConstructionAxis, quantityTwo, distanceTwo)
    rectangularPattern = rectangularPatterns.add(input)

    print_design_signature(design)
