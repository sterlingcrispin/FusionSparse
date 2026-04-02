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


class FakeObjectCollection(FakeAdskBase):
    CLASS_TYPE = "adsk::core::ObjectCollection"

    def __init__(self):
        self.items = []

    @staticmethod
    def create():
        return FakeObjectCollection()

    def add(self, value):
        self.items.append(value)
        return True

    @property
    def count(self):
        return len(self.items)

    def item(self, index):
        return self.items[index]


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


class FakePatternDistanceType:
    SpacingPatternDistanceType = 0
    ExtentPatternDistanceType = 1


class FakeDistanceExtentDefinition(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::DistanceExtentDefinition"

    def __init__(self, distance):
        self.distance = distance

    @staticmethod
    def create(distance):
        return FakeDistanceExtentDefinition(distance)


class FakeThroughAllExtentDefinition(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::ThroughAllExtentDefinition"

    @staticmethod
    def create():
        return FakeThroughAllExtentDefinition()


class FakeProfile(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::Profile"

    def __init__(self, label):
        self.label = label


class FakeBody(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::BRepBody"

    def __init__(self, name):
        self.name = name


class FakeProfileCollection(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::Profiles"

    def __init__(self):
        self.items = []

    @property
    def count(self):
        return len(self.items)

    def item(self, index):
        return self.items[index]


class FakeSketchPoint(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchPoint"

    def __init__(self, geometry):
        self.geometry = geometry


class FakeSketchLine(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchLine"

    def __init__(self, start, end):
        self.startSketchPoint = FakeSketchPoint(start)
        self.endSketchPoint = FakeSketchPoint(end)


class FakeSketchArc(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchArc"

    def __init__(self, center, start, end, radius=None):
        self.centerSketchPoint = FakeSketchPoint(center)
        self.startSketchPoint = FakeSketchPoint(start)
        self.endSketchPoint = FakeSketchPoint(end)
        self.radius = radius


class FakeSketchEllipse(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchEllipse"

    def __init__(self, center, major_axis_point, through_point):
        self.centerSketchPoint = FakeSketchPoint(center)
        self.majorAxis = SimpleNamespace(
            x=major_axis_point.x - center.x,
            y=major_axis_point.y - center.y,
            z=major_axis_point.z - center.z,
        )
        self.majorAxisRadius = abs(major_axis_point.x - center.x) or abs(major_axis_point.y - center.y) or 0
        self.minorAxisRadius = abs(through_point.y - center.y) or abs(through_point.x - center.x) or 0


class FakeSketchFittedSpline(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchFittedSpline"

    def __init__(self, fit_points):
        self.fitPoints = FakeObjectCollection.create()
        for point in fit_points:
            self.fitPoints.add(FakeSketchPoint(point))
        self.length = len(fit_points)


class FakeSketchTextInput(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchTextInput"

    def __init__(self, text, height):
        self.text = text
        self.height = height
        self.fontName = None
        self.isHorizontalFlip = False
        self.isVerticalFlip = False
        self.definition = None

    def setAsMultiLine(self, corner_point, diagonal_point, horizontal_alignment, vertical_alignment, character_spacing):
        self.definition = {
            "kind": "multiline",
            "corner": corner_point,
            "diagonal": diagonal_point,
            "horizontal_alignment": horizontal_alignment,
            "vertical_alignment": vertical_alignment,
            "character_spacing": character_spacing,
        }
        return True

    def setAsAlongPath(self, path, is_above_path, horizontal_alignment, character_spacing):
        self.definition = {
            "kind": "along_path",
            "path": path,
            "is_above_path": is_above_path,
            "horizontal_alignment": horizontal_alignment,
            "character_spacing": character_spacing,
        }
        return True

    def setAsFitOnPath(self, path, is_above_path):
        self.definition = {
            "kind": "fit_path",
            "path": path,
            "is_above_path": is_above_path,
        }
        return True


class FakeSketchText(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchText"

    def __init__(self, input_obj):
        self.text = input_obj.text
        self.height = input_obj.height
        self.fontName = input_obj.fontName
        definition = input_obj.definition or {}
        if definition.get("kind") == "multiline":
            min_point = definition["corner"]
            max_point = definition["diagonal"]
        else:
            min_point = FakePoint3D.create(0, 0, 0)
            max_point = FakePoint3D.create(len(self.text), self.height, 0)
        self.boundingBox = SimpleNamespace(minPoint=min_point, maxPoint=max_point)


class FakeSketchCircle(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchCircle"

    def __init__(self, center, radius):
        self.centerSketchPoint = FakeSketchPoint(center)
        self.radius = radius


class FakeSketchPoints(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchPoints"

    def __init__(self):
        self.calls = []
        self.items = []

    @property
    def count(self):
        return len(self.items)

    def item(self, index):
        return self.items[index]

    def add(self, point):
        self.calls.append(point)
        sketch_point = FakeSketchPoint(point)
        self.items.append(sketch_point)
        return sketch_point


class FakeSketchLines(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchLines"

    def __init__(self, sketch):
        self.sketch = sketch
        self.line_calls = []
        self.rect_calls = []

    def addByTwoPoints(self, start_point, end_point):
        self.line_calls.append((start_point, end_point))
        return FakeSketchLine(start_point, end_point)

    def addTwoPointRectangle(self, point_one, point_two):
        self.rect_calls.append((point_one, point_two))
        if not self.sketch.profiles.items:
            self.sketch.profiles.items.append(FakeProfile("rect"))
        return [
            FakeSketchLine(point_one, point_two),
            FakeSketchLine(point_one, point_two),
            FakeSketchLine(point_one, point_two),
            FakeSketchLine(point_one, point_two),
        ]


class FakeSketchCircles(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchCircles"

    def __init__(self, sketch):
        self.calls = []
        self.sketch = sketch

    def addByCenterRadius(self, center_point, radius):
        self.calls.append({"center": center_point, "radius": radius})
        if not self.sketch.profiles.items:
            self.sketch.profiles.items.append(FakeProfile("circle"))
        return FakeSketchCircle(center_point, radius)

    def addByTwoPoints(self, point_one, point_two):
        center = FakePoint3D.create((point_one.x + point_two.x) / 2, (point_one.y + point_two.y) / 2, 0)
        radius = abs(point_two.x - point_one.x) / 2 or abs(point_two.y - point_one.y) / 2
        self.calls.append({"center": center, "radius": radius})
        return FakeSketchCircle(center, radius)

    def addByThreePoints(self, point_one, point_two, point_three):
        self.calls.append({"center": point_one, "radius": 0})
        return FakeSketchCircle(point_one, 0)


class FakeSketchArcs(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchArcs"

    def __init__(self):
        self.calls = []

    def addByCenterStartSweep(self, center_point, start_point, sweep):
        arc = FakeSketchArc(center_point, start_point, start_point, sweep)
        self.calls.append({"kind": "center_start_sweep", "arc": arc, "sweep": sweep})
        return arc

    def addByThreePoints(self, point_one, point_two, point_three):
        arc = FakeSketchArc(point_one, point_one, point_three)
        self.calls.append({"kind": "three_points", "arc": arc, "mid": point_two})
        return arc


class FakeSketchEllipses(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchEllipses"

    def __init__(self):
        self.calls = []

    def add(self, center_point, major_axis_point, through_point):
        ellipse = FakeSketchEllipse(center_point, major_axis_point, through_point)
        self.calls.append((center_point, major_axis_point, through_point))
        return ellipse


class FakeSketchFittedSplines(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchFittedSplines"

    def __init__(self):
        self.calls = []

    def add(self, points):
        fit_points = [points.item(index) for index in range(points.count)]
        spline = FakeSketchFittedSpline(fit_points)
        self.calls.append(fit_points)
        return spline


class FakeSketchTexts(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchTexts"

    def __init__(self):
        self.inputs = []
        self.calls = []

    def createInput2(self, text, height):
        input_obj = FakeSketchTextInput(text, height)
        self.inputs.append(input_obj)
        return input_obj

    def add(self, input_obj):
        text = FakeSketchText(input_obj)
        self.calls.append(input_obj)
        return text


class FakeSketchCurves(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::SketchCurves"

    def __init__(self, sketch):
        self.sketchArcs = FakeSketchArcs()
        self.sketchEllipses = FakeSketchEllipses()
        self.sketchFittedSplines = FakeSketchFittedSplines()
        self.sketchLines = FakeSketchLines(sketch)
        self.sketchCircles = FakeSketchCircles(sketch)


class FakeSketch(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::Sketch"

    def __init__(self, plane):
        self.plane = plane
        self.profiles = FakeProfileCollection()
        self.sketchPoints = FakeSketchPoints()
        self.sketchTexts = FakeSketchTexts()
        self.sketchCurves = FakeSketchCurves(self)


class FakeHorizontalAlignments:
    LeftHorizontalAlignment = 0
    CenterHorizontalAlignment = 1
    RightHorizontalAlignment = 2


class FakeVerticalAlignments:
    TopVerticalAlignment = 0
    MiddleVerticalAlignment = 1
    BottomVerticalAlignment = 2


class FakeSketches(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::Sketches"

    def __init__(self):
        self.calls = []

    def add(self, plane):
        self.calls.append(plane)
        return FakeSketch(plane)


class FakeExtrudeFeatureInput(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::ExtrudeFeatureInput"

    def __init__(self, profile, operation):
        self.profile = profile
        self.operation = operation
        self.isSolid = True
        self.one_side_calls = []
        self.symmetric_calls = []
        self.participantBodies = []

    def setOneSideExtent(self, extent, direction, taper_angle=None):
        self.one_side_calls.append((extent, direction, taper_angle))
        return True

    def setSymmetricExtent(self, distance, is_full_length, taper_angle=None):
        self.symmetric_calls.append((distance, is_full_length, taper_angle))
        return True


class FakeExtrudeFeature(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::ExtrudeFeature"

    def __init__(self, mode):
        self.mode = mode


class FakeExtrudeFeatures(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::ExtrudeFeatures"

    def __init__(self):
        self.simple_calls = []
        self.builder_inputs = []
        self.builder_calls = []

    def addSimple(self, profile, distance, operation):
        self.simple_calls.append({"profile": profile, "distance": distance, "operation": operation})
        return FakeExtrudeFeature("simple")

    def createInput(self, profile, operation):
        input_obj = FakeExtrudeFeatureInput(profile, operation)
        self.builder_inputs.append(input_obj)
        return input_obj

    def add(self, input_obj):
        self.builder_calls.append(input_obj)
        return FakeExtrudeFeature("builder")


class FakeCombineFeatureInput(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::CombineFeatureInput"

    def __init__(self, target_body, tool_bodies):
        self.targetBody = target_body
        self.toolBodies = tool_bodies
        self.operation = None
        self.isKeepToolBodies = False
        self.isNewComponent = False


class FakeCombineFeatures(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::CombineFeatures"

    def __init__(self):
        self.inputs = []
        self.calls = []

    def createInput(self, target_body, tool_bodies):
        input_obj = FakeCombineFeatureInput(target_body, tool_bodies)
        self.inputs.append(input_obj)
        return input_obj

    def add(self, input_obj):
        self.calls.append(input_obj)
        return FakeFeatureResult("combine", input_obj)


class FakeMirrorFeatureInput(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::MirrorFeatureInput"

    def __init__(self, input_entities, mirror_plane):
        self.inputEntities = input_entities
        self.mirrorPlane = mirror_plane


class FakeMirrorFeatures(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::MirrorFeatures"

    def __init__(self):
        self.inputs = []
        self.calls = []

    def createInput(self, input_entities, mirror_plane):
        input_obj = FakeMirrorFeatureInput(input_entities, mirror_plane)
        self.inputs.append(input_obj)
        return input_obj

    def add(self, input_obj):
        self.calls.append(input_obj)
        return FakeFeatureResult("mirror", input_obj)


class FakeCircularPatternFeatureInput(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::CircularPatternFeatureInput"

    def __init__(self, input_entities, axis):
        self.inputEntities = input_entities
        self.axis = axis
        self.quantity = None
        self.totalAngle = None
        self.isSymmetric = False


class FakeCircularPatternFeatures(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::CircularPatternFeatures"

    def __init__(self):
        self.inputs = []
        self.calls = []

    def createInput(self, input_entities, axis):
        input_obj = FakeCircularPatternFeatureInput(input_entities, axis)
        self.inputs.append(input_obj)
        return input_obj

    def add(self, input_obj):
        self.calls.append(input_obj)
        return FakeFeatureResult("circular_pattern", input_obj)


class FakeRectangularPatternFeatureInput(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::RectangularPatternFeatureInput"

    def __init__(self, input_entities, direction_one, quantity_one, distance_one, pattern_distance_type):
        self.inputEntities = input_entities
        self.directionOneEntity = direction_one
        self.quantityOne = quantity_one
        self.distanceOne = distance_one
        self.patternDistanceType = pattern_distance_type
        self.isSymmetricInDirectionOne = False
        self.isSymmetricInDirectionTwo = False
        self.directionTwoArgs = None

    def setDirectionTwo(self, direction_two, quantity_two, distance_two):
        self.directionTwoArgs = (direction_two, quantity_two, distance_two)
        return True


class FakeRectangularPatternFeatures(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::RectangularPatternFeatures"

    def __init__(self):
        self.inputs = []
        self.calls = []

    def createInput(self, input_entities, direction_one, quantity_one, distance_one, pattern_distance_type):
        input_obj = FakeRectangularPatternFeatureInput(
            input_entities,
            direction_one,
            quantity_one,
            distance_one,
            pattern_distance_type,
        )
        self.inputs.append(input_obj)
        return input_obj

    def add(self, input_obj):
        self.calls.append(input_obj)
        return FakeFeatureResult("rectangular_pattern", input_obj)


class FakeFeatureResult(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::Feature"

    def __init__(self, kind, input_obj):
        self.kind = kind
        self.input = input_obj


class FakeFeatures(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::Features"

    def __init__(self):
        self.extrudeFeatures = FakeExtrudeFeatures()
        self.combineFeatures = FakeCombineFeatures()
        self.mirrorFeatures = FakeMirrorFeatures()
        self.circularPatternFeatures = FakeCircularPatternFeatures()
        self.rectangularPatternFeatures = FakeRectangularPatternFeatures()


class FakeComponent(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::Component"

    def __init__(self):
        self.xYConstructionPlane = "xy-plane"
        self.xZConstructionPlane = "xz-plane"
        self.yZConstructionPlane = "yz-plane"
        self.sketches = FakeSketches()
        self.features = FakeFeatures()


class FakeDesign(FakeAdskBase):
    CLASS_TYPE = "adsk::fusion::Design"

    def __init__(self):
        self.designType = "parametric"
        self.rootComponent = FakeComponent()

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
    core.HorizontalAlignments = FakeHorizontalAlignments
    core.ObjectCollection = FakeObjectCollection
    core.Point3D = FakePoint3D
    core.ValueInput = FakeValueInput
    core.VerticalAlignments = FakeVerticalAlignments

    fusion.Design = FakeDesign
    fusion.DistanceExtentDefinition = FakeDistanceExtentDefinition
    fusion.ThroughAllExtentDefinition = FakeThroughAllExtentDefinition
    fusion.ExtentDirections = FakeExtentDirections
    fusion.FeatureOperations = FakeFeatureOperations
    fusion.PatternDistanceType = FakePatternDistanceType

    adsk_pkg.core = core
    adsk_pkg.fusion = fusion
    adsk_pkg.cam = cam

    sys.modules["adsk"] = adsk_pkg
    sys.modules["adsk.core"] = core
    sys.modules["adsk.fusion"] = fusion
    sys.modules["adsk.cam"] = cam

    try:
        yield application
    finally:
        FakeApplication.CURRENT = None
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class CompactWorkflowTests(unittest.TestCase):
    def test_generated_dispatch_and_compact_workflow(self) -> None:
        fusion_sparse = import_module("fusion_sparse")
        from fusion_sparse.compact.component import ComponentRef
        from fusion_sparse.compact.design import DesignRef
        from fusion_sparse.compact.extrude import ExtrudeBuilder
        from fusion_sparse.compact.sketch import SketchRef
        from fusion_sparse.runtime.refs import Ref

        with fake_adsk_environment() as application:
            design = fusion_sparse.new_design()
            self.assertIsInstance(design, DesignRef)
            self.assertEqual(application.documents.calls[-1], (0, True, None))

            root = design.root
            self.assertIsInstance(root, ComponentRef)

            sketch = root.sketch("xy")
            self.assertIsInstance(sketch, SketchRef)
            self.assertEqual(root.raw.sketches.calls[-1], "xy-plane")

            circle = sketch.circle((0, 0), "20 mm")
            self.assertIsInstance(circle, Ref)
            self.assertEqual(sketch.raw.sketchCurves.sketchCircles.calls[-1]["radius"], 2.0)

            profile = sketch.profile()
            self.assertIsInstance(profile, Ref)

            simple_feature = root.extrude(profile, "10 mm", op="new_body")
            self.assertIsInstance(simple_feature, Ref)
            simple_call = root.raw.features.extrudeFeatures.simple_calls[-1]
            self.assertEqual(simple_call["operation"], 3)
            self.assertEqual((simple_call["distance"].kind, simple_call["distance"].value), ("string", "10 mm"))

            builder = root.extrude(profile)
            self.assertIsInstance(builder, ExtrudeBuilder)
            built_feature = builder.one_side("5 mm", direction="negative").taper("2 deg").surface().build()
            self.assertIsInstance(built_feature, Ref)

            built_input = root.raw.features.extrudeFeatures.builder_calls[-1]
            self.assertFalse(built_input.isSolid)
            one_side_call = built_input.one_side_calls[-1]
            self.assertEqual(one_side_call[1], 1)
            self.assertEqual((one_side_call[2].kind, one_side_call[2].value), ("string", "2 deg"))

    def test_rectangle_and_new_component_workflow(self) -> None:
        fusion_sparse = import_module("fusion_sparse")
        from fusion_sparse.runtime.refs import Ref

        with fake_adsk_environment():
            root = fusion_sparse.new_design().root
            sketch = root.sketch("xz")

            line = sketch.line((0, 0), (5, 0))
            self.assertIsInstance(line, Ref)
            self.assertEqual(sketch.raw.sketchCurves.sketchLines.line_calls[-1][1].x, 5)

            rectangle = sketch.rect((0, 0), (10, 5))
            self.assertEqual(len(rectangle), 4)
            self.assertTrue(all(isinstance(item, Ref) for item in rectangle))

            profile = sketch.profile()
            feature = root.extrude(profile, "25 mm", op="new_component")
            self.assertIsInstance(feature, Ref)

            simple_call = root.raw.features.extrudeFeatures.simple_calls[-1]
            self.assertEqual(simple_call["operation"], 4)
            self.assertEqual((simple_call["distance"].kind, simple_call["distance"].value), ("string", "25 mm"))

    def test_extended_sketch_operations(self) -> None:
        fusion_sparse = import_module("fusion_sparse")
        from fusion_sparse.runtime.refs import Ref

        with fake_adsk_environment():
            root = fusion_sparse.new_design().root
            sketch = root.sketch("xy")

            point = sketch.point((5, 4))
            self.assertIsInstance(point, Ref)
            self.assertEqual(sketch.raw.sketchPoints.calls[-1].x, 5)

            ellipse = sketch.ellipse((0, 0), (10, 0), (5, 4))
            self.assertIsInstance(ellipse, Ref)
            ellipse_call = sketch.raw.sketchCurves.sketchEllipses.calls[-1]
            self.assertEqual((ellipse_call[1].x, ellipse_call[2].y), (10, 4))

            spline = sketch.spline((0, 0), (5, 1), (6, 4, 3), (7, 6, 6))
            self.assertIsInstance(spline, Ref)
            self.assertEqual(len(sketch.raw.sketchCurves.sketchFittedSplines.calls[-1]), 4)

            arc = sketch.arc3p((-10, 0), (-5, 3), (0, 0))
            multiline = sketch.text("Autodesk", (0, 0), (10, 5), 0.5, font="Arial")
            path_text = sketch.text_path("Along", arc, 0.5, align="center")
            fit_text = sketch.text_fit("Fit", arc, 0.5, above=True)

            self.assertIsInstance(multiline, Ref)
            self.assertIsInstance(path_text, Ref)
            self.assertIsInstance(fit_text, Ref)

            text_input = sketch.raw.sketchTexts.calls[0]
            self.assertEqual(text_input.definition["kind"], "multiline")
            self.assertEqual(text_input.fontName, "Arial")
            self.assertEqual(text_input.definition["horizontal_alignment"], 0)

            path_input = sketch.raw.sketchTexts.calls[1]
            self.assertEqual(path_input.definition["kind"], "along_path")
            self.assertFalse(path_input.definition["is_above_path"])
            self.assertEqual(path_input.definition["horizontal_alignment"], 1)

            fit_input = sketch.raw.sketchTexts.calls[2]
            self.assertEqual(fit_input.definition["kind"], "fit_path")
            self.assertTrue(fit_input.definition["is_above_path"])

    def test_symmetric_builder_with_participant_bodies(self) -> None:
        fusion_sparse = import_module("fusion_sparse")
        from fusion_sparse.runtime.refs import Ref

        with fake_adsk_environment():
            root = fusion_sparse.new_design().root
            sketch = root.sketch("xy")
            sketch.circle((0, 0), "10 mm")
            profile = sketch.profile()
            body = Ref(FakeBody("existing-body"))

            feature = root.extrude(profile).symmetric("8 mm").participant_bodies(body).build()
            self.assertIsInstance(feature, Ref)

            built_input = root.raw.features.extrudeFeatures.builder_calls[-1]
            symmetric_call = built_input.symmetric_calls[-1]
            self.assertEqual((symmetric_call[0].kind, symmetric_call[0].value), ("string", "8 mm"))
            self.assertTrue(symmetric_call[1])
            self.assertEqual(len(built_input.participantBodies), 1)
            self.assertEqual(built_input.participantBodies[0].name, "existing-body")

    def test_symmetric_builder_half_length(self) -> None:
        fusion_sparse = import_module("fusion_sparse")
        from fusion_sparse.runtime.refs import Ref

        with fake_adsk_environment():
            root = fusion_sparse.new_design().root
            sketch = root.sketch("xy")
            sketch.circle((0, 0), "10 mm")
            profile = sketch.profile()

            feature = root.extrude(profile).symmetric("8 mm", full_length=False).build()
            self.assertIsInstance(feature, Ref)

            built_input = root.raw.features.extrudeFeatures.builder_calls[-1]
            symmetric_call = built_input.symmetric_calls[-1]
            self.assertEqual((symmetric_call[0].kind, symmetric_call[0].value), ("string", "8 mm"))
            self.assertFalse(symmetric_call[1])

    def test_through_all_builder(self) -> None:
        fusion_sparse = import_module("fusion_sparse")
        from fusion_sparse.runtime.refs import Ref

        with fake_adsk_environment():
            root = fusion_sparse.new_design().root
            sketch = root.sketch("xy")
            sketch.rect((0, 0), (4, 4))
            profile = sketch.profile()

            feature = root.extrude(profile, op="cut").through_all("negative").build()
            self.assertIsInstance(feature, Ref)

            built_input = root.raw.features.extrudeFeatures.builder_calls[-1]
            one_side_call = built_input.one_side_calls[-1]
            self.assertIsInstance(one_side_call[0], FakeThroughAllExtentDefinition)
            self.assertEqual(one_side_call[1], 1)

    def test_wave_two_feature_helpers(self) -> None:
        fusion_sparse = import_module("fusion_sparse")
        from fusion_sparse.runtime.refs import Ref

        with fake_adsk_environment():
            root = fusion_sparse.new_design().root
            target = Ref(FakeBody("target"))
            tool_a = Ref(FakeBody("tool-a"))
            tool_b = Ref(FakeBody("tool-b"))
            axis = Ref(SimpleNamespace(name="z-axis"))
            edge = Ref(SimpleNamespace(name="edge-1"))
            direction = Ref(SimpleNamespace(name="edge-direction"))

            combine_feature = root.combine(target, [tool_a, tool_b], op="cut", keep_tools=True)
            self.assertIsInstance(combine_feature, Ref)
            combine_input = root.raw.features.combineFeatures.calls[-1]
            self.assertEqual(combine_input.operation, 1)
            self.assertTrue(combine_input.isKeepToolBodies)
            self.assertEqual(combine_input.toolBodies.count, 2)

            mirror_feature = root.mirror([target, tool_a], "xy")
            self.assertIsInstance(mirror_feature, Ref)
            mirror_input = root.raw.features.mirrorFeatures.calls[-1]
            self.assertEqual(mirror_input.mirrorPlane, "xy-plane")
            self.assertEqual(mirror_input.inputEntities.count, 2)

            circular_feature = root.circular_pattern([target], axis, 3, "180 deg", symmetric=True)
            self.assertIsInstance(circular_feature, Ref)
            circular_input = root.raw.features.circularPatternFeatures.calls[-1]
            self.assertEqual((circular_input.quantity.kind, circular_input.quantity.value), ("real", 3))
            self.assertEqual((circular_input.totalAngle.kind, circular_input.totalAngle.value), ("string", "180 deg"))
            self.assertTrue(circular_input.isSymmetric)

            rect_feature = root.rect_pattern(
                [target],
                direction,
                4,
                "12 mm",
                direction_two=edge,
                quantity_two=2,
                distance_two="6 mm",
                distance_type="extent",
                symmetric_one=True,
                symmetric_two=True,
            )
            self.assertIsInstance(rect_feature, Ref)
            rect_input = root.raw.features.rectangularPatternFeatures.calls[-1]
            self.assertEqual(rect_input.patternDistanceType, 1)
            self.assertTrue(rect_input.isSymmetricInDirectionOne)
            self.assertTrue(rect_input.isSymmetricInDirectionTwo)
            self.assertIsNotNone(rect_input.directionTwoArgs)
            self.assertEqual((rect_input.directionTwoArgs[1].kind, rect_input.directionTwoArgs[1].value), ("real", 2))
            self.assertEqual((rect_input.directionTwoArgs[2].kind, rect_input.directionTwoArgs[2].value), ("string", "6 mm"))


if __name__ == "__main__":
    unittest.main()
