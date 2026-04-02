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
    center = adsk.core.Point3D.create(0, 0, 0)
    circles.addByCenterRadius(center, 3)
    circles.addByCenterRadius(center, 10)

    profile1 = sketch.profiles.item(0)
    profile2 = sketch.profiles.item(1)
    area1 = profile1.areaProperties().area
    area2 = profile2.areaProperties().area
    outerProfile = profile1 if area1 > area2 else profile2

    extrudes = rootComp.features.extrudeFeatures
    extrudeFeature = extrudes.addSimple(
        outerProfile,
        adsk.core.ValueInput.createByString("1 cm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )

    endFace = extrudeFeature.endFaces.item(0)
    innerLoop = endFace.loops.item(1)
    boundaryEdge = innerLoop.edges.item(0)

    patches = rootComp.features.patchFeatures
    patchInput = patches.createInput(boundaryEdge, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    patches.add(patchInput)

    print_design_signature(design)
