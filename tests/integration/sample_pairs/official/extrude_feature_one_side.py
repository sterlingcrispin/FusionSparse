import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    root_comp = design.rootComponent
    sketch = root_comp.sketches.add(root_comp.xZConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 5)

    profile = sketch.profiles.item(0)
    extrudes = root_comp.features.extrudeFeatures
    extrude_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString("100 mm"))
    extrude_input.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    extrudes.add(extrude_input)

    print_design_signature(design)
