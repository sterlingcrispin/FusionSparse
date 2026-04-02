from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.corpus_loader import CorpusError, discover_corpus, write_corpus_lockfile


class CorpusLoaderTests(unittest.TestCase):
    def test_discover_corpus_counts_required_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "FusionAPIReference"
            (root / "Fusion_API_Python_Reference" / "defs").mkdir(parents=True)
            (root / "Fusion_API_CPP_Reference" / "include").mkdir(parents=True)
            (root / "Fusion_API_Documentation" / "files").mkdir(parents=True)
            (root / "processed_docs" / "md").mkdir(parents=True)

            (root / "Fusion_API_Python_Reference" / "defs" / "adsk.py").write_text("print('x')\n", encoding="utf-8")
            (root / "Fusion_API_CPP_Reference" / "include" / "Example.h").write_text("// header\n", encoding="utf-8")
            (root / "Fusion_API_Documentation" / "files" / "Example.htm").write_text("<html></html>\n", encoding="utf-8")
            (root / "processed_docs" / "md" / "Example.md").write_text("# Example\n", encoding="utf-8")

            manifest = discover_corpus(root)

            self.assertEqual(manifest.file_counts["python_defs"], 1)
            self.assertEqual(manifest.file_counts["cpp_headers"], 1)
            self.assertEqual(manifest.file_counts["docs"], 1)
            self.assertEqual(manifest.file_counts["processed_docs"], 1)

    def test_missing_required_path_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "FusionAPIReference"
            root.mkdir()

            with self.assertRaises(CorpusError) as ctx:
                discover_corpus(root)

            self.assertIn("missing required paths", str(ctx.exception))

    def test_lockfile_uses_stable_non_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "FusionAPIReference"
            (root / "Fusion_API_Python_Reference" / "defs").mkdir(parents=True)
            (root / "Fusion_API_CPP_Reference" / "include").mkdir(parents=True)
            (root / "Fusion_API_Documentation" / "files").mkdir(parents=True)

            manifest = discover_corpus(root)
            lockfile = Path(tmp_dir) / "corpus.lock.json"
            write_corpus_lockfile(manifest, lockfile)
            payload = json.loads(lockfile.read_text(encoding="utf-8"))

            self.assertEqual(payload["source_root"], "<external>")
            self.assertEqual(payload["required_paths"]["python_defs"], "Fusion_API_Python_Reference/defs")
            self.assertEqual(payload["required_paths"]["cpp_headers"], "Fusion_API_CPP_Reference/include")
            self.assertEqual(payload["required_paths"]["docs"], "Fusion_API_Documentation/files")
            self.assertNotIn(tmp_dir, lockfile.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
