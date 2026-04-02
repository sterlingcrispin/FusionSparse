from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from pprint import pformat
import re
import shutil


IR_FILENAMES = {
    "symbols": "symbols.json",
    "enums": "enums.json",
    "doc_pages": "doc_pages.json",
    "families": "families.json",
    "corpus_lock": "corpus.lock.json",
}

MAX_PREVIEW_ITEMS = 40

RISK_PATTERNS = {
    "design intent changes": (
        r"designtype",
        r"timeline",
        r"snapshot",
        r"parametric",
        r"workingmodel",
        r"configuration",
        r"directmodel",
    ),
    "new design modes": (
        r"designtype",
        r"workingmodel",
        r"isconfigureddesign",
        r"isconfiguration",
        r"configuration",
        r"flatpattern",
    ),
    "new external component APIs": (
        r"externalcomponent",
        r"externalcomponents",
        r"externalreference",
        r"linkedcomponent",
        r"xref",
    ),
    "embedded Python version changes": (
        r"python",
        r"embedded python",
        r"3\.\d+",
    ),
}


@dataclass(frozen=True)
class IRState:
    symbols: list[dict[str, object]]
    enums: list[dict[str, object]]
    doc_pages: list[dict[str, object]]
    families: list[dict[str, object]]
    corpus_lock: dict[str, object]


def snapshot_ir(
    repo_root: str | Path | None = None,
    *,
    snapshot_name: str | None = None,
    source_ir_dir: str | Path | None = None,
    snapshot_root: str | Path | None = None,
) -> dict[str, object]:
    root = _repo_root(repo_root)
    ir_dir = Path(source_ir_dir).resolve() if source_ir_dir else root / "build" / "ir"
    destination_root = Path(snapshot_root).resolve() if snapshot_root else root / "snapshots"
    state = _load_current_state(root, ir_dir)
    name = snapshot_name or _default_snapshot_name(state.corpus_lock)
    snapshot_dir = destination_root / name
    if snapshot_dir.exists():
        raise RuntimeError(f"Snapshot already exists: {snapshot_dir}")

    snapshot_dir.mkdir(parents=True, exist_ok=False)
    copied = {}
    for key, filename in IR_FILENAMES.items():
        if key == "corpus_lock":
            src = root / "corpus" / filename
        else:
            src = ir_dir / filename
        dst = snapshot_dir / filename
        shutil.copyfile(src, dst)
        copied[key] = str(dst)

    manifest = {
        "name": name,
        "git_commit": state.corpus_lock.get("git_commit"),
        "generated_at": state.corpus_lock.get("generated_at"),
    }
    manifest_path = snapshot_dir / "snapshot.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "snapshot_name": name,
        "snapshot_dir": str(snapshot_dir),
        "manifest_path": str(manifest_path),
        "files": copied,
    }


def diff_ir(
    repo_root: str | Path | None = None,
    *,
    snapshot_name: str | None = None,
    snapshot_dir: str | Path | None = None,
    current_ir_dir: str | Path | None = None,
    snapshots_root: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, object]:
    root = _repo_root(repo_root)
    current_dir = Path(current_ir_dir).resolve() if current_ir_dir else root / "build" / "ir"
    previous_dir = _resolve_snapshot_dir(root, snapshot_name=snapshot_name, snapshot_dir=snapshot_dir, snapshots_root=snapshots_root)
    report_path = Path(output_path).resolve() if output_path else root / "build" / "reports" / "ir_diff.md"

    previous = _load_state_from_snapshot(root, previous_dir)
    current = _load_current_state(root, current_dir)

    symbols = _diff_symbols(previous.symbols, current.symbols)
    enums = _diff_enums(previous.enums, current.enums)
    doc_pages = _diff_doc_pages(previous.doc_pages, current.doc_pages)
    risks = _detect_risks(symbols, enums, doc_pages, previous.doc_pages, current.doc_pages)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_diff_report(
            previous_dir=previous_dir,
            previous=previous,
            current=current,
            symbol_diff=symbols,
            enum_diff=enums,
            doc_diff=doc_pages,
            risks=risks,
        ),
        encoding="utf-8",
    )

    return {
        "snapshot_dir": str(previous_dir),
        "report_path": str(report_path),
        "previous_git_commit": previous.corpus_lock.get("git_commit"),
        "current_git_commit": current.corpus_lock.get("git_commit"),
        "added_symbol_count": len(symbols["added"]),
        "removed_symbol_count": len(symbols["removed"]),
        "changed_signature_count": len(symbols["changed_signatures"]),
        "changed_enum_count": len(enums["changed"]),
        "new_doc_page_count": len(doc_pages["new"]),
        "risk_count": sum(len(item["matches"]) for item in risks),
    }


