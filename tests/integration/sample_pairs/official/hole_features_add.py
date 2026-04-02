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
    lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(6, 6, 0))
    profile = sketch.profiles.item(0)

    feature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByString("15 mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )

    body = feature.bodies.item(0)
    face = body.faces.item(0)
    edge1 = body.edges.item(0)
    edge2 = body.edges.item(1)
    facePoint = face.pointOnFace

    holes = rootComp.features.holeFeatures
    holeInput = holes.createSimpleInput(adsk.core.ValueInput.createByString("20 mm"))
    holeInput.setDistanceExtent(adsk.core.ValueInput.createByReal(5))
    holeInput.setPositionByPlaneAndOffsets(
        face,
        facePoint,
        edge1,
        adsk.core.ValueInput.createByReal(4),
        edge2,
        adsk.core.ValueInput.createByReal(6),
    )
    hole = holes.add(holeInput)

    print_design_signature(design)
