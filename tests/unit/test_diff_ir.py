from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.diff_ir import diff_ir, snapshot_ir


class DiffIRTests(unittest.TestCase):
    def test_snapshot_ir_copies_current_ir_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "build" / "ir").mkdir(parents=True)
            (root / "corpus").mkdir(parents=True)

            self._write_state(
                root / "build" / "ir",
                root / "corpus",
                symbols=[{"id": "A", "signatures": [], "kind": "class"}],
                enums=[],
                doc_pages=[],
                families=[],
                corpus_lock={"git_commit": "abc1234567", "generated_at": "2026-04-01T00:00:00Z"},
            )

            result = snapshot_ir(repo_root=root, snapshot_name="baseline")

            snapshot_dir = Path(result["snapshot_dir"])
            self.assertTrue((snapshot_dir / "symbols.json").exists())
            self.assertTrue((snapshot_dir / "corpus.lock.json").exists())
            manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["name"], "baseline")
            self.assertEqual(manifest["git_commit"], "abc1234567")

    def test_diff_ir_reports_symbol_enum_and_doc_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "build" / "ir").mkdir(parents=True)
            (root / "corpus").mkdir(parents=True)
            (root / "snapshots" / "baseline").mkdir(parents=True)

            self._write_state(
                root / "snapshots" / "baseline",
                root / "snapshots" / "baseline",
                symbols=[
                    {"id": "OldOnly", "signatures": [], "kind": "class"},
                    {"id": "SharedMethod", "signatures": [{"language": "python", "params": [{"name": "a"}], "returns": "int"}], "kind": "method"},
                    {"id": "Design.designType", "signatures": [], "kind": "property"},
                ],
                enums=[
                    {"id": "Mode", "members": [{"name": "One", "value": "1"}]},
                ],
                doc_pages=[
                    {"source_path": "OldPage.htm", "title": "Old Page", "symbol_id": "OldOnly"},
                ],
                families=[],
                corpus_lock={"git_commit": "abc1234", "generated_at": "2026-04-01T00:00:00Z"},
            )

            self._write_state(
                root / "build" / "ir",
                root / "corpus",
                symbols=[
                    {"id": "SharedMethod", "signatures": [{"language": "python", "params": [{"name": "a"}, {"name": "b"}], "returns": "int"}], "kind": "method"},
                    {"id": "NewOnly", "signatures": [], "kind": "class"},
                    {"id": "Design.designType", "signatures": [], "kind": "property"},
                ],
                enums=[
                    {"id": "Mode", "members": [{"name": "One", "value": "2"}, {"name": "Two", "value": "3"}]},
                ],
                doc_pages=[
                    {"source_path": "OldPage.htm", "title": "Old Page", "symbol_id": "OldOnly"},
                    {"source_path": "Python_3_14_Update.htm", "title": "Embedded Python 3.14", "symbol_id": None},
                ],
                families=[],
                corpus_lock={"git_commit": "def5678", "generated_at": "2026-04-02T00:00:00Z"},
            )

            result = diff_ir(repo_root=root, snapshot_name="baseline")
            report = Path(result["report_path"]).read_text(encoding="utf-8")

            self.assertEqual(result["added_symbol_count"], 1)
            self.assertEqual(result["removed_symbol_count"], 1)
            self.assertEqual(result["changed_signature_count"], 1)
            self.assertEqual(result["changed_enum_count"], 1)
            self.assertEqual(result["new_doc_page_count"], 1)
            self.assertIn("`NewOnly`", report)
            self.assertIn("`OldOnly`", report)
            self.assertIn("`SharedMethod`", report)
            self.assertIn("`Mode`", report)
            self.assertIn("`Python_3_14_Update.htm`", report)
            self.assertIn("embedded Python version changes", report)
            self.assertIn("design intent changes", report)

    def _write_state(
        self,
        ir_dir: Path,
        corpus_dir: Path,
        *,
        symbols: list[dict[str, object]],
        enums: list[dict[str, object]],
        doc_pages: list[dict[str, object]],
        families: list[dict[str, object]],
        corpus_lock: dict[str, object],
    ) -> None:
        ir_dir.mkdir(parents=True, exist_ok=True)
        corpus_dir.mkdir(parents=True, exist_ok=True)
        (ir_dir / "symbols.json").write_text(json.dumps(symbols), encoding="utf-8")
        (ir_dir / "enums.json").write_text(json.dumps(enums), encoding="utf-8")
        (ir_dir / "doc_pages.json").write_text(json.dumps(doc_pages), encoding="utf-8")
        (ir_dir / "families.json").write_text(json.dumps(families), encoding="utf-8")
        (corpus_dir / "corpus.lock.json").write_text(json.dumps(corpus_lock), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
