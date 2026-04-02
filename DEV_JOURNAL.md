# DEV_JOURNAL

## 2026-04-01

### Status

- Initialized the repository on `main`.
- Connected `origin` to `https://github.com/sterlingcrispin/FusionSparse.git`.
- Read the implementation plan and aligned the first work pass to Phase 0 and Phase 1.
- Added the Autodesk `FusionAPIReference` corpus at `corpus/FusionAPIReference` and converted it into a proper git submodule.

### Milestones

- M0: Repository bootstrap in progress.
- M1: Corpus ingestion plumbing in progress.
- M2: Python defs parsing started.
- M3: HTML doc parsing complete.
- M4: First canonical IR merge complete.
- M5: Runtime core foundation complete.
- M6: Rule-driven metadata generator online.
- M7: Generated public API and wrapper dispatch online.
- M8: First compact design/sketch/extrude slice online.
- M9: Legacy scaffolding cleanup complete.
- M10: Generated compact policy online.
- M11: Generated compact reference and raw mapping docs online.
- M12: Final compact cleanup pass complete.
- M13: Generated update workflow and symbol stats docs online.
- M14: Generated compact surface metadata online.
- M15: Next workflow slice proven with examples and tests.
- M16: Fusion smoke layer online.
- M17: Real Fusion MCP validation complete.
- M18: Sparsity benchmarks and report complete.
- M19: IR snapshot and diff pipeline complete.
- M20: Official-vs-compact sample-pair harness online with first real Fusion equivalence proof.
- M21: Expanded sample-pair coverage to a four-pair real Fusion extrusion regression set.
- M22: Sample-pair report now includes code-size reductions and a through-all cut equivalence case.
- M23: Heavy generated metadata moved out of the shipped runtime package; golden tests now lock the lean generated surface.
- M24: Compact sample translations are now generated from normalized Autodesk baselines instead of being handwritten fixtures.
- M25: Sketch-only sample pairs are now covered by geometry-aware signatures, not just body-based comparisons.
- M26: Fusion deployment lane complete with `sync-fusion`, a self-contained smoke script bundle, and a real workbench add-in.
- M27: Merge/diff signal tightened enough that conflict noise is back to double digits instead of four-figure churn.
- M28: Automated API coverage map online, separating raw reachability from compact and sample-validated support.
- M29: Design-workspace backlog is now the official scope driver, and wave-one Design families are validated in real Fusion through official-vs-compact sample pairs.

### Decisions

- The Autodesk corpus is being treated as an external development input, not as part of the shipped runtime.
- The Autodesk corpus should be maintained as a git submodule so the parent repo pins an exact upstream snapshot while keeping the corpus refresh workflow explicit.
- The project should now prioritize Phase 6 and Phase 7 over any further handwritten compact wrapper expansion.
- Handwritten compact wrappers should be treated as provisional. If the generator can own that behavior cleanly, delete or shrink the handwritten layer rather than duplicating it.
- The Design workspace is now the active compact-coverage scope; non-Design namespaces remain raw-first unless later product evidence justifies promotion.

### Hypotheses

- H1: The Autodesk Python definitions are a strong enough primary source to produce a stable first-pass Python IR without touching the HTML docs yet.
- H2: The defs layout is flat enough that a deterministic parser over `defs/adsk/*.py` can produce useful symbol coverage quickly.
- H3: A small CLI plus a corpus lock/report step will keep the rest of the project grounded and reproducible from the beginning.

### Hypotheses tested

- HT1: The official Autodesk repo contains the required corpus directories from the plan.
  - Result: confirmed.
- HT2: The Python defs are organized as top-level `adsk/*.py` modules rather than a deep tree.
  - Result: confirmed.
- HT3: A submodule can be added directly in this environment.
  - Result: confirmed after full-access mode was enabled.
- HT4: A first-pass Python IR can be produced directly from the Autodesk defs without touching C++ headers or docs yet.
  - Result: confirmed.
