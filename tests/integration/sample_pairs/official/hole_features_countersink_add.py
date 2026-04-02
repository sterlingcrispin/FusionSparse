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
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 4)
    profile = sketch.profiles.item(0)

    feature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByString("15 mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )

    face = feature.endFaces.item(0)
    circleEdge = face.edges.item(0)

    holes = rootComp.features.holeFeatures
    holeInput = holes.createCountersinkInput(
        adsk.core.ValueInput.createByString("20 mm"),
        adsk.core.ValueInput.createByString("35 mm"),
        adsk.core.ValueInput.createByString("120 deg"),
    )
    holeInput.setDistanceExtent(adsk.core.ValueInput.createByReal(5))
    holeInput.setPositionAtCenter(face, circleEdge)
    hole = holes.add(holeInput)

    print_design_signature(design)
