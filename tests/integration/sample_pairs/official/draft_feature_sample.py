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
    lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(6, 4, 0))
    profile = sketch.profiles.item(0)

    box = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByReal(4),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = box.bodies.item(0)
    neutralFace = body.faces.item(0)
    draftFaces = [body.faces.item(1)]

    drafts = rootComp.features.draftFeatures
    draftInput = drafts.createInput(draftFaces, neutralFace, True)
    draftInput.isDirectionFlipped = False
    draftInput.setSingleAngle(True, adsk.core.ValueInput.createByString("10 deg"))
    drafts.add(draftInput)

    print_design_signature(design)
