from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


SCRIPT_BUNDLE_NAME = "FusionSparseSmoke"
ADDIN_BUNDLE_NAME = "FusionSparseWorkbench"
IGNORED_NAMES = {".DS_Store", "__pycache__"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def sync_to_fusion(
    repo_root: str | Path | None = None,
    *,
    api_root: str | Path | None = None,
    scripts_dir: str | Path | None = None,
    addins_dir: str | Path | None = None,
    mode: str = "link",
    sync_smoke: bool = True,
    sync_workbench: bool = True,
) -> dict[str, object]:
    if mode not in {"copy", "link"}:
        raise RuntimeError(f"Unsupported sync mode: {mode}")
    if not sync_smoke and not sync_workbench:
        raise RuntimeError("sync_to_fusion requires at least one of sync_smoke or sync_workbench.")

    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent
    resolved_api_root = _resolve_api_root(api_root)
    resolved_scripts_dir = Path(scripts_dir).expanduser().resolve() if scripts_dir else resolved_api_root / "Scripts"
    resolved_addins_dir = Path(addins_dir).expanduser().resolve() if addins_dir else resolved_api_root / "AddIns"

    synced = []
    if sync_smoke:
        synced.append(
            _sync_bundle(
                repo_root=root,
                source_bundle=root / "fusion" / "scripts" / SCRIPT_BUNDLE_NAME,
                target_root=resolved_scripts_dir,
                bundle_name=SCRIPT_BUNDLE_NAME,
                mode=mode,
            )
        )
    if sync_workbench:
        synced.append(
            _sync_bundle(
                repo_root=root,
                source_bundle=root / "fusion" / "addins" / ADDIN_BUNDLE_NAME,
                target_root=resolved_addins_dir,
                bundle_name=ADDIN_BUNDLE_NAME,
                mode=mode,
            )
        )

    return {
        "api_root": str(resolved_api_root),
        "scripts_dir": str(resolved_scripts_dir),
        "addins_dir": str(resolved_addins_dir),
        "mode": mode,
        "synced": synced,
    }


def _sync_bundle(
    *,
    repo_root: Path,
    source_bundle: Path,
    target_root: Path,
    bundle_name: str,
    mode: str,
) -> dict[str, object]:
    if not source_bundle.exists():
        raise RuntimeError(f"Bundle source does not exist: {source_bundle}")

    _stage_bundle_libs(repo_root, source_bundle)
    target_root.mkdir(parents=True, exist_ok=True)
    target_bundle = target_root / bundle_name
    _remove_path(target_bundle)
    if mode == "link":
        target_bundle.symlink_to(source_bundle, target_is_directory=True)
    else:
        _copy_tree(source_bundle, target_bundle)
    return {
        "bundle": bundle_name,
        "source_bundle": str(source_bundle),
        "target_bundle": str(target_bundle),
        "mode": mode,
    }


def _stage_bundle_libs(repo_root: Path, bundle_root: Path) -> None:
    lib_root = bundle_root / "lib"
    lib_root.mkdir(parents=True, exist_ok=True)
    _sync_package(repo_root / "src" / "fusion_sparse", lib_root / "fusion_sparse")
    _sync_package(repo_root / "fusion" / "harness", lib_root / "fusion_harness")


def _sync_package(source: Path, destination: Path) -> None:
    if not source.exists():
        raise RuntimeError(f"Sync source does not exist: {source}")
    _remove_path(destination)
    _copy_tree(source, destination)


def _copy_tree(source: Path, destination: Path) -> None:
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return
    destination.mkdir(parents=True, exist_ok=True)
    for child in sorted(source.iterdir(), key=lambda path: path.name):
        if _should_skip(child):
            continue
        target = destination / child.name
        if child.is_dir():
            _copy_tree(child, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def _should_skip(path: Path) -> bool:
    return path.name in IGNORED_NAMES or path.suffix in IGNORED_SUFFIXES


def _remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)


def _resolve_api_root(value: str | Path | None) -> Path:
    if value is not None:
        return Path(value).expanduser().resolve()
    for env_name in ("FUSION_SPARSE_FUSION_API", "FUSION_API_ROOT"):
        env_value = os.environ.get(env_name)
        if env_value:
            return Path(env_value).expanduser().resolve()
    default = _default_api_root()
    if default is None:
        raise RuntimeError("Could not determine the Fusion API directory. Pass --api-root explicitly.")
    return default


def _default_api_root() -> Path | None:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Autodesk" / "Autodesk Fusion 360" / "API"
    if sys.platform.startswith("win"):
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "Autodesk" / "Autodesk Fusion 360" / "API"
    return None
