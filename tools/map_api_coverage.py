from __future__ import annotations

import ast
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from tools.apply_rules import load_rules
from tools.sample_pairs.rules import load_sample_pair_rules


CONTEXT_EXPORTS = {"app", "ui", "ctx", "new_design", "new_or_active_design"}
HELPER_EXPORTS = {"p", "vec", "oc", "u", "v", "op", "dir"}
HANDWRITTEN_DIRECT_SYMBOLS = {
    "app": ["adsk.core.Application"],
    "ui": ["adsk.core.Application.userInterface", "adsk.core.UserInterface"],
    "ctx": [
        "adsk.core.Application.activeProduct",
        "adsk.core.Application.activeDocument",
        "adsk.fusion.Design",
        "adsk.fusion.Design.rootComponent",
    ],
    "new_design": ["adsk.core.Application.documents", "adsk.core.Documents.add", "adsk.fusion.Design"],
    "new_or_active_design": ["adsk.core.Application.activeProduct", "adsk.fusion.Design"],
    "ComponentRef.extrude": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.extrudeFeatures",
        "adsk.fusion.ExtrudeFeatures.addSimple",
        "adsk.fusion.ExtrudeFeatures.createInput",
    ],
    "ExtrudeBuilder.one_side": [
        "adsk.fusion.DistanceExtentDefinition.create",
        "adsk.fusion.ExtrudeFeatureInput.setOneSideExtent",
    ],
    "ExtrudeBuilder.symmetric": ["adsk.fusion.ExtrudeFeatureInput.setSymmetricExtent"],
    "ExtrudeBuilder.through_all": [
        "adsk.fusion.ThroughAllExtentDefinition.create",
        "adsk.fusion.ExtrudeFeatureInput.setOneSideExtent",
    ],
    "ExtrudeBuilder.solid": ["adsk.fusion.ExtrudeFeatureInput.isSolid"],
    "ExtrudeBuilder.participant_bodies": ["adsk.fusion.ExtrudeFeatureInput.participantBodies"],
    "ExtrudeBuilder.build": ["adsk.fusion.ExtrudeFeatures.add"],
    "ComponentRef.plane": ["adsk.fusion.Component.constructionPlanes"],
    "PlaneHelper.offset": [
        "adsk.fusion.Component.constructionPlanes",
        "adsk.fusion.ConstructionPlanes.createInput",
        "adsk.fusion.ConstructionPlaneInput.setByOffset",
        "adsk.fusion.ConstructionPlanes.add",
    ],
    "PlaneHelper.angle": [
        "adsk.fusion.Component.constructionPlanes",
        "adsk.fusion.ConstructionPlanes.createInput",
        "adsk.fusion.ConstructionPlaneInput.setByAngle",
        "adsk.fusion.ConstructionPlanes.add",
    ],
    "PlaneHelper.between": [
        "adsk.fusion.Component.constructionPlanes",
        "adsk.fusion.ConstructionPlanes.createInput",
        "adsk.fusion.ConstructionPlaneInput.setByTwoPlanes",
        "adsk.fusion.ConstructionPlanes.add",
    ],
    "PlaneHelper.tangent": [
        "adsk.fusion.Component.constructionPlanes",
        "adsk.fusion.ConstructionPlanes.createInput",
        "adsk.fusion.ConstructionPlaneInput.setByTangent",
        "adsk.fusion.ConstructionPlanes.add",
    ],
    "PlaneHelper.edges": [
        "adsk.fusion.Component.constructionPlanes",
        "adsk.fusion.ConstructionPlanes.createInput",
        "adsk.fusion.ConstructionPlaneInput.setByTwoEdges",
        "adsk.fusion.ConstructionPlanes.add",
    ],
    "PlaneHelper.three_points": [
        "adsk.fusion.Component.constructionPlanes",
        "adsk.fusion.ConstructionPlanes.createInput",
        "adsk.fusion.ConstructionPlaneInput.setByThreePoints",
        "adsk.fusion.ConstructionPlanes.add",
    ],
    "PlaneHelper.tangent_at": [
        "adsk.fusion.Component.constructionPlanes",
        "adsk.fusion.ConstructionPlanes.createInput",
        "adsk.fusion.ConstructionPlaneInput.setByTangentAtPoint",
        "adsk.fusion.ConstructionPlanes.add",
    ],
    "PlaneHelper.on_path": [
        "adsk.fusion.Component.constructionPlanes",
        "adsk.fusion.ConstructionPlanes.createInput",
        "adsk.fusion.ConstructionPlaneInput.setByDistanceOnPath",
        "adsk.fusion.ConstructionPlanes.add",
    ],
    "ComponentRef.axis": ["adsk.fusion.Component.constructionAxes"],
    "AxisHelper.circular_face": [
        "adsk.fusion.Component.constructionAxes",
        "adsk.fusion.ConstructionAxes.createInput",
        "adsk.fusion.ConstructionAxisInput.setByCircularFace",
        "adsk.fusion.ConstructionAxes.add",
    ],
    "AxisHelper.perpendicular": [
        "adsk.fusion.Component.constructionAxes",
        "adsk.fusion.ConstructionAxes.createInput",
        "adsk.fusion.ConstructionAxisInput.setByPerpendicularAtPoint",
        "adsk.fusion.ConstructionAxes.add",
    ],
    "AxisHelper.between_planes": [
        "adsk.fusion.Component.constructionAxes",
        "adsk.fusion.ConstructionAxes.createInput",
        "adsk.fusion.ConstructionAxisInput.setByTwoPlanes",
        "adsk.fusion.ConstructionAxes.add",
    ],
    "AxisHelper.between_points": [
        "adsk.fusion.Component.constructionAxes",
        "adsk.fusion.ConstructionAxes.createInput",
        "adsk.fusion.ConstructionAxisInput.setByTwoPoints",
        "adsk.fusion.ConstructionAxes.add",
    ],
    "AxisHelper.edge": [
        "adsk.fusion.Component.constructionAxes",
        "adsk.fusion.ConstructionAxes.createInput",
        "adsk.fusion.ConstructionAxisInput.setByEdge",
        "adsk.fusion.ConstructionAxes.add",
    ],
    "AxisHelper.normal": [
        "adsk.fusion.Component.constructionAxes",
        "adsk.fusion.ConstructionAxes.createInput",
        "adsk.fusion.ConstructionAxisInput.setByNormalToFaceAtPoint",
        "adsk.fusion.ConstructionAxes.add",
    ],
    "ComponentRef.point": ["adsk.fusion.Component.constructionPoints"],
    "PointHelper.edges": [
        "adsk.fusion.Component.constructionPoints",
        "adsk.fusion.ConstructionPoints.createInput",
        "adsk.fusion.ConstructionPointInput.setByTwoEdges",
        "adsk.fusion.ConstructionPoints.add",
    ],
    "PointHelper.planes": [
        "adsk.fusion.Component.constructionPoints",
        "adsk.fusion.ConstructionPoints.createInput",
        "adsk.fusion.ConstructionPointInput.setByThreePlanes",
        "adsk.fusion.ConstructionPoints.add",
    ],
    "PointHelper.edge_plane": [
        "adsk.fusion.Component.constructionPoints",
        "adsk.fusion.ConstructionPoints.createInput",
        "adsk.fusion.ConstructionPointInput.setByEdgePlane",
        "adsk.fusion.ConstructionPoints.add",
    ],
    "PointHelper.center": [
        "adsk.fusion.Component.constructionPoints",
        "adsk.fusion.ConstructionPoints.createInput",
        "adsk.fusion.ConstructionPointInput.setByCenter",
        "adsk.fusion.ConstructionPoints.add",
    ],
    "PointHelper.at": [
        "adsk.fusion.Component.constructionPoints",
        "adsk.fusion.ConstructionPoints.createInput",
        "adsk.fusion.ConstructionPointInput.setByPoint",
        "adsk.fusion.ConstructionPoints.add",
    ],
    "SketchRef.text": [
        "adsk.fusion.Sketch.sketchTexts",
        "adsk.fusion.SketchTexts.createInput2",
        "adsk.fusion.SketchTextInput.setAsMultiLine",
        "adsk.fusion.SketchTextInput.fontName",
        "adsk.fusion.SketchTextInput.isHorizontalFlip",
        "adsk.fusion.SketchTextInput.isVerticalFlip",
        "adsk.fusion.SketchTexts.add",
    ],
    "SketchRef.text_path": [
        "adsk.fusion.Sketch.sketchTexts",
        "adsk.fusion.SketchTexts.createInput2",
        "adsk.fusion.SketchTextInput.setAsAlongPath",
        "adsk.fusion.SketchTextInput.fontName",
        "adsk.fusion.SketchTextInput.isHorizontalFlip",
        "adsk.fusion.SketchTextInput.isVerticalFlip",
        "adsk.fusion.SketchTexts.add",
    ],
    "SketchRef.text_fit": [
        "adsk.fusion.Sketch.sketchTexts",
        "adsk.fusion.SketchTexts.createInput2",
        "adsk.fusion.SketchTextInput.setAsFitOnPath",
        "adsk.fusion.SketchTextInput.fontName",
        "adsk.fusion.SketchTextInput.isHorizontalFlip",
        "adsk.fusion.SketchTextInput.isVerticalFlip",
        "adsk.fusion.SketchTexts.add",
    ],
    "ComponentRef.revolve": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.revolveFeatures",
        "adsk.fusion.RevolveFeatures.createInput",
        "adsk.fusion.RevolveFeatureInput.setAngleExtent",
        "adsk.fusion.RevolveFeatures.add",
    ],
    "RevolveBuilder.angle": ["adsk.fusion.RevolveFeatureInput.setAngleExtent"],
    "RevolveBuilder.build": ["adsk.fusion.RevolveFeatures.add"],
    "ComponentRef.sweep": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.sweepFeatures",
        "adsk.fusion.Features.createPath",
        "adsk.fusion.SweepFeatures.createInput",
        "adsk.fusion.SweepFeatures.add",
    ],
    "ComponentRef.loft": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.loftFeatures",
        "adsk.fusion.LoftFeatures.createInput",
        "adsk.fusion.LoftSections.add",
        "adsk.fusion.LoftFeatures.add",
    ],
    "ComponentRef.patch": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.patchFeatures",
        "adsk.fusion.PatchFeatures.createInput",
        "adsk.fusion.PatchFeatures.add",
    ],
    "ComponentRef.shell": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.shellFeatures",
        "adsk.fusion.ShellFeatures.createInput",
        "adsk.fusion.ShellFeatures.add",
    ],
    "ComponentRef.draft": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.draftFeatures",
        "adsk.fusion.DraftFeatures.createInput",
        "adsk.fusion.DraftFeatureInput.setSingleAngle",
        "adsk.fusion.DraftFeatures.add",
    ],
    "ComponentRef.move": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.moveFeatures",
        "adsk.fusion.MoveFeatures.createInput2",
        "adsk.fusion.MoveFeatureInput.defineAsFreeMove",
        "adsk.fusion.MoveFeatures.add",
    ],
    "ComponentRef.offset": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.offsetFeatures",
        "adsk.fusion.OffsetFeatures.createInput",
        "adsk.fusion.OffsetFeatures.add",
    ],
    "ComponentRef.replace_face": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.replaceFaceFeatures",
        "adsk.fusion.ReplaceFaceFeatures.createInput",
        "adsk.fusion.ReplaceFaceFeatures.add",
    ],
    "ComponentRef.scale": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.scaleFeatures",
        "adsk.fusion.ScaleFeatures.createInput",
        "adsk.fusion.ScaleFeatureInput.setToNonUniform",
        "adsk.fusion.ScaleFeatures.add",
    ],
    "ComponentRef.split_body": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.splitBodyFeatures",
        "adsk.fusion.SplitBodyFeatures.createInput",
        "adsk.fusion.SplitBodyFeatures.add",
    ],
    "ComponentRef.thread": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.threadFeatures",
        "adsk.fusion.ThreadFeatures.threadDataQuery",
        "adsk.fusion.ThreadDataQuery.recommendThreadData",
        "adsk.fusion.ThreadInfo.create",
        "adsk.fusion.ThreadFeatures.createInput",
        "adsk.fusion.ThreadFeatures.add",
    ],
    "ComponentRef.trim": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.trimFeatures",
        "adsk.fusion.TrimFeatures.createInput",
        "adsk.fusion.TrimFeatureInput.bRepCells",
        "adsk.fusion.TrimFeatures.add",
    ],
    "ComponentRef.hole": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.holeFeatures",
        "adsk.fusion.HoleFeatures.createSimpleInput",
        "adsk.fusion.HoleFeatures.add",
    ],
    "HoleBuilder.counterbore": ["adsk.fusion.HoleFeatures.createCounterboreInput"],
    "HoleBuilder.countersink": ["adsk.fusion.HoleFeatures.createCountersinkInput"],
    "HoleBuilder.depth": ["adsk.fusion.HoleFeatureInput.setDistanceExtent"],
    "HoleBuilder.by_offsets": ["adsk.fusion.HoleFeatureInput.setPositionByPlaneAndOffsets"],
    "HoleBuilder.on_edge": ["adsk.fusion.HoleFeatureInput.setPositionOnEdge"],
    "HoleBuilder.at_center": ["adsk.fusion.HoleFeatureInput.setPositionAtCenter"],
    "HoleBuilder.by_points": ["adsk.fusion.HoleFeatureInput.setPositionBySketchPoints"],
    "HoleBuilder.build": ["adsk.fusion.HoleFeatures.add"],
    "ComponentRef.fillet": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.filletFeatures",
        "adsk.fusion.FilletFeatures.createInput",
        "adsk.fusion.FilletEdgeSetInputs.addConstantRadiusEdgeSet",
        "adsk.fusion.FilletFeatures.add",
    ],
    "ComponentRef.chamfer": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.chamferFeatures",
        "adsk.fusion.ChamferFeatures.createInput2",
        "adsk.fusion.ChamferEdgeSets.addEqualDistanceChamferEdgeSet",
        "adsk.fusion.ChamferFeatures.add",
    ],
    "ComponentRef.combine": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.combineFeatures",
        "adsk.fusion.CombineFeatures.createInput",
        "adsk.fusion.CombineFeatures.add",
    ],
    "ComponentRef.mirror": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.mirrorFeatures",
        "adsk.fusion.MirrorFeatures.createInput",
        "adsk.fusion.MirrorFeatures.add",
    ],
    "ComponentRef.circular_pattern": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.circularPatternFeatures",
        "adsk.fusion.CircularPatternFeatures.createInput",
        "adsk.fusion.CircularPatternFeatures.add",
    ],
    "ComponentRef.rect_pattern": [
        "adsk.fusion.Component.features",
        "adsk.fusion.Features.rectangularPatternFeatures",
        "adsk.fusion.RectangularPatternFeatures.createInput",
        "adsk.fusion.RectangularPatternFeatures.add",
    ],
}


