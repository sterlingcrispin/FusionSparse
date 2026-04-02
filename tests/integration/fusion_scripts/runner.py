from __future__ import annotations

import importlib
import traceback

from tests.integration.fusion_scripts._bootstrap import ensure_repo_on_path


SMOKE_MODULES = [
    "smoke_context",
    "smoke_new_design",
    "smoke_sketch_extrude",
    "smoke_builder_extrude",
    "smoke_raw_escape_hatch",
]


def run_all(context=None) -> dict[str, object]:
    ensure_repo_on_path(__file__)
    results = []
    failures = []
    for module_name in SMOKE_MODULES:
        module = importlib.import_module(f"tests.integration.fusion_scripts.{module_name}")
        try:
            payload = module.run(context) or {}
            payload.setdefault("name", module_name)
            payload.setdefault("ok", True)
            results.append(payload)
        except Exception as exc:
            failures.append(
                {
                    "name": module_name,
                    "ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
    return {
        "ok": not failures,
        "results": results,
        "failures": failures,
    }


def format_summary(summary: dict[str, object]) -> str:
    lines = ["FusionSparse smoke results", ""]
    for result in summary["results"]:
        detail_parts = [f"{key}={value}" for key, value in sorted(result.items()) if key not in {"name", "ok"}]
        suffix = f": {', '.join(detail_parts)}" if detail_parts else ""
        lines.append(f"PASS {result['name']}{suffix}")
    for failure in summary["failures"]:
        lines.append(f"FAIL {failure['name']}: {failure['error']}")
    lines.extend(["", f"overall_ok={summary['ok']}"])
    return "\n".join(lines)