def _repo_root(repo_root: str | Path | None) -> Path:
    return Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent


def _default_snapshot_name(corpus_lock: dict[str, object]) -> str:
    generated_at = str(corpus_lock.get("generated_at") or "unknown").replace(":", "-")
    date_part = generated_at.split("T", 1)[0]
    commit = str(corpus_lock.get("git_commit") or "unknown")[:7]
    return f"{date_part}_{commit}"


def _resolve_snapshot_dir(
    root: Path,
    *,
    snapshot_name: str | None,
    snapshot_dir: str | Path | None,
    snapshots_root: str | Path | None,
) -> Path:
    if snapshot_dir is not None:
        directory = Path(snapshot_dir).resolve()
        if not directory.exists():
            raise RuntimeError(f"Snapshot directory does not exist: {directory}")
        return directory

    base = Path(snapshots_root).resolve() if snapshots_root else root / "snapshots"
    if snapshot_name is not None:
        directory = base / snapshot_name
        if not directory.exists():
            raise RuntimeError(f"Snapshot does not exist: {directory}")
        return directory

    candidates = sorted(path for path in base.iterdir() if path.is_dir()) if base.exists() else []
    if not candidates:
        raise RuntimeError(f"No snapshots found in {base}")
    return candidates[-1]


def _load_current_state(root: Path, ir_dir: Path) -> IRState:
    return IRState(
        symbols=_load_json(ir_dir / IR_FILENAMES["symbols"]),
        enums=_load_json(ir_dir / IR_FILENAMES["enums"]),
        doc_pages=_load_json(ir_dir / IR_FILENAMES["doc_pages"]),
        families=_load_json(ir_dir / IR_FILENAMES["families"]),
        corpus_lock=_load_json(root / "corpus" / IR_FILENAMES["corpus_lock"]),
    )


def _load_state_from_snapshot(root: Path, snapshot_dir: Path) -> IRState:
    return IRState(
        symbols=_load_json(snapshot_dir / IR_FILENAMES["symbols"]),
        enums=_load_json(snapshot_dir / IR_FILENAMES["enums"]),
        doc_pages=_load_json(snapshot_dir / IR_FILENAMES["doc_pages"]),
        families=_load_json(snapshot_dir / IR_FILENAMES["families"]),
        corpus_lock=_load_json(snapshot_dir / IR_FILENAMES["corpus_lock"]),
    )


def _load_json(path: Path):
    if not path.exists():
        raise RuntimeError(f"Required IR file is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _diff_symbols(previous: list[dict[str, object]], current: list[dict[str, object]]) -> dict[str, object]:
    previous_by_id = {item["id"]: item for item in previous}
    current_by_id = {item["id"]: item for item in current}
    previous_ids = set(previous_by_id)
    current_ids = set(current_by_id)

    added = sorted(current_ids - previous_ids)
    removed = sorted(previous_ids - current_ids)
    changed_signatures = []
    for symbol_id in sorted(previous_ids & current_ids):
        before = _normalize_signatures(previous_by_id[symbol_id].get("signatures", []))
        after = _normalize_signatures(current_by_id[symbol_id].get("signatures", []))
        if before != after:
            changed_signatures.append(
                {
                    "id": symbol_id,
                    "before": before,
                    "after": after,
                }
            )
    return {
        "added": added,
        "removed": removed,
        "changed_signatures": changed_signatures,
    }


def _normalize_signatures(signatures: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized = []
    for signature in signatures:
        params = []
        for param in signature.get("params", []):
            params.append(
                {
                    "name": param.get("name"),
                    "kind": param.get("kind"),
                    "type": param.get("type") or param.get("annotation"),
                    "default": param.get("default"),
                }
            )
        normalized.append(
            {
                "language": signature.get("language"),
                "params": params,
                "returns": signature.get("returns"),
                "static": bool(signature.get("static")),
                "classmethod": bool(signature.get("classmethod")),
                "property": bool(signature.get("property")),
            }
        )
    return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True))


