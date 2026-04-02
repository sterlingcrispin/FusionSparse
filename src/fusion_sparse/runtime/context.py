"""Helpers for resolving Fusion application and design context lazily."""

from __future__ import annotations

from dataclasses import dataclass

from fusion_sparse.runtime._adsk import import_adsk_module, looks_like_type
from fusion_sparse.runtime.errors import InvalidContextError


@dataclass(frozen=True)
class FusionContext:
    app: object
    ui: object | None
    product: object | None
    design: object | None
    doc: object | None
    root: object | None


def app():
    core = import_adsk_module("adsk.core")
    application_cls = getattr(core, "Application", None)
    if application_cls is None or not hasattr(application_cls, "get"):
        raise InvalidContextError("adsk.core.Application.get is not available.")
    application = application_cls.get()
    if application is None:
        raise InvalidContextError("Fusion did not return an active Application instance.")
    return application


def ui():
    return getattr(app(), "userInterface", None)


def active_product():
    return getattr(app(), "activeProduct", None)


def active_design(strict: bool = True):
    product = active_product()
    if product is None:
        if strict:
            raise InvalidContextError("No active product is available.")
        return None

    fusion = import_adsk_module("adsk.fusion")
    design_cls = getattr(fusion, "Design", None)
    design = None
    if design_cls is not None and hasattr(design_cls, "cast"):
        design = design_cls.cast(product)
    elif looks_like_type(product, "Design"):
        design = product

    if design is None and strict:
        raise InvalidContextError("The active product is not a Fusion design.")
    return design


def ctx(strict: bool = True) -> FusionContext:
    application = app()
    product = getattr(application, "activeProduct", None)
    design = active_design(strict=strict)
    document = getattr(application, "activeDocument", None)
    root = getattr(design, "rootComponent", None) if design is not None else None
    return FusionContext(
        app=application,
        ui=getattr(application, "userInterface", None),
        product=product,
        design=design,
        doc=document,
        root=root,
    )


def new_design(visible: bool = True, options=None):
    application = app()
    documents = getattr(application, "documents", None)
    if documents is None or not hasattr(documents, "add"):
        raise InvalidContextError("Application.documents.add is not available.")

    core = import_adsk_module("adsk.core")
    document_types = getattr(core, "DocumentTypes", None)
    if document_types is None or not hasattr(document_types, "FusionDesignDocumentType"):
        raise InvalidContextError("adsk.core.DocumentTypes.FusionDesignDocumentType is not available.")

    doc_type = document_types.FusionDesignDocumentType
    try:
        if options is None and visible is True:
            documents.add(doc_type)
        elif options is None:
            documents.add(doc_type, visible)
        else:
            documents.add(doc_type, visible, options)
    except Exception as exc:
        raise InvalidContextError(
            "Failed to create a new design. Documents.add is not supported during command-related events "
            "or other open command transactions."
        ) from exc

    design = active_design(strict=False)
    if design is None:
        raise InvalidContextError("A new document was created but no active design could be resolved afterward.")
    return design


def new_or_active_design():
    existing = active_design(strict=False)
    if existing is not None:
        return existing
    return new_design()
