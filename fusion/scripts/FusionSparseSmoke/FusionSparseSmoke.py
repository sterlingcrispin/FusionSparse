from __future__ import annotations

from pathlib import Path
import sys


def _bundle_root() -> Path:
    return Path(__file__).resolve().parent


def _ensure_bundle_on_path() -> None:
    bundle_root = _bundle_root()
    for path in (bundle_root, bundle_root / "lib"):
        rendered = str(path)
        if rendered not in sys.path:
            sys.path.insert(0, rendered)


def _report(text: str) -> None:
    import adsk.core

    app = adsk.core.Application.get()
    ui = getattr(app, "userInterface", None)
    if ui is not None and hasattr(ui, "messageBox"):
        ui.messageBox(text)
    print(text)


def run(context):
    _ensure_bundle_on_path()
    from fusion_harness import format_summary, run_all

    summary = run_all(context)
    text = format_summary(summary)
    _report(text)
    if not summary["ok"]:
        raise RuntimeError(text)
