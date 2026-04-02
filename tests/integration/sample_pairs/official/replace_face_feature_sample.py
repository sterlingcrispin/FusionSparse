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
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 3)
    profile = sketch.profiles.item(0)

    extrudeFeature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByReal(2.5),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    endFace = extrudeFeature.endFaces.item(0)

    planes = rootComp.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByOffset(endFace, adsk.core.ValueInput.createByString("1 cm"))
    offsetPlane = planes.add(planeInput)

    sourceFaces = adsk.core.ObjectCollection.create()
    sourceFaces.add(endFace)

    replaceFaceFeatures = rootComp.features.replaceFaceFeatures
    replaceInput = replaceFaceFeatures.createInput(sourceFaces, False, offsetPlane)
    replaceFaceFeatures.add(replaceInput)

    print_design_signature(design)
