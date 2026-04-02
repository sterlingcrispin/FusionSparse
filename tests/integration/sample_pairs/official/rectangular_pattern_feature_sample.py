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
        adsk.core.ValueInput.createByReal(5),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = bodyFeature.bodies.item(0)

    inputEntities = adsk.core.ObjectCollection.create()
    inputEntities.add(body)

    xAxis = rootComp.xConstructionAxis
    yAxis = rootComp.yConstructionAxis
    quantityOne = adsk.core.ValueInput.createByString("3")
    distanceOne = adsk.core.ValueInput.createByString("8 cm")
    quantityTwo = adsk.core.ValueInput.createByString("3")
    distanceTwo = adsk.core.ValueInput.createByString("8 cm")

    rectangularPatterns = rootComp.features.rectangularPatternFeatures
    rectangularPatternInput = rectangularPatterns.createInput(
        inputEntities,
        xAxis,
        quantityOne,
        distanceOne,
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )
    rectangularPatternInput.setDirectionTwo(yAxis, quantityTwo, distanceTwo)
    rectangularFeature = rectangularPatterns.add(rectangularPatternInput)

    print_design_signature(design)
