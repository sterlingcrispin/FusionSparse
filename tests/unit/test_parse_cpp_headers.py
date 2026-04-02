from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.parse_cpp_headers import parse_cpp_headers


FUSION_TYPEDEFS = """
namespace adsk { namespace fusion {
enum FeatureOperations
{
    JoinFeatureOperation,
    CutFeatureOperation,
    NewBodyFeatureOperation = 4
};
}}
"""


EXTRUDE_FEATURES = """
namespace adsk { namespace fusion {
class ExtrudeFeatures : public core::Base {
public:
    core::Ptr<ExtrudeFeature> item(size_t index) const;
    core::Ptr<ExtrudeFeatureInput> createInput(const core::Ptr<core::Base>& profile, FeatureOperations operation) const;
    static const char* classType();
private:
    virtual ExtrudeFeature* item_raw(size_t index) const = 0;
};
}}
"""


class ParseCppHeadersTests(unittest.TestCase):
    def test_parse_enums_and_public_methods(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            include_root = Path(tmp_dir) / "include"
            (include_root / "Fusion").mkdir(parents=True)
            (include_root / "Fusion" / "Features").mkdir(parents=True)

            (include_root / "Fusion" / "FusionTypeDefs.h").write_text(FUSION_TYPEDEFS, encoding="utf-8")
            (include_root / "Fusion" / "Features" / "ExtrudeFeatures.h").write_text(EXTRUDE_FEATURES, encoding="utf-8")

            parsed = parse_cpp_headers(include_root)
            enums = {enum["id"]: enum for enum in parsed["enums"]}
            symbols = {symbol["id"]: symbol for symbol in parsed["symbols"]}

            self.assertIn("adsk.fusion.FeatureOperations", enums)
            self.assertEqual(enums["adsk.fusion.FeatureOperations"]["members"][0]["name"], "JoinFeatureOperation")
            self.assertEqual(enums["adsk.fusion.FeatureOperations"]["members"][2]["numeric_value"], 4)

            self.assertIn("adsk.fusion.ExtrudeFeatures", symbols)
            self.assertIn("adsk.fusion.ExtrudeFeatures.item", symbols)
            self.assertIn("adsk.fusion.ExtrudeFeatures.createInput", symbols)
            self.assertEqual(symbols["adsk.fusion.ExtrudeFeatures.classType"]["flags"]["static"], True)
            self.assertNotIn("adsk.fusion.ExtrudeFeatures.item_raw", symbols)


if __name__ == "__main__":
    unittest.main()
