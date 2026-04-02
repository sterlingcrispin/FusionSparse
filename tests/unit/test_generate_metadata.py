from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.generate_metadata import generate_metadata


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _seed_generation_root(root: Path) -> None:
    (root / "build" / "ir").mkdir(parents=True)
    (root / "corpus").mkdir(parents=True)
    (root / "rules").mkdir(parents=True)
    (root / "src" / "fusion_sparse" / "generated").mkdir(parents=True)

    (root / "rules" / "aliases.yaml").write_text("exports:\n  app: runtime.context.app\n", encoding="utf-8")
    (root / "rules" / "compact_exports.yaml").write_text("exports:\n  - app\n", encoding="utf-8")
    (root / "rules" / "compact_policy.yaml").write_text(
        "\n".join(
            [
                "design_workspace:",
                "  scope_namespaces: [adsk.fusion]",
                "  waves:",
                "    wave_one: [ConstructionPlanes, ConstructionAxes, ConstructionPoints, SketchArcs, RevolveFeatures, HoleFeatures, FilletFeatures, ChamferFeatures]",
                "    wave_two: [CombineFeatures, MirrorFeatures, RectangularPatternFeatures, CircularPatternFeatures]",
                "  adjacent: [ExtrudeFeatures, RevolveFeatures]",
                "planes:",
                "  xy: xYConstructionPlane",
                "sketch:",
                "  targets:",
                "    point: [sketchPoints]",
                "  collections:",
                "    point: sketchPoints",
                "    line: sketchLines",
                "    circle: sketchCircles",
                "    arc: sketchArcs",
                "    ellipse: sketchEllipses",
                "    spline: sketchFittedSplines",
                "    rect: sketchLines",
                "  coercers:",
                "    point: [point]",
                "    line: [point, point]",
                "    circle: [point, length_cm]",
                "    arc: [point, point, identity]",
                "    ellipse: [point, point, point]",
                "    spline: [point_collection]",
                "    rect: [point, point]",
                "  methods:",
                "    point: add",
                "    line: addByTwoPoints",
                "    circle: addByCenterRadius",
                "    arc: addByCenterStartSweep",
                "    ellipse: add",
                "    spline: add",
                "    rect: addTwoPointRectangle",
                "  length_units_cm:",
                "    mm: 0.1",
                "text:",
                "  family_id: adsk.fusion.SketchTexts",
                "  collection_attr: sketchTexts",
                "  builder_input: createInput2",
                "  builder_terminal: add",
                "  input_methods:",
                "    multiline: setAsMultiLine",
                "    along_path: setAsAlongPath",
                "    fit_path: setAsFitOnPath",
                "  input_attrs:",
                "    horizontal_flip: isHorizontalFlip",
                "    vertical_flip: isVerticalFlip",
                "    font_name: fontName",
                "  horizontal_alignments:",
                "    left: LeftHorizontalAlignment",
                "    center: CenterHorizontalAlignment",
                "    right: RightHorizontalAlignment",
                "  vertical_alignments:",
                "    top: TopVerticalAlignment",
                "    center: MiddleVerticalAlignment",
                "    bottom: BottomVerticalAlignment",
                "extrude:",
                "  family_id: adsk.fusion.ExtrudeFeatures",
                "  extent_types:",
                "    distance: DistanceExtentDefinition",
                "  input_attrs:",
                "    participant_bodies: participantBodies",
                "    solid: isSolid",
                "  input_methods:",
                "    one_side: setOneSideExtent",
                "    symmetric: setSymmetricExtent",
                "construction:",
                "  plane:",
                "    family_id: adsk.fusion.ConstructionPlanes",
                "    builder_input: createInput",
                "    builder_terminal: add",
                "    methods:",
                "      offset: setByOffset",
                "  axis:",
                "    family_id: adsk.fusion.ConstructionAxes",
                "    builder_input: createInput",
                "    builder_terminal: add",
                "    methods:",
                "      edge: setByEdge",
                "  point:",
                "    family_id: adsk.fusion.ConstructionPoints",
                "    builder_input: createInput",
                "    builder_terminal: add",
                "    methods:",
                "      at: setByPoint",
                "revolve:",
                "  family_id: adsk.fusion.RevolveFeatures",
                "  builder_input: createInput",
                "  builder_terminal: add",
                "  input_methods:",
                "    angle: setAngleExtent",
                "hole:",
                "  family_id: adsk.fusion.HoleFeatures",
                "  builder_terminal: add",
                "  create_methods:",
                "    simple: createSimpleInput",
                "    counterbore: createCounterboreInput",
                "    countersink: createCountersinkInput",
                "  input_methods:",
                "    depth: setDistanceExtent",
                "    by_offsets: setPositionByPlaneAndOffsets",
                "    on_edge: setPositionOnEdge",
                "    at_center: setPositionAtCenter",
                "    by_points: setPositionBySketchPoints",
                "  edge_positions:",
                "    start: start",
                "    mid: mid",
                "    end: end",
                "fillet:",
                "  family_id: adsk.fusion.FilletFeatures",
                "  builder_input: createInput",
                "  builder_terminal: add",
                "  input_attrs:",
                "    edge_sets: edgeSetInputs",
                "  input_methods:",
                "    constant_radius: addConstantRadiusEdgeSet",
                "chamfer:",
                "  family_id: adsk.fusion.ChamferFeatures",
                "  builder_input: createInput2",
                "  builder_terminal: add",
                "  input_attrs:",
                "    edge_sets: chamferEdgeSets",
                "  input_methods:",
                "    equal_distance: addEqualDistanceChamferEdgeSet",
                "combine:",
                "  family_id: adsk.fusion.CombineFeatures",
                "  builder_input: createInput",
                "  builder_terminal: add",
                "  input_attrs:",
                "    operation: operation",
                "    keep_tools: isKeepToolBodies",
                "    new_component: isNewComponent",
                "mirror:",
                "  family_id: adsk.fusion.MirrorFeatures",
                "  builder_input: createInput",
                "  builder_terminal: add",
                "circular_pattern:",
                "  family_id: adsk.fusion.CircularPatternFeatures",
                "  builder_input: createInput",
                "  builder_terminal: add",
                "  input_attrs:",
                "    quantity: quantity",
                "    total_angle: totalAngle",
                "    symmetric: isSymmetric",
                "rectangular_pattern:",
                "  family_id: adsk.fusion.RectangularPatternFeatures",
                "  builder_input: createInput",
                "  builder_terminal: add",
                "  input_methods:",
                "    direction_two: setDirectionTwo",
                "  input_attrs:",
                "    symmetric_one: isSymmetricInDirectionOne",
                "    symmetric_two: isSymmetricInDirectionTwo",
                "    distance_type: patternDistanceType",
                "  distance_types:",
                "    spacing: spacing",
                "    extent: extent",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "rules" / "compact_reference.yaml").write_text(
        "\n".join(
            [
                "exports:",
                "  app:",
                "    raw_mapping: adsk.core.Application.get",
                "    arguments: []",
                "    example: |",
                "      app = fs.app()",
                "    escape_hatch: Use `.raw` for the original Autodesk object.",
                "methods:",
                "  ComponentRef.extrude:",
                "    raw_mapping: adsk.fusion.ExtrudeFeatures.addSimple or createInput + add",
                "    arguments:",
                "      - profile",
                "      - distance=None",
                "      - op=\"new_body\"",
                "    example: |",
                "      ext = root.extrude(sk.profile(), \"10 mm\")",
                "    escape_hatch: Use `root.raw.features.extrudeFeatures` directly.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "rules" / "doc_overrides.yaml").write_text("overrides: {}\n", encoding="utf-8")
    (root / "rules" / "enum_aliases.yaml").write_text(
        "aliases:\n  FeatureOperations:\n    new_body: NewBodyFeatureOperation\n  HoleEdgePositions:\n    mid: EdgeMidPointPosition\n  PatternDistanceType:\n    spacing: SpacingPatternDistanceType\n",
        encoding="utf-8",
    )
    (root / "rules" / "exclusions.yaml").write_text("symbols: []\npages: []\n", encoding="utf-8")
    (root / "rules" / "family_overrides.yaml").write_text(
        "\n".join(
            [
                "families:",
                "  ExtrudeFeatures:",
                "    compact_method: extrude",
                "    simple_method: addSimple",
                "    builder_input: createInput",
                "    builder_terminal: add",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "rules" / "wrapper_dispatch.yaml").write_text(
        "wrappers:\n  adsk.fusion.Design: compact.design.DesignRef\n",
        encoding="utf-8",
    )

    (root / "corpus" / "corpus.lock.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-01T00:00:00Z",
                "source_root": "/tmp/FusionAPIReference",
                "git_commit": "abc123",
                "required_paths": {},
                "optional_paths": {},
                "file_counts": {},
            }
        ),
        encoding="utf-8",
    )

    (root / "build" / "ir" / "symbols.json").write_text(
        json.dumps(
            [
                {
                    "id": "adsk.fusion.Design",
                    "kind": "class",
                    "name": "Design",
                    "owner": "adsk.fusion",
                    "namespace": "adsk.fusion",
                    "display_name": "Design",
                    "traits": {},
                    "signatures": [],
                    "doc": {"title": "Design Object", "introduced_in": "August 2014"},
                    "lineage": {"docs": []},
                },
                {
                    "id": "adsk.core.Application.get",
                    "kind": "method",
                    "name": "get",
                    "owner": "adsk.core.Application",
                    "namespace": "adsk.core",
                    "display_name": "Application.get",
                    "traits": {"is_static_constructor": True},
                    "signatures": [{}],
                    "doc": {"title": "Application.get Method", "introduced_in": "August 2014"},
                    "lineage": {"docs": []},
                },
                {
                    "id": "adsk.fusion.ExtrudeFeatures",
                    "kind": "class",
                    "name": "ExtrudeFeatures",
                    "owner": "adsk.fusion",
                    "namespace": "adsk.fusion",
                    "display_name": "ExtrudeFeatures",
                    "traits": {"has_add": True, "has_add_simple": True, "has_create_input": True},
                    "signatures": [],
                    "doc": {"title": "ExtrudeFeatures Object", "introduced_in": "August 2014"},
                    "lineage": {"docs": []},
                },
            ]
        ),
        encoding="utf-8",
    )
    (root / "build" / "ir" / "enums.json").write_text(
        json.dumps(
            [
                {
                    "id": "adsk.fusion.FeatureOperations",
                    "name": "FeatureOperations",
                    "namespace": "adsk.fusion",
                    "members": [{"name": "NewBodyFeatureOperation", "value": "3"}],
                    "doc": None,
                },
                {
                    "id": "adsk.fusion.HoleEdgePositions",
                    "name": "HoleEdgePositions",
                    "namespace": "adsk.fusion",
                    "members": [{"name": "EdgeMidPointPosition", "value": "1"}],
                    "doc": None,
                },
                {
                    "id": "adsk.fusion.PatternDistanceType",
                    "name": "PatternDistanceType",
                    "namespace": "adsk.fusion",
                    "members": [{"name": "SpacingPatternDistanceType", "value": "0"}],
                    "doc": None,
                },
            ]
        ),
        encoding="utf-8",
    )
    (root / "build" / "ir" / "families.json").write_text(
        json.dumps(
            [
                {
                    "id": "adsk.fusion.ExtrudeFeatures",
                    "name": "ExtrudeFeatures",
                    "namespace": "adsk.fusion",
                    "methods": ["add", "addSimple", "createInput"],
                    "traits": {"has_add": True},
                },
                {"id": "adsk.fusion.RevolveFeatures", "name": "RevolveFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.HoleFeatures", "name": "HoleFeatures", "namespace": "adsk.fusion", "methods": ["add", "createSimpleInput"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.FilletFeatures", "name": "FilletFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.ChamferFeatures", "name": "ChamferFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput2"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.ConstructionPlanes", "name": "ConstructionPlanes", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.ConstructionAxes", "name": "ConstructionAxes", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.ConstructionPoints", "name": "ConstructionPoints", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.SketchTexts", "name": "SketchTexts", "namespace": "adsk.fusion", "methods": ["add", "createInput2"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.CombineFeatures", "name": "CombineFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.MirrorFeatures", "name": "MirrorFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.CircularPatternFeatures", "name": "CircularPatternFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {"has_add": True}},
                {"id": "adsk.fusion.RectangularPatternFeatures", "name": "RectangularPatternFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {"has_add": True}},
            ]
        ),
        encoding="utf-8",
    )


class GenerateMetadataTests(unittest.TestCase):
    def test_generate_metadata_emits_python_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _seed_generation_root(root)

            result = generate_metadata(repo_root=root, build_ir_first=False)

            enum_index = _load_module(Path(result["enum_index_path"]), "generated_enum_index")
            family_index = _load_module(Path(result["families_path"]), "generated_families")
            compact_policy = _load_module(Path(result["compact_policy_path"]), "generated_compact_policy")
            compact_surface = _load_module(Path(result["compact_surface_path"]), "generated_compact_surface")
            compact_reference = _load_module(Path(result["compact_reference_path"]), "generated_compact_reference")
            release_info = _load_module(Path(result["release_info_path"]), "generated_release_info")
            wrapper_dispatch = _load_module(Path(result["wrapper_dispatch_path"]), "generated_wrapper_dispatch")
            public_api_text = Path(result["public_api_path"]).read_text(encoding="utf-8")
            compact_reference_doc = Path(result["compact_reference_doc_path"]).read_text(encoding="utf-8")
            raw_mapping_doc = Path(result["raw_mapping_doc_path"]).read_text(encoding="utf-8")
            update_workflow_doc = Path(result["update_workflow_doc_path"]).read_text(encoding="utf-8")
            symbol_stats_report = Path(result["symbol_stats_report_path"]).read_text(encoding="utf-8")

            self.assertEqual(enum_index.ENUM_ALIASES_BY_NAME["FeatureOperations"]["new_body"], "NewBodyFeatureOperation")
            self.assertEqual(enum_index.ENUM_ALIASES_BY_NAME["HoleEdgePositions"]["mid"], "EdgeMidPointPosition")
            self.assertEqual(family_index.FAMILY_INDEX["adsk.fusion.ExtrudeFeatures"]["override"]["compact_method"], "extrude")
            self.assertEqual(compact_policy.PLANE_ALIASES["xy"], "xYConstructionPlane")
            self.assertEqual(compact_policy.SKETCH_TARGETS["point"], ["sketchPoints"])
            self.assertEqual(compact_policy.EXTRUDE_POLICY["builder_input"], "createInput")
            self.assertEqual(compact_policy.TEXT_POLICY["builder_input"], "createInput2")
            self.assertEqual(compact_policy.CONSTRUCTION_POLICY["plane"]["family_id"], "adsk.fusion.ConstructionPlanes")
            self.assertEqual(compact_policy.REVOLVE_POLICY["builder_input"], "createInput")
            self.assertEqual(compact_policy.HOLE_POLICY["builder_terminal"], "add")
            self.assertEqual(compact_policy.FILLET_POLICY["input_methods"]["constant_radius"], "addConstantRadiusEdgeSet")
            self.assertEqual(compact_policy.CHAMFER_POLICY["builder_input"], "createInput2")
            self.assertEqual(compact_policy.COMBINE_POLICY["builder_input"], "createInput")
            self.assertEqual(compact_policy.MIRROR_POLICY["builder_terminal"], "add")
            self.assertEqual(compact_policy.CIRCULAR_PATTERN_POLICY["input_attrs"]["quantity"], "quantity")
            self.assertEqual(
                compact_policy.RECTANGULAR_PATTERN_POLICY["input_methods"]["direction_two"],
                "setDirectionTwo",
            )
            self.assertEqual(compact_surface.COMPACT_PROPERTIES["DesignRef.root"]["attr_path"], ["rootComponent"])
            self.assertEqual(compact_surface.COMPACT_METHODS["SketchRef.point"]["target_attrs"], ["sketchPoints"])
            self.assertEqual(compact_surface.COMPACT_METHODS["SketchRef.circle"]["method"], "addByCenterRadius")
            self.assertEqual(compact_surface.COMPACT_METHODS["SketchRef.arc"]["method"], "addByCenterStartSweep")
            self.assertEqual(compact_reference.COMPACT_REFERENCE_EXPORTS[0]["public_name"], "app")
            self.assertEqual(
                compact_reference.COMPACT_REFERENCE_INDEX["ComponentRef.extrude"]["raw_mapping"],
                "adsk.fusion.ExtrudeFeatures.addSimple or createInput + add",
            )
            self.assertEqual(release_info.RELEASE_INFO["git_commit"], "abc123")
            self.assertNotIn("generated_at", release_info.RELEASE_INFO)
            self.assertNotIn("source_root", release_info.RELEASE_INFO)
            self.assertEqual(tuple(wrapper_dispatch.WRAPPER_CLASS_PATHS["adsk::fusion::Design"]), ("fusion_sparse.compact.design", "DesignRef"))
            self.assertIn("/build/generated/", result["symbol_index_path"])
            self.assertIn("/build/generated/", result["families_path"])
            self.assertIn("/build/generated/", result["compact_reference_path"])
            self.assertIn("from fusion_sparse.runtime.context import app", public_api_text)
            self.assertIn("__all__ = ['app']", public_api_text)
            self.assertIn("## Public Helpers", compact_reference_doc)
            self.assertIn("`app`", compact_reference_doc)
            self.assertIn("| `ComponentRef.extrude` | `adsk.fusion.ExtrudeFeatures.addSimple or createInput + add` |", raw_mapping_doc)
            self.assertIn("# Update Workflow", update_workflow_doc)
            self.assertIn("`abc123`", update_workflow_doc)
            self.assertIn("# Symbol Stats", symbol_stats_report)
            self.assertIn("| `class` | `2` |", symbol_stats_report)
            self.assertIn("| `method` | `1` |", symbol_stats_report)

    def test_generate_metadata_matches_golden_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _seed_generation_root(root)
            result = generate_metadata(repo_root=root, build_ir_first=False)
            golden_dir = Path(__file__).resolve().parents[1] / "golden" / "generated"

            expected_files = {
                "public_api_path": "public_api.py.golden",
                "enum_index_path": "enum_index.py.golden",
                "wrapper_dispatch_path": "wrapper_dispatch.py.golden",
                "update_workflow_doc_path": "update_workflow.md.golden",
            }

            for result_key, golden_name in expected_files.items():
                actual = Path(result[result_key]).read_text(encoding="utf-8")
                expected = (golden_dir / golden_name).read_text(encoding="utf-8")
                self.assertEqual(actual, expected, result_key)


if __name__ == "__main__":
    unittest.main()
