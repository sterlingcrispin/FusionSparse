# Implementation Plan: Generated Fusion Sparse Python Layer, 'FusionSparse'

## 1. Purpose

Build a Python project that generates and maintains a token-sparse, agent-friendly layer on top of the Autodesk Fusion API.

The project must satisfy five requirements at the same time:

1. Be easy for coding agents to read and write.
2. Reduce token count and ceremony for common modeling tasks.
3. Preserve full practical compatibility with the existing Fusion API.
4. Be updateable when Autodesk publishes new API releases.
5. Be usable both in ordinary Fusion scripts and in add-ins.

This plan assumes the implementation language is Python and that the generated runtime will execute inside Fusion's embedded Python environment. Build tooling may use external Python packages, but the runtime library that ships into Fusion should have zero third-party runtime dependencies.

This document is written for a coding agent that will execute the work locally.

## 2. Executive Decision Summary

Do not hand-wrap the entire Autodesk API.

Instead, implement a generator-driven system with four layers:

1. Official corpus ingestion
   - Use the official `AutodeskFusion360/FusionAPIReference` repository as the source corpus.
   - Use its Python definitions first, C++ headers second, and docs third.

2. Normalized intermediate representation
   - Build a machine-readable API IR that represents classes, methods, properties, enums, inheritance, samples, versions, and doc metadata.

3. Generated metadata and compatibility layer
   - Generate registries, symbol maps, enum aliases, version diffs, and wrapper dispatch tables from the IR.

4. Handwritten ergonomic runtime with generated policy inputs
   - Keep only a small handwritten runtime.
   - Generate the large, repetitive pieces.
   - Apply a small rule set to create the compact user-facing API.

The generator is the product. The wrapper library is a generated artifact plus a thin handwritten core.

## 3. Hard Constraints

The implementation must obey the following:

### 3.1 Source of truth priority

When there is a conflict or ambiguity, use this precedence order:

1. `Fusion_API_Python_Reference/defs/`
2. `Fusion_API_CPP_Reference/include/`
3. `Fusion_API_Documentation/files/` or `processed_docs/md/` if available
4. Sample code repositories only as examples or regression fixtures, never as the schema source

### 3.2 Compatibility rule

The compact layer must never block access to the raw Autodesk API.

Every wrapper object must support:

- `.raw` to access the original Autodesk object
- pass-through access to raw camelCase members where practical
- use of raw Autodesk objects as arguments to compact helpers
- use of compact wrappers as arguments to raw Autodesk methods

If a compact helper does not exist for some API area, the user must still be able to reach the official API immediately.

### 3.3 Runtime dependency rule

The runtime package that is copied into Fusion must use only the Python standard library plus `adsk.*`.

All parsing, code generation, HTML conversion, and indexing dependencies belong in build tooling only.

### 3.4 Unit safety rule

Never treat bare numeric literals as document units.

For the compact layer:

- bare numbers mean Fusion internal units only
- strings mean Fusion expressions
- explicit unit helpers such as `u.mm(5)` and `u.deg(30)` are preferred

This rule is non-negotiable.

### 3.5 Design target rule

Do not hide the modeling target.

Compact APIs must make the target component or design context explicit. Do not create geometry implicitly in some guessed "active" component.

### 3.6 Generation rule

Never manually edit generated files.

All manual behavior must live in handwritten runtime modules or in rule files consumed by the generator.

## 4. Project Outcome

The minimum acceptable first release is a generated library that supports this workflow:

```python
import fusion_sparse as fx

def run(_):
    design = fx.new_design()
    root = design.root
    sk = root.sketch("xy")
    sk.circle((0, 0), r="20 mm")
    root.extrude(sk.profile(), "50 mm", op="new_component")
```

And also this more explicit builder-style workflow:

```python
import fusion_sparse as fx

def run(_):
    design = fx.new_design()
    root = design.root
    sk = root.sketch("xy")
    sk.rect((0, 0), (40, 20))
    ext = (
        root.extrude(sk.profile(), op="new_body")
            .one_side("10 mm", direction="positive")
            .build()
    )
```

The first release does not need to provide compact wrappers for the full API surface. It does need to provide complete metadata coverage and raw fallback coverage, plus a high-quality compact layer for the most important modeling operations.

## 5. Success Metrics

Measure success explicitly.

### 5.1 Sparsity metrics

For common workflows, compare official-style code to compact-wrapper code.

Create benchmark pairs for:

- create application context and new design document
- create sketch on default plane
- draw circle
- draw rectangle
- extrude simple new body
- extrude new component
- set one-side extent with builder path

For each pair compute:

- character count
- line count
- token count using a deterministic tokenizer script
- number of Autodesk enum references
- number of `adsk.` symbol occurrences

Initial targets:

- 40 percent or greater reduction in character count for common workflows
- 50 percent or greater reduction in line count for common workflows
- 50 percent or greater reduction in `adsk.` symbol occurrences for common workflows
- no loss of capability for those workflows

### 5.2 Compatibility metrics

- 100 percent of wrapper objects expose `.raw`
- unsupported raw API access works without monkey patching or manual conversions
- all compact helper arguments accept either compact wrappers or raw Autodesk objects where sensible

### 5.3 Updateability metrics

When the corpus is refreshed:

