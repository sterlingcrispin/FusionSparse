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
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 1.5)
    profile = sketch.profiles.item(0)

    extrudeFeature = rootComp.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByReal(4.0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    threadFace = extrudeFeature.sideFaces.item(0)

    threadFaces = adsk.core.ObjectCollection.create()
    threadFaces.add(threadFace)

    threadFeatures = rootComp.features.threadFeatures
    threadDataQuery = threadFeatures.threadDataQuery
    threadType = threadDataQuery.defaultMetricThreadType
    recommended = threadDataQuery.recommendThreadData(3.0, False, threadType)
    threadDesignation = recommended[1]
    threadClass = recommended[2]
    threadInfo = adsk.fusion.ThreadInfo.create(False, False, threadType, threadDesignation, threadClass, True)

    threadInput = threadFeatures.createInput(threadFaces, threadInfo)
    threadInput.isFullLength = False
    threadInput.threadLength = adsk.core.ValueInput.createByReal(2.5)
    threadFeatures.add(threadInput)

    print_design_signature(design)