- HT5: A conservative line-oriented C++ parser can extract useful enum and public method metadata without blocking on a full parser.
  - Result: confirmed.
- HT6: The Autodesk HTML docs are structured consistently enough for a standard-library parser to extract titles, sections, parameter tables, return values, versions, sample links, and code blocks at corpus scale.
  - Result: confirmed.
- HT7: A first merged IR across Python defs, C++ headers, and docs can be produced deterministically before rule generation or runtime work begins.
  - Result: confirmed.
- HT8: The handwritten runtime core can stay importable outside Fusion if every `adsk` dependency is resolved lazily at call time.
  - Result: confirmed.
- HT9: The generator can own the package public API and wrapper dispatch while keeping the handwritten layer thin.
  - Result: confirmed.
- HT10: A narrow handwritten compact layer backed by generated dispatch and family metadata can cover the first modeling workflow without broad manual wrapper expansion.
  - Result: confirmed.
- HT11: Plane aliases, sketch method mapping, sketch unit parsing, and extrude builder policy can move out of wrapper-local code and into generated metadata without widening the runtime surface.
  - Result: confirmed.
- HT12: Compact helper/method reference docs and compact-to-raw Autodesk mapping tables can be generated from rules plus metadata instead of being maintained by hand.
  - Result: confirmed.
- HT13: Additional introspection docs such as update workflow guidance and symbol stats can be generated directly from the corpus lock and canonical IR instead of being maintained manually.
  - Result: confirmed.
- HT14: Repetitive compact wrapper behavior for properties, sketch methods, and profile access can move into generated surface metadata without forcing full wrapper code generation.
  - Result: confirmed.
- HT15: The current compact slice already supports the next planned workflows, including rectangle sketch, `new_component` simple extrude, and symmetric builder use with participant bodies.
  - Result: confirmed.
- HT16: The compact slice can be exercised through a thin Fusion smoke harness without adding new public API surface or a large deployment framework.
  - Result: confirmed in the simulated Fusion environment.
- HT17: The current compact slice and smoke runner can execute successfully inside a real Fusion session through the local MCP add-in.
  - Result: confirmed.
- HT18: The first compact slice produces materially smaller source than the raw Autodesk call chains for the core modeling workflows in the plan.
  - Result: confirmed.
- HT19: IR snapshots and release-diff reports can be generated deterministically enough that corpus updates become a mostly mechanical review step.
  - Result: confirmed.
- HT20: Normalized Autodesk sample scripts and FusionSparse translations can be executed side by side through Fusion MCP, compared by structural signature, and validated with paired screenshots.
  - Result: confirmed.
- HT21: The current compact extrusion slice is broad enough to reproduce several Autodesk extrusion samples, not just one toy case, with matching geometry in real Fusion.
  - Result: confirmed.
- HT22: A richer geometry signature including face count and body volume is sufficient to validate subtractive equivalence for the current extrusion sample set, not just bounding-box equality.
  - Result: confirmed.
- HT23: The runtime package can stay materially smaller if heavy introspection metadata is emitted to build artifacts instead of being shipped under `src/`, without regressing real Fusion behavior.
  - Result: confirmed.
- HT24: The current compact extrusion slice is regular enough that normalized Autodesk-style baseline scripts can be rewritten deterministically into FusionSparse form, eliminating handwritten compact sample fixtures for this batch.
  - Result: confirmed.
- HT25: Sketch-only Autodesk samples can be validated meaningfully if the comparison signature records sketch circles, lines, and profile counts instead of only body geometry.
  - Result: confirmed.

### TODO

- Tighten merge heuristics so `merge_conflicts.md` highlights meaningful compatibility risks instead of representation noise.
- Expand rule coverage beyond the initial alias, enum, and family overrides.
- Move more hardcoded compact policy into generated metadata where appropriate.
- Expand generated compact reference coverage as the compact surface grows.
- Expand golden coverage beyond the current representative generated files as the compact surface grows.
- Decide on the final project license before publishing.
- Expand the official-vs-compact sample-pair manifest so more Autodesk documentation examples are covered by real Fusion equivalence runs.
- Keep strengthening the sample-pair signature so future feature classes can be compared by meaningful geometry, not just coarse shape envelopes.
- Push more sample coverage through the converter before adding any new handwritten sample translations.

