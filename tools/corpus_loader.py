from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess


REQUIRED_PATHS = {
    "python_defs": Path("Fusion_API_Python_Reference/defs"),
    "cpp_headers": Path("Fusion_API_CPP_Reference/include"),
    "docs": Path("Fusion_API_Documentation/files"),
}

OPTIONAL_PATHS = {
    "processed_docs": Path("processed_docs/md"),
    "generate_index": Path("tools/generate_index.py"),
    "llms_txt": Path("llms.txt"),
}


class CorpusError(RuntimeError):
    """Raised when the Autodesk corpus is missing or malformed."""


@dataclass(frozen=True)
class CorpusManifest:
    generated_at: str
    source_root: str
    git_commit: str | None
    required_paths: dict[str, str]
    optional_paths: dict[str, str | None]
    file_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_corpus_root(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "corpus" / "FusionAPIReference"


def resolve_corpus_root(corpus_root: str | os.PathLike[str] | None = None, root: Path | None = None) -> Path:
    if corpus_root:
        return Path(corpus_root).expanduser().resolve()

    env_value = os.environ.get("FUSION_SPARSE_CORPUS")
    if env_value:
        return Path(env_value).expanduser().resolve()

    return default_corpus_root(root).resolve()


def discover_corpus(corpus_root: str | os.PathLike[str] | Path | None = None, root: Path | None = None) -> CorpusManifest:
    root_path = resolve_corpus_root(corpus_root, root)
    if not root_path.exists():
        raise CorpusError(
            f"Fusion API corpus not found at {root_path}. "
            "Clone AutodeskFusion360/FusionAPIReference into corpus/FusionAPIReference "
            "or set FUSION_SPARSE_CORPUS."
        )

    missing = []
    required = {}
    for name, relative in REQUIRED_PATHS.items():
        candidate = root_path / relative
        if not candidate.exists():
            missing.append(f"{name}: {relative.as_posix()}")
        required[name] = str(candidate)

    if missing:
        formatted = ", ".join(missing)
        raise CorpusError(f"Fusion API corpus is missing required paths: {formatted}")

    optional = {}
    for name, relative in OPTIONAL_PATHS.items():
        candidate = root_path / relative
        optional[name] = str(candidate) if candidate.exists() else None

    manifest = CorpusManifest(
        generated_at=_timestamp(),
        source_root=str(root_path),
        git_commit=_git_commit(root_path),
        required_paths=required,
        optional_paths=optional,
        file_counts={
            "python_defs": _count_files(root_path / REQUIRED_PATHS["python_defs"], suffixes={".py", ".pyi"}),
            "cpp_headers": _count_files(root_path / REQUIRED_PATHS["cpp_headers"], suffixes={".h", ".hpp", ".hh", ".hxx"}),
            "docs": _count_files(root_path / REQUIRED_PATHS["docs"], suffixes={".htm", ".html", ".md"}),
            "processed_docs": _count_files(Path(optional["processed_docs"]), suffixes={".md"}) if optional["processed_docs"] else 0,
        },
    )
    return manifest


def write_corpus_lockfile(manifest: CorpusManifest, output_path: str | os.PathLike[str] | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(_serialized_manifest(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def write_corpus_summary_report(manifest: CorpusManifest, output_path: str | os.PathLike[str] | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    serialized = _serialized_manifest(manifest)
    lines = [
        "# Corpus Summary",
        "",
        f"- Generated at: `{manifest.generated_at}`",
        f"- Source root: `{serialized['source_root']}`",
        f"- Git commit: `{manifest.git_commit or 'unknown'}`",
        "",
        "## Required paths",
        "",
    ]

    for name, path in sorted(serialized["required_paths"].items()):
        lines.append(f"- `{name}`: `{path}`")

    lines.extend(["", "## Optional paths", ""])
    for name, path in sorted(serialized["optional_paths"].items()):
        lines.append(f"- `{name}`: `{path or 'absent'}`")

    lines.extend(["", "## File counts", ""])
    for name, count in sorted(manifest.file_counts.items()):
        lines.append(f"- `{name}`: `{count}`")

    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_commit(root_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root_path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _count_files(directory: Path, suffixes: set[str] | None = None) -> int:
    count = 0
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(directory).parts):
            continue
        if suffixes and path.suffix not in suffixes:
            continue
        count += 1
    return count


def _serialized_manifest(manifest: CorpusManifest) -> dict[str, object]:
    source_root = Path(manifest.source_root)
    repo = repo_root()
    try:
        source_root_text = source_root.relative_to(repo).as_posix()
        relative_to_source_root = False
    except ValueError:
        source_root_text = "<external>"
        relative_to_source_root = True
    return {
        "generated_at": manifest.generated_at,
        "source_root": source_root_text,
        "git_commit": manifest.git_commit,
        "required_paths": {
            name: _serialized_path(path, repo, source_root, relative_to_source_root)
            for name, path in manifest.required_paths.items()
        },
        "optional_paths": {
            name: _serialized_path(path, repo, source_root, relative_to_source_root)
            for name, path in manifest.optional_paths.items()
        },
        "file_counts": manifest.file_counts,
    }


def _serialized_path(
    value: str | None,
    repo: Path,
    source_root: Path,
    relative_to_source_root: bool,
) -> str | None:
    if value is None:
        return None
    path = Path(value)
    if relative_to_source_root:
        return path.relative_to(source_root).as_posix()
    return path.relative_to(repo).as_posix()
