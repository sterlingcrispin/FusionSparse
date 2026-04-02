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
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 10)
    profile = sketch.profiles.item(0)

    extrudeFeature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByReal(2.5),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )

    entities = adsk.core.ObjectCollection.create()
    entities.add(extrudeFeature.endFaces.item(0))

    shells = rootComp.features.shellFeatures
    shellInput = shells.createInput(entities, False)
    shellInput.insideThickness = adsk.core.ValueInput.createByReal(0.5)
    shellInput.shellType = adsk.fusion.ShellTypes.SharpOffsetShellType
    shells.add(shellInput)

    print_design_signature(design)