- IR diff is produced automatically
- generator output is deterministic
- release report highlights new symbols, changed signatures, added enums, and possible compatibility risks
- at least one smoke script still runs in Fusion after regeneration

## 6. Scope and Non-Goals

### 6.1 In scope for the first execution phase

- corpus ingestion from `FusionAPIReference`
- parser pipeline and IR
- deterministic code generation
- runtime core
- compact layer for design and solid-modeling basics
- tests, smoke scripts, and benchmarks
- release diff tooling
- optional add-in test harness
- optional MCP-driven integration harness if available locally

### 6.2 Explicitly out of scope for the first execution phase

Do not start with these:

- full CAM compact wrappers
- full UI command abstraction for every command feature
- custom features
- complete custom graphics abstraction
- generative art DSL
- full assembly authoring abstraction
- perfect automation of Fusion GUI interactions

These can come later. The first goal is a robust generated foundation plus a thin, useful compact layer.

## 7. Source Corpus and Reference Usage

### 7.1 Official corpus

Use the official Autodesk repository as the primary local corpus:

- `AutodeskFusion360/FusionAPIReference`

Treat its contents as follows:

- `Fusion_API_Python_Reference/defs/`
  - primary source for Python-facing names, signatures, return annotations, and type hints

- `Fusion_API_CPP_Reference/include/`
  - verifier for enums, overloads, missing type detail, inheritance, and method prototypes

- `Fusion_API_Documentation/files/`
  - semantic layer for descriptions, sections, examples, sample links, version metadata, and workflow hints

- `processed_docs/md/`
  - if present, use as preferred cleaned prose source before raw HTML

### 7.2 Sample repositories

Use Autodesk GitHub sample repositories and `FusionMCPSample` only as:

- regression fixtures
- example call chains to compress
- optional integration test harness inspiration

Do not infer API completeness from them.

### 7.3 Legal handling

The reference corpus is licensed separately from the library code.

Implementation rule:

- do not ship Autodesk HTML documentation or large copied doc text inside the runtime package
- generated metadata shipped with runtime should be limited to what is necessary for operation
- keep the full corpus as an external dev-time input
- if redistributing generated metadata derived from Autodesk documentation, do a separate licensing review

## 8. High-Level Architecture

The system has three major code areas.

### 8.1 Build system

This lives outside Fusion and can use external dependencies.

Responsibilities:

- load corpus
- parse Python defs
- parse C++ headers
- parse docs
- merge into IR
- apply manual override rules
- generate metadata and code
- diff current API against previous snapshots
- generate docs for humans and agents

### 8.2 Runtime library

This is the package copied into Fusion.

Responsibilities:

- wrap Autodesk objects
- adapt arguments and return values
- provide explicit context helpers
- provide unit-safe values and transient geometry helpers
- expose compact wrapper classes
- preserve raw access
- load generated registries

### 8.3 Integration harnesses

Responsibilities:

- smoke scripts runnable directly in Fusion
- add-in bundle for command testing
- optional MCP-driven automation for screenshot or script execution

## 9. Repository Layout

Create the repository with this structure.

```text
fusion_sparse/
  pyproject.toml
  README.md
  implementation_plan.md
  LICENSE
  .gitignore

  docs/
    compact_reference.md
    raw_mapping.md

  corpus/
    README.md
    FusionAPIReference/               # optional git submodule or local checkout, ignored if absent
    corpus.lock.json

  rules/
    aliases.yaml
    compact_exports.yaml
    compact_policy.yaml
    compact_reference.yaml
    family_overrides.yaml
    enum_aliases.yaml
    exclusions.yaml
    doc_overrides.yaml
    wrapper_dispatch.yaml

  tools/
    __init__.py
    cli.py
    corpus_loader.py
    parse_python_defs.py
    parse_cpp_headers.py
    parse_docs.py
    build_ir.py
    apply_rules.py
    generate_metadata.py

  build/
    ir/
    generated/
    reports/

  src/
    fusion_sparse/
      __init__.py
      runtime/
        adapter.py
        refs.py
        context.py
        values.py
        geom.py
        enums.py
        errors.py
        _adsk.py
      compact/
        __init__.py
        app.py
        design.py
        component.py
        sketch.py
        extrude.py
      generated/
        __init__.py
        compact_policy.py
        compact_surface.py
        public_api.py
        enum_index.py
        wrapper_dispatch.py
        release_info.py

  tests/
    unit/
    golden/
    integration/
      fusion_scripts/
      fusion_addin/

  benchmarks/
    baselines/
    compact/

  examples/
    simple_extrude.py
    sketch_playground.py
    context_debug.py

  fusion/
    scripts/
      FusionSparseSmoke/
    addins/
      FusionSparseWorkbench/
```

Notes:

- `build/` is generated and can be cleaned.
- `src/fusion_sparse/generated/` is generated but committed once the project stabilizes.
- `fusion/` contains test bundles that can be linked into Fusion's Scripts and Add-Ins UI.

## 9A. Fusion deployment model

Develop the codebase as a normal Python project outside Fusion, but deploy testable artifacts into Fusion-compatible script and add-in bundles.

### Script bundle pattern

Use a smoke script bundle like this:

```text
fusion/scripts/FusionSparseSmoke/
  FusionSparseSmoke.py
  FusionSparseSmoke.manifest
  lib/
    fusion_sparse/
```

