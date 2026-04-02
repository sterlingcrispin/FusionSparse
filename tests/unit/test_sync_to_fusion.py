from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.sync_to_fusion import sync_to_fusion


class SyncToFusionTests(unittest.TestCase):
    def test_sync_to_fusion_copy_mode_stages_clean_bundle_libs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            self._seed_repo(root)
            scripts_dir = Path(tmp_dir) / "API" / "Scripts"
            addins_dir = Path(tmp_dir) / "API" / "AddIns"

            result = sync_to_fusion(
                repo_root=root,
                scripts_dir=scripts_dir,
                addins_dir=addins_dir,
                mode="copy",
            )

            self.assertEqual(result["mode"], "copy")
            self.assertTrue((scripts_dir / "FusionSparseSmoke" / "FusionSparseSmoke.py").exists())
            self.assertTrue((addins_dir / "FusionSparseWorkbench" / "FusionSparseWorkbench.py").exists())
            self.assertTrue((scripts_dir / "FusionSparseSmoke" / "lib" / "fusion_sparse" / "__init__.py").exists())
            self.assertTrue((addins_dir / "FusionSparseWorkbench" / "lib" / "fusion_harness" / "smoke_suite.py").exists())
            self.assertFalse((scripts_dir / "FusionSparseSmoke" / "lib" / "fusion_sparse" / "stale.py").exists())
            self.assertFalse((scripts_dir / "FusionSparseSmoke" / "lib" / "fusion_sparse" / "__pycache__").exists())
            self.assertFalse((addins_dir / "FusionSparseWorkbench" / "lib" / "fusion_sparse" / "bad.pyc").exists())

    def test_sync_to_fusion_link_mode_creates_bundle_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            self._seed_repo(root)
            scripts_dir = Path(tmp_dir) / "API" / "Scripts"
            addins_dir = Path(tmp_dir) / "API" / "AddIns"

            sync_to_fusion(
                repo_root=root,
                scripts_dir=scripts_dir,
                addins_dir=addins_dir,
                mode="link",
            )

            self.assertTrue((scripts_dir / "FusionSparseSmoke").is_symlink())
            self.assertTrue((addins_dir / "FusionSparseWorkbench").is_symlink())
            self.assertTrue((root / "fusion" / "scripts" / "FusionSparseSmoke" / "lib" / "fusion_sparse" / "__init__.py").exists())
            self.assertTrue((root / "fusion" / "addins" / "FusionSparseWorkbench" / "lib" / "fusion_harness" / "__init__.py").exists())

    def _seed_repo(self, root: Path) -> None:
        (root / "src" / "fusion_sparse").mkdir(parents=True)
        (root / "src" / "fusion_sparse" / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "src" / "fusion_sparse" / "bad.pyc").write_bytes(b"pyc")
        (root / "src" / "fusion_sparse" / "__pycache__").mkdir()
        (root / "src" / "fusion_sparse" / "__pycache__" / "ignored.pyc").write_bytes(b"pyc")

        (root / "fusion" / "harness").mkdir(parents=True)
        (root / "fusion" / "harness" / "__init__.py").write_text("from .smoke_suite import run_all\n", encoding="utf-8")
        (root / "fusion" / "harness" / "smoke_suite.py").write_text("def run_all(context=None):\n    return {'ok': True}\n", encoding="utf-8")

        (root / "fusion" / "scripts" / "FusionSparseSmoke").mkdir(parents=True)
        (root / "fusion" / "scripts" / "FusionSparseSmoke" / "FusionSparseSmoke.py").write_text("print('smoke')\n", encoding="utf-8")
        (root / "fusion" / "scripts" / "FusionSparseSmoke" / "FusionSparseSmoke.manifest").write_text("{}", encoding="utf-8")
        (root / "fusion" / "scripts" / "FusionSparseSmoke" / "lib" / "fusion_sparse").mkdir(parents=True)
        (root / "fusion" / "scripts" / "FusionSparseSmoke" / "lib" / "fusion_sparse" / "stale.py").write_text("stale\n", encoding="utf-8")

        (root / "fusion" / "addins" / "FusionSparseWorkbench" / "commands" / "smoke_command").mkdir(parents=True)
        (root / "fusion" / "addins" / "FusionSparseWorkbench" / "FusionSparseWorkbench.py").write_text("print('addin')\n", encoding="utf-8")
        (root / "fusion" / "addins" / "FusionSparseWorkbench" / "FusionSparseWorkbench.manifest").write_text("{}", encoding="utf-8")
        (root / "fusion" / "addins" / "FusionSparseWorkbench" / "config.py").write_text("ADDIN_ID = 'x'\n", encoding="utf-8")
        (root / "fusion" / "addins" / "FusionSparseWorkbench" / "commands" / "__init__.py").write_text("", encoding="utf-8")
        (root / "fusion" / "addins" / "FusionSparseWorkbench" / "commands" / "smoke_command" / "__init__.py").write_text("", encoding="utf-8")
        (root / "fusion" / "addins" / "FusionSparseWorkbench" / "commands" / "smoke_command" / "entry.py").write_text(
            "def start():\n    return None\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
