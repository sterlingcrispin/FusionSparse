import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    rootComp = design.rootComponent
    sketches = rootComp.sketches

    profileSketch = sketches.add(rootComp.xYConstructionPlane)
    circles = profileSketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 3)
    prof = profileSketch.profiles.item(0)

    pathSketch = sketches.add(rootComp.xZConstructionPlane)
    lines = pathSketch.sketchCurves.sketchLines
    line1 = lines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(0, 10, 0))
    line2 = lines.addByTwoPoints(adsk.core.Point3D.create(3, 0, 0), adsk.core.Point3D.create(6, 10, 0))

    path = rootComp.features.createPath(line1)
    guide = rootComp.features.createPath(line2)

    sweeps = rootComp.features.sweepFeatures
    sweepInput = sweeps.createInput(prof, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    sweepInput.guideRail = guide
    sweepInput.isDirectionFlipped = False
    sweepInput.profileScaling = adsk.fusion.SweepProfileScalingOptions.SweepProfileScaleOption
    sweeps.add(sweepInput)

    print_design_signature(design)