The script entry file should be tiny and only import the library and call a test function.

### Add-in bundle pattern

Use an add-in bundle like this, following the Autodesk Python add-in template shape:

```text
fusion/addins/FusionSparseWorkbench/
  FusionSparseWorkbench.py
  FusionSparseWorkbench.manifest
  config.py
  commands/
    smoke_command/
      __init__.py
      entry.py
      resources/
  lib/
    fusion_sparse/
    fusion360utils/
```

Important implementation rules:

- Keep the add-in top-level `.py` file minimal, mirroring the official template pattern with `run(context)` and `stop(context)`.
- Put most test command logic under `commands/.../entry.py`.
- Do not make the library depend on `fusion360utils`; that dependency belongs only to the optional add-in harness.
- Provide a `tools/sync_to_fusion.py` script that copies or syncs the runtime package into `lib/fusion_sparse/` for both the smoke script and the workbench add-in.
- Prefer linked script and add-in folders in Fusion during development so the local repo remains the editable source of truth.

### `sync_to_fusion.py` responsibilities

Implement `tools/sync_to_fusion.py` with these capabilities:

- locate target Fusion script/add-in directories from configuration or CLI flags
- copy `src/fusion_sparse/` into target `lib/fusion_sparse/`
- optionally copy smoke scripts and workbench add-in files
- remove stale generated files in target bundles before syncing
- preserve only source `.py` files and required metadata, not `.pyc`
- print a clear summary of what was synced

### Acceptance criteria

- After sync, Fusion can see the linked script or add-in.
- The smoke script can import `fusion_sparse` from the local repo copy.
- The workbench add-in follows the official Autodesk template structure closely enough that a Fusion developer immediately recognizes it.

## 10. Technology Choices

### 10.1 Build-time dependencies

Use these build-time libraries unless the local environment strongly suggests an equivalent:

- `libcst` for parsing Python definitions and stubs
- `beautifulsoup4` and `lxml` for HTML parsing
- `pyyaml` for rule files
- `jinja2` for deterministic code generation templates
- `pydantic` or dataclasses for IR modeling
- `pytest` for unit tests
- optional `rich` or `typer` for CLI ergonomics

### 10.2 Runtime dependencies

Runtime inside Fusion must use:

- standard library only
- `adsk.core`
- `adsk.fusion`
- `adsk.cam`

No third-party runtime dependencies.

### 10.3 Python compatibility

Build tooling can target a normal desktop Python version.

Runtime code must stay conservative and compatible with Fusion's embedded Python. Since Fusion updated embedded Python from 3.12 to 3.14 in January 2026, do not rely on shipping `.pyc` files or version-specific bytecode artifacts. Ship source `.py` files only.

## 11. Detailed Implementation Phases

## Phase 0: Bootstrap and conventions

### Goal

Create a stable repo skeleton and execution model before touching the parser.

### Tasks

1. Create repository structure shown above.
2. Add `pyproject.toml` with build and dev dependencies.
3. Add `Makefile` or task aliases if desired, but do not require it.
4. Add `README.md` with one-paragraph project summary.
5. Add `rules/` placeholder files with comments.
6. Add `tools/cli.py` entry point with commands:
   - `build-ir`
   - `generate`
   - `diff`
   - `measure`
   - `sync-fusion`
7. Add `corpus/README.md` explaining how to place or submodule the Autodesk corpus.
8. Add `corpus/corpus.lock.json` schema now even if empty.

### Acceptance criteria

- Repo installs in a local virtual environment.
- `python -m tools.cli --help` works.
- Empty build commands fail clearly with missing corpus instructions.

## Phase 1: Corpus loader and lockfile

### Goal

Load the local Autodesk corpus deterministically and record exactly what was used.

### Tasks

1. Implement `tools/corpus_loader.py`.
2. Detect repository root for `FusionAPIReference`.
3. Verify presence of:
   - `Fusion_API_Python_Reference/defs`
   - `Fusion_API_CPP_Reference/include`
   - `Fusion_API_Documentation/files`
4. Detect optional:
   - `processed_docs/md`
   - `tools/generate_index.py`
   - `llms.txt`
5. Record a corpus manifest:
   - source root path
   - commit hash if available from `.git`
   - timestamp
   - discovered paths
   - counts of files per source type
6. Write `corpus/corpus.lock.json`.
7. Add a build report at `build/reports/corpus_summary.md`.

### Acceptance criteria

- Build reports list the discovered corpus and file counts.
- Failure modes are explicit if required directories are missing.
- Lockfile is deterministic.

## Phase 2: Parse Python definitions

### Goal

Extract the Python-facing API surface from Autodesk's defs.

### Parser requirements

Use `libcst` or an equally robust parser. Do not depend on fragile regex for Python defs.

### Extract at minimum

For each module, class, function, method, property, enum-like constant, and assignment:

- module path
- namespace inferred from module path
- class name
- fully qualified symbol name
- kind: module, class, method, property, function, enum, constant
- decorators
- parameter list
- parameter annotations
- default values as strings
- return annotations
- docstring if present
- staticmethod/classmethod/property status
- inheritance bases
- source path and line spans

### Important behavior

- Support both `.py` and `.pyi` style syntax.
- Preserve unknown type names as raw strings.
- Do not try to resolve every import at first.
- Do preserve enough module information to reconstruct fully qualified names.

