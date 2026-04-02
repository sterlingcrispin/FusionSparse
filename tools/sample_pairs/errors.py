from __future__ import annotations

from dataclasses import dataclass, field


class SampleConversionError(RuntimeError):
    """Raised when an Autodesk sample cannot be converted deterministically."""


@dataclass
class BuilderState:
    base_expr: str
    chain: list[str] = field(default_factory=list)

    def append(self, fragment: str) -> None:
        self.chain.append(fragment)

    def render(self) -> str:
        return self.base_expr + "".join(self.chain)
