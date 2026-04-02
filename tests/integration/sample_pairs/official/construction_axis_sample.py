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
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 5)
    lines = sketch.sketchCurves.sketchLines
    axisLine = lines.addByTwoPoints(adsk.core.Point3D.create(0, 8, 0), adsk.core.Point3D.create(10, 8, 0))

    profile = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setSymmetricExtent(adsk.core.ValueInput.createByReal(4), True)
    ext = extrudes.add(extInput)

    body = ext.bodies.item(0)
    circularFace = ext.sideFaces.item(0)
    planarFace = ext.endFaces.item(0)
    vertex = body.vertices.item(0)

    axes = rootComp.constructionAxes

    circularInput = axes.createInput()
    circularInput.setByCircularFace(circularFace)
    circularAxis = axes.add(circularInput)

    perpendicularInput = axes.createInput()
    perpendicularInput.setByPerpendicularAtPoint(planarFace, vertex)
    perpendicularAxis = axes.add(perpendicularInput)

    planesInput = axes.createInput()
    planesInput.setByTwoPlanes(rootComp.xYConstructionPlane, rootComp.xZConstructionPlane)
    planesAxis = axes.add(planesInput)

    pointsInput = axes.createInput()
    pointsInput.setByTwoPoints(axisLine.startSketchPoint, axisLine.endSketchPoint)
    pointsAxis = axes.add(pointsInput)

    edgeInput = axes.createInput()
    edgeInput.setByEdge(axisLine)
    edgeAxis = axes.add(edgeInput)

    normalInput = axes.createInput()
    normalInput.setByNormalToFaceAtPoint(planarFace, vertex)
    normalAxis = axes.add(normalInput)

    print_design_signature(design)