### Next steps

- Expand generated metadata so more compact behavior and more compact reference entries are driven by rule files instead of wrapper-local defaults.
- Expand the current compact vertical slice carefully from `new_design -> sketch -> circle -> extrude` to adjacent high-value operations while keeping the handwritten layer thin.
- Revisit the current handwritten runtime and compact surface regularly to delete anything the generator now subsumes.
- Expand golden coverage as the generated surface grows so generator drift stays explicit.
- Keep extending the generated docs/introspection layer as the compact surface grows.
- Grow sample-pair coverage in small automation-friendly batches so Autodesk documentation examples become a regression suite, not just spot checks.
- Prefer sample additions that either add a new feature or materially strengthen the equivalence proof.
- Keep normalized official baselines readable and minimal so the converter stays deterministic instead of turning into a generic transpiler.
- Keep the deployment lane self-contained so Fusion validation does not depend on importing repo-only test modules.

### Results

- Repository scaffold created for `rules/`, `tools/`, `src/fusion_sparse/`, and `tests/unit/`.
- `python -m tools.cli --help` works with the required project interpreter.
- Unit tests are passing.
- `build-ir` now loads the Autodesk corpus, writes `corpus/corpus.lock.json`, writes `build/reports/corpus_summary.md`, and emits `build/ir/python_symbols.json`.
- `build-ir` now also emits `build/ir/cpp_symbols.json`, `build/ir/cpp_enums.json`, and `build/reports/cpp_symbols_summary.md`.
- `build-ir` now parses Autodesk HTML docs into `build/ir/doc_pages.json` and `build/ir/doc_symbol_links.json`.
- `build-ir` now merges Python, C++, and docs into `build/ir/symbols.json`, `build/ir/enums.json`, `build/ir/families.json`, and `build/reports/merge_conflicts.md`.
- The runtime core now has real implementations for adapter/wrapping, refs, lazy context helpers, unit-safe value coercion, transient geometry helpers, and compact enum aliases.
- The package top level is now generated from rule files instead of using a handwritten export list.
- `tools/apply_rules.py` and `tools/generate_metadata.py` are now implemented.
- `python -m tools.cli generate` now emits generated runtime metadata under `src/fusion_sparse/generated/`.
- The runtime enum aliases now consume generated metadata instead of a handwritten alias table.
- A rules report is now produced at `build/reports/rules_summary.md`.
- Generated wrapper dispatch now maps Autodesk `Design`, `Component`, and `Sketch` objects to compact wrappers.
- Generated compact policy now drives plane aliases, sketch curve method names, sketch length parsing units, and extrude builder method names.
- A first compact modeling slice now works through generated dispatch and generated family metadata: `new_design`, `root.sketch(...)`, `sketch.circle(...)`, `root.extrude(...)`, and `ExtrudeBuilder`.
- Generated compact reference metadata now emits `build/generated/compact_reference.py`.
- Generated docs now emit `docs/compact_reference.md` and `docs/raw_mapping.md` from metadata plus rule files instead of maintaining reference prose by hand.
- The last stray handwritten compact helpers outside the active vertical slice were removed from `DesignRef` and `SketchRef`.
- Generated docs now also emit `docs/update_workflow.md` and `build/reports/symbol_stats.md`.
- Repetitive compact wrapper execution now flows through generated surface metadata in `src/fusion_sparse/generated/compact_surface.py` plus a single generic executor in `src/fusion_sparse/compact/_surface.py`.
- Example scripts now exist for the simple and builder workflows under `examples/`.
- Fusion smoke scripts now exist under `tests/integration/fusion_scripts/` and a runnable Fusion script bundle now exists under `fusion/scripts/FusionSparseSmoke/`.
- Real Fusion validation now exists through the local Fusion MCP add-in using `execute_api_script` and `get_screenshot`.
- Benchmark pairs now exist under `benchmarks/baselines/` and `benchmarks/compact/`, and `tools/measure_sparsity.py` now emits `build/reports/sparsity_report.md`.
- IR snapshots now live under `snapshots/`, and `tools/diff_ir.py` now provides snapshot creation plus deterministic update reports.
- `tools/run_sample_pairs.py` now executes normalized Autodesk sample scripts and FusionSparse translations side by side through Fusion MCP, captures screenshots, and writes `build/reports/sample_pairs/sample_pairs_report.md`.
- The first official-vs-compact sample pair now proves real Fusion equivalence for `SimpleExtrusionSample_Sample.htm`.
- The sample-pair suite now covers four real Fusion extrusion workflows with `4/4` exact signature matches and visually identical screenshot pairs.
- The sample-pair suite now covers five real Fusion workflows, including a through-all cut case whose equivalence depends on matching face counts and volume, not just outer bounds.
- The sample-pair report now records per-pair and total size reductions for the official and compact scripts.
- The Design-workspace backlog report now ranks `adsk.fusion` families into `validated`, `candidate`, and `raw` buckets using only repo-local evidence, and wave one is now the main expansion lane.
- Wave-one Design coverage now includes construction planes/axes/points, sketch arcs, revolve, holes, fillets, and chamfers through generated policy plus thin handwritten runtime shells.
- The official-vs-compact regression suite now covers the wave-one Design sample set in real Fusion, not just the original extrusion and sketch slice.
- Runtime-critical generated modules are now separated from build-only introspection artifacts; `src/fusion_sparse/generated/` is small enough to stay agent-readable while `build/generated/` holds the bulky indexes.
- Golden fixtures now exist for representative generated outputs, so generator drift is explicit.
- `tools/generate_sample_pairs.py` now rewrites normalized Autodesk-style baseline scripts into generated FusionSparse sample translations under `build/generated/sample_pairs/`.
- The easy official baselines are now generated from Autodesk doc code blocks too, so only the more behavior-heavy official variants remain hand-normalized.
- The handwritten compact sample fixtures under `tests/integration/sample_pairs/compact/` were deleted; the sample-pair runner now generates its manifest and compact scripts on demand.
- The sample-pair suite now also covers `CircleByCenterRadius_Sample.htm`, `SketchLines_addByTwoPoints_Sample.htm`, and `SketchLines_addTwoPointRectangle_Sample.htm`.
- `tests/integration/sample_pairs/common.py` now records sketch circles, sketch lines, and sketch profile counts in the equivalence signature so sketch-only samples are real regressions, not trivial zero-body matches.
- The sketch shape registry is now shared rule data: runtime surface generation and official sample conversion both read the same sketch collection/method/coercer policy.
- The sample-pair suite now also covers `SketchLines_addCenterPointRectangle_Sample.htm`, `SketchLines_addThreePointRectangle_Sample.htm`, `SketchCircles_addByTwoPoints_Sample.htm`, and `SketchCircles_addByThreePoints_Sample.htm`.
- The sample-pair generator has been split into `tools/sample_pairs/` modules for rules, official wrapping, policy, translation, and orchestration instead of keeping that logic in one monolithic file.
- `tools/sync_to_fusion.py` now stages `fusion_sparse` and `fusion_harness` into bundle-local `lib/` directories and syncs both the smoke script and the workbench add-in into Fusion's API folders.
- `fusion/scripts/FusionSparseSmoke/` and `fusion/addins/FusionSparseWorkbench/` are now self-contained bundle entry points instead of depending on imports from `tests/`.
- Merge normalization now bridges common doc/property and scalar-type naming mismatches, which reduced `build/reports/merge_conflicts.md` from `1011` conflicts to `139`.
- `tools/map_api_coverage.py` now emits an automated support map that distinguishes raw reachability, compact surface coverage, and real sample-validated coverage.
- Wave two is now implemented and validated in the compact layer for `CombineFeatures`, `MirrorFeatures`, `CircularPatternFeatures`, and `RectangularPatternFeatures`.
- The active official-vs-compact manifest is `33` deterministic pairs after removing `MirrorFeatureSample_Sample.htm` from the automated suite; that normalized baseline was destabilizing the Fusion MCP session.
- A restarted Fusion MCP session completed the remaining wave-two pattern-family runs, so the Design backlog now marks all four wave-two families as `validated`.
- Wave three is now implemented and validated in the compact layer for `SweepFeatures`, `LoftFeatures`, `PatchFeatures`, `ShellFeatures`, and `DraftFeatures`.
- The sample translator now converts official sweep/loft/patch/shell/draft feature-input patterns into compact FusionSparse calls instead of relying on handwritten compact sample fixtures.
- The active official-vs-compact manifest now contains `40` deterministic pairs, and the full real-Fusion MCP suite passes `40/40`.
- Wave four is now implemented and validated in the compact layer for `MoveFeatures`, `OffsetFeatures`, `ReplaceFaceFeatures`, `ScaleFeatures`, `SplitBodyFeatures`, `ThreadFeatures`, and `TrimFeatures`.
- The modification helpers are still thin handwritten shells, but their family behavior is generator-owned through `rules/compact_policy.yaml` and the generated compact policy module.
- The full one-shot `47`-pair Fusion MCP run stalled late in the modification cluster, but the remaining wave-four pairs were completed in a focused live subset and merged back into the main report. The validated state is still real-Fusion-backed; it just came from two live passes instead of one uninterrupted session.
- The active official-vs-compact manifest now contains `47` deterministic pairs, and the current validated report is `47/47`.
- The sketch authoring slice now also includes `SketchPoints`, `SketchEllipses`, `SketchFittedSplines`, and `SketchTexts` through generator-owned sketch policy plus a thin handwritten sketch-text helper.
- The sample-pair suite now also covers `SketchPoint_add_Sample.htm`, `SketchEllipses_add_Sample.htm`, `SketchFittedSplines_add_Sample.htm`, `SketchTextInput_setAsMultiLine_Sample.htm`, `SketchTextinput_setAsAlongPath_Sample.htm`, and `SketchTextInput_setAsFitOnPath_Sample.htm`.
- `tests/integration/sample_pairs/common.py` now records sketch points, ellipses, fitted splines, and sketch text in the design signature, so the expanded sketch layer is validated structurally and not just by screenshots.
- The generated sketch executor now preserves raw Autodesk `SketchPoint` inputs instead of coercing them to `Point3D`, which fixed the `CircleByCenterRadius_Sample.htm` equivalence mismatch introduced by the richer sketch signature.
- The active official-vs-compact manifest now contains `53` deterministic pairs, and the current validated report is `53/53`.

