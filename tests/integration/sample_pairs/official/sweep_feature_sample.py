import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    rootComp = design.rootComponent
    sketches = rootComp.sketches

    sketch = sketches.add(rootComp.xZConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 3)
    prof = sketch.profiles.item(0)

    pathSketch = sketches.add(rootComp.yZConstructionPlane)
    lines = pathSketch.sketchCurves.sketchLines
    line1 = lines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(0, 3, 0))
    line2 = lines.addByTwoPoints(adsk.core.Point3D.create(0, 3, 0), adsk.core.Point3D.create(2, 6, 0))
    line1.endSketchPoint.merge(line2.startSketchPoint)
    path = rootComp.features.createPath(line1)

    sweeps = rootComp.features.sweepFeatures
    sweepInput = sweeps.createInput(prof, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    sweepInput.taperAngle = adsk.core.ValueInput.createByString("5 deg")
    sweepInput.twistAngle = adsk.core.ValueInput.createByString("10 deg")
    sweeps.add(sweepInput)

    print_design_signature(design)
