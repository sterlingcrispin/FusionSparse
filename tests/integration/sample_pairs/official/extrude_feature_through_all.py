import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    root_comp = design.rootComponent

    base_sketch = root_comp.sketches.add(root_comp.xYConstructionPlane)
    base_lines = base_sketch.sketchCurves.sketchLines
    base_lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(10, 10, 0))
    base_profile = base_sketch.profiles.item(0)
    base_distance = adsk.core.ValueInput.createByString("10 mm")
    extrude_features = root_comp.features.extrudeFeatures
    extrude_features.addSimple(base_profile, base_distance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

    cut_sketch = root_comp.sketches.add(root_comp.xYConstructionPlane)
    cut_lines = cut_sketch.sketchCurves.sketchLines
    cut_lines.addTwoPointRectangle(adsk.core.Point3D.create(3, 3, 0), adsk.core.Point3D.create(7, 7, 0))
    cut_profile = cut_sketch.profiles.item(0)

    extrude_input = extrude_features.createInput(cut_profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
    extent = adsk.fusion.ThroughAllExtentDefinition.create()
    extrude_input.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    extrude_features.add(extrude_input)

    print_design_signature(design)
