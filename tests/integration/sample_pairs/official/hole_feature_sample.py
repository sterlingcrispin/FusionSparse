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

    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(5)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection,
    )
    ext = extrudes.add(extInput)

    endFace = ext.endFaces.item(0)
    planes = rootComp.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByOffset(endFace, adsk.core.ValueInput.createByString("2 cm"))
    offsetPlane = planes.add(planeInput)

    offsetSketch = rootComp.sketches.add(offsetPlane)
    offsetSketchPoints = offsetSketch.sketchPoints
    sPt0 = offsetSketchPoints.add(adsk.core.Point3D.create(1, 0, 0))
    sPt1 = offsetSketchPoints.add(adsk.core.Point3D.create(0, 1, 0))
    sPt2 = offsetSketchPoints.add(adsk.core.Point3D.create(-1, 0, 0))
    sPt3 = offsetSketchPoints.add(adsk.core.Point3D.create(0, -1, 0))

    pointCollection = adsk.core.ObjectCollection.create()
    pointCollection.add(sPt0)
    pointCollection.add(sPt1)
    pointCollection.add(sPt2)
    pointCollection.add(sPt3)

    holes = rootComp.features.holeFeatures
    holeInput = holes.createSimpleInput(adsk.core.ValueInput.createByString("2 mm"))
    holeInput.setPositionBySketchPoints(pointCollection)
    holeInput.setDistanceExtent(adsk.core.ValueInput.createByReal(5))
    hole = holes.add(holeInput)

    print_design_signature(design)
