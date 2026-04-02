from __future__ import annotations

from pathlib import Path
import sys
import traceback

import adsk.core

import config


_BUNDLE_ROOT = Path(__file__).resolve().parents[2]
_LIB_ROOT = _BUNDLE_ROOT / "lib"
for _path in (_BUNDLE_ROOT, _LIB_ROOT):
    _rendered = str(_path)
    if _rendered not in sys.path:
        sys.path.insert(0, _rendered)


_handlers = []
_command_definition = None
_toolbar_control = None


def start() -> None:
    global _command_definition, _toolbar_control

    app = adsk.core.Application.get()
    ui = getattr(app, "userInterface", None)
    if ui is None:
        raise RuntimeError("Fusion userInterface is not available.")

    command_definitions = ui.commandDefinitions
    command_definition = command_definitions.itemById(config.COMMAND_ID)
    if command_definition is None:
        command_definition = command_definitions.addButtonDefinition(
            config.COMMAND_ID,
            config.COMMAND_NAME,
            config.COMMAND_TOOLTIP,
            "",
        )
    on_created = _CommandCreatedHandler()
    command_definition.commandCreated.add(on_created)
    _handlers.append(on_created)
    _command_definition = command_definition

    panel = ui.allToolbarPanels.itemById(config.PANEL_ID)
    if panel is not None:
        control = panel.controls.itemById(config.COMMAND_ID)
        if control is None:
            control = panel.controls.addCommand(command_definition)
        _toolbar_control = control


def stop() -> None:
    global _command_definition, _toolbar_control

    if _toolbar_control is not None:
        _toolbar_control.deleteMe()
        _toolbar_control = None
    if _command_definition is not None:
        _command_definition.deleteMe()
        _command_definition = None
    _handlers.clear()


class _CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        on_execute = _CommandExecuteHandler()
        args.command.execute.add(on_execute)
        _handlers.append(on_execute)


class _CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        app = adsk.core.Application.get()
        ui = getattr(app, "userInterface", None)
        try:
            from fusion_harness import format_summary, run_all

            summary = run_all()
            text = format_summary(summary)
            if ui is not None and hasattr(ui, "messageBox"):
                ui.messageBox(text)
            app.log(text)
            if not summary["ok"]:
                raise RuntimeError(text)
        except Exception:
            detail = traceback.format_exc()
            if ui is not None and hasattr(ui, "messageBox"):
                ui.messageBox(detail)
            app.log(detail)
            raise
