from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any
from urllib import request

from tools.code_metrics import FileMetrics, add_metrics, measure_file, metrics_dict, reduction_dict, zero_metrics
from tools.generate_sample_pairs import generate_sample_pairs

SAMPLE_MARKER_GROUP = "FusionSparseSamplePairs"
SAMPLE_MARKER_NAME = "owned"


@dataclass(frozen=True)
class PairVariantResult:
    signature: dict[str, object]
    screenshot_path: str
    script_path: str
    metrics: dict[str, int]


def run_sample_pairs(
    repo_root: str | Path | None = None,
    *,
    manifest_path: str | Path | None = None,
    mcp_url: str = "http://localhost:9100/",
    output_root: str | Path | None = None,
) -> dict[str, object]:
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent
    generated = None
    if manifest_path:
        manifest = Path(manifest_path).resolve()
    else:
        generated = generate_sample_pairs(repo_root=root)
        manifest = Path(generated["manifest_path"]).resolve()
    output_dir = Path(output_root).resolve() if output_root else root / "build" / "reports" / "sample_pairs"
    pairs = json.loads(manifest.read_text(encoding="utf-8"))

    results = []
    official_total = zero_metrics()
    compact_total = zero_metrics()
    for pair in pairs:
        pair_dir = output_dir / pair["id"]
        pair_dir.mkdir(parents=True, exist_ok=True)
        official = _run_variant(root, mcp_url, pair, "official", pair_dir)
        compact = _run_variant(root, mcp_url, pair, "compact", pair_dir)
        official_total = add_metrics(official_total, measure_file(official.script_path))
        compact_total = add_metrics(compact_total, measure_file(compact.script_path))
        equivalent = official.signature == compact.signature
        result = {
            "id": pair["id"],
            "title": pair["title"],
            "source_page": pair["source_page"],
            "equivalent": equivalent,
            "official": {
                "script_path": official.script_path,
                "metrics": official.metrics,
                "signature": official.signature,
                "screenshot_path": official.screenshot_path,
            },
            "compact": {
                "script_path": compact.script_path,
                "metrics": compact.metrics,
                "signature": compact.signature,
                "screenshot_path": compact.screenshot_path,
            },
            "reduction": reduction_dict(
                _metrics_from_dict(official.metrics),
                _metrics_from_dict(compact.metrics),
            ),
        }
        (pair_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        results.append(result)

    report_path = output_dir / "sample_pairs_report.md"
    report_path.write_text(_render_report(results, official_total, compact_total), encoding="utf-8")
    return {
        "pair_count": len(results),
        "equivalent_count": sum(1 for item in results if item["equivalent"]),
        "official_totals": metrics_dict(official_total),
        "compact_totals": metrics_dict(compact_total),
        "reduction_totals": reduction_dict(official_total, compact_total),
        "report_path": str(report_path),
        "manifest_path": str(manifest),
        "generated": generated,
        "results": results,
    }


def _run_variant(root: Path, mcp_url: str, pair: dict[str, object], variant: str, pair_dir: Path) -> PairVariantResult:
    _close_owned_active_doc(mcp_url)
    time.sleep(0.5)
    script_path = root / pair[f"{variant}_script"]
    script = _bootstrap_script(root) + script_path.read_text(encoding="utf-8")
    signature = _execute_script(mcp_url, script)
    screenshot_path = pair_dir / f"{variant}.png"
    _save_screenshot(mcp_url, screenshot_path, view=pair.get("view", "iso-top-right"))
    _close_owned_active_doc(mcp_url)
    time.sleep(0.25)
    return PairVariantResult(
        signature=signature,
        screenshot_path=str(screenshot_path),
        script_path=str(script_path),
        metrics=metrics_dict(measure_file(script_path)),
    )


def _bootstrap_script(root: Path) -> str:
    repo = str(root)
    src = str(root / "src")
    return (
        "import sys\n"
        "for prefix in ('fusion_sparse', 'tests.integration.sample_pairs'):\n"
        "    for name in [module_name for module_name in list(sys.modules) if module_name == prefix or module_name.startswith(prefix + '.')]:\n"
        "        del sys.modules[name]\n"
        f"for path in ({repo!r}, {src!r}):\n"
        "    if path not in sys.path:\n"
        "        sys.path.insert(0, path)\n\n"
        "from tests.integration.sample_pairs import common as _fusion_sparse_sample_pairs_common\n"
        "_fusion_sparse_original_print_design_signature = _fusion_sparse_sample_pairs_common.print_design_signature\n"
        f"_FUSION_SPARSE_SAMPLE_MARKER_GROUP = {SAMPLE_MARKER_GROUP!r}\n"
        f"_FUSION_SPARSE_SAMPLE_MARKER_NAME = {SAMPLE_MARKER_NAME!r}\n"
        "def _fusion_sparse_mark_sample_design(design):\n"
        "    attributes = getattr(design, 'attributes', None)\n"
        "    if attributes is not None:\n"
        "        attributes.add(_FUSION_SPARSE_SAMPLE_MARKER_GROUP, _FUSION_SPARSE_SAMPLE_MARKER_NAME, '1')\n"
        "    _fusion_sparse_original_print_design_signature(design)\n"
        "_fusion_sparse_sample_pairs_common.print_design_signature = _fusion_sparse_mark_sample_design\n\n"
    )


def _execute_script(mcp_url: str, script: str) -> dict[str, object]:
    payload = _call_tool(mcp_url, "execute_api_script", {"script": script})
    text_parts = [item["text"] for item in payload.get("content", []) if item.get("type") == "text"]
    if not text_parts:
        raise RuntimeError("Fusion MCP script execution returned no text output.")
    return json.loads(text_parts[-1])


def _save_screenshot(mcp_url: str, destination: Path, *, view: str) -> None:
    payload = _call_tool(mcp_url, "get_screenshot", {"view": view, "width": 1200, "height": 900})
    image = next((item for item in payload.get("content", []) if item.get("type") == "image"), None)
    if image is None:
        raise RuntimeError("Fusion MCP screenshot call returned no image payload.")
    destination.write_bytes(base64.b64decode(image["data"]))


def _close_owned_active_doc(mcp_url: str) -> None:
    script = f"""
import adsk.core
import adsk.fusion

def run(context):
    app = adsk.core.Application.get()
    docs = getattr(app, "documents", None)
    if docs is None:
        return
    current = getattr(app, "activeDocument", None)
    current_name = getattr(current, "name", None) if current is not None else None
    count = getattr(docs, "count", 0)
    for index in range(count - 1, -1, -1):
        doc = docs.item(index)
        if getattr(doc, "name", None) != "Untitled" or getattr(doc, "isSaved", None) is not False:
            continue
        try:
            doc.activate()
        except Exception:
            continue
        design = adsk.fusion.Design.cast(getattr(app, "activeProduct", None))
        if design is None:
            continue
        attributes = getattr(design, "attributes", None)
        if attributes is None:
            continue
        marker = attributes.itemByName({SAMPLE_MARKER_GROUP!r}, {SAMPLE_MARKER_NAME!r})
        if marker is not None:
            doc.close(False)
    if current_name is None:
        return
    refreshed = getattr(app, "activeDocument", None)
    if refreshed is not None and getattr(refreshed, "name", None) == current_name:
        return
    count = getattr(docs, "count", 0)
    for index in range(count - 1, -1, -1):
        doc = docs.item(index)
        if getattr(doc, "name", None) == current_name:
            try:
                doc.activate()
            except Exception:
                pass
            return
"""
    _call_tool(mcp_url, "execute_api_script", {"script": script})


def _call_tool(mcp_url: str, name: str, arguments: dict[str, Any]) -> dict[str, object]:
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }
    ).encode("utf-8")
    req = request.Request(mcp_url, data=body, headers={"Content-Type": "application/json"})
    with request.urlopen(req) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload.get("result", {})
    if result.get("isError"):
        text = "\n".join(item.get("text", "") for item in result.get("content", []) if item.get("type") == "text")
        raise RuntimeError(text or result.get("message") or f"Fusion MCP tool call failed: {name}")
    return result


