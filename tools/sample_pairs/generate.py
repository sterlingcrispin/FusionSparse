from __future__ import annotations

import json
from pathlib import Path

from .official import resolve_official_script
from .rules import load_sample_pair_rules, path_for_manifest
from .translate import translate_official_script


def generate_sample_pairs(
    repo_root: str | Path | None = None,
    *,
    rules_path: str | Path | None = None,
    output_root: str | Path | None = None,
) -> dict[str, object]:
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[2]
    rules_file = Path(rules_path).resolve() if rules_path else root / "rules" / "sample_pairs.yaml"
    generated_root = Path(output_root).resolve() if output_root else root / "build" / "generated" / "sample_pairs"
    generated_root.mkdir(parents=True, exist_ok=True)

    rules = load_sample_pair_rules(rules_file)
    docs_root = root / "corpus" / "FusionAPIReference" / "Fusion_API_Documentation" / "files"
    official_dir = generated_root / "official"
    official_dir.mkdir(parents=True, exist_ok=True)
    compact_dir = generated_root / "compact"
    compact_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []
    generated_official_scripts: list[str] = []
    generated_scripts: list[str] = []
    for pair in rules["pairs"]:
        official_path = resolve_official_script(root, docs_root, official_dir, pair)
        if pair.get("official_generation") is not None:
            generated_official_scripts.append(str(official_path))
        compact_path = compact_dir / f"{pair['id']}.py"
        compact_source = translate_official_script(official_path.read_text(encoding="utf-8"), repo_root=root)
        compact_path.write_text(compact_source, encoding="utf-8")
        generated_scripts.append(str(compact_path))
        manifest.append(
            {
                "id": pair["id"],
                "title": pair["title"],
                "source_page": pair["source_page"],
                "official_script": path_for_manifest(root, official_path),
                "compact_script": path_for_manifest(root, compact_path),
                "view": pair.get("view", "iso-top-right"),
            }
        )

    manifest_path = generated_root / "pairs.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "pair_count": len(manifest),
        "manifest_path": str(manifest_path),
        "generated_official_scripts": generated_official_scripts,
        "generated_scripts": generated_scripts,
    }
