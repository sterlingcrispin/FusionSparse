import adsk.core
import adsk.fusion

from tests.integration.sample_pairs.common import print_design_signature


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    rootComp = design.rootComponent
    sketches = rootComp.sketches
    planes = rootComp.constructionPlanes

    sketch0 = sketches.add(rootComp.xZConstructionPlane)
    circles0 = sketch0.sketchCurves.sketchCircles
    circles0.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 5)
    profile0 = sketch0.profiles.item(0)

    planeInput1 = planes.createInput()
    offset = adsk.core.ValueInput.createByString("10 cm")
    planeInput1.setByOffset(rootComp.xZConstructionPlane, offset)
    plane1 = planes.add(planeInput1)
    sketch1 = sketches.add(plane1)
    circles1 = sketch1.sketchCurves.sketchCircles
    circles1.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 2)
    profile1 = sketch1.profiles.item(0)

    planeInput2 = planes.createInput()
    planeInput2.setByOffset(plane1, offset)
    plane2 = planes.add(planeInput2)
    sketch2 = sketches.add(plane2)
    circles2 = sketch2.sketchCurves.sketchCircles
    circles2.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 10)
    profile2 = sketch2.profiles.item(0)

    lofts = rootComp.features.loftFeatures
    loftInput = lofts.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    loftInput.loftSections.add(profile0)
    loftInput.loftSections.add(profile1)
    loftInput.loftSections.add(profile2)
    loftInput.isSolid = False
    loftInput.isClosed = False
    loftInput.isTangentEdgesMerged = True
    loftInput.startLoftEdgeAlignment = adsk.fusion.LoftEdgeAlignments.FreeEdgesLoftEdgeAlignment
    loftInput.endLoftEdgeAlignment = adsk.fusion.LoftEdgeAlignments.FreeEdgesLoftEdgeAlignment
    lofts.add(loftInput)

    print_design_signature(design)
