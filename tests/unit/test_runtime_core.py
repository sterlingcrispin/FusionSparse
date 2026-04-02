from __future__ import annotations

from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


class FakeAdskBase:
    CLASS_TYPE = "adsk::core::Base"

    @staticmethod
    def classType():
        return FakeAdskBase.CLASS_TYPE

    def objectType(self):
        return self.CLASS_TYPE

    @property
    def isValid(self):
        return True


class FakeValueInput(FakeAdskBase):
    CLASS_TYPE = "adsk::core::ValueInput"

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    @staticmethod
    def createByReal(value):
        return FakeValueInput("real", value)

    @staticmethod
    def createByString(value):
        return FakeValueInput("string", value)

    @staticmethod
    def createByBoolean(value):
        return FakeValueInput("boolean", value)

    @staticmethod
    def createByObject(value):
        return FakeValueInput("object", value)


class FakePoint3D(FakeAdskBase):
    CLASS_TYPE = "adsk::core::Point3D"

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def create(x, y, z):
        return FakePoint3D(x, y, z)


class FakeVector3D(FakeAdskBase):
    CLASS_TYPE = "adsk::core::Vector3D"

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def create(x, y, z):
        return FakeVector3D(x, y, z)


class FakeMatrix3D(FakeAdskBase):
    CLASS_TYPE = "adsk::core::Matrix3D"

    def __init__(self):
        self.identity = False

    @staticmethod
    def create():
        return FakeMatrix3D()

    def setToIdentity(self):
        self.identity = True


class FakeObjectCollection(FakeAdskBase):
    CLASS_TYPE = "adsk::core::ObjectCollection"

    def __init__(self):
        self.items = []

    @staticmethod
    def create():
        return FakeObjectCollection()

    def add(self, item):
        self.items.append(item)


class FakeDocumentTypes:
    FusionDesignDocumentType = 0


class FakeFeatureOperations:
    JoinFeatureOperation = 0
    CutFeatureOperation = 1
    IntersectFeatureOperation = 2
    NewBodyFeatureOperation = 3
    NewComponentFeatureOperation = 4


class FakeExtentDirections:
    PositiveExtentDirection = 0
    NegativeExtentDirection = 1
    SymmetricExtentDirection = 2