def _diff_enums(previous: list[dict[str, object]], current: list[dict[str, object]]) -> dict[str, object]:
    previous_by_id = {item["id"]: item for item in previous}
    current_by_id = {item["id"]: item for item in current}
    changed = []
    for enum_id in sorted(set(previous_by_id) & set(current_by_id)):
        before_members = _normalize_enum_members(previous_by_id[enum_id].get("members", []))
        after_members = _normalize_enum_members(current_by_id[enum_id].get("members", []))
        if before_members != after_members:
            before_map = {item["name"]: item["value"] for item in before_members}
            after_map = {item["name"]: item["value"] for item in after_members}
            changed.append(
                {
                    "id": enum_id,
                    "added_members": sorted(name for name in after_map if name not in before_map),
                    "removed_members": sorted(name for name in before_map if name not in after_map),
                    "value_changes": [
                        {
                            "name": name,
                            "before": before_map[name],
                            "after": after_map[name],
                        }
                        for name in sorted(before_map.keys() & after_map.keys())
                        if before_map[name] != after_map[name]
                    ],
                }
            )
    return {"changed": changed}


def _normalize_enum_members(members: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized = [
        {
            "name": member.get("name"),
            "value": member.get("value"),
        }
        for member in members
    ]
    return sorted(normalized, key=lambda item: (str(item["name"]), str(item["value"])))


def _diff_doc_pages(previous: list[dict[str, object]], current: list[dict[str, object]]) -> dict[str, object]:
    previous_pages = {item["source_path"]: item for item in previous}
    current_pages = {item["source_path"]: item for item in current}
    new_paths = sorted(set(current_pages) - set(previous_pages))
    return {
        "new": [
            {
                "source_path": source_path,
                "title": current_pages[source_path].get("title"),
                "symbol_id": current_pages[source_path].get("symbol_id"),
            }
            for source_path in new_paths
        ]
    }


def _detect_risks(
    symbol_diff: dict[str, object],
    enum_diff: dict[str, object],
    doc_diff: dict[str, object],
    previous_doc_pages: list[dict[str, object]],
    current_doc_pages: list[dict[str, object]],
) -> list[dict[str, object]]:
    previous_docs = {item["source_path"]: item for item in previous_doc_pages}
    current_docs = {item["source_path"]: item for item in current_doc_pages}

    change_strings = []
    for symbol_id in symbol_diff["added"]:
        change_strings.append(("symbol", symbol_id, symbol_id))
    for symbol_id in symbol_diff["removed"]:
        change_strings.append(("symbol", symbol_id, symbol_id))
    for item in symbol_diff["changed_signatures"]:
        change_strings.append(("signature", item["id"], item["id"]))
    for item in enum_diff["changed"]:
        change_strings.append(("enum", item["id"], item["id"]))
    for page in doc_diff["new"]:
        text = " ".join(
            part
            for part in (page["source_path"], page.get("title"), page.get("symbol_id"))
            if part
        )
        change_strings.append(("doc_page", page["source_path"], text))
    for source_path, page in current_docs.items():
        if source_path in previous_docs:
            continue
        text = " ".join(
            part
            for part in (source_path, page.get("title"), page.get("description"))
            if isinstance(part, str)
        )
        change_strings.append(("doc_page_full", source_path, text))

    risk_entries = []
    for label, patterns in RISK_PATTERNS.items():
        regex = re.compile("|".join(patterns), re.IGNORECASE)
        matches = []
        for item_type, item_id, text in change_strings:
            if regex.search(text):
                matches.append({"type": item_type, "id": item_id})
        deduped = []
        seen = set()
        for match in matches:
            key = (match["type"], match["id"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(match)
        risk_entries.append({"label": label, "matches": deduped})
    return risk_entries


def _render_diff_report(
    *,
    previous_dir: Path,
    previous: IRState,
    current: IRState,
    symbol_diff: dict[str, object],
    enum_diff: dict[str, object],
    doc_diff: dict[str, object],
    risks: list[dict[str, object]],
) -> str:
    lines = [
        "# IR Diff Report",
        "",
        "Deterministic comparison between a previous IR snapshot and the current build output.",
        "",
        "## Compare",
        "",
        f"- Previous snapshot: `{previous_dir}`",
        f"- Previous corpus commit: `{previous.corpus_lock.get('git_commit')}`",
        f"- Previous generated at: `{previous.corpus_lock.get('generated_at')}`",
        f"- Current corpus commit: `{current.corpus_lock.get('git_commit')}`",
        f"- Current generated at: `{current.corpus_lock.get('generated_at')}`",
        "",
        "## Counts",
        "",
        f"- Added symbols: `{len(symbol_diff['added'])}`",
        f"- Removed symbols: `{len(symbol_diff['removed'])}`",
        f"- Changed signatures: `{len(symbol_diff['changed_signatures'])}`",
        f"- Changed enums: `{len(enum_diff['changed'])}`",
        f"- New doc pages: `{len(doc_diff['new'])}`",
        "",
        "## Release Risk Summary",
        "",
    ]
    for risk in risks:
        matches = risk["matches"]
        if matches:
            rendered = ", ".join(f"`{item['id']}`" for item in matches[:10])
            suffix = "" if len(matches) <= 10 else f" and `{len(matches) - 10}` more"
            lines.append(f"- {risk['label']}: `{len(matches)}` match(es) -> {rendered}{suffix}")
        else:
            lines.append(f"- {risk['label']}: none detected")

    lines.extend(["", "## Added Symbols", ""])
    lines.extend(_render_simple_list(symbol_diff["added"]))
    lines.extend(["", "## Removed Symbols", ""])
    lines.extend(_render_simple_list(symbol_diff["removed"]))
    lines.extend(["", "## Changed Signatures", ""])
    lines.extend(_render_signature_changes(symbol_diff["changed_signatures"]))
    lines.extend(["", "## Changed Enums", ""])
    lines.extend(_render_enum_changes(enum_diff["changed"]))
    lines.extend(["", "## New Doc Pages", ""])
    lines.extend(_render_doc_changes(doc_diff["new"]))
    lines.append("")
    return "\n".join(lines)


def _render_simple_list(items: list[str]) -> list[str]:
    if not items:
        return ["No entries."]
    rendered = [f"- `{item}`" for item in items[:MAX_PREVIEW_ITEMS]]
    if len(items) > MAX_PREVIEW_ITEMS:
        rendered.append(f"- ... `{len(items) - MAX_PREVIEW_ITEMS}` more")
    return rendered


def _render_signature_changes(items: list[dict[str, object]]) -> list[str]:
    if not items:
        return ["No signature changes."]
    rendered = []
    for item in items[:MAX_PREVIEW_ITEMS]:
        before = pformat(item["before"], width=80, compact=True, sort_dicts=True)
        after = pformat(item["after"], width=80, compact=True, sort_dicts=True)
        rendered.append(f"- `{item['id']}`")
        rendered.append(f"  before: `{before}`")
        rendered.append(f"  after: `{after}`")
    if len(items) > MAX_PREVIEW_ITEMS:
        rendered.append(f"- ... `{len(items) - MAX_PREVIEW_ITEMS}` more")
    return rendered


def _render_enum_changes(items: list[dict[str, object]]) -> list[str]:
    if not items:
        return ["No enum changes."]
    rendered = []
    for item in items[:MAX_PREVIEW_ITEMS]:
        parts = []
        if item["added_members"]:
            parts.append(f"added={item['added_members']}")
        if item["removed_members"]:
            parts.append(f"removed={item['removed_members']}")
        if item["value_changes"]:
            parts.append(f"value_changes={item['value_changes']}")
        details = ", ".join(parts) if parts else "structure changed"
        rendered.append(f"- `{item['id']}`: {details}")
    if len(items) > MAX_PREVIEW_ITEMS:
        rendered.append(f"- ... `{len(items) - MAX_PREVIEW_ITEMS}` more")
    return rendered


def _render_doc_changes(items: list[dict[str, object]]) -> list[str]:
    if not items:
        return ["No new doc pages."]
    rendered = []
    for item in items[:MAX_PREVIEW_ITEMS]:
        title = item.get("title") or "untitled"
        symbol = item.get("symbol_id") or "unlinked"
        rendered.append(f"- `{item['source_path']}` -> `{title}` (`{symbol}`)")
    if len(items) > MAX_PREVIEW_ITEMS:
        rendered.append(f"- ... `{len(items) - MAX_PREVIEW_ITEMS}` more")
    return rendered