### Output

Write:

- `build/ir/python_symbols.json`

### Acceptance criteria

- Can parse the corpus without crashing.
- Produces symbols for core sample classes such as `Application`, `Design`, `Component`, `Sketch`, `ExtrudeFeatures`, `ValueInput`.
- Unit tests cover representative parser cases.

## Phase 3: Parse C++ headers

### Goal

Use headers to verify and enrich types, not to replace the Python defs parser.

### Strategy

Start simple. Parse only what is high value:

- enum names and values
- class declarations
- inheritance
- method signatures where they are easy to extract
- static methods
- header-defined namespaces

Do not block the project on full C++ parsing.

### Recommended implementation

Start with a conservative regex or line-oriented parser because this is a verifier pass, not the primary source. If local tooling already has a workable C++ parser, use it, but do not make that a hard dependency.

### Extract at minimum

- enum name
- enum members and numeric values if present
- class name
- namespace
- method name
- return type
- parameter types and names
- static flag if inferable
- source header path

### Output

Write:

- `build/ir/cpp_symbols.json`
- `build/ir/cpp_enums.json`

### Acceptance criteria

- Enum extraction works for `DocumentTypes`, `FeatureOperations`, `ExtentDirections`, and a few other core enums.
- Header parsing enriches missing type detail where Python defs are thin.
- Parser never crashes the build if a header is not understood; it logs and continues.

## Phase 4: Parse docs and semantic enrichment

### Goal

Enrich the IR with prose, examples, version info, section structure, and workflow hints.

### Strategy

Use `processed_docs/md` if present. Otherwise parse the HTML under `Fusion_API_Documentation/files`.

### Extract at minimum

From each page, when available:

- page title
- page kind inferred from title or file stem:
  - object
  - method
  - property
  - sample
  - user-manual topic
- description section
- syntax section
- parameters table
- return value section
- samples list
- version section
- headings hierarchy
- code blocks
- related links
- owner object
- namespace
- header file
- file stem

### Important heuristics

- Normalize `Application_get.htm` to symbol key `Application.get`
- Normalize `ValueInput_createByString.htm` to `ValueInput.createByString`
- Preserve sample page references
- Strip navigation/footer boilerplate aggressively
- Keep code blocks and parameter tables intact

### Output

Write:

- `build/ir/doc_pages.json`
- `build/ir/doc_symbol_links.json`

### Acceptance criteria

- Can resolve docs for:
  - `Application.get`
  - `Documents.add`
  - `ValueInput.createByString`
  - `ValueInput.createByReal`
  - `ExtrudeFeatures.addSimple`
  - `ExtrudeFeatures.createInput`
- Version metadata is captured when present.
- Sample associations are captured.

## Phase 5: Build the normalized IR

### Goal

Merge all sources into a single canonical API representation.

### IR design principles

- One canonical symbol record per logical API symbol
- Multiple source evidence entries per symbol
- Preserve ambiguity instead of guessing
- Track provenance for every field

### Required IR schema

At minimum each symbol record should support:

```json
{
	"id": "adsk.core.Application.get",
	"kind": "method",
	"name": "get",
	"owner": "adsk.core.Application",
	"namespace": "adsk.core",
	"display_name": "Application.get",
	"python_path": "adsk.core.Application.get",
	"cpp_qualified_name": "adsk::core::Application::get",
	"source_paths": [
		"Fusion_API_Python_Reference/defs/...",
		"Fusion_API_CPP_Reference/include/...",
		"Fusion_API_Documentation/files/Application_get.htm"
	],
	"signatures": [
		{
			"language": "python",
			"params": [],
			"returns": "Application",
			"static": true
		}
	],
	"doc": {
		"title": "Application.get Method",
		"description": "Access to the root Application object.",
		"parameters": [],
		"return_description": "Return the root Application object or null if it failed.",
		"samples": [],
		"introduced_in": "August 2014"
	},
	"traits": {
		"collection_like": false,
		"static_constructor": true,
		"compact_candidate": true
	},
	"provenance": {
		"signature_source": "python_defs",
		"doc_source": "html"
	}
}
```

### Merge rules

1. Use Python defs as canonical Python signature source where available.
2. Use C++ to verify types and fill gaps.
3. Use docs to enrich descriptions and versions.
4. If sources disagree:
   - preserve both values in provenance
   - choose one canonical value using precedence
   - emit a warning entry in `build/reports/merge_conflicts.md`

### Additional derived traits

Compute these during IR building:

- `collection_like`
  - if object has `count` and `item`
- `has_add`
- `has_create_input`
- `has_add_simple`
- `supports_samples`
- `is_enum`
- `is_input_object`
- `returns_base_product`
- `is_static_constructor`
- `is_cast_helper`

### Output

Write:

- `build/ir/symbols.json`
- `build/ir/enums.json`
- `build/ir/families.json`
- `build/reports/merge_conflicts.md`

### Acceptance criteria

- IR contains stable IDs and provenance.
- Re-running build yields identical output ordering.
- Conflict report is deterministic.

## Phase 6: Manual rule system

### Goal

Define the small handwritten policy layer that drives ergonomic generation.

### Rule files

Implement these files:

#### `rules/aliases.yaml`

Maps compact public names to symbols or wrapper methods.

Example:

