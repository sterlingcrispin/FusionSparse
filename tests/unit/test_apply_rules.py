from __future__ import annotations

from pathlib import Path
import unittest

from tools.apply_rules import apply_rules, load_rules


class ApplyRulesTests(unittest.TestCase):
    def test_load_rules_reads_repo_defaults(self) -> None:
        rules = load_rules()
        self.assertIn("new_design", rules["aliases"]["exports"])
        self.assertIn("xy", rules["compact_policy"]["planes"])
        self.assertIn("app", rules["compact_reference"]["exports"])
        self.assertIn("FeatureOperations", rules["enum_aliases"]["aliases"])
        self.assertIn("ExtrudeFeatures", rules["family_overrides"]["families"])
        self.assertIn("adsk.fusion.Design", rules["wrapper_dispatch"]["wrappers"])

    def test_apply_rules_attaches_enum_and_family_overrides(self) -> None:
        result = apply_rules(
            symbols=[
                {
                    "id": "adsk.fusion.Design",
                    "kind": "class",
                    "name": "Design",
                    "namespace": "adsk.fusion",
                    "lineage": {"docs": []},
                },
                {
                    "id": "adsk.fusion.Component",
                    "kind": "class",
                    "name": "Component",
                    "namespace": "adsk.fusion",
                    "lineage": {"docs": []},
                },
                {
                    "id": "adsk.fusion.Sketch",
                    "kind": "class",
                    "name": "Sketch",
                    "namespace": "adsk.fusion",
                    "lineage": {"docs": []},
                },
            ],
            enums=[
                {
                    "id": "adsk.fusion.FeatureOperations",
                    "name": "FeatureOperations",
                    "namespace": "adsk.fusion",
                    "members": [],
                    "doc": None,
                },
                {
                    "id": "adsk.fusion.PatternDistanceType",
                    "name": "PatternDistanceType",
                    "namespace": "adsk.fusion",
                    "members": [],
                    "doc": None,
                },
            ],
            families=[
                {
                    "id": "adsk.fusion.ExtrudeFeatures",
                    "name": "ExtrudeFeatures",
                    "namespace": "adsk.fusion",
                    "methods": ["add", "addSimple", "createInput"],
                    "traits": {},
                },
                {"id": "adsk.fusion.RevolveFeatures", "name": "RevolveFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.HoleFeatures", "name": "HoleFeatures", "namespace": "adsk.fusion", "methods": ["add", "createSimpleInput"], "traits": {}},
                {"id": "adsk.fusion.FilletFeatures", "name": "FilletFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ChamferFeatures", "name": "ChamferFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput2"], "traits": {}},
                {"id": "adsk.fusion.ConstructionPlanes", "name": "ConstructionPlanes", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ConstructionAxes", "name": "ConstructionAxes", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ConstructionPoints", "name": "ConstructionPoints", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.SketchTexts", "name": "SketchTexts", "namespace": "adsk.fusion", "methods": ["add", "createInput2"], "traits": {}},
                {"id": "adsk.fusion.CombineFeatures", "name": "CombineFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.MirrorFeatures", "name": "MirrorFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.CircularPatternFeatures", "name": "CircularPatternFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.RectangularPatternFeatures", "name": "RectangularPatternFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.SweepFeatures", "name": "SweepFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.LoftFeatures", "name": "LoftFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.PatchFeatures", "name": "PatchFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ShellFeatures", "name": "ShellFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.DraftFeatures", "name": "DraftFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.MoveFeatures", "name": "MoveFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput2"], "traits": {}},
                {"id": "adsk.fusion.OffsetFeatures", "name": "OffsetFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ReplaceFaceFeatures", "name": "ReplaceFaceFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ScaleFeatures", "name": "ScaleFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.SplitBodyFeatures", "name": "SplitBodyFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ThreadFeatures", "name": "ThreadFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.TrimFeatures", "name": "TrimFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
            ],
        )

        self.assertEqual(result["enums"][0]["aliases"]["new_body"], "NewBodyFeatureOperation")
        self.assertEqual(result["families"][0]["override"]["compact_method"], "extrude")
        self.assertEqual(result["compact_policy"]["extrude"]["family_id"], "adsk.fusion.ExtrudeFeatures")
        self.assertEqual(result["compact_policy"]["text"]["family_id"], "adsk.fusion.SketchTexts")

    def test_apply_rules_returns_wrapper_dispatch_entries(self) -> None:
        result = apply_rules(
            symbols=[
                {
                    "id": "adsk.fusion.Design",
                    "kind": "class",
                    "name": "Design",
                    "namespace": "adsk.fusion",
                    "lineage": {"docs": []},
                },
                {
                    "id": "adsk.fusion.Component",
                    "kind": "class",
                    "name": "Component",
                    "namespace": "adsk.fusion",
                    "lineage": {"docs": []},
                },
                {
                    "id": "adsk.fusion.Sketch",
                    "kind": "class",
                    "name": "Sketch",
                    "namespace": "adsk.fusion",
                    "lineage": {"docs": []},
                },
            ],
            enums=[],
            families=[
                {
                    "id": "adsk.fusion.ExtrudeFeatures",
                    "name": "ExtrudeFeatures",
                    "namespace": "adsk.fusion",
                    "methods": ["add", "addSimple", "createInput"],
                    "traits": {},
                },
                {"id": "adsk.fusion.RevolveFeatures", "name": "RevolveFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.HoleFeatures", "name": "HoleFeatures", "namespace": "adsk.fusion", "methods": ["add", "createSimpleInput"], "traits": {}},
                {"id": "adsk.fusion.FilletFeatures", "name": "FilletFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ChamferFeatures", "name": "ChamferFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput2"], "traits": {}},
                {"id": "adsk.fusion.ConstructionPlanes", "name": "ConstructionPlanes", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ConstructionAxes", "name": "ConstructionAxes", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ConstructionPoints", "name": "ConstructionPoints", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.SketchTexts", "name": "SketchTexts", "namespace": "adsk.fusion", "methods": ["add", "createInput2"], "traits": {}},
                {"id": "adsk.fusion.CombineFeatures", "name": "CombineFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.MirrorFeatures", "name": "MirrorFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.CircularPatternFeatures", "name": "CircularPatternFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.RectangularPatternFeatures", "name": "RectangularPatternFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.SweepFeatures", "name": "SweepFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.LoftFeatures", "name": "LoftFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.PatchFeatures", "name": "PatchFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ShellFeatures", "name": "ShellFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.DraftFeatures", "name": "DraftFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.MoveFeatures", "name": "MoveFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput2"], "traits": {}},
                {"id": "adsk.fusion.OffsetFeatures", "name": "OffsetFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ReplaceFaceFeatures", "name": "ReplaceFaceFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ScaleFeatures", "name": "ScaleFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.SplitBodyFeatures", "name": "SplitBodyFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.ThreadFeatures", "name": "ThreadFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
                {"id": "adsk.fusion.TrimFeatures", "name": "TrimFeatures", "namespace": "adsk.fusion", "methods": ["add", "createInput"], "traits": {}},
            ],
        )

        self.assertEqual(
            result["wrapper_dispatch"]["adsk.fusion.Design"],
            "compact.design.DesignRef",
        )


if __name__ == "__main__":
    unittest.main()
