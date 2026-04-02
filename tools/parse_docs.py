from __future__ import annotations

from collections import Counter, OrderedDict
import html
import json
from pathlib import Path
import re


META_RE = re.compile(r'<meta\s+name="([^"]+)"\s+content="([^"]*)"', re.IGNORECASE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
BODY_RE = re.compile(r"<body[^>]*>(.*?)</body>", re.IGNORECASE | re.DOTALL)
H1_RE = re.compile(r'<h1 class="api">(.*?)</h1>', re.IGNORECASE | re.DOTALL)
SECTION_RE = re.compile(
    r'<h2 class="api">\s*(.*?)\s*</h2>(.*?)(?=(<h2 class="api">|<div id="CopyrightNotice"|$))',
    re.IGNORECASE | re.DOTALL,
)
TABLE_RE = re.compile(r"<table[^>]*class=\"api-list\"[^>]*>(.*?)</table>", re.IGNORECASE | re.DOTALL)
TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
A_RE = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
PRE_RE = re.compile(r"<pre[^>]*?(?:id=\"([^\"]+)\")?[^>]*>(.*?)</pre>", re.IGNORECASE | re.DOTALL)
NAMESPACE_RE = re.compile(
    r'Defined in namespace "([^"]+)" and the header file is &lt;([^&]+)&gt;',
    re.IGNORECASE | re.DOTALL,
)
PARENT_RE = re.compile(r'Parent Object:\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
DERIVED_RE = re.compile(r'Derived from:\s*<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
SCRIPT_RE = re.compile(r"<script\b.*?</script>", re.IGNORECASE | re.DOTALL)
STYLE_RE = re.compile(r"<style\b.*?</style>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
DEFINED_SENTENCE_RE = re.compile(r'Defined in namespace\s+"[^"]+"\s+and the header file is\s+<[^>]+>', re.IGNORECASE)


def parse_docs(docs_root: str | Path) -> dict[str, list[dict[str, object]]]:
    root = Path(docs_root)
    pages: list[dict[str, object]] = []
    links: list[dict[str, object]] = []

    for path in sorted(_iter_doc_files(root)):
        page = parse_doc_page(path, root)
        pages.append(page)
        if page["symbol_id"]:
            links.append(
                {
                    "symbol_id": page["symbol_id"],
                    "symbol_key": page["symbol_key"],
                    "file_stem": page["file_stem"],
                    "source_path": page["source_path"],
                    "page_kind": page["page_kind"],
                    "title": page["title"],
                }
            )

    pages.sort(key=lambda item: (str(item["source_path"]), str(item["title"])))
    links.sort(key=lambda item: (str(item["symbol_id"]), str(item["file_stem"])))
    return {"pages": pages, "symbol_links": links}


def parse_doc_page(path: str | Path, docs_root: str | Path | None = None) -> dict[str, object]:
    page_path = Path(path)
    root = Path(docs_root) if docs_root else page_path.parent
    raw_html = page_path.read_text(encoding="utf-8", errors="ignore")
    body_html = _extract_body(raw_html)
    body_without_scripts = _strip_non_content(body_html)

    title = _clean_title(_extract_first(TITLE_RE, raw_html) or _extract_first(H1_RE, body_html) or page_path.stem)
    metadata = {name: value for name, value in META_RE.findall(raw_html)}
    namespace, header_file = _extract_namespace_and_header(raw_html)
    parent_object = _clean_title(_extract_first(PARENT_RE, body_html))
    derived_from = _clean_title(_extract_first(DERIVED_RE, body_html))
    page_kind = _infer_page_kind(page_path.stem, title)
    symbol_key = _infer_symbol_key(page_path.stem, title, page_kind, parent_object)
    symbol_id = f"{namespace.replace('::', '.')}.{symbol_key}" if namespace and symbol_key else None

    sections = _extract_sections(body_without_scripts)
    headings = list(sections.keys())
    section_text = OrderedDict((heading, _section_text(html_fragment)) for heading, html_fragment in sections.items())
    section_tables = OrderedDict(
        (heading, tables)
        for heading, tables in (
            (heading, _parse_tables(html_fragment))
            for heading, html_fragment in sections.items()
        )
        if tables
    )

    description = _remove_defined_sentence(section_text.get("Description"))
    parameters = _extract_named_rows(section_tables.get("Parameters", []))
    return_value = _extract_return_value(section_tables.get("Return Value", []))
    samples = _extract_samples(section_tables.get("Samples", []))
    code_blocks = _extract_code_blocks(body_without_scripts)
    related_links = _extract_related_links(body_without_scripts)

    return {
        "file_stem": page_path.stem,
        "source_path": str(page_path.relative_to(root)),
        "title": title,
        "page_kind": page_kind,
        "symbol_key": symbol_key,
        "symbol_id": symbol_id,
        "owner_object": parent_object,
        "derived_from": derived_from,
        "namespace": namespace,
        "header_file": header_file,
        "description": description,
        "remarks": section_text.get("Remarks"),
        "syntax": section_text.get("Syntax"),
        "parameters": parameters,
        "return_value": return_value,
        "samples": samples,
        "version": _extract_version(section_text.get("Version")),
        "headings": headings,
        "code_blocks": code_blocks,
        "related_links": related_links,
        "sections": section_text,
        "tables": section_tables,
        "meta": metadata,
    }


def write_doc_pages(pages: list[dict[str, object]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(pages, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def write_doc_symbol_links(symbol_links: list[dict[str, object]], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(symbol_links, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def write_doc_summary_report(
    pages: list[dict[str, object]],
    symbol_links: list[dict[str, object]],
    output_path: str | Path,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    kinds = Counter(page["page_kind"] for page in pages)
    namespaces = Counter(page["namespace"] for page in pages if page["namespace"])
    lines = [
        "# Doc Pages Summary",
        "",
        f"- Total pages: `{len(pages)}`",
        f"- Symbol-linked pages: `{len(symbol_links)}`",
        "",
        "## By page kind",
        "",
    ]
    for kind, count in sorted(kinds.items()):
        lines.append(f"- `{kind}`: `{count}`")

    lines.extend(["", "## Top namespaces", ""])
    for namespace, count in namespaces.most_common(10):
        lines.append(f"- `{namespace}`: `{count}`")

    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _iter_doc_files(root: Path):
    for path in root.rglob("*.htm"):
        parts = path.relative_to(root).parts
        if any(part.startswith(".") for part in parts):
            continue
        yield path
    for path in root.rglob("*.html"):
        parts = path.relative_to(root).parts
        if any(part.startswith(".") for part in parts):
            continue
        yield path


def _extract_body(raw_html: str) -> str:
    match = BODY_RE.search(raw_html)
    return match.group(1) if match else raw_html


def _strip_non_content(fragment: str) -> str:
    without_comments = COMMENT_RE.sub("", fragment)
    without_scripts = SCRIPT_RE.sub("", without_comments)
    return STYLE_RE.sub("", without_scripts)


def _extract_sections(body_html: str) -> OrderedDict[str, str]:
    sections: OrderedDict[str, str] = OrderedDict()
    for heading, section_html, _ in SECTION_RE.findall(body_html):
        normalized_heading = _normalize_whitespace(_html_to_text(heading))
        sections[normalized_heading] = section_html
    return sections


def _parse_tables(section_html: str) -> list[list[dict[str, str]]]:
    tables = []
    for table_html in TABLE_RE.findall(section_html):
        rows = []
        headers: list[str] | None = None
        for row_index, row_html in enumerate(TR_RE.findall(table_html)):
            cells = [_normalize_whitespace(_html_to_text(cell)) for cell in TD_RE.findall(row_html)]
            if not cells:
                continue
            if row_index == 0:
                headers = cells
                continue
            row = []
            for index, cell_text in enumerate(cells):
                key = headers[index] if headers and index < len(headers) and headers[index] else f"col_{index}"
                row.append({"key": key, "text": cell_text, "href": _first_local_href(TD_RE.findall(row_html)[index])})
            rows.append(row)
        if rows:
            tables.append(rows)
    return tables


def _extract_named_rows(tables: list[list[dict[str, str]]]) -> list[dict[str, object]]:
    if not tables:
        return []
    rows = []
    for row in tables[0]:
        mapped = {cell["key"]: cell["text"] for cell in row}
        hrefs = {cell["key"]: cell["href"] for cell in row if cell["href"]}
        if hrefs:
            mapped["_hrefs"] = hrefs
        rows.append(mapped)
    return rows


def _extract_return_value(tables: list[list[dict[str, str]]]) -> dict[str, object] | None:
    if not tables or not tables[0]:
        return None
    mapped = {cell["key"]: cell["text"] for cell in tables[0][0]}
    hrefs = {cell["key"]: cell["href"] for cell in tables[0][0] if cell["href"]}
    if hrefs:
        mapped["_hrefs"] = hrefs
    return mapped


def _extract_samples(tables: list[list[dict[str, str]]]) -> list[dict[str, object]]:
    if not tables:
        return []
    samples = []
    for row in tables[0]:
        mapped = {cell["key"]: cell["text"] for cell in row}
        href = None
        for cell in row:
            if cell["key"] == "Name":
                href = cell["href"]
                break
        samples.append(
            {
                "name": mapped.get("Name"),
                "description": mapped.get("Description"),
                "href": href,
                "file_stem": Path(href).stem if href else None,
            }
        )
    return samples


def _extract_code_blocks(body_html: str) -> list[dict[str, object]]:
    blocks = []
    for block_id, code_html in PRE_RE.findall(body_html):
        language = _language_hint(block_id, body_html, code_html)
        blocks.append(
            {
                "language_hint": language,
                "content": _html_to_code(code_html),
            }
        )
    return blocks


def _extract_related_links(body_html: str) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    links = []
    for href, text in A_RE.findall(body_html):
        if href.startswith(("mailto:", "javascript:", "#", "/")):
            continue
        if not href.lower().endswith((".htm", ".html")):
            continue
        normalized_text = _normalize_whitespace(_html_to_text(text))
        key = (href, normalized_text)
        if key in seen:
            continue
        seen.add(key)
        links.append({"href": href, "text": normalized_text, "file_stem": Path(href).stem})
    return links


def _extract_namespace_and_header(raw_html: str) -> tuple[str | None, str | None]:
    match = NAMESPACE_RE.search(raw_html)
    if not match:
        return None, None
    namespace, header_file = match.groups()
    return namespace, header_file.replace("\\", "/")


def _extract_version(version_text: str | None) -> str | None:
    if not version_text:
        return None
    match = re.search(r"Introduced in version\s+(.+)", version_text)
    return match.group(1).strip() if match else version_text.strip()


def _infer_page_kind(file_stem: str, title: str) -> str:
    if file_stem.endswith("_Sample") or "sample" in title.lower():
        return "sample"
    if title.endswith(" Method") or title.endswith(" Function"):
        return "method"
    if title.endswith(" Property"):
        return "property"
    if title.endswith(" Event"):
        return "event"
    if title.endswith(" Enumerator") or title.endswith(" Enum"):
        return "enum"
    if title.endswith(" Object"):
        return "object"
    return "user_manual_topic"


def _infer_symbol_key(file_stem: str, title: str, page_kind: str, parent_object: str | None) -> str | None:
    if page_kind == "sample" or page_kind == "user_manual_topic":
        return None
    if page_kind in {"method", "property", "event"}:
        if "_" in file_stem:
            owner, member = file_stem.split("_", 1)
            return f"{owner}.{member}"
        base = _strip_title_suffix(title, page_kind)
        return base if "." in base else f"{parent_object}.{base}" if parent_object else base
    if page_kind in {"object", "enum"}:
        return file_stem
    return None


def _strip_title_suffix(title: str, page_kind: str) -> str:
    suffix_map = {
        "method": " Method",
        "property": " Property",
        "event": " Event",
        "object": " Object",
        "enum": " Enumerator",
    }
    suffix = suffix_map.get(page_kind)
    if suffix and title.endswith(suffix):
        return title[: -len(suffix)]
    if page_kind == "enum" and title.endswith(" Enum"):
        return title[: -len(" Enum")]
    return title


def _language_hint(block_id: str | None, body_html: str, code_html: str) -> str | None:
    if block_id:
        if block_id.startswith("Python"):
            return "Python"
        if block_id.startswith("C++") or block_id.startswith("Cxx") or block_id.startswith("Cpp"):
            return "C++"
    snippet = code_html[:200]
    if "adsk.core" in snippet or "def run(" in snippet:
        return "Python"
    if "#include" in snippet or "->" in snippet:
        return "C++"
    if 'href="#Python"' in body_html:
        return "Python"
    if 'href="#C++"' in body_html:
        return "C++"
    return None


def _first_local_href(fragment: str) -> str | None:
    for href, _ in A_RE.findall(fragment):
        if href.lower().endswith((".htm", ".html")) and not href.startswith(("mailto:", "javascript:", "#", "/")):
            return href
    return None


def _remove_defined_sentence(text: str | None) -> str | None:
    if not text:
        return text
    cleaned = DEFINED_SENTENCE_RE.sub("", text).strip()
    return _normalize_whitespace(cleaned) if cleaned else None


def _section_text(section_html: str) -> str | None:
    text = _html_to_text(section_html)
    return _normalize_whitespace(text) if text else None


def _extract_first(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1) if match else None


def _html_to_text(fragment: str) -> str:
    prepared = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.IGNORECASE)
    prepared = re.sub(r"</p\s*>", "\n", prepared, flags=re.IGNORECASE)
    prepared = re.sub(r"</div\s*>", "\n", prepared, flags=re.IGNORECASE)
    prepared = TAG_RE.sub("", prepared)
    prepared = html.unescape(prepared)
    prepared = prepared.replace("\xa0", " ")
    return prepared


def _html_to_code(fragment: str) -> str:
    text = _html_to_text(fragment)
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _clean_title(value: str | None) -> str | None:
    if value is None:
        return None
    return _normalize_whitespace(_html_to_text(value))


def _normalize_whitespace(text: str | None) -> str | None:
    if text is None:
        return None
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()
