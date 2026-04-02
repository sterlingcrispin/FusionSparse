# Update Workflow

Generated workflow for refreshing FusionSparse from the Autodesk corpus.

## Current Corpus Snapshot

- Pinned Autodesk commit: `6f5edc3905ac6bbd2b759f5ce5fab32d67f6aebe`

## Steps

1. Run `python -m tools.cli snapshot-ir` before refreshing the Autodesk corpus if you want to preserve the previous IR state.
2. Update the Autodesk `corpus/FusionAPIReference` submodule to the target upstream commit.
3. Run `python -m tools.cli build-ir` with the project interpreter.
4. Run `python -m tools.cli diff-ir` to compare the new IR against the latest snapshot.
5. Review `build/reports/corpus_summary.md`, `build/reports/merge_conflicts.md`, `build/reports/rules_summary.md`, and `build/reports/ir_diff.md`.
6. Run `python -m tools.cli generate` to regenerate runtime metadata and generated docs.
7. Review generated diffs under `src/fusion_sparse/generated/` and `docs/`.
8. Run `python -m tools.cli sync-fusion` to stage the smoke script and the workbench add-in into Fusion's API folders.
9. Run the unit test suite.
10. Start `fusion/scripts/FusionSparseSmoke/` or the `FusionSparseWorkbench` add-in inside Fusion and verify the smoke summary.
11. If the local Fusion MCP add-in is available, run the same smoke flows through `execute_api_script` and capture a screenshot with `get_screenshot`.
12. Run `python -m tools.cli run-sample-pairs` to compare normalized Autodesk sample scripts against FusionSparse translations and capture matched screenshots.
13. Review `build/reports/sample_pairs/sample_pairs_report.md` plus the paired screenshots under `build/reports/sample_pairs/`. The expected state is a growing set of exact signature matches with per-pair size reductions.
14. Run `python -m tools.cli measure-sparsity` to regenerate the compact-vs-baseline benchmark report.

## Outputs To Review

- `build/ir/symbols.json`
- `build/ir/enums.json`
- `build/ir/families.json`
- `build/reports/merge_conflicts.md`
- `build/reports/rules_summary.md`
- `build/reports/symbol_stats.md`
- `build/reports/sparsity_report.md`
- `build/reports/ir_diff.md`
- `docs/compact_reference.md`
- `docs/raw_mapping.md`
- `fusion/scripts/FusionSparseSmoke/`
- `fusion/addins/FusionSparseWorkbench/`
- `build/reports/fusion_mcp_pre.png`
- `build/reports/fusion_mcp_post.png`
- `tests/integration/sample_pairs/`
- `build/reports/sample_pairs/sample_pairs_report.md`

## Command Reference

```bash
python -m tools.cli build-ir
python -m tools.cli snapshot-ir
python -m tools.cli diff-ir
python -m tools.cli generate
python -m tools.cli sync-fusion
python -m tools.cli run-sample-pairs
python -m tools.cli measure-sparsity
python -m unittest discover -s tests/unit -p 'test_*.py'
```
