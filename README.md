# FusionSparse

FusionSparse is a generator-driven Python layer for the Autodesk Fusion API.

The project keeps the full raw `adsk.*` surface reachable while generating a smaller, cleaner, more token-sparse interface for common Design workspace workflows.

## Goals

- Keep raw Fusion access available at all times.
- Generate as much surface area as possible from Autodesk's official API corpus.
- Make common modeling code much shorter and easier for agents to read and write.
- Keep updates mechanical: refresh corpus, rebuild IR, regenerate artifacts, review diffs.

## Current scope

FusionSparse is focused on the Design workspace, not the whole Fusion app.

Current compact coverage includes:
- context/bootstrap
- sketches
- construction planes / axes / points
- extrude / revolve / sweep / loft / patch
- shell / draft / hole / fillet / chamfer
- combine / mirror / circular pattern / rectangular pattern
- move / offset / replace face / scale / split body / thread / trim

Everything else remains available through raw `adsk.*` access and `.raw`.

## Status

- generator pipeline is working end to end
- Autodesk corpus is pinned as a submodule
- IR build, diff, and regeneration are in place
- Fusion deployment exists for both scripts and add-ins
- official-vs-compact validation runs in real Fusion through MCP

Current proof points:
- `53/53` official-vs-compact sample pairs matched in real Fusion
- paired samples are `61.9%` smaller by characters and `52.7%` smaller by estimated tokens
- Design-workspace validated families: `41`

## Example

This is a real Autodesk sample workflow from `extrudeFeatures_addSimple_Sample.htm`, compared with the FusionSparse remake that produces the same result in real Fusion.

Official Autodesk style:

```python
import adsk.core
import adsk.fusion

def run(context):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)

    root_comp = design.rootComponent
    sketch = root_comp.sketches.add(root_comp.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(3, 2, 0))

    profile = sketch.profiles.item(0)
    distance = adsk.core.ValueInput.createByString("100 mm")
    operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    extrude_features = root_comp.features.extrudeFeatures
    extrude_features.addSimple(profile, distance, operation)
```

FusionSparse:

```python
import fusion_sparse as fx

def run(context):
    design = fx.new_design()
    root = design.root
    sketch = root.sketch("xy")
    sketch.rect((0, 0), (3, 2))
    profile = sketch.profile()
    root.extrude(profile, "100 mm")
```

Measured on this exact validated pair:
- lines: `23 -> 13` (`43.5%` smaller)
- characters: `871 -> 342` (`60.7%` smaller)
- estimated tokens: `176 -> 82` (`53.4%` smaller)

Benefits:
- less boilerplate around `Application`, document creation, casting, and feature collections
- much fewer API ceremony tokens for agents to read and write
- the code describes the modeling intent directly: sketch rectangle, get profile, extrude
- raw escape hatch is still available through `.raw` when the compact layer is not enough

## Repo shape

- [src/fusion_sparse](src/fusion_sparse): shipped library
- [tools](tools): parsers, generators, reporting, validation
- [rules](rules): handwritten policy
- [corpus/FusionAPIReference](corpus/FusionAPIReference): pinned Autodesk source corpus
- [fusion](fusion): Fusion script/add-in deployment assets
- [tests](tests): unit and integration coverage

## Useful commands

```bash
python -m tools.cli build-ir
python -m tools.cli generate --skip-build-ir
python -m tools.cli run-sample-pairs
python -m tools.cli map-coverage
python -m unittest discover -s tests/unit -p 'test_*.py'
```

## Generated docs and reports

- [compact_reference.md](docs/compact_reference.md)
- [raw_mapping.md](docs/raw_mapping.md)
- [update_workflow.md](docs/update_workflow.md)
- `build/reports/api_coverage_map.md`
- `build/reports/design_workspace_backlog.md`
- `build/reports/sample_pairs/sample_pairs_report.md`
