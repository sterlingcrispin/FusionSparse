from __future__ import annotations

import argparse
import json
import sys

from tools.build_ir import build_ir
from tools.corpus_loader import CorpusError
from tools.diff_ir import diff_ir, snapshot_ir
from tools.generate_metadata import generate_metadata
from tools.map_api_coverage import map_api_coverage
from tools.generate_sample_pairs import generate_sample_pairs
from tools.measure_sparsity import measure_sparsity
from tools.run_sample_pairs import run_sample_pairs
from tools.sync_to_fusion import sync_to_fusion


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "build-ir":
            result = build_ir(repo_root=args.repo_root, corpus_root=args.corpus_root)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        if args.command == "generate":
            result = generate_metadata(
                repo_root=args.repo_root,
                corpus_root=args.corpus_root,
                build_ir_first=not args.skip_build_ir,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        if args.command == "measure-sparsity":
            result = measure_sparsity(
                repo_root=args.repo_root,
                baselines_dir=args.baselines_dir,
                compact_dir=args.compact_dir,
                output_path=args.output_path,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        if args.command == "map-coverage":
            result = map_api_coverage(
                repo_root=args.repo_root,
                output_path=args.output_path,
                json_output_path=args.json_output_path,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        if args.command == "snapshot-ir":
            result = snapshot_ir(
                repo_root=args.repo_root,
                snapshot_name=args.snapshot_name,
                source_ir_dir=args.source_ir_dir,
                snapshot_root=args.snapshot_root,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        if args.command == "diff-ir":
            result = diff_ir(
                repo_root=args.repo_root,
                snapshot_name=args.snapshot_name,
                snapshot_dir=args.snapshot_dir,
                current_ir_dir=args.current_ir_dir,
                snapshots_root=args.snapshots_root,
                output_path=args.output_path,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        if args.command == "run-sample-pairs":
            result = run_sample_pairs(
                repo_root=args.repo_root,
                manifest_path=args.manifest_path,
                mcp_url=args.mcp_url,
                output_root=args.output_root,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        if args.command == "generate-sample-pairs":
            result = generate_sample_pairs(
                repo_root=args.repo_root,
                rules_path=args.rules_path,
                output_root=args.output_root,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        if args.command == "sync-fusion":
            result = sync_to_fusion(
                repo_root=args.repo_root,
                api_root=args.api_root,
                scripts_dir=args.scripts_dir,
                addins_dir=args.addins_dir,
                mode=args.mode,
                sync_smoke=not args.skip_smoke,
                sync_workbench=not args.skip_workbench,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        parser.print_help()
        return 0
    except (CorpusError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FusionSparse build and generation tooling.")
    subparsers = parser.add_subparsers(dest="command")

    build_ir_parser = subparsers.add_parser("build-ir", help="Load the corpus and generate the first-pass Python IR.")
    build_ir_parser.add_argument("--repo-root", default=None, help="Path to the FusionSparse repository root.")
    build_ir_parser.add_argument("--corpus-root", default=None, help="Path to the Autodesk FusionAPIReference checkout.")

    generate_parser = subparsers.add_parser("generate", help="Generate runtime and metadata artifacts.")
    generate_parser.add_argument("--repo-root", default=None, help="Path to the FusionSparse repository root.")
    generate_parser.add_argument("--corpus-root", default=None, help="Path to the Autodesk FusionAPIReference checkout.")
    generate_parser.add_argument(
        "--skip-build-ir",
        action="store_true",
        help="Reuse existing build/ir artifacts instead of rebuilding them first.",
    )

    measure_parser = subparsers.add_parser("measure-sparsity", help="Measure compact-vs-baseline benchmark sparsity.")
    measure_parser.add_argument("--repo-root", default=None, help="Path to the FusionSparse repository root.")
    measure_parser.add_argument("--baselines-dir", default=None, help="Path to the baseline benchmark directory.")
    measure_parser.add_argument("--compact-dir", default=None, help="Path to the compact benchmark directory.")
    measure_parser.add_argument("--output-path", default=None, help="Path to the generated sparsity markdown report.")

    coverage_parser = subparsers.add_parser(
        "map-coverage",
        help="Generate a coverage map showing raw reachability, compact surface coverage, and validated sample coverage.",
    )
    coverage_parser.add_argument("--repo-root", default=None, help="Path to the FusionSparse repository root.")
    coverage_parser.add_argument("--output-path", default=None, help="Path to the generated coverage markdown report.")
    coverage_parser.add_argument("--json-output-path", default=None, help="Path to the generated coverage JSON report.")

    snapshot_parser = subparsers.add_parser("snapshot-ir", help="Copy the current IR into a named snapshot directory.")
    snapshot_parser.add_argument("--repo-root", default=None, help="Path to the FusionSparse repository root.")
    snapshot_parser.add_argument("--snapshot-name", default=None, help="Snapshot directory name. Defaults to date + corpus commit.")
    snapshot_parser.add_argument("--source-ir-dir", default=None, help="Path to the current IR directory.")
    snapshot_parser.add_argument("--snapshot-root", default=None, help="Root directory containing IR snapshots.")

    diff_parser = subparsers.add_parser("diff-ir", help="Compare a previous IR snapshot against the current IR.")
    diff_parser.add_argument("--repo-root", default=None, help="Path to the FusionSparse repository root.")
    diff_parser.add_argument("--snapshot-name", default=None, help="Snapshot directory name under the snapshots root.")
    diff_parser.add_argument("--snapshot-dir", default=None, help="Explicit path to the snapshot directory.")
    diff_parser.add_argument("--current-ir-dir", default=None, help="Path to the current IR directory.")
    diff_parser.add_argument("--snapshots-root", default=None, help="Root directory containing IR snapshots.")
    diff_parser.add_argument("--output-path", default=None, help="Path to the generated diff markdown report.")

    sample_parser = subparsers.add_parser("run-sample-pairs", help="Run official-vs-compact sample pairs through Fusion MCP.")
    sample_parser.add_argument("--repo-root", default=None, help="Path to the FusionSparse repository root.")
    sample_parser.add_argument("--manifest-path", default=None, help="Path to a pre-generated sample-pair manifest JSON file.")
    sample_parser.add_argument("--mcp-url", default="http://localhost:9100/", help="Fusion MCP base URL.")
    sample_parser.add_argument("--output-root", default=None, help="Path to the output directory for reports and screenshots.")

    generate_sample_parser = subparsers.add_parser(
        "generate-sample-pairs",
        help="Generate compact sample translations and the sample-pair manifest.",
    )
    generate_sample_parser.add_argument("--repo-root", default=None, help="Path to the FusionSparse repository root.")
    generate_sample_parser.add_argument("--rules-path", default=None, help="Path to the sample-pair rules YAML file.")
    generate_sample_parser.add_argument("--output-root", default=None, help="Path to the generated sample-pair output directory.")

    sync_parser = subparsers.add_parser(
        "sync-fusion",
        help="Stage the FusionSparse script/add-in bundles and sync them into Fusion's API folders.",
    )
    sync_parser.add_argument("--repo-root", default=None, help="Path to the FusionSparse repository root.")
    sync_parser.add_argument("--api-root", default=None, help="Path to Fusion's API root directory.")
    sync_parser.add_argument("--scripts-dir", default=None, help="Path to Fusion's Scripts directory.")
    sync_parser.add_argument("--addins-dir", default=None, help="Path to Fusion's AddIns directory.")
    sync_parser.add_argument("--mode", choices=("copy", "link"), default="link", help="Deploy bundles by copying or symlinking them.")
    sync_parser.add_argument("--skip-smoke", action="store_true", help="Do not sync the FusionSparse smoke script bundle.")
    sync_parser.add_argument("--skip-workbench", action="store_true", help="Do not sync the FusionSparseWorkbench add-in bundle.")

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
