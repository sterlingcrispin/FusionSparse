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
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 2)
    lines = sketch.sketchCurves.sketchLines
    axisLine = lines.addByTwoPoints(adsk.core.Point3D.create(0, -5, 0), adsk.core.Point3D.create(0, 5, 0))

    profile = sketch.profiles.item(0)
    revolves = rootComp.features.revolveFeatures
    revolveInput = revolves.createInput(profile, axisLine, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    revolveInput.setAngleExtent(False, adsk.core.ValueInput.createByString("90 deg"))
    revolve = revolves.add(revolveInput)

    print_design_signature(design)