```yaml
exports:
  new_design: adsk.core.Documents.add:FusionDesignDocumentType
  app: runtime.app
  ctx: runtime.ctx
  p: runtime.geom.point
  vec: runtime.geom.vector
  oc: runtime.geom.object_collection
```

#### `rules/enum_aliases.yaml`

Maps readable compact enum aliases.

Example:

```yaml
FeatureOperations:
  new_body: NewBodyFeatureOperation
  new_component: NewComponentFeatureOperation
  join: JoinFeatureOperation
  cut: CutFeatureOperation
  intersect: IntersectFeatureOperation
```

#### `rules/family_overrides.yaml`

Defines builder families and high-value compact methods.

Example:

```yaml
families:
  ExtrudeFeatures:
    compact_method: extrude
    simple_method: addSimple
    builder_input: createInput
    builder_terminal: add
```

#### `rules/exclusions.yaml`

Symbols or pages to skip from compact generation.

#### `rules/compact_exports.yaml`

Controls what the package exports publicly in `fusion_sparse.__init__`.

### Acceptance criteria

- Generator can consume rule files and fail clearly on invalid entries.
- Manual rule layer remains small and focused.
- No generated logic is hardcoded in handwritten runtime if it belongs in rules.

## Phase 7: Generate metadata artifacts

### Goal

Generate the minimal but complete metadata needed by the runtime and by update tooling.

### Generate at minimum

- `build/generated/symbol_index.py`
- `src/fusion_sparse/generated/enum_index.py`
- `src/fusion_sparse/generated/wrapper_dispatch.py`
- `build/generated/families.py`
- `src/fusion_sparse/generated/release_info.py`

### Content requirements

#### `symbol_index.py`

- compact searchable mapping of symbol IDs to metadata
- enough to support debugging, introspection, and future doc tooling

#### `enum_index.py`

- canonical enum aliases
- reverse lookup from compact alias to Autodesk enum member

#### `wrapper_dispatch.py`

- map `objectType` strings or class names to compact wrapper classes

#### `families.py`

- collection and builder family metadata

#### `release_info.py`

- corpus lock details
- generated timestamp
- corpus commit or version metadata if known

### Acceptance criteria

- Generated files are importable in a normal Python environment without `adsk`.
- Runtime can use them lazily when `adsk` exists.

## Phase 8: Runtime core

### Goal

Implement the handwritten runtime that everything else builds on.

### 8.1 `runtime/errors.py`

Define a small error hierarchy:

- `FusionSparseError`
- `InvalidContextError`
- `UnitCoercionError`
- `UnsupportedOperationError`
- `GenerationMismatchError`

### 8.2 `runtime/adapter.py`

This is one of the most important files.

Responsibilities:

- `unwrap(value)`:
  - compact wrapper to raw Autodesk object
  - recursive for tuples/lists/dicts where appropriate
- `wrap(value)`:
  - raw Autodesk object to wrapper
  - recursive for tuples
  - leave primitives untouched
  - do not automatically convert Autodesk vector returns into Python lists globally
- `wrap_callable(raw_callable)`:
  - returns a small proxy that unwraps inputs and wraps outputs
  - used for delegated raw method access

### 8.3 `runtime/refs.py`

Define a base wrapper:

```python
class Ref:
    raw: object

    @property
    def object_type(self) -> str: ...
    @property
    def class_type(self) -> str: ...
    @property
    def is_valid(self) -> bool: ...
```

Behavior rules:

- `.raw` is always available
- raw camelCase members can be delegated through `__getattr__`
- compact methods use snake_case names so they do not collide with raw camelCase names
- wrapper equality should delegate to Autodesk object equality semantics where possible

### 8.4 `runtime/context.py`

Centralize application and design resolution.

Required helpers:

- `app()`
- `ui()`
- `active_product()`
- `active_design(strict=True)`
- `ctx()` returning an object with:
  - `.app`
  - `.ui`
  - `.product`
  - `.design`
  - `.doc`
  - `.root`

Also add:

- `new_design()`
- `new_or_active_design()`

Important rule:

- `new_design()` must document or guard against usage during command transactions because `Documents.add` is not allowed inside command-related events.

### 8.5 `runtime/values.py`

Implement the unit-safe value system.

Required public helpers:

- `v(value)` generic coercion
- `u.mm(x)`
- `u.cm(x)`
- `u.m(x)`
- `u.inch(x)` or `u.in_(x)` if naming conflict
- `u.deg(x)`
- `u.rad(x)`
- `u.expr(text)`

Rules:

- number -> `ValueInput.createByReal`
- string -> `ValueInput.createByString`
- already a `ValueInput` -> pass through
- wrapper around `ValueInput` -> unwrap
- explicit unit helpers build strings or internal-unit values consistently

### 8.6 `runtime/geom.py`

Implement transient geometry helpers:

- `p(x, y, z=0)`
- `vec(x, y, z=0)`
- `mat_identity()`
- `oc(*items)` for `ObjectCollection.create()` plus population

Point coercion rules:

- `(x, y)` -> `Point3D.create(x, y, 0)`
- `(x, y, z)` -> `Point3D.create(x, y, z)`
- already point object -> pass through

### 8.7 `runtime/enums.py`

Expose compact enum alias namespaces:

- `op.new_body`
- `op.new_component`
- `op.join`
- `op.cut`
- `op.intersect`
- `dir.positive`
- `dir.negative`
- `dir.symmetric`

