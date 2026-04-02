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


def run(context):
    _ensure_bundle_on_path()
    from commands.smoke_command import entry as smoke_command

    smoke_command.start()


def stop(context):
    _ensure_bundle_on_path()
    from commands.smoke_command import entry as smoke_command

    smoke_command.stop()
