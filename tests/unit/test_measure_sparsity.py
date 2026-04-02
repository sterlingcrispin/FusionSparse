from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.measure_sparsity import measure_sparsity


class MeasureSparsityTests(unittest.TestCase):
    def test_measure_sparsity_generates_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            baseline_dir = root / "benchmarks" / "baselines"
            compact_dir = root / "benchmarks" / "compact"
            baseline_dir.mkdir(parents=True)
            compact_dir.mkdir(parents=True)

            (baseline_dir / "01_demo.py").write_text(
                "import adsk.core\n\n\ndef run(context):\n    return adsk.core.Application.get()\n",
                encoding="utf-8",
            )
            (compact_dir / "01_demo.py").write_text(
                "import fusion_sparse as fx\n\n\ndef run(context):\n    return fx.app()\n",
                encoding="utf-8",
            )

            result = measure_sparsity(repo_root=root)
            report = Path(result["report_path"]).read_text(encoding="utf-8")

            self.assertEqual(result["pair_count"], 1)
            self.assertGreater(result["baseline_totals"]["chars"], result["compact_totals"]["chars"])
            self.assertGreater(result["baseline_totals"]["tokens"], result["compact_totals"]["tokens"])
            self.assertEqual(result["compact_totals"]["adsk_refs"], 0)
            self.assertIn("# Sparsity Report", report)
            self.assertIn("Token reduction", report)


if __name__ == "__main__":
    unittest.main()
