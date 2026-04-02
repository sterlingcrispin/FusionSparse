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
    targetProfile = sketch.profiles.item(0)

    toolSketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
    toolLines = toolSketch.sketchCurves.sketchLines
    toolLines.addTwoPointRectangle(adsk.core.Point3D.create(4, 0, 0), adsk.core.Point3D.create(12, 8, 0))
    toolProfile = toolSketch.profiles.item(0)

    extrudes = rootComp.features.extrudeFeatures
    target = extrudes.addSimple(
        targetProfile,
        adsk.core.ValueInput.createByString("5 mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    tool = extrudes.addSimple(
        toolProfile,
        adsk.core.ValueInput.createByString("5 mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )

    targetBody = target.bodies.item(0)
    toolBody = tool.bodies.item(0)

    combineFeatures = rootComp.features.combineFeatures
    tools = adsk.core.ObjectCollection.create()
    tools.add(toolBody)
    input = combineFeatures.createInput(targetBody, tools)
    input.isNewComponent = False
    input.isKeepToolBodies = False
    input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    combineFeature = combineFeatures.add(input)

    print_design_signature(design)
