from __future__ import annotations

from pathlib import Path

from tools.corpus_loader import CorpusManifest, discover_corpus, write_corpus_lockfile, write_corpus_summary_report
from tools.merge_ir import merge_sources, write_enums, write_families, write_merge_conflicts, write_symbols
from tools.parse_cpp_headers import parse_cpp_headers, write_cpp_enums, write_cpp_summary_report, write_cpp_symbols
from tools.parse_docs import parse_docs, write_doc_pages, write_doc_summary_report, write_doc_symbol_links
from tools.parse_python_defs import parse_python_defs, write_python_summary_report, write_python_symbols


def build_ir(repo_root: str | Path | None = None, corpus_root: str | Path | None = None) -> dict[str, object]:
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent
    manifest: CorpusManifest = discover_corpus(corpus_root=corpus_root, root=root)

    lockfile_path = write_corpus_lockfile(manifest, root / "corpus" / "corpus.lock.json")
    corpus_report_path = write_corpus_summary_report(manifest, root / "build" / "reports" / "corpus_summary.md")

    symbols = parse_python_defs(Path(manifest.required_paths["python_defs"]))
    python_symbols_path = write_python_symbols(symbols, root / "build" / "ir" / "python_symbols.json")
    python_report_path = write_python_summary_report(symbols, root / "build" / "reports" / "python_symbols_summary.md")

    cpp_parsed = parse_cpp_headers(Path(manifest.required_paths["cpp_headers"]))
    cpp_symbols_path = write_cpp_symbols(cpp_parsed["symbols"], root / "build" / "ir" / "cpp_symbols.json")
    cpp_enums_path = write_cpp_enums(cpp_parsed["enums"], root / "build" / "ir" / "cpp_enums.json")
    cpp_report_path = write_cpp_summary_report(
        cpp_parsed["symbols"],
        cpp_parsed["enums"],
        root / "build" / "reports" / "cpp_symbols_summary.md",
    )

    docs_parsed = parse_docs(Path(manifest.required_paths["docs"]))
    doc_pages_path = write_doc_pages(docs_parsed["pages"], root / "build" / "ir" / "doc_pages.json")
    doc_symbol_links_path = write_doc_symbol_links(
        docs_parsed["symbol_links"],
        root / "build" / "ir" / "doc_symbol_links.json",
    )
    doc_report_path = write_doc_summary_report(
        docs_parsed["pages"],
        docs_parsed["symbol_links"],
        root / "build" / "reports" / "doc_pages_summary.md",
    )

    merged = merge_sources(
        python_symbols=symbols,
        cpp_symbols=cpp_parsed["symbols"],
        cpp_enums=cpp_parsed["enums"],
        doc_pages=docs_parsed["pages"],
    )
    symbols_path = write_symbols(merged["symbols"], root / "build" / "ir" / "symbols.json")
    enums_path = write_enums(merged["enums"], root / "build" / "ir" / "enums.json")
    families_path = write_families(merged["families"], root / "build" / "ir" / "families.json")
    merge_conflicts_path = write_merge_conflicts(
        merged["conflicts"],
        root / "build" / "reports" / "merge_conflicts.md",
    )

    return {
        "manifest": manifest.to_dict(),
        "python_symbol_count": len(symbols),
        "cpp_symbol_count": len(cpp_parsed["symbols"]),
        "cpp_enum_count": len(cpp_parsed["enums"]),
        "doc_page_count": len(docs_parsed["pages"]),
        "doc_symbol_link_count": len(docs_parsed["symbol_links"]),
        "merged_symbol_count": len(merged["symbols"]),
        "merged_enum_count": len(merged["enums"]),
        "family_count": len(merged["families"]),
        "merge_conflict_count": len(merged["conflicts"]),
        "lockfile_path": str(lockfile_path),
        "corpus_report_path": str(corpus_report_path),
        "python_symbols_path": str(python_symbols_path),
        "python_report_path": str(python_report_path),
        "cpp_symbols_path": str(cpp_symbols_path),
        "cpp_enums_path": str(cpp_enums_path),
        "cpp_report_path": str(cpp_report_path),
        "doc_pages_path": str(doc_pages_path),
        "doc_symbol_links_path": str(doc_symbol_links_path),
        "doc_report_path": str(doc_report_path),
        "symbols_path": str(symbols_path),
        "enums_path": str(enums_path),
        "families_path": str(families_path),
        "merge_conflicts_path": str(merge_conflicts_path),
    }