### Current metrics

- Corpus commit: `6f5edc3905ac6bbd2b759f5ce5fab32d67f6aebe`
- Python defs files discovered: `6`
- C++ headers discovered: `871`
- Doc pages discovered: `15242`
- First-pass Python symbols extracted: `12008`
- First-pass C++ class and method symbols extracted: `9791`
- First-pass C++ enums extracted: `157`
- Doc pages parsed: `15242`
- Symbol-linked doc pages: `14945`
- First merged canonical symbols: `20398`
- First merged enum records: `234`
- First detected family records: `290`
- Current merge conflicts after normalized type and property/event heuristics: `139`
- Export aliases configured: `12`
- Plane aliases configured: `3`
- Enum alias groups configured: `7`
- Family overrides configured: `1`
- Wrapper dispatch rules configured: `3`
- Compact reference exports configured: `12`
- Compact reference methods configured: `40`
- Generated compact property specs: `1`
- Generated compact method specs: `15`
- Unit tests passing: `42`
- Fusion smoke scripts: `5`
- Real Fusion MCP smoke results: `5/5` passing
- Official-vs-compact active sample pairs: `53`
- Official-vs-compact real Fusion equivalence: `53/53`
- Direct compact Autodesk symbols: `158`
- Covered Autodesk families/classes: `116`
- Sample-pair validated compact symbols: `140`
- Design-workspace families in scope: `188`
- Design-workspace validated families: `41`
- Official-vs-compact size totals:
  - characters reduced: `61.9%`
  - lines reduced: `50.7%`
  - tokens reduced: `52.7%`
  - `adsk.` refs reduced: `100.0%`
