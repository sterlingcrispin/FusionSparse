import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    return adsk.fusion.Design.cast(app.activeProduct)
