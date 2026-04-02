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
    circle = circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 5)
    lines = sketch.sketchCurves.sketchLines
    axisLine = lines.addByTwoPoints(adsk.core.Point3D.create(5, 5, 0), adsk.core.Point3D.create(5, 10, 0))
    edgeLine = lines.addByTwoPoints(adsk.core.Point3D.create(5, 5, 0), adsk.core.Point3D.create(10, 5, 0))

    profile = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setSymmetricExtent(adsk.core.ValueInput.createByReal(5), True)
    ext = extrudes.add(extInput)

    body = ext.bodies.item(0)
    circularFace = ext.sideFaces.item(0)

    planes = rootComp.constructionPlanes

    offsetInput = planes.createInput()
    offsetInput.setByOffset(profile, adsk.core.ValueInput.createByString("10 mm"))
    offsetPlane = planes.add(offsetInput)

    angleInput = planes.createInput()
    angleInput.setByAngle(axisLine, adsk.core.ValueInput.createByString("45 deg"), rootComp.xZConstructionPlane)
    anglePlane = planes.add(angleInput)

    betweenInput = planes.createInput()
    betweenInput.setByTwoPlanes(rootComp.xYConstructionPlane, rootComp.xZConstructionPlane)
    betweenPlane = planes.add(betweenInput)

    edgesInput = planes.createInput()
    edgesInput.setByTwoEdges(axisLine, edgeLine)
    edgePlane = planes.add(edgesInput)

    print_design_signature(design)
