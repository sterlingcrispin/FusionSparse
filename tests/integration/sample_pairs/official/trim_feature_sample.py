import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    rootComp = design.rootComponent
    sketches = rootComp.sketches
    extrudes = rootComp.features.extrudeFeatures

    sketch = sketches.add(rootComp.xZConstructionPlane)
    sketchCircles = sketch.sketchCurves.sketchCircles
    sketchCircle = sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 3.0)
    openProfile = rootComp.createOpenProfile(sketchCircle)

    extrudeInput = extrudes.createInput(openProfile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrudeInput.isSolid = False
    extrudeInput.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(3.0)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection,
    )
    extrude = extrudes.add(extrudeInput)
    body = extrude.bodies.item(0)

    sketch2 = sketches.add(rootComp.xYConstructionPlane)
    sketchLines = sketch2.sketchCurves.sketchLines
    sketchLine = sketchLines.addByTwoPoints(adsk.core.Point3D.create(-5, 0, 0), adsk.core.Point3D.create(5, 0, 0))
    openProfile2 = rootComp.createOpenProfile(sketchLine)

    extrudeInput2 = extrudes.createInput(openProfile2, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrudeInput2.isSolid = False
    extrudeInput2.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(5.0)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection,
    )
    extrudes.add(extrudeInput2)

    trims = rootComp.features.trimFeatures
    trimInput = trims.createInput(body)
    cells = trimInput.bRepCells
    cell = cells.item(0)
    cell.isSelected = True
    trims.add(trimInput)

    print_design_signature(design)