def _render_report(results: list[dict[str, object]], official_total, compact_total) -> str:
    total_reduction = reduction_dict(official_total, compact_total)
    lines = [
        "# Sample Pair Report",
        "",
        "Comparison between normalized Autodesk sample scripts and FusionSparse translations executed through Fusion MCP.",
        "",
        "## Totals",
        "",
        "| Metric | Official | Compact | Reduction |",
        "| --- | ---: | ---: | ---: |",
        f"| Characters | `{official_total.chars}` | `{compact_total.chars}` | `{total_reduction['chars_pct']:.1f}%` |",
        f"| Lines | `{official_total.lines}` | `{compact_total.lines}` | `{total_reduction['lines_pct']:.1f}%` |",
        f"| Tokens | `{official_total.tokens}` | `{compact_total.tokens}` | `{total_reduction['tokens_pct']:.1f}%` |",
        f"| `adsk.` refs | `{official_total.adsk_refs}` | `{compact_total.adsk_refs}` | `{total_reduction['adsk_refs_pct']:.1f}%` |",
        "",
    ]
    for result in results:
        lines.append(f"## {result['title']}")
        lines.append("")
        lines.append(f"- Source page: `{result['source_page']}`")
        lines.append(f"- Equivalent signature: `{result['equivalent']}`")
        lines.append(
            f"- Size reduction: `{result['reduction']['chars_pct']:.1f}%` chars, "
            f"`{result['reduction']['tokens_pct']:.1f}%` tokens"
        )
        lines.append(f"- Official script: `{result['official']['script_path']}`")
        lines.append(f"- Compact script: `{result['compact']['script_path']}`")
        lines.append(f"- Official screenshot: `{result['official']['screenshot_path']}`")
        lines.append(f"- Compact screenshot: `{result['compact']['screenshot_path']}`")
        lines.append(
            f"- Official size: `{result['official']['metrics']['chars']}` chars, "
            f"`{result['official']['metrics']['lines']}` lines, "
            f"`{result['official']['metrics']['tokens']}` tokens"
        )
        lines.append(
            f"- Compact size: `{result['compact']['metrics']['chars']}` chars, "
            f"`{result['compact']['metrics']['lines']}` lines, "
            f"`{result['compact']['metrics']['tokens']}` tokens"
        )
        lines.append("- Official signature:")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(result["official"]["signature"], indent=2, sort_keys=True))
        lines.append("```")
        lines.append("")
        lines.append("- Compact signature:")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(result["compact"]["signature"], indent=2, sort_keys=True))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _metrics_from_dict(metrics: dict[str, int]):
    return FileMetrics(
        chars=metrics["chars"],
        lines=metrics["lines"],
        tokens=metrics["tokens"],
        adsk_refs=metrics["adsk_refs"],
    )
