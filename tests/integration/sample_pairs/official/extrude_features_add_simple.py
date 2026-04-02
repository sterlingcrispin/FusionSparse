import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    root_comp = design.rootComponent
    sketch = root_comp.sketches.add(root_comp.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(3, 2, 0))

    profile = sketch.profiles.item(0)
    distance = adsk.core.ValueInput.createByString("100 mm")
    operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    extrude_features = root_comp.features.extrudeFeatures
    extrude_features.addSimple(profile, distance, operation)

    print_design_signature(design)
