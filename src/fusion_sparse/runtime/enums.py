"""Compact enum aliases backed by generated metadata."""

from __future__ import annotations

from fusion_sparse.generated.enum_index import ENUM_ALIASES_BY_NAME, ENUM_NAME_TO_MODULE
from fusion_sparse.runtime._adsk import import_adsk_module


class EnumNamespace:
    def __init__(self, enum_name: str):
        self._enum_name = enum_name

    def __getattr__(self, name: str):
        try:
            member_name = ENUM_ALIASES_BY_NAME[self._enum_name][name]
        except KeyError as exc:
            raise AttributeError(name) from exc
        module_name = ENUM_NAME_TO_MODULE[self._enum_name]
        module = import_adsk_module(module_name)
        enum_type = getattr(module, self._enum_name)
        return getattr(enum_type, member_name)

    def __dir__(self):
        return sorted(ENUM_ALIASES_BY_NAME.get(self._enum_name, {}))


op = EnumNamespace("FeatureOperations")

dir = EnumNamespace("ExtentDirections")

hole_pos = EnumNamespace("HoleEdgePositions")

pattern_dist = EnumNamespace("PatternDistanceType")

sweep_scale = EnumNamespace("SweepProfileScalingOptions")

loft_align = EnumNamespace("LoftEdgeAlignments")

shell_type = EnumNamespace("ShellTypes")