### 8.8 Runtime feature detection

Keep feature detection inside the thin runtime instead of introducing a separate compatibility module.

Rules:

- prefer capability checks over explicit version checks
- use `hasattr` against raw objects when possible
- keep feature-specific checks close to the compact helper or runtime context that needs them

### Acceptance criteria

- Runtime imports cleanly inside Fusion.
- Wrapper adaptation works for raw Autodesk objects and tuples.
- Public helpers work for basic context and value coercion.

## Phase 9: Compact wrapper classes, v0

### Goal

Implement a high-value compact layer for the core modeling workflow.

Use handwritten wrapper classes backed by generated dispatch tables.

### 9.1 `compact/app.py`

Provide top-level exported helpers:

- `app()`
- `ctx()`
- `new_design()`

### 9.2 `compact/design.py`

Implement `DesignRef`.

Required properties and methods:

- `.root`
- `.params` optional if easy
- `.mode` optional compatibility helper if design intent fields exist
- `.component(name=None)` optional future helper

### 9.3 `compact/component.py`

Implement `ComponentRef`.

Required methods for v0:

- `sketch(plane)`
- `extrude(profile, distance=None, op="new_body")`
- `occurrences()` optional
- `new_occurrence(transform=None)` optional if easy

Plane resolution rules:

- `"xy"` -> `xYConstructionPlane`
- `"xz"` -> `xZConstructionPlane`
- `"yz"` -> `yZConstructionPlane`
- raw plane object -> use directly

### 9.4 `compact/sketch.py`

Implement `SketchRef`.

Required methods for v0:

- `line(a, b)`
- `circle(center, r)`
- `rect(a, b)`
- `point(x, y, z=0)` optional
- `profile(i=0)`
- `profiles()`

Implementation detail:

- `circle((0, 0), r="20 mm")` should coerce center via `p` and radius via value rules if needed
- sketch primitives should return wrapped sketch entities where possible

### 9.5 `compact/extrude.py`

Implement both compact simple path and builder path.

#### Simple path

If `distance` is provided, use `ExtrudeFeatures.addSimple`.

Example:

```python
root.extrude(sk.profile(), "10 mm", op="new_body")
```

#### Builder path

If `distance` is omitted or advanced options are chained, return `ExtrudeBuilder`.

Required builder methods for v0:

- `one_side(distance, direction="positive")`
- `symmetric(distance)`
- `solid(flag=True)`
- `surface()`
- `taper(angle)`
- `build()`

Optional builder methods if straightforward:

- `participant_bodies(*bodies)`
- `from_entity(entity, offset=None)`
- `to_entity(entity, offset=None, chained=None)`

#### Internal mapping

- simple path -> `ExtrudeFeatures.addSimple`
- builder path -> `ExtrudeFeatures.createInput` then `ExtrudeFeatures.add`

### Acceptance criteria

- The compact API can create a new design, sketch a circle, and extrude it.
- The simple path uses `addSimple`.
- The builder path uses `createInput` and `add`.
- Raw access is preserved.

## Phase 10: Dynamic dispatch and raw passthrough

### Goal

Avoid generating thousands of handwritten wrapper methods while preserving broad compatibility.

### Implementation approach

Use generated dispatch tables to wrap only known Autodesk objects into the right compact wrapper class.

Recommended wrapper strategy:

1. `wrap(raw_obj)` inspects `objectType` or Python type and returns:
   - `DesignRef`
   - `ComponentRef`
   - `SketchRef`
   - generic `Ref`
   - etc.

2. `Ref.__getattr__` delegates unknown attributes:
   - if attribute is a raw Autodesk object, wrap it
   - if attribute is callable, return a callable proxy that unwraps inputs and wraps outputs
   - else return attribute unchanged

### Important cautions

- Do not let dynamic passthrough hide compact method errors
- Prefer compact snake_case names so raw camelCase members remain accessible
- If passthrough becomes fragile in some edge cases, keep `.raw` as the official escape hatch

### Acceptance criteria

- Unknown raw members are still reachable on wrappers
- Returned Autodesk objects are wrapped automatically in common cases
- Returned tuples preserve wrapping of contained Autodesk objects

## Phase 11: Generated docs and introspection aids

### Goal

Make the library itself agent-friendly.

### Tasks

Generate:

- `docs/compact_reference.md`
- `docs/raw_mapping.md`
- `docs/update_workflow.md`
- `build/reports/symbol_stats.md`

The compact reference should include, for each public compact helper:

- public compact name
- raw Autodesk mapping
- arguments
- common examples
- escape hatch notes

This is important because coding agents will search this project and should be able to map compact helpers back to the official API quickly.

### Acceptance criteria

- Documentation is generated from metadata plus manual templates
- Public compact methods clearly state their raw mapping

## Phase 12: Testing

## 12.1 Unit tests outside Fusion

These must run in a normal Python environment.

Cover:

- corpus loading
- parser extraction
- IR merge behavior
- rule application
- code generation determinism
- adapter unwrap/wrap with mocked Autodesk-like objects
- enum alias resolution
- point and unit coercion helpers with mocked `adsk` factory functions where possible

## 12.2 Golden tests

Store golden snapshots for:

- a few parsed symbol records
- generated enum alias files
- generated wrapper dispatch
- generated docs

