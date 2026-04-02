from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.generate_sample_pairs import generate_sample_pairs, translate_official_script


REPO_ROOT = Path(__file__).resolve().parents[2]


class GenerateSamplePairsTests(unittest.TestCase):
    def test_translate_official_simple_extrusion_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            generate_sample_pairs(repo_root=REPO_ROOT, output_root=tmp_dir)
            source = (Path(tmp_dir) / "official" / "simple_extrusion_sample.py").read_text(encoding="utf-8")

            translated = translate_official_script(source)

            self.assertIn('sketch = root.sketch("xy")', translated)
            self.assertIn("sketch.circle((0, 0), 2)", translated)
            self.assertIn('root.extrude(prof, 5, op="new_component")', translated)
            self.assertIn("print_design_signature(design.raw)", translated)
            self.assertNotIn("adsk.", translated)

    def test_translate_official_builder_script(self) -> None:
        source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "extrude_feature_through_all.py"
        ).read_text(encoding="utf-8")

        translated = translate_official_script(source)

        self.assertIn('base_sketch = root.sketch("xy")', translated)
        self.assertIn("base_sketch.rect((0, 0), (10, 10))", translated)
        self.assertIn('root.extrude(base_profile, "10 mm")', translated)
        self.assertIn('root.extrude(cut_profile, op="cut").through_all().build()', translated)
        self.assertNotIn("adsk.", translated)

    def test_translate_official_symmetric_half_length_builder_script(self) -> None:
        source = """
import adsk.core, adsk.fusion
from tests.integration.sample_pairs.common import print_design_signature

def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    rootComp = design.rootComponent
    sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 2)
    prof = sketch.profiles.item(0)
    distance = adsk.core.ValueInput.createByString('8 mm')
    extrudes = rootComp.features.extrudeFeatures
    extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    fullLength = False
    extrudeInput.setSymmetricExtent(distance, fullLength)
    extrudes.add(extrudeInput)
    print_design_signature(design)
"""

        translated = translate_official_script(source)

        self.assertIn('root.extrude(prof).symmetric("8 mm", full_length=False).build()', translated)
        self.assertNotIn("adsk.", translated)

    def test_translate_official_circle_by_center_radius_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            generate_sample_pairs(repo_root=REPO_ROOT, output_root=tmp_dir)
            source = (Path(tmp_dir) / "official" / "circle_by_center_radius.py").read_text(encoding="utf-8")

            translated = translate_official_script(source)

            self.assertIn('sketch = root.sketch("xy")', translated)
            self.assertIn("circle2 = sketch.circle((8, 3), 3)", translated)
            self.assertIn("sketch.circle(circle2.centerSketchPoint, 4)", translated)
            self.assertNotIn("adsk.", translated)

    def test_translate_generated_official_sketch_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            generate_sample_pairs(repo_root=REPO_ROOT, output_root=tmp_dir)

            rect_source = (Path(tmp_dir) / "official" / "sketch_lines_add_center_point_rectangle.py").read_text(
                encoding="utf-8"
            )
            circle_source = (Path(tmp_dir) / "official" / "sketch_circles_add_by_three_points.py").read_text(
                encoding="utf-8"
            )

            rect_translated = translate_official_script(rect_source)
            circle_translated = translate_official_script(circle_source)

            self.assertIn("sketch.rect_center((5, 5), (25, 25))", rect_translated)
            self.assertIn("sketch.circle3p((0, 0), (5, 5), (9, 14))", circle_translated)
            self.assertNotIn("adsk.", rect_translated)
            self.assertNotIn("adsk.", circle_translated)

    def test_translate_generated_official_extended_sketch_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            generate_sample_pairs(repo_root=REPO_ROOT, output_root=tmp_dir)

            point_source = (Path(tmp_dir) / "official" / "sketch_point_add.py").read_text(encoding="utf-8")
            ellipse_source = (Path(tmp_dir) / "official" / "sketch_ellipses_add.py").read_text(encoding="utf-8")
            spline_source = (Path(tmp_dir) / "official" / "sketch_fitted_splines_add.py").read_text(encoding="utf-8")
            multiline_source = (Path(tmp_dir) / "official" / "sketch_text_multiline.py").read_text(encoding="utf-8")
            along_path_source = (Path(tmp_dir) / "official" / "sketch_text_along_path.py").read_text(encoding="utf-8")
            fit_path_source = (Path(tmp_dir) / "official" / "sketch_text_fit_on_path.py").read_text(encoding="utf-8")

            point_translated = translate_official_script(point_source)
            ellipse_translated = translate_official_script(ellipse_source)
            spline_translated = translate_official_script(spline_source)
            multiline_translated = translate_official_script(multiline_source)
            along_path_translated = translate_official_script(along_path_source)
            fit_path_translated = translate_official_script(fit_path_source)

            self.assertIn("sketch.point((5, 4))", point_translated)
            self.assertIn("sketch.ellipse((0, 0), (10, 0), (5, 4))", ellipse_translated)
            self.assertIn("sketch.spline((0, 0), (5, 1), (6, 4, 3), (7, 6, 6), (2, 3), (0, 1))", spline_translated)
            self.assertIn('sketch.text("This is a long line of text that is broken automatically.\\n\\nAnd this is a defined line break.", (0, 0), (10, 5), 0.5)', multiline_translated)
            self.assertIn('sketch.text_path("Autodesk", path, 0.5)', along_path_translated)
            self.assertIn('sketch.text_fit("Autodesk", path, 0.5)', fit_path_translated)
            self.assertNotIn("adsk.", point_translated)
            self.assertNotIn("adsk.", ellipse_translated)
            self.assertNotIn("adsk.", spline_translated)
            self.assertNotIn("adsk.", multiline_translated)
            self.assertNotIn("adsk.", along_path_translated)
            self.assertNotIn("adsk.", fit_path_translated)

    def test_generate_sample_pairs_writes_generated_manifest_and_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = generate_sample_pairs(repo_root=REPO_ROOT, output_root=tmp_dir)

            manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
            self.assertEqual(result["pair_count"], 53)
            self.assertEqual(len(manifest), 53)
            self.assertGreaterEqual(len(result["generated_official_scripts"]), 10)
            first_compact = Path(manifest[0]["compact_script"])
            if not first_compact.is_absolute():
                first_compact = REPO_ROOT / first_compact
            self.assertTrue(first_compact.exists())
            self.assertIn("import fusion_sparse as fx", first_compact.read_text(encoding="utf-8"))
            generated_official = Path(tmp_dir) / "official" / "simple_extrusion_sample.py"
            self.assertTrue(generated_official.exists())
            self.assertIn("print_design_signature", generated_official.read_text(encoding="utf-8"))

    def test_translate_wave_two_official_samples(self) -> None:
        combine_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "combine_features_add.py"
        ).read_text(encoding="utf-8")
        pattern_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "rectangular_pattern_feature_sample.py"
        ).read_text(encoding="utf-8")

        combine_translated = translate_official_script(combine_source)
        pattern_translated = translate_official_script(pattern_source)

        self.assertIn("root.combine(targetBody, toolBody)", combine_translated)
        self.assertIn('root.rect_pattern(body, xAxis, "3", "8 cm", yAxis, "3", "8 cm")', pattern_translated)
        self.assertNotIn("adsk.", combine_translated)
        self.assertNotIn("adsk.", pattern_translated)

    def test_translate_wave_three_official_samples(self) -> None:
        sweep_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "sweep_feature_sample.py"
        ).read_text(encoding="utf-8")
        loft_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "loft_feature_sample.py"
        ).read_text(encoding="utf-8")
        shell_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "shell_feature_sample.py"
        ).read_text(encoding="utf-8")
        draft_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "draft_feature_sample.py"
        ).read_text(encoding="utf-8")

        sweep_translated = translate_official_script(sweep_source)
        loft_translated = translate_official_script(loft_source)
        shell_translated = translate_official_script(shell_source)
        draft_translated = translate_official_script(draft_source)

        self.assertIn('root.sweep(prof, path, taper="5 deg", twist="10 deg")', sweep_translated)
        self.assertIn("root.loft(profile0, profile1, profile2)", loft_translated)
        self.assertIn("root.shell(extrudeFeature.endFaces.item(0), inside=0.5, tangent_chain=False)", shell_translated)
        self.assertIn('root.draft(draftFaces, neutralFace, "10 deg")', draft_translated)
        self.assertNotIn("adsk.", sweep_translated)
        self.assertNotIn("adsk.", loft_translated)
        self.assertNotIn("adsk.", shell_translated)
        self.assertNotIn("adsk.", draft_translated)

    def test_translate_modification_cluster_official_samples(self) -> None:
        move_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "move_feature_sample.py"
        ).read_text(encoding="utf-8")
        scale_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "scale_feature_sample.py"
        ).read_text(encoding="utf-8")
        thread_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "thread_feature_sample.py"
        ).read_text(encoding="utf-8")
        trim_source = (
            REPO_ROOT / "tests" / "integration" / "sample_pairs" / "official" / "trim_feature_sample.py"
        ).read_text(encoding="utf-8")

        move_translated = translate_official_script(move_source)
        scale_translated = translate_official_script(scale_source)
        thread_translated = translate_official_script(thread_source)
        trim_translated = translate_official_script(trim_source)

        self.assertIn("root.move(body, translation=(2, 1))", move_translated)
        self.assertIn("root.scale(body, basePt, 1, xyz=(1.5, 0.75, 0.5))", scale_translated)
        self.assertIn("root.thread(threadFace, length=2.5)", thread_translated)
        self.assertIn("root.trim(body)", trim_translated)
        self.assertIn(".surface().one_side(3)", trim_translated)
        self.assertNotIn("adsk.", move_translated)
        self.assertNotIn("adsk.", scale_translated)
        self.assertNotIn("adsk.", thread_translated)
        self.assertNotIn("adsk.", trim_translated)


if __name__ == "__main__":
    unittest.main()