def map_api_coverage(
    repo_root: str | Path | None = None,
    *,
    output_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
) -> dict[str, object]:
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent
    symbols = _load_json(root / "build" / "ir" / "symbols.json")
    families = _load_json(root / "build" / "ir" / "families.json")
    public_api = _parse_public_api(root / "src" / "fusion_sparse" / "generated" / "public_api.py")
    wrapper_dispatch = _extract_generated_json(
        root / "src" / "fusion_sparse" / "generated" / "wrapper_dispatch.py",
        "WRAPPER_CLASS_PATHS",
    )
    compact_properties = _extract_generated_json(
        root / "src" / "fusion_sparse" / "generated" / "compact_surface.py",
        "COMPACT_PROPERTIES",
    )
    compact_methods = _extract_generated_json(
        root / "src" / "fusion_sparse" / "generated" / "compact_surface.py",
        "COMPACT_METHODS",
    )
    wrapper_surfaces = _parse_wrapper_surfaces(root / "src" / "fusion_sparse" / "compact")
    sample_rules = load_sample_pair_rules(root / "rules" / "sample_pairs.yaml")
    sample_results = _load_sample_results(root / "build" / "reports" / "sample_pairs")
    rules = load_rules(root)

    symbols_by_id = {symbol["id"]: symbol for symbol in symbols}
    members_by_owner: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for symbol in symbols:
        owner = symbol.get("owner")
        name = symbol.get("name")
        if owner and name:
            members_by_owner[(owner, name)].append(symbol)

    wrapper_target_types = _wrapper_target_types(wrapper_dispatch)
    generated_entries = _generated_coverage_entries(
        compact_properties=compact_properties,
        compact_methods=compact_methods,
        wrapper_target_types=wrapper_target_types,
        members_by_owner=members_by_owner,
        symbols_by_id=symbols_by_id,
    )
    handwritten_entries = _handwritten_coverage_entries(symbols_by_id)
    direct_symbol_entries = generated_entries + handwritten_entries

    direct_symbol_ids = sorted({symbol_id for entry in direct_symbol_entries for symbol_id in entry["direct_symbols"]})
    direct_symbols = [symbols_by_id[symbol_id] for symbol_id in direct_symbol_ids if symbol_id in symbols_by_id]
    covered_family_ids = _covered_family_ids(direct_symbols, symbols_by_id, wrapper_target_types)
    validated_pages = {result["source_page"] for result in sample_results if result.get("equivalent")}
    validated_symbol_ids = sorted(
        symbol["id"]
        for symbol in direct_symbols
        if _symbol_links_to_sample_pages(symbol, validated_pages)
    )
    validated_symbols = [symbols_by_id[symbol_id] for symbol_id in validated_symbol_ids]
    validated_pair_count = sum(1 for result in sample_results if result.get("equivalent"))

    family_index = {family["id"]: family for family in families}
    uncovered_sample_families = [
        family
        for family in families
        if family.get("traits", {}).get("supports_samples") and family["id"] not in covered_family_ids
    ]
    uncovered_sample_families.sort(key=_uncovered_family_sort_key, reverse=True)

    namespace_rows = _namespace_rows(
        symbols=symbols,
        families=families,
        direct_symbols=direct_symbols,
        validated_symbols=validated_symbols,
        public_exports=public_api["exports"],
        wrapper_target_types=wrapper_target_types,
    )
    design_backlog = _build_design_backlog(
        families=families,
        symbols=symbols,
        covered_family_ids=covered_family_ids,
        validated_family_ids=_validated_family_ids(validated_symbols, symbols_by_id, wrapper_target_types),
        compact_policy=rules["compact_policy"],
    )

    payload = {
        "official_api": {
            "symbol_count": len(symbols),
            "family_count": len(families),
            "sample_support_family_count": sum(1 for family in families if family.get("traits", {}).get("supports_samples")),
            "namespace_symbol_counts": Counter(symbol["namespace"] for symbol in symbols),
            "namespace_family_counts": Counter(family["namespace"] for family in families),
        },
        "compact_surface": {
            "public_exports": public_api["exports"],
            "context_exports": [name for name in public_api["exports"] if name in CONTEXT_EXPORTS],
            "helper_exports": [name for name in public_api["exports"] if name in HELPER_EXPORTS],
            "wrapper_dispatch": wrapper_target_types,
            "wrapper_surfaces": wrapper_surfaces,
            "generated_entries": generated_entries,
            "handwritten_entries": handwritten_entries,
            "direct_symbol_ids": direct_symbol_ids,
            "covered_family_ids": sorted(covered_family_ids),
        },
        "validation": {
            "pair_count": len(sample_rules.get("pairs", [])),
            "validated_pair_count": validated_pair_count,
            "validated_pages": sorted(validated_pages),
            "validated_symbol_ids": validated_symbol_ids,
            "sample_results": sample_results,
        },
        "namespace_rows": namespace_rows,
        "uncovered_sample_families": [
            {
                "id": family["id"],
                "namespace": family["namespace"],
                "method_count": len(family.get("methods", [])),
                "traits": family.get("traits", {}),
                "reason": _gap_reason(family),
            }
            for family in uncovered_sample_families[:20]
        ],
        "design_backlog": design_backlog,
    }

    coverage_path = Path(output_path).resolve() if output_path else root / "build" / "reports" / "api_coverage_map.md"
    coverage_json_path = (
        Path(json_output_path).resolve() if json_output_path else root / "build" / "reports" / "api_coverage_map.json"
    )
    design_backlog_path = root / "build" / "reports" / "design_workspace_backlog.md"
    design_backlog_json_path = root / "build" / "reports" / "design_workspace_backlog.json"
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_json_path.parent.mkdir(parents=True, exist_ok=True)
    design_backlog_path.parent.mkdir(parents=True, exist_ok=True)
    design_backlog_json_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_path.write_text(_render_markdown(payload), encoding="utf-8")
    coverage_json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    design_backlog_path.write_text(_render_design_backlog_markdown(design_backlog), encoding="utf-8")
    design_backlog_json_path.write_text(json.dumps(design_backlog, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "output_path": str(coverage_path),
        "json_output_path": str(coverage_json_path),
        "design_backlog_path": str(design_backlog_path),
        "design_backlog_json_path": str(design_backlog_json_path),
        "symbol_count": len(symbols),
        "family_count": len(families),
        "direct_compact_symbol_count": len(direct_symbol_ids),
        "covered_family_count": len(covered_family_ids),
        "validated_pair_count": validated_pair_count,
        "validated_symbol_count": len(validated_symbol_ids),
    }


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_public_api(path: Path) -> dict[str, list[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    exports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                    exports = [elt.value for elt in node.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]
    return {"exports": exports}


def _extract_generated_json(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != name:
                continue
            value = node.value
            if not isinstance(value, ast.Call) or not value.args:
                continue
            payload = value.args[0]
            if isinstance(payload, ast.Constant) and isinstance(payload.value, str):
                return json.loads(payload.value)
    raise RuntimeError(f"Could not extract generated JSON constant {name} from {path}")


def _parse_wrapper_surfaces(compact_dir: Path) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    for path in sorted(compact_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods: list[str] = []
                properties: list[str] = []
                for item in node.body:
                    if not isinstance(item, ast.FunctionDef) or item.name.startswith("_"):
                        continue
                    if any(isinstance(decorator, ast.Name) and decorator.id == "property" for decorator in item.decorator_list):
                        properties.append(item.name)
                    else:
                        methods.append(item.name)
                surfaces.append({"kind": "class", "name": node.name, "module": path.stem, "methods": methods, "properties": properties})
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                surfaces.append({"kind": "function", "name": node.name, "module": path.stem})
    return surfaces


def _wrapper_target_types(wrapper_dispatch: dict[str, list[str]]) -> dict[str, list[str]]:
    targets: dict[str, set[str]] = defaultdict(set)
    for raw_type, path in wrapper_dispatch.items():
        if not raw_type.startswith("adsk."):
            continue
        _, class_name = path
        targets[class_name].add(raw_type)
    return {class_name: sorted(values) for class_name, values in sorted(targets.items())}


def _generated_coverage_entries(
    *,
    compact_properties: dict[str, dict[str, Any]],
    compact_methods: dict[str, dict[str, Any]],
    wrapper_target_types: dict[str, list[str]],
    members_by_owner: dict[tuple[str, str], list[dict[str, Any]]],
    symbols_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for mapping_name, specs in (("property", compact_properties), ("method", compact_methods)):
        for surface_id, spec in sorted(specs.items()):
            wrapper_name, _ = surface_id.split(".", 1)
            target_types = wrapper_target_types.get(wrapper_name, [])
            if not target_types:
                continue
            start_owner = target_types[0]
            owner = start_owner
            direct_symbols: list[str] = []
            attr_path = spec.get("attr_path") or spec.get("target_attrs") or []
            for attr_name in attr_path:
                symbol = _resolve_member(members_by_owner, owner, attr_name)
                if symbol is None:
                    break
                direct_symbols.append(symbol["id"])
                owner = _resolve_return_owner(symbol) or owner
            else:
                if spec.get("kind") == "call":
                    symbol = _resolve_member(members_by_owner, owner, spec["method"], kind_hint="method")
                    if symbol is not None:
                        direct_symbols.append(symbol["id"])
                entries.append(
                    {
                        "surface_id": surface_id,
                        "wrapper": wrapper_name,
                        "kind": mapping_name,
                        "direct_symbols": [symbol_id for symbol_id in direct_symbols if symbol_id in symbols_by_id],
                    }
                )
    return entries


def _handwritten_coverage_entries(symbols_by_id: dict[str, dict[str, Any]]) -> list[dict[str, object]]:
    entries = []
    for surface_id, symbol_ids in sorted(HANDWRITTEN_DIRECT_SYMBOLS.items()):
        entries.append(
            {
                "surface_id": surface_id,
                "wrapper": surface_id.split(".", 1)[0],
                "kind": "handwritten",
                "direct_symbols": [symbol_id for symbol_id in symbol_ids if symbol_id in symbols_by_id],
            }
        )
    return entries


def _resolve_member(
    members_by_owner: dict[tuple[str, str], list[dict[str, Any]]],
    owner: str,
    name: str,
    *,
    kind_hint: str | None = None,
) -> dict[str, Any] | None:
    matches = members_by_owner.get((owner, name), [])
    if not matches:
        return None
    if kind_hint:
        for symbol in matches:
            if symbol["kind"] == kind_hint:
                return symbol
    preferred_order = {"property": 0, "method": 1, "class": 2}
    return sorted(matches, key=lambda symbol: preferred_order.get(symbol["kind"], 99))[0]


def _resolve_return_owner(symbol: dict[str, Any]) -> str | None:
    owner = symbol.get("owner") or symbol.get("id")
    namespace = owner.rsplit(".", 1)[0] if owner and "." in owner else symbol.get("namespace")
    for signature in symbol.get("signatures", []):
        if signature.get("language") == "python" and signature.get("returns"):
            return _qualify_type(signature["returns"], namespace)
    for signature in symbol.get("signatures", []):
        if signature.get("returns"):
            return _qualify_type(signature["returns"], namespace)
    return None


def _qualify_type(type_name: str, namespace: str | None) -> str | None:
    if not type_name:
        return None
    normalized = type_name
    wrappers = ("core::Ptr<", "std::shared_ptr<", "Ptr<")
    for prefix in wrappers:
        if normalized.startswith(prefix) and normalized.endswith(">"):
            normalized = normalized[len(prefix) : -1]
    if "::" in normalized:
        normalized = normalized.replace("::", ".").replace("adsk.", "adsk.")
    if normalized.startswith("adsk."):
        return normalized
    primitive = {"bool", "double", "float", "int", "size_t", "string", "void", "Base", "object", "None"}
    if normalized in primitive:
        return None
    if namespace and "." not in normalized:
        return f"{namespace}.{normalized}"
    return normalized if normalized.startswith("adsk.") else None


def _covered_family_ids(
    direct_symbols: list[dict[str, Any]],
    symbols_by_id: dict[str, dict[str, Any]],
    wrapper_target_types: dict[str, list[str]],
) -> set[str]:
    family_ids = {family_id for values in wrapper_target_types.values() for family_id in values}
    for symbol in direct_symbols:
        owner = symbol.get("owner")
        if owner:
            family_ids.add(owner)
        next_owner = _resolve_return_owner(symbol)
        if next_owner and next_owner in symbols_by_id:
            family_ids.add(next_owner)
        elif next_owner:
            family_ids.add(next_owner)
    return family_ids


def _validated_family_ids(
    validated_symbols: list[dict[str, Any]],
    symbols_by_id: dict[str, dict[str, Any]],
    wrapper_target_types: dict[str, list[str]],
) -> set[str]:
    family_ids = {family_id for values in wrapper_target_types.values() for family_id in values}
    for symbol in validated_symbols:
        owner = symbol.get("owner")
        if owner:
            family_ids.add(owner)
        next_owner = _resolve_return_owner(symbol)
        if next_owner and next_owner in symbols_by_id:
            family_ids.add(next_owner)
        elif next_owner:
            family_ids.add(next_owner)
    return family_ids


def _symbol_links_to_sample_pages(symbol: dict[str, Any], sample_pages: set[str]) -> bool:
    doc = symbol.get("doc") or {}
    for section_name in ("samples", "related_links"):
        for entry in doc.get(section_name, []) or []:
            href = entry.get("href")
            if href in sample_pages:
                return True
    return False


def _load_sample_results(report_root: Path) -> list[dict[str, Any]]:
    results = []
    if not report_root.exists():
        return results
    for path in sorted(report_root.glob("*/result.json")):
        results.append(json.loads(path.read_text(encoding="utf-8")))
    return results


def _namespace_rows(
    *,
    symbols: list[dict[str, Any]],
    families: list[dict[str, Any]],
    direct_symbols: list[dict[str, Any]],
    validated_symbols: list[dict[str, Any]],
    public_exports: list[str],
    wrapper_target_types: dict[str, list[str]],
) -> list[dict[str, object]]:
    symbol_counts = Counter(symbol["namespace"] for symbol in symbols)
    family_counts = Counter(family["namespace"] for family in families)
    sample_family_counts = Counter(
        family["namespace"] for family in families if family.get("traits", {}).get("supports_samples")
    )
    direct_counts = Counter(symbol["namespace"] for symbol in direct_symbols)
    validated_counts = Counter(symbol["namespace"] for symbol in validated_symbols)
    wrapper_counts = Counter()
    for values in wrapper_target_types.values():
        for family_id in values:
            wrapper_counts[family_id.rsplit(".", 1)[0]] += 1

    rows = []
    for namespace in sorted(symbol_counts):
        if namespace == "adsk":
            status = "raw bootstrap only"
        elif direct_counts[namespace] and validated_counts[namespace]:
            status = "compact + validated"
        elif namespace == "adsk.core" and any(name in public_exports for name in CONTEXT_EXPORTS):
            status = "bootstrap + raw"
        elif direct_counts[namespace]:
            status = "compact, not sample-proven"
        else:
            status = "raw-only"
        rows.append(
            {
                "namespace": namespace,
                "official_symbols": symbol_counts[namespace],
                "families": family_counts[namespace],
                "sample_support_families": sample_family_counts[namespace],
                "wrapped_classes": wrapper_counts[namespace],
                "direct_compact_symbols": direct_counts[namespace],
                "validated_symbols": validated_counts[namespace],
                "status": status,
            }
        )
    return rows


def _uncovered_family_sort_key(family: dict[str, Any]) -> tuple[int, int, int, int]:
    traits = family.get("traits", {})
    return (
        int(bool(traits.get("has_create_input"))),
        int(bool(traits.get("has_add_simple"))),
        int(bool(traits.get("has_add"))),
        len(family.get("methods", [])),
    )


def _gap_reason(family: dict[str, Any]) -> str:
    traits = family.get("traits", {})
    if traits.get("has_create_input") or traits.get("has_add_simple"):
        return "Needs family-specific builder/coercion rules before it can be compacted cleanly."
    if traits.get("has_add"):
        return "Needs a deterministic compact call shape and sample-backed validation."
    if traits.get("collection_like"):
        return "Collection is reachable through raw refs, but no compact ergonomics have been designed for it."
    return "Still raw-only because it has not been prioritized into the compact surface yet."


def _build_design_backlog(
    *,
    families: list[dict[str, Any]],
    symbols: list[dict[str, Any]],
    covered_family_ids: set[str],
    validated_family_ids: set[str],
    compact_policy: dict[str, Any],
) -> dict[str, Any]:
    design_policy = compact_policy["design_workspace"]
    scope_namespaces = set(design_policy["scope_namespaces"])
    wave_map = {
        family_name: wave_name
        for wave_name, names in design_policy["waves"].items()
        for family_name in names
    }
    adjacent = set(design_policy["adjacent"])
    sample_counts = _family_sample_counts(symbols)

    rows = []
    for family in families:
        if family["namespace"] not in scope_namespaces:
            continue
        family_name = family["name"]
        family_id = family["id"]
        wave = wave_map.get(family_name, "deferred")
        status = _family_status(family_id, family_name, covered_family_ids, validated_family_ids, wave_map)
        score = _family_priority_score(family, sample_counts.get(family_id, 0), adjacent, wave)
        rows.append(
            {
                "id": family_id,
                "name": family_name,
                "namespace": family["namespace"],
                "wave": wave,
                "status": status,
                "priority_score": score,
                "sample_count": sample_counts.get(family_id, 0),
                "has_add": bool(family.get("traits", {}).get("has_add")),
                "has_add_simple": bool(family.get("traits", {}).get("has_add_simple")),
                "has_create_input": bool(family.get("traits", {}).get("has_create_input")),
                "reason": _gap_reason(family) if status in {"raw", "candidate"} else "Covered by the compact layer.",
            }
        )

    rows.sort(key=lambda row: (-row["priority_score"], row["wave"], row["name"]))
    grouped = {wave_name: [] for wave_name in ("wave_one", "wave_two", "wave_three", "wave_four", "deferred")}
    for row in rows:
        grouped.setdefault(row["wave"], []).append(row)

    return {
        "summary": {
            "family_count": len(rows),
            "validated_count": sum(1 for row in rows if row["status"] == "validated"),
            "compact_count": sum(1 for row in rows if row["status"] == "compact"),
            "candidate_count": sum(1 for row in rows if row["status"] == "candidate"),
            "raw_count": sum(1 for row in rows if row["status"] == "raw"),
        },
        "waves": grouped,
    }


def _family_status(
    family_id: str,
    family_name: str,
    covered_family_ids: set[str],
    validated_family_ids: set[str],
    wave_map: dict[str, str],
) -> str:
    if family_id in validated_family_ids:
        return "validated"
    if family_id in covered_family_ids:
        return "compact"
    if family_name in wave_map:
        return "candidate"
    return "raw"


def _family_priority_score(
    family: dict[str, Any],
    sample_count: int,
    adjacent: set[str],
    wave: str,
) -> int:
    traits = family.get("traits", {})
    score = sample_count * 10
    if traits.get("has_create_input"):
        score += 7
    if traits.get("has_add_simple"):
        score += 5
    if traits.get("has_add"):
        score += 3
    if family["name"] in adjacent:
        score += 8
    score += {"wave_one": 40, "wave_two": 20, "wave_three": 10, "wave_four": 5, "deferred": 0}.get(wave, 0)
    return score


def _family_sample_counts(symbols: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, set[str]] = defaultdict(set)
    for symbol in symbols:
        family_id = symbol["id"] if symbol.get("kind") == "class" else symbol.get("owner")
        if not family_id:
            continue
        doc = symbol.get("doc") or {}
        for section_name in ("samples", "related_links"):
            for entry in doc.get(section_name, []) or []:
                href = entry.get("href")
                if href and href.endswith("_Sample.htm"):
                    counts[family_id].add(href)
    return {family_id: len(entries) for family_id, entries in counts.items()}


def _render_markdown(payload: dict[str, Any]) -> str:
    official = payload["official_api"]
    compact = payload["compact_surface"]
    validation = payload["validation"]
    rows = payload["namespace_rows"]
    uncovered = payload["uncovered_sample_families"]

    lines = [
        "# API Coverage Map",
        "",
        "Generated map of FusionSparse coverage over the Autodesk Fusion API.",
        "",
        "## Coverage Model",
        "",
        "- Raw reachability: any Autodesk object that enters FusionSparse is still reachable through `Ref`, forwarded attribute access, and `.raw`.",
        "- Compact coverage: only the high-value ergonomic surface that has explicit wrapper/policy/generator support.",
        "- Validated coverage: compact workflows that have been executed against Autodesk sample pairs in real Fusion and matched by structural signature.",
        "",
        "## Official API Size",
        "",
        f"- Canonical symbols: `{official['symbol_count']}`",
        f"- Families: `{official['family_count']}`",
        f"- Families with sample support in the docs: `{official['sample_support_family_count']}`",
        "",
        "## FusionSparse Compact Surface",
        "",
        f"- Public exports: `{len(compact['public_exports'])}`",
        f"- Context/bootstrap exports: `{len(compact['context_exports'])}`",
        f"- Helper exports: `{len(compact['helper_exports'])}`",
        f"- Wrapper-dispatched Autodesk classes: `{sum(len(v) for v in compact['wrapper_dispatch'].values())}`",
        f"- Direct compact Autodesk symbols: `{len(compact['direct_symbol_ids'])}`",
        f"- Covered Autodesk families/classes: `{len(compact['covered_family_ids'])}`",
        f"- Sample-pair validated compact symbols: `{len(validation['validated_symbol_ids'])}`",
        "",
        "### Public Exports",
        "",
        f"- Context/bootstrap: `{', '.join(compact['context_exports'])}`",
        f"- Helpers: `{', '.join(compact['helper_exports'])}`",
        "",
        "### Wrapped Classes",
        "",
        "| Wrapper | Autodesk types | Properties | Methods |",
        "| --- | --- | --- | --- |",
    ]
    for surface in compact["wrapper_surfaces"]:
        if surface["kind"] != "class":
            continue
        target_types = compact["wrapper_dispatch"].get(surface["name"], [])
        lines.append(
            f"| `{surface['name']}` | `{', '.join(target_types) or '-'}` | "
            f"`{', '.join(surface.get('properties', [])) or '-'}` | `{', '.join(surface.get('methods', [])) or '-'}` |"
        )

    lines.extend(
        [
            "",
            "## Namespace Map",
            "",
            "| Namespace | Official symbols | Families | Sample-backed families | Wrapped classes | Direct compact symbols | Validated symbols | Status |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row['namespace']}` | `{row['official_symbols']}` | `{row['families']}` | "
            f"`{row['sample_support_families']}` | `{row['wrapped_classes']}` | "
            f"`{row['direct_compact_symbols']}` | `{row['validated_symbols']}` | {row['status']} |"
        )

    lines.extend(
        [
            "",
            "## Real Fusion Validation",
            "",
            f"- Declared sample pairs: `{validation['pair_count']}`",
            f"- Equivalent sample pairs: `{validation['validated_pair_count']}`",
            f"- Validated sample pages: `{', '.join(validation['validated_pages'])}`",
            "",
            "## What Is Actually Covered Compactly",
            "",
            "The compact layer is concentrated in the Design-workspace modeling slice:",
            "",
            "- Context/bootstrap: `app`, `ui`, `ctx`, `new_design`, `new_or_active_design`",
            "- Design/component/sketch access: `DesignRef.root`, `ComponentRef.sketch(...)`",
            "- Construction helpers: `ComponentRef.plane`, `ComponentRef.axis`, `ComponentRef.point`",
            "- Sketch constructors: `line`, `circle`, `arc`, `arc3p`, `circle2p`, `circle3p`, `rect`, `rect_center`, `rect3p`",
            "- Sketch profile access: `profile`, `profiles`",
            "- Feature workflows: `ComponentRef.extrude(...)`, `ComponentRef.revolve(...)`, `ComponentRef.sweep(...)`, `ComponentRef.loft(...)`, `ComponentRef.patch(...)`, `ComponentRef.shell(...)`, `ComponentRef.draft(...)`, `ComponentRef.move(...)`, `ComponentRef.offset(...)`, `ComponentRef.replace_face(...)`, `ComponentRef.scale(...)`, `ComponentRef.split_body(...)`, `ComponentRef.thread(...)`, `ComponentRef.trim(...)`, `ComponentRef.hole(...)`, `ComponentRef.fillet(...)`, `ComponentRef.chamfer(...)`, `ComponentRef.combine(...)`, `ComponentRef.mirror(...)`, `ComponentRef.circular_pattern(...)`, `ComponentRef.rect_pattern(...)`",
            "- Builder workflows: `ExtrudeBuilder.one_side/symmetric/through_all/build`, `RevolveBuilder.angle/build`, `HoleBuilder.counterbore/countersink/depth/by_offsets/on_edge/at_center/by_points/build`",
            "",
            "Everything else is currently raw-first, not absent. You can still reach it through wrapped Autodesk objects and `.raw`, but it has not been promoted into the compact ergonomic layer yet.",
            "",
            "## Largest Sample-Backed Gaps",
            "",
            "| Family | Namespace | Methods | Why it is not compact yet |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for family in uncovered:
        lines.append(
            f"| `{family['id']}` | `{family['namespace']}` | `{family['method_count']}` | {family['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Why FusionSparse Does Not Cover All Of It Yet",
            "",
            "- The project goal is not to hand-wrap the entire Autodesk API. The compact layer is intentionally narrow and generator-driven.",
            "- Raw capability is broader than compact capability. Most of the Autodesk surface is still reachable through `Ref` and `.raw` without dedicated shorthand.",
            "- A family only earns compact support when we can describe it cleanly in rules/metadata and prove it with real sample execution.",
            "- Many uncovered families need family-specific coercion, builder state, or geometry/signature comparison before they can be promoted without bloat.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_design_backlog_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Design Workspace Backlog",
        "",
        "Generated Design-workspace coverage ranking derived from the canonical IR, compact policy, and live sample results.",
        "",
        "## Summary",
        "",
        f"- Families in scope: `{summary['family_count']}`",
        f"- `validated`: `{summary['validated_count']}`",
        f"- `compact`: `{summary['compact_count']}`",
        f"- `candidate`: `{summary['candidate_count']}`",
        f"- `raw`: `{summary['raw_count']}`",
        "",
    ]
    for wave_name in ("wave_one", "wave_two", "wave_three", "wave_four", "deferred"):
        rows = payload["waves"].get(wave_name, [])
        title = wave_name.replace("_", " ").title()
        lines.extend(
            [
                f"## {title}",
                "",
                "| Family | Status | Priority | Samples | Traits | Why |",
                "| --- | --- | ---: | ---: | --- | --- |",
            ]
        )
        for row in rows:
            traits = ", ".join(
                label
                for label, enabled in (
                    ("add", row["has_add"]),
                    ("add_simple", row["has_add_simple"]),
                    ("create_input", row["has_create_input"]),
                )
                if enabled
            ) or "-"
            lines.append(
                f"| `{row['name']}` | `{row['status']}` | `{row['priority_score']}` | "
                f"`{row['sample_count']}` | `{traits}` | {row['reason']} |"
            )
        lines.append("")
    return "\n".join(lines)