class FakeDesign(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::Design"

    def __init__(self):
        self.rootComponent = SimpleNamespace(name="root")

    @staticmethod
    def cast(product):
        return product if isinstance(product, FakeDesign) else None


class FakeDocument(FakeAdskBase):
    CLASS_TYPE = "adsk::core::Document"

    def __init__(self, design):
        self.design = design


class FakeDocuments(FakeAdskBase):
    CLASS_TYPE = "adsk::core::Documents"

    def __init__(self, application):
        self.application = application
        self.calls = []

    def add(self, document_type, visible=True, options=None):
        self.calls.append((document_type, visible, options))
        design = FakeDesign()
        self.application.activeProduct = design
        self.application.activeDocument = FakeDocument(design)
        return self.application.activeDocument


class FakeApplication(FakeAdskBase):
    CLASS_TYPE = "adsk::core::Application"
    CURRENT = None

    def __init__(self):
        self.userInterface = SimpleNamespace(name="ui")
        self.activeProduct = FakeDesign()
        self.activeDocument = FakeDocument(self.activeProduct)
        self.documents = FakeDocuments(self)

    @staticmethod
    def get():
        return FakeApplication.CURRENT


class FakeEntity(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::FakeEntity"

    def __init__(self, name="entity"):
        self.name = name
        self.child = None
        self.received = None

    def echo(self, value):
        self.received = value
        return value

    def pair(self, left, right):
        return (left, right)


@contextmanager
def fake_adsk_environment():
    previous = {name: sys.modules.get(name) for name in ("adsk", "adsk.core", "adsk.fusion", "adsk.cam")}

    adsk_pkg = ModuleType("adsk")
    core = ModuleType("adsk.core")
    fusion = ModuleType("adsk.fusion")
    cam = ModuleType("adsk.cam")

    application = FakeApplication()
    FakeApplication.CURRENT = application

    core.Application = FakeApplication
    core.DocumentTypes = FakeDocumentTypes
    core.ValueInput = FakeValueInput
    core.Point3D = FakePoint3D
    core.Vector3D = FakeVector3D
    core.Matrix3D = FakeMatrix3D
    core.ObjectCollection = FakeObjectCollection

    fusion.Design = FakeDesign
    fusion.FeatureOperations = FakeFeatureOperations
    fusion.ExtentDirections = FakeExtentDirections

    adsk_pkg.core = core
    adsk_pkg.fusion = fusion
    adsk_pkg.cam = cam

    sys.modules["adsk"] = adsk_pkg
    sys.modules["adsk.core"] = core
    sys.modules["adsk.fusion"] = fusion
    sys.modules["adsk.cam"] = cam

    try:
        yield SimpleNamespace(app=application, core=core, fusion=fusion, cam=cam)
    finally:
        FakeApplication.CURRENT = None
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class RuntimeCoreTests(unittest.TestCase):
    def test_package_imports_without_adsk(self) -> None:
        fusion_sparse = import_module("fusion_sparse")
        self.assertTrue(hasattr(fusion_sparse, "app"))
        self.assertTrue(hasattr(fusion_sparse, "new_design"))
        self.assertTrue(hasattr(fusion_sparse, "ctx"))

    def test_wrap_unwrap_and_ref_passthrough(self) -> None:
        from fusion_sparse.runtime.adapter import unwrap, wrap
        from fusion_sparse.runtime.refs import Ref

        left = FakeEntity("left")
        right = FakeEntity("right")
        left.child = right

        wrapped = wrap(left)
        self.assertIsInstance(wrapped, Ref)
        self.assertEqual(wrapped.object_type, "adsk::fusion::FakeEntity")
        self.assertIsInstance(wrapped.child, Ref)

        echoed = wrapped.echo(wrapped.child)
        self.assertIs(left.received, right)
        self.assertIsInstance(echoed, Ref)

        pair = wrapped.pair(wrapped, right)
        self.assertEqual(tuple(type(item).__name__ for item in pair), ("Ref", "Ref"))
        self.assertIs(unwrap({"value": wrapped})["value"], left)

    def test_context_values_geom_and_enums(self) -> None:
        from fusion_sparse.runtime.context import active_design, app, ctx, new_design, new_or_active_design
        from fusion_sparse.runtime.enums import dir, op
        from fusion_sparse.runtime.geom import mat_identity, oc, p, vec
        from fusion_sparse.runtime.values import u, v

        with fake_adsk_environment() as env:
            self.assertIs(app(), env.app)
            self.assertIs(active_design(), env.app.activeProduct)
            self.assertIs(new_or_active_design(), env.app.activeProduct)

            design = new_design()
            self.assertIsInstance(design, FakeDesign)
            self.assertEqual(env.app.documents.calls[-1], (0, True, None))

            context = ctx()
            self.assertIs(context.design, design)
            self.assertEqual(context.root.name, "root")

            real = v(5)
            expr = v(u.mm(5))
            boolean = v(True)
            raw_object = FakeEntity("body")
            object_value = v(raw_object)
            from fusion_sparse.runtime.adapter import wrap

            wrapped_value = v(wrap(FakeValueInput.createByReal(2.5)))

            self.assertEqual((real.kind, real.value), ("real", 5.0))
            self.assertEqual((expr.kind, expr.value), ("string", "5 mm"))
            self.assertEqual((boolean.kind, boolean.value), ("boolean", True))
            self.assertEqual((object_value.kind, object_value.value), ("object", raw_object))
            self.assertEqual((wrapped_value.kind, wrapped_value.value), ("real", 2.5))

            point = p((1, 2))
            vector = vec(1, 2, 3)
            matrix = mat_identity()
            collection = oc(raw_object, wrap(FakeEntity("other")))

            self.assertEqual((point.x, point.y, point.z), (1, 2, 0))
            self.assertEqual((vector.x, vector.y, vector.z), (1, 2, 3))
            self.assertTrue(matrix.identity)
            self.assertEqual(len(collection.items), 2)

            self.assertEqual(op.new_body, 3)
            self.assertEqual(dir.symmetric, 2)


if __name__ == "__main__":
    unittest.main()
