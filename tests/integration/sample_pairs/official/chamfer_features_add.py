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
    lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(8, 8, 0))
    profile = sketch.profiles.item(0)

    feature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByString("10 mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )

    body = feature.bodies.item(0)
    edge = body.edges.item(0)
    edgeCollection = adsk.core.ObjectCollection.create()
    edgeCollection.add(edge)

    chamferFeatures = rootComp.features.chamferFeatures
    chamferInput = chamferFeatures.createInput2()
    chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edgeCollection, adsk.core.ValueInput.createByReal(1), True)
    chamferFeature = chamferFeatures.add(chamferInput)

    print_design_signature(design)
