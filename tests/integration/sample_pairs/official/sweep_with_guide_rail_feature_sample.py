import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    rootComp = design.rootComponent
    sketches = rootComp.sketches

    profileSketch = sketches.add(rootComp.xZConstructionPlane)
    circles = profileSketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 1)
    prof = profileSketch.profiles.item(0)

    pathSketch = sketches.add(rootComp.yZConstructionPlane)
    lines = pathSketch.sketchCurves.sketchLines
    pathLine = lines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(3, 10, 0))
    guideLine = lines.addByTwoPoints(adsk.core.Point3D.create(-2, 0, 0), adsk.core.Point3D.create(-2, 10, 0))

    path = rootComp.features.createPath(pathLine)
    guide = rootComp.features.createPath(guideLine)

    sweeps = rootComp.features.sweepFeatures
    sweepInput = sweeps.createInput(prof, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    sweepInput.guideRail = guide
    sweepInput.profileScaling = adsk.fusion.SweepProfileScalingOptions.SweepProfileScaleOption
    sweeps.add(sweepInput)

    print_design_signature(design)
