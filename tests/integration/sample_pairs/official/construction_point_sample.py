import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    rootComp = design.rootComponent
    sketch = rootComp.sketches.add(rootComp.xZConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(5, 5, 0))
    circles = sketch.sketchCurves.sketchCircles
    circle = circles.addByCenterRadius(adsk.core.Point3D.create(8, 8, 0), 2)

    profile = sketch.profiles.item(0)
    extrudeFeatures = rootComp.features.extrudeFeatures
    box = extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByString("20 mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )

    body = box.bodies.item(0)
    edgeOne = body.edges.item(0)
    edgeTwo = body.edges.item(1)
    faceOne = body.faces.item(0)
    vertex = body.vertices.item(0)

    points = rootComp.constructionPoints

    edgeInput = points.createInput()
    edgeInput.setByTwoEdges(edgeOne, edgeTwo)
    edgePoint = points.add(edgeInput)

    planeInput = points.createInput()
    planeInput.setByThreePlanes(rootComp.xYConstructionPlane, rootComp.xZConstructionPlane, rootComp.yZConstructionPlane)
    planePoint = points.add(planeInput)

    edgePlaneInput = points.createInput()
    edgePlaneInput.setByEdgePlane(rootComp.zConstructionAxis, rootComp.xYConstructionPlane)
    edgePlanePoint = points.add(edgePlaneInput)

    centerInput = points.createInput()
    centerInput.setByCenter(circle)
    centerPoint = points.add(centerInput)

    atInput = points.createInput()
    atInput.setByPoint(vertex)
    atPoint = points.add(atInput)

    print_design_signature(design)
