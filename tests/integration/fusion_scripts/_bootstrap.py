from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys


def repo_root(anchor: str | Path | None = None) -> Path:
    override = os.environ.get("FUSION_SPARSE_REPO")
    if override:
        root = Path(override).expanduser().resolve()
        if (root / "pyproject.toml").exists():
            return root
        raise RuntimeError(f"FUSION_SPARSE_REPO does not point at a FusionSparse repo: {root}")

    start = Path(anchor).resolve() if anchor else Path(__file__).resolve()
    for parent in (start, *start.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not locate the FusionSparse repo root from the current script path.")


def ensure_repo_on_path(anchor: str | Path | None = None) -> Path:
    root = repo_root(anchor)
    for path in (root, root / "src"):
        rendered = str(path)
        if rendered not in sys.path:
            sys.path.insert(0, rendered)
    return root


def load_fusion_sparse(anchor: str | Path | None = None):
    root = ensure_repo_on_path(anchor)
    return importlib.import_module("fusion_sparse"), root


def class_label(value) -> str:
    for attr_name in ("class_type", "object_type"):
        candidate = getattr(value, attr_name, None)
        if isinstance(candidate, str) and candidate:
            return candidate
    raw = getattr(value, "raw", None)
    for attr_name in ("classType", "objectType"):
        getter = getattr(raw, attr_name, None)
        if callable(getter):
            try:
                candidate = getter()
            except Exception:
                continue
            if isinstance(candidate, str) and candidate:
                return candidate
    return type(value).__name__