- Sparsity benchmark pairs: `5`
- Sparsity totals:
  - characters reduced: `70.0%`
  - lines reduced: `48.6%`
  - tokens reduced: `59.7%`
  - `adsk.` refs reduced: `100.0%`
- Current IR snapshot: `snapshots/2026-04-01_6f5edc3`
- Current diff report status: clean against the current snapshot
- Symbol breakdown:
  - classes: `1097`
  - enums: `203`
  - constants: `1032`
  - methods: `5347`
  - properties: `4320`
- C++ breakdown:
  - classes: `888`
  - methods: `8903`
  - namespaces with highest coverage: `adsk.fusion`, `adsk.cam`, `adsk.volume`

### Notes

- The parser now normalizes `__init__.py` to module `adsk` instead of `adsk.__init__`.
- Autodesk docstrings contained invalid escape sequences that produced `SyntaxWarning` noise under `ast.parse`; those warnings are now suppressed during corpus parsing only.
- The first C++ enum parser initially broke on comment text containing commas; switching enum extraction to a line-oriented pass fixed that issue.
- The Autodesk corpus has now been converted from a plain nested clone to a proper git submodule at `corpus/FusionAPIReference`.
- `git submodule absorbgitdirs` was run so the submodule uses standard parent-managed metadata under `.git/modules/`.
- The doc parser uses only the standard library because the required base interpreter does not currently have `bs4` or `lxml` installed.
- The first merge pass now prefers getter-shaped C++ overloads when Python exposes a property, which reduced merge conflict noise substantially.
- Remaining merge conflicts are mostly real representation mismatches such as `objectType` appearing as a doc property while Python defs expose it as a method, or Python/C++ scalar type naming differences like `str` vs `string` and `None` vs `void`.
- The runtime core includes a small internal lazy-import layer for `adsk` so `fusion_sparse` can still be imported in a normal Python environment and tested with mocked Autodesk modules.
- `build-ir` still passes after the runtime changes, which keeps the build-time and runtime sides of the repo from drifting apart.
- The architecture has been corrected back toward the plan: the next major work should be improving and consuming generated metadata, not broadening the handwritten compact wrapper layer.
- Some of the current handwritten surface may still be temporary; if a generated equivalent becomes cleaner, the handwritten version should be removed rather than preserved out of inertia.
- The top-level import surface is now generator-owned, which is an important maintenance milestone because API shape changes can now be reviewed as rule and generated-file diffs instead of handwritten package edits.
- The current compact wrappers are intentionally narrow and lean on generated dispatch plus generated family metadata; if future generator work can replace more of this handwritten glue, that should be preferred.
- Early placeholder files and unimplemented CLI stubs have been removed instead of being kept around as dormant compatibility or scaffold paths.
- Generated release metadata now records stable corpus facts only and no longer embeds machine-specific absolute paths or per-run timestamps.
- The next generator-focused work should target more compact family policy and more generated compact surface, not broad handwritten wrapper growth.
- The next major validation step after unit coverage is running the new smoke bundle inside real Fusion.
- A real Fusion MCP run created geometry successfully and wrote screenshots to `build/reports/fusion_mcp_pre.png` and `build/reports/fusion_mcp_post.png`.
- The first measured benchmark set meets the practical intent of the project: significantly fewer characters, tokens, and raw Autodesk references for the core workflows.
- The update pipeline now has working `snapshot-ir` and `diff-ir` commands, and the first repo-local snapshot/diff loop produced a zero-drift report as expected.
- The first sample-pair report shows matching screenshots and identical design signatures for the normalized Autodesk simple extrusion sample and the FusionSparse compact translation.
- The sample-pair suite now includes `SimpleExtrusionSample_Sample.htm`, `extrudeFeatures_addSimple_Sample.htm`, and two normalized builder-path variants from `ExtrudeFeatureSample_Sample.htm`.
- The sample-pair suite now also includes `extrudeFeaturesThroughAllExtent_add_Sample.htm`, and the comparison signature now records face counts plus body volume so subtractive equivalence is actually provable for this slice.
- The sample-pair suite now also includes `CircleByCenterRadius_Sample.htm`, `SketchLines_addByTwoPoints_Sample.htm`, and `SketchLines_addTwoPointRectangle_Sample.htm`, with sketch signatures proving equivalence even when no solid bodies exist.
- The sample-pair suite now also includes `ConstructionPlaneSample_Sample.htm`, `ConstructionAxisSample_Sample.htm`, `ConstructionPointSample_Sample.htm`, `SketchArcs_addByCenterStartaSweep_Sample.htm`, `SketchArcs_addByThreePoints_Sample.htm`, `SimpleRevolveFeatureSample_Sample.htm`, `revolveFeatures_add_Sample.htm`, `HoleFeatureSample_Sample.htm`, `holeFeatures_add_Sample.htm`, `holeFeaturesCounterBore_add_Sample.htm`, `holeFeaturesCounterSink_add_Sample.htm`, `ConstantRadiusFillet_Sample.htm`, `filletFeatures_add_Sample.htm`, `EqualDistanceChamferFeature_Sample.htm`, and `chamferFeatures_add_Sample.htm`.
- The Design-workspace backlog is now generated automatically, and all eight wave-one families are marked `validated` after a `27/27` real Fusion MCP run.
- The compact Design slice now covers helper-based construction workflows plus revolve, hole, fillet, and chamfer in addition to the earlier sketch/extrude path.
- The compact Design slice now also includes combine, mirror, circular pattern, and rectangular pattern helpers driven by generated policy.
- The active sample-pair manifest now excludes `MirrorFeatureSample_Sample.htm` because that normalized baseline was hanging or destabilizing the Fusion MCP session; `mirrorFeatures_add_Sample.htm` remains the live mirror-family validator.
- After the Fusion MCP session was restarted, the remaining `circularPatternFeatures_add`, `CircularPatternFeatureSample`, `rectangularPatter_add`, and `RectangularPatternFeatureSample` pairs all passed and wave two moved fully into `validated`.
- The shipped generated package shrank from roughly `15.0 MB` to roughly `73 KB`, with the large symbol/family/reference artifacts moved to `build/generated/`.
- The sample-pair harness no longer sweeps and closes every unsaved `Untitled` document; it now tags harness-owned sample designs and closes only the active harness document.
- `ExtrudeBuilder.symmetric(...)` now preserves Autodesk's `isFullLength` boolean, and the sample translator emits `full_length=False` when the official sample uses half-length symmetric behavior.
- C++ type normalization no longer corrupts nested generic/template types like `std::vector<core::Ptr<URL>>`, and additional canonicalization now reduces merge-conflict noise to `139`.
- `corpus/corpus.lock.json` now stores stable relative corpus paths instead of workstation-specific absolute paths.
- The Fusion deployment path now exists end to end: `python -m tools.cli sync-fusion` links or copies both the smoke bundle and the workbench add-in into Fusion's `API/Scripts` and `API/AddIns` folders.
- The Design-workspace compact slice now also includes move, offset, replace-face, scale, split-body, thread, and trim helpers, all validated against normalized Autodesk samples in real Fusion.
- `ThreadInfo.create(...)` needed the modern six-argument form in both the runtime helper and the normalized official baseline; the old four-argument shape was retired Autodesk API surface.
- The live sample-pair suite is now large enough that periodic Fusion-session instability is starting to matter operationally even when the feature work is correct. If that keeps happening, the next harness improvement should be resumable chunked execution, not broader API work.