Golden tests should fail on unintentional generator drift.

## 12.3 Integration tests inside Fusion

Create smoke scripts under `tests/integration/fusion_scripts/`:

1. `smoke_context.py`
   - resolve app, design, root

2. `smoke_new_design.py`
   - create a design document

3. `smoke_sketch_extrude.py`
   - sketch a circle and extrude

4. `smoke_builder_extrude.py`
   - use the builder path

5. `smoke_raw_escape_hatch.py`
   - call raw Autodesk API through wrapper `.raw`

### Add-in test bundle

Create `fusion/addins/FusionSparseWorkbench/` based on the Python add-in template structure:

- top-level `.py`, `.manifest`, `config.py`
- `commands/`
- `lib/` or packaged library copy

Use it to validate command integration later, but do not block core progress on it.

### Manual boundary

Assume some integration steps may require Fusion to be opened and a script or add-in to be run manually unless a local MCP or automation harness exists.

## Phase 13: Benchmarking and sparsity measurement

### Goal

Quantify value for coding agents.

### Tasks

1. Add baseline scripts modeled after official call chains.
2. Add compact scripts with equivalent behavior.
3. Implement `tools/measure_sparsity.py` to compute:
   - characters
   - lines
   - tokens
   - `adsk.` symbol count
4. Generate `build/reports/sparsity_report.md`

### Benchmark pairs to include

1. new design document
2. circle sketch
3. rectangle sketch
4. simple extrude
5. builder extrude

### Acceptance criteria

- Report is generated automatically
- Compact layer clearly beats the baseline on the target metrics

## Phase 14: Release diff and update pipeline

### Goal

Keep the project maintainable as Fusion changes.

### Tasks

1. Snapshot previous IR under `build/ir/snapshots/` or `snapshots/`.
2. Implement `tools/diff_ir.py`.
3. Produce reports:
   - added symbols
   - removed symbols
   - changed signatures
   - changed enums
   - new doc pages
   - release-risk summary
4. Detect high-risk topics:
   - design intent changes
   - new design modes
   - new external component APIs
   - embedded Python version changes

### Update workflow

On corpus update:

1. refresh corpus checkout
2. rebuild IR
3. run diff report
4. inspect merge conflicts
5. update rule overrides only if needed
6. regenerate code
7. run unit tests
8. run at least one Fusion smoke script
9. inspect benchmark drift

### Acceptance criteria

- Update is mostly mechanical
- Diff report is readable and deterministic

## Phase 15: Optional MCP or automation harness

### Goal

Allow local automation if the environment already supports it.

This is optional and should not block the core library.

### Option A: Use local Fusion add-in harness only

Use linked script/add-in folders and manual execution in Fusion.

### Option B: Use `FusionMCPSample` patterns or a local MCP server

If a local Fusion MCP setup already exists, use it for:

- executing smoke scripts
- capturing screenshots
- verifying outcomes
- keeping Fusion API calls on the main thread via custom-event-based task routing

Do not make MCP a required dependency of the core library.

### Important rule

Never call Fusion API from background threads directly. If background execution is needed in an add-in or MCP harness, marshal work to the main thread using Fusion's event system.

## 16. API Design Rules for the Compact Layer

These rules are mandatory.

### Rule 1: Compact methods are snake_case

Examples:

- `new_design`
- `one_side`
- `participant_bodies`

Reason:

- avoids collisions with raw Autodesk camelCase members
- is Pythonic
- makes it obvious what belongs to the compact layer

### Rule 2: Raw Autodesk members remain camelCase

Examples:

- `component.raw.features.extrudeFeatures`
- `component.features`
- `extrude_input.setDistanceExtent(...)`

If passthrough is enabled, raw camelCase members should still be callable directly on wrappers.

### Rule 3: `.raw` is the escape hatch

Never remove this.

### Rule 4: Bare numbers mean internal units

Examples:

- `5` means 5 cm when used as a length
- `0.5` means 0.5 rad when used as an angle

### Rule 5: Strings mean Fusion expressions

Examples:

- `"10 mm"`
- `"90 deg"`
- `"d0 / 2"`

### Rule 6: Do not hide context

Examples:

Good:

```python
root = design.root
sk = root.sketch("xy")
```

Bad:

```python
sk = sketch("xy")
```

unless a context object is explicitly being used and makes the target obvious.

### Rule 7: Provide a short path and a full path

Examples:

- `extrude(..., "10 mm")` for simple use
- `extrude(...).one_side(...).build()` for advanced use

### Rule 8: Preserve wrapper composability

Everything should accept either:

- compact wrapper objects
- raw Autodesk objects
- simple coercible literals such as tuples or expressions

## 17. Exact First-Cut Public API

This is the public surface to implement first.

```python
import fusion_sparse as fx

fx.app()
fx.ctx()
fx.new_design()

fx.p(x, y, z=0)
fx.vec(x, y, z=0)
fx.oc(*items)
fx.u.mm(x)
fx.u.cm(x)
fx.u.deg(x)
fx.u.rad(x)
fx.u.expr(text)

design.root
component.sketch("xy" | "xz" | "yz" | raw_plane)
component.extrude(profile, distance=None, op="new_body")

sketch.line(a, b)
sketch.circle(center, r)
sketch.rect(a, b)
sketch.profile(i=0)
sketch.profiles()

builder.one_side(distance, direction="positive")
builder.symmetric(distance)
builder.solid(flag=True)
builder.surface()
builder.taper(angle)
builder.build()
```

