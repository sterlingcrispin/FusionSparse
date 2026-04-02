from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.map_api_coverage import map_api_coverage


REPO_ROOT = Path(__file__).resolve().parents[2]


class MapApiCoverageTests(unittest.TestCase):
    def test_map_api_coverage_writes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            md_path = Path(tmp_dir) / "coverage.md"
            json_path = Path(tmp_dir) / "coverage.json"

            result = map_api_coverage(repo_root=REPO_ROOT, output_path=md_path, json_output_path=json_path)

            self.assertTrue(md_path.exists())
            self.assertTrue(json_path.exists())
            self.assertGreater(result["symbol_count"], 0)
            self.assertGreater(result["family_count"], 0)
            self.assertGreater(result["direct_compact_symbol_count"], 0)
            self.assertGreaterEqual(result["validated_pair_count"], 12)

            rendered = md_path.read_text(encoding="utf-8")
            payload = json.loads(json_path.read_text(encoding="utf-8"))

            self.assertIn("# API Coverage Map", rendered)
            self.assertIn("Namespace Map", rendered)
            self.assertIn("adsk.fusion", rendered)
            self.assertEqual(payload["validation"]["validated_pair_count"], result["validated_pair_count"])
            self.assertIn("adsk.fusion.ExtrudeFeatures.addSimple", payload["compact_surface"]["direct_symbol_ids"])


if __name__ == "__main__":
    unittest.main()