Do not expand this public surface until the generator and runtime are stable.

## 18. Concrete File-Level Work Plan

Implement in this order.

### Step 1

Create repo skeleton, `pyproject.toml`, CLI scaffolding, placeholder rules.

### Step 2

Implement corpus loader and lockfile.

### Step 3

Implement Python defs parser with tests.

### Step 4

Implement C++ enum and signature verifier parser.

### Step 5

Implement doc parser and symbol-link normalization.

### Step 6

Implement IR merge pipeline and write stable JSON outputs.

### Step 7

Implement rule loader and override application.

### Step 8

Generate metadata artifacts only. Do not generate runtime code yet.

### Step 9

Implement handwritten runtime core:

- errors
- adapter
- refs
- values
- geom
- context
- enums

### Step 10

Implement compact wrappers:

- DesignRef
- ComponentRef
- SketchRef
- ExtrudeBuilder

### Step 11

Hook wrapper dispatch to generated metadata.

### Step 12

Create smoke scripts and run them in Fusion.

### Step 13

Implement sparsity benchmarks and report.

### Step 14

Implement release diff tooling.

### Step 15

Only after all of the above, add optional add-in harness and optional MCP integration.

## 19. Definition of Done for v0

The first execution phase is done when all of the following are true:

1. The project can ingest a local `FusionAPIReference` checkout and produce a merged IR.
2. The project can generate deterministic metadata artifacts.
3. The runtime library imports inside Fusion.
4. `fx.new_design()` works.
5. `root.sketch("xy")` works.
6. `sk.circle((0, 0), r="20 mm")` works.
7. `root.extrude(sk.profile(), "10 mm", op="new_body")` works.
8. The builder path works for at least one one-side extent case.
9. `.raw` access works.
10. Unit tests pass.
11. At least three Fusion smoke scripts run successfully.
12. A sparsity report is generated and shows clear code reduction for common workflows.
13. An update diff report can be generated from two IR snapshots.

## 20. Risk Register and Mitigations

### Risk: Python defs are incomplete or inconsistent

Mitigation:

- treat them as primary but not exclusive
- verify against headers and docs
- preserve ambiguity in IR

### Risk: C++ parsing is difficult

Mitigation:

- keep header parsing narrow and high-value
- use it mainly for enums and verification
- never block the build on perfect C++ parsing

### Risk: Dynamic passthrough becomes too magical

Mitigation:

- keep compact methods explicit
- keep `.raw` official and well-documented
- if needed, reduce passthrough scope and require `.raw` for edge cases

### Risk: Fusion runtime environment differs from local build Python

Mitigation:

- keep runtime stdlib-only
- avoid heavy modern features in runtime code
- ship `.py` only

### Risk: Command transaction rules break `new_design()`

Mitigation:

- document and guard
- keep document creation outside command execute contexts
- add integration coverage for script vs add-in scenarios

### Risk: New design intent modes affect behavior

Mitigation:

- compatibility layer should use feature detection
- smoke tests should include explicit checks if local Fusion version supports design intent

### Risk: Overbuilding too early

Mitigation:

- enforce the first-cut public API
- do not expand beyond sketch plus extrude until generator and tests are solid

## 21. Guidance to the Coding Agent

Implement the work in small, reviewable slices.

For every slice:

1. modify the smallest number of files possible
2. add or update tests immediately
3. regenerate outputs if generator behavior changed
4. never manually patch generated files
5. document any ambiguity in a report instead of guessing
6. preserve deterministic ordering in all generated artifacts
7. keep runtime code dependency-free
8. prefer simpler designs that preserve raw compatibility over elaborate abstractions

When uncertain about an API symbol:

1. inspect Python defs
2. inspect C++ headers
3. inspect docs
4. if still ambiguous, mark the IR field as uncertain and continue

Do not stall the project on perfect completeness.

## 22. Immediate Next Actions

The first concrete implementation session should do exactly this:

1. scaffold repo and CLI
2. add corpus loader
3. parse Python defs
4. build initial IR for a tiny allowlist:
   - `Application`
   - `Documents`
   - `DocumentTypes`
   - `ValueInput`
   - `Design`
   - `Component`
   - `Sketch`
   - `ExtrudeFeatures`
5. generate a minimal symbol index
6. implement `new_design`, `p`, `u`, `ComponentRef.sketch`, `SketchRef.circle`, and `ComponentRef.extrude`
7. create and run the first smoke script in Fusion

That thin slice proves the full architecture end-to-end. Only after it works should the implementation widen to the rest of the API surface.

## 23. Appendix: Key External References

These are the core external references this plan assumes are available locally or online:

- AutodeskFusion360/FusionAPIReference
- AutodeskFusion360/FusionMCPSample
- Fusion API User's Manual
- Fusion API Reference Manual
- Python Specific Issues
- Python Add-in Template
- Creating Scripts and Add-Ins
- Commands
- Working in a Separate Thread
- Understanding Units in Fusion
- Documents, Products, Components, Occurrences, and Proxies
- What's New in the Fusion API

The project should encode the useful parts of those references into generated metadata and handwritten runtime rules so that future development depends less on re-reading the raw sources.
