from __future__ import annotations

import ast
import json
from pathlib import Path

from .errors import BuilderState, SampleConversionError
from .policy import (
    DIRECTION_ALIASES,
    FEATURE_OPERATION_ALIASES,
    PLANE_ALIASES,
    load_compact_policy,
    load_construction_translation_policy,
    load_sketch_translation_policy,
)


FEATURE_COLLECTION_ALIASES = {
    "root_comp.features.extrudeFeatures": "extrude",
    "rootComp.features.extrudeFeatures": "extrude",
    "root_comp.features.revolveFeatures": "revolve",
    "rootComp.features.revolveFeatures": "revolve",
    "root_comp.features.sweepFeatures": "sweep",
    "rootComp.features.sweepFeatures": "sweep",
    "root_comp.features.loftFeatures": "loft",
    "rootComp.features.loftFeatures": "loft",
    "root_comp.features.patchFeatures": "patch",
    "rootComp.features.patchFeatures": "patch",
    "root_comp.features.shellFeatures": "shell",
    "rootComp.features.shellFeatures": "shell",
    "root_comp.features.draftFeatures": "draft",
    "rootComp.features.draftFeatures": "draft",
    "root_comp.features.moveFeatures": "move",
    "rootComp.features.moveFeatures": "move",
    "root_comp.features.offsetFeatures": "offset",
    "rootComp.features.offsetFeatures": "offset",
    "root_comp.features.replaceFaceFeatures": "replace_face",
    "rootComp.features.replaceFaceFeatures": "replace_face",
    "root_comp.features.scaleFeatures": "scale",
    "rootComp.features.scaleFeatures": "scale",
    "root_comp.features.splitBodyFeatures": "split_body",
    "rootComp.features.splitBodyFeatures": "split_body",
    "root_comp.features.threadFeatures": "thread",
    "rootComp.features.threadFeatures": "thread",
    "root_comp.features.trimFeatures": "trim",
    "rootComp.features.trimFeatures": "trim",
    "root_comp.features.holeFeatures": "hole",
    "rootComp.features.holeFeatures": "hole",
    "root_comp.features.filletFeatures": "fillet",
    "rootComp.features.filletFeatures": "fillet",
    "root_comp.features.chamferFeatures": "chamfer",
    "rootComp.features.chamferFeatures": "chamfer",
    "root_comp.features.combineFeatures": "combine",
    "rootComp.features.combineFeatures": "combine",
    "root_comp.features.mirrorFeatures": "mirror",
    "rootComp.features.mirrorFeatures": "mirror",
    "root_comp.features.circularPatternFeatures": "circular_pattern",
    "rootComp.features.circularPatternFeatures": "circular_pattern",
    "root_comp.features.rectangularPatternFeatures": "rectangular_pattern",
    "rootComp.features.rectangularPatternFeatures": "rectangular_pattern",
    "root_comp.constructionPlanes": "construction:plane",
    "rootComp.constructionPlanes": "construction:plane",
    "root_comp.constructionAxes": "construction:axis",
    "rootComp.constructionAxes": "construction:axis",
    "root_comp.constructionPoints": "construction:point",
    "rootComp.constructionPoints": "construction:point",
}

ROOT_ALIASES = {"rootComp", "root_comp"}
PATTERN_DISTANCE_TYPE_ALIASES = {
    "SpacingPatternDistanceType": "spacing",
    "ExtentPatternDistanceType": "extent",
}
SWEEP_PROFILE_SCALING_ALIASES = {
    "SweepProfileNoScalingOption": "none",
    "SweepProfileScaleOption": "scale",
    "SweepProfileStretchOption": "stretch",
}
LOFT_EDGE_ALIGNMENT_ALIASES = {
    "AlignEdgesLoftEdgeAlignment": "align",
    "AlignToSurfaceLoftEdgeAlignment": "surface",
    "FreeEdgesLoftEdgeAlignment": "free",
}
SHELL_TYPE_ALIASES = {
    "RoundedOffsetShellType": "rounded",
    "SharpOffsetShellType": "sharp",
}


def translate_official_script(source: str, *, repo_root: str | Path | None = None) -> str:
    module = ast.parse(source)
    run_fn = next(
        (node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "run"),
        None,
    )
    if run_fn is None:
        raise SampleConversionError("Official sample must define run(context).")

    used_names = {node.id for node in ast.walk(module) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    state = _ConversionState(used_names, repo_root)
    for statement in run_fn.body:
        state.translate(statement)
    state.finish()
    return state.render()


class _ConversionState:
    def __init__(self, used_names: set[str], repo_root: str | Path | None) -> None:
        self.used_names = used_names
        self.compact_policy = load_compact_policy(repo_root)
        self.sketch_policy = load_sketch_translation_policy(repo_root)
        self.construction_policy = load_construction_translation_policy(repo_root)
        self.text_policy = self.compact_policy.get("text", {})
        self.text_horizontal_aliases = {
            member_name: alias
            for alias, member_name in self.text_policy.get("horizontal_alignments", {}).items()
        }
        self.text_vertical_aliases = {
            member_name: alias
            for alias, member_name in self.text_policy.get("vertical_alignments", {}).items()
        }
        self.text_horizontal_values: dict[str, str] = {}
        self.text_vertical_values: dict[str, str] = {}
        self.hole_position_aliases = {
            member_name: alias
            for alias, member_name in self.compact_policy.get("hole", {}).get("edge_positions", {}).items()
        }
        self.lines = [
            "import fusion_sparse as fx",
            "",
            "from tests.integration.sample_pairs.common import print_design_signature",
            "",
            "",
            "def run(context):",
            "    design = fx.new_design()",
            "    root = design.root",
        ]
        self.planes: dict[str, str] = {}
        self.name_aliases: dict[str, str] = {}
        self.sketch_collections: set[str] = set()
        self.collection_targets: dict[str, tuple[str, str]] = {}
        self.feature_collections: dict[str, str] = {}
        self.object_collections: dict[str, list[str]] = {}
        self.value_inputs: dict[str, str] = {}
        self.feature_ops: dict[str, str] = {}
        self.extents: dict[str, tuple[str, str | None]] = {}
        self.bools: dict[str, bool] = {}
        self.points: dict[str, tuple[str, str]] = {}
        self.vectors: dict[str, str] = {}
        self.matrices: dict[str, dict[str, object]] = {}
        self.scalars: dict[str, str] = {}
        self.builders: dict[str, BuilderState] = {}
        self.revolves: dict[str, dict[str, object]] = {}
        self.sweeps: dict[str, dict[str, object]] = {}
        self.lofts: dict[str, dict[str, object]] = {}
        self.patches: dict[str, dict[str, object]] = {}
        self.shells: dict[str, dict[str, object]] = {}
        self.drafts: dict[str, dict[str, object]] = {}
        self.moves: dict[str, dict[str, object]] = {}
        self.offsets: dict[str, dict[str, object]] = {}
        self.replace_faces: dict[str, dict[str, object]] = {}
        self.scales: dict[str, dict[str, object]] = {}
        self.split_bodies: dict[str, dict[str, object]] = {}
        self.threads: dict[str, dict[str, object]] = {}
        self.thread_queries: set[str] = set()
        self.trims: dict[str, dict[str, object]] = {}
        self.trim_cells: dict[str, str] = {}
        self.trim_cell_refs: dict[str, tuple[str, int]] = {}
        self.holes: dict[str, BuilderState] = {}
        self.constructions: dict[str, dict[str, object]] = {}
        self.fillets: dict[str, dict[str, object]] = {}
        self.chamfers: dict[str, dict[str, object]] = {}
        self.combines: dict[str, dict[str, object]] = {}
        self.mirrors: dict[str, dict[str, object]] = {}
        self.circular_patterns: dict[str, dict[str, object]] = {}
        self.rectangular_patterns: dict[str, dict[str, object]] = {}
        self.texts: dict[str, dict[str, object]] = {}
        self.signature_emitted = False

    def translate(self, statement: ast.stmt) -> None:
        if isinstance(statement, ast.Try):
            for inner in statement.body:
                self.translate(inner)
            return
        if isinstance(statement, ast.Assign):
            self._translate_assign(statement)
            return
        if isinstance(statement, ast.Expr):
            self._translate_expr(statement.value)
            return
        raise SampleConversionError(f"Unsupported statement type in official sample: {statement.__class__.__name__}")

    def finish(self) -> None:
        dangling = []
        for label, mapping in (
            ("extrude", self.builders),
            ("revolve", self.revolves),
            ("sweep", self.sweeps),
            ("loft", self.lofts),
            ("patch", self.patches),
            ("shell", self.shells),
            ("draft", self.drafts),
            ("move", self.moves),
            ("offset", self.offsets),
            ("replace_face", self.replace_faces),
            ("scale", self.scales),
            ("split_body", self.split_bodies),
            ("thread", self.threads),
            ("trim", self.trims),
            ("hole", self.holes),
            ("construction", self.constructions),
            ("fillet", self.fillets),
            ("chamfer", self.chamfers),
            ("combine", self.combines),
            ("mirror", self.mirrors),
            ("circular_pattern", self.circular_patterns),
            ("rectangular_pattern", self.rectangular_patterns),
            ("text", self.texts),
        ):
            if mapping:
                dangling.extend(f"{label}:{name}" for name in sorted(mapping))
        if dangling:
            raise SampleConversionError(f"Dangling builders were never built: {', '.join(dangling)}")
        if not self.signature_emitted:
            raise SampleConversionError("Official sample did not emit print_design_signature(design).")

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"

    def _translate_assign(self, statement: ast.Assign) -> None:
        if len(statement.targets) != 1:
            raise SampleConversionError("Only single-target assignments are supported in official samples.")
        target_node = statement.targets[0]
        value = statement.value

        if isinstance(target_node, ast.Attribute):
            if self._translate_attribute_assign(target_node, value):
                return
            raise SampleConversionError(f"Unsupported attribute assignment in official sample: {ast.unparse(statement).strip()}")
        if not isinstance(target_node, ast.Name):
            raise SampleConversionError("Only name and attribute assignments are supported in official samples.")
        target = target_node.id

        if plane := _parse_plane_alias(value):
            self.planes[target] = plane
            return
        if _is_sketches_alias(value):
            self.sketch_collections.add(target)
            return
        if alias := _parse_root_alias(value):
            self.name_aliases[target] = alias
            return
        if feature_collection := _parse_feature_collection(value):
            self.feature_collections[target] = feature_collection
            return
        if _is_object_collection_create(value):
            self.object_collections[target] = []
            return
        if _is_boilerplate_assign(value):
            return
        if plane := _parse_sketch_plane(value, self.planes, self.sketch_collections, self):
            plane_expr, is_alias = plane
            rendered = json.dumps(plane_expr) if is_alias else plane_expr
            self._emit_assignment(target, f"root.sketch({rendered})")
            return
        if collection := _parse_sketch_collection(value):
            self.collection_targets[target] = collection
            return
        if point := _parse_point(value, self.points):
            self.points[target] = point
            return
        if vector := _parse_vector(value, self.vectors):
            self.vectors[target] = vector
            return
        if _is_matrix_create(value):
            self.matrices[target] = {"translation": None}
            return
        boolean = _parse_bool(value, self.bools)
        if boolean is not None:
            self.bools[target] = boolean
            return
        if horizontal_align := _parse_alignment(
            value,
            self.text_horizontal_aliases,
            "HorizontalAlignments",
            self.text_horizontal_values,
        ):
            self.text_horizontal_values[target] = horizontal_align
            return
        if vertical_align := _parse_alignment(
            value,
            self.text_vertical_aliases,
            "VerticalAlignments",
            self.text_vertical_values,
        ):
            self.text_vertical_values[target] = vertical_align
            return
        if scalar := _parse_scalar(value, self.scalars):
            self.scalars[target] = scalar
            return
        if profile := _parse_profile(value):
            index_suffix = "" if profile[1] == 0 else str(profile[1])
            expr = f"{profile[0]}.profile()" if not index_suffix else f"{profile[0]}.profile({index_suffix})"
            self._emit_assignment(target, expr)
            return
        if value_input := _parse_value_input(value, self.value_inputs):
            self.value_inputs[target] = value_input
            return
        if operation := _parse_feature_operation(value, self.feature_ops):
            self.feature_ops[target] = operation
            return
        if extent := _parse_extent_definition(value, self.value_inputs):
            self.extents[target] = extent
            return
        if text_builder := _parse_text_create_input(
            value,
            self.collection_targets,
            self.value_inputs,
            self.scalars,
            self.text_policy,
        ):
            self.texts[target] = text_builder
            return
        if builder := _parse_extrude_create_input(value, self.feature_collections, self.feature_ops):
            self.builders[target] = BuilderState(base_expr=_component_extrude(builder["profile"], builder["operation"]))
            return
        if revolve := _parse_revolve_create_input(value, self.feature_collections, self.feature_ops, self):
            self.revolves[target] = revolve
            return
        if sweep := _parse_sweep_create_input(value, self.feature_collections, self.feature_ops, self):
            self.sweeps[target] = sweep
            return
        if loft := _parse_loft_create_input(value, self.feature_collections, self.feature_ops):
            self.lofts[target] = loft
            return
        if patch := _parse_patch_create_input(value, self.feature_collections, self.feature_ops, self):
            self.patches[target] = patch
            return
        if shell := _parse_shell_create_input(value, self.feature_collections, self.bools, self):
            self.shells[target] = shell
            return
        if draft := _parse_draft_create_input(value, self.feature_collections, self.bools, self):
            self.drafts[target] = draft
            return
        if move := _parse_move_create_input(value, self.feature_collections, self.object_collections):
            self.moves[target] = move
            return
        if offset := _parse_offset_create_input(value, self.feature_collections, self.object_collections, self.value_inputs, self.feature_ops, self):
            self.offsets[target] = offset
            return
        if replace_face := _parse_replace_face_create_input(
            value,
            self.feature_collections,
            self.object_collections,
            self.bools,
            self,
        ):
            self.replace_faces[target] = replace_face
            return
        if scale := _parse_scale_create_input(value, self.feature_collections, self.object_collections, self.value_inputs, self):
            self.scales[target] = scale
            return
        if split_body := _parse_split_body_create_input(value, self.feature_collections, self):
            self.split_bodies[target] = split_body
            return
        if thread := _parse_thread_create_input(value, self.feature_collections, self.object_collections, self):
            self.threads[target] = thread
            return
        if trim := _parse_trim_create_input(value, self.feature_collections, self):
            self.trims[target] = trim
            return
        if _parse_thread_query_alias(value, self.feature_collections, self.thread_queries):
            self.thread_queries.add(target)
            return
        if _parse_thread_query_value(value, self.thread_queries, self):
            self.scalars[target] = json.dumps(target)
            return
        if _parse_thread_info_create(value, self.feature_collections, self.thread_queries):
            self.scalars[target] = json.dumps(target)
            return
        if trim_cells := _parse_trim_cells_alias(value, self.trims):
            self.trim_cells[target] = trim_cells
            return
        if trim_cell_ref := _parse_trim_cell_ref(value, self.trim_cells):
            self.trim_cell_refs[target] = trim_cell_ref
            return
        if hole_builder := _parse_hole_create_input(value, self.feature_collections, self.value_inputs):
            self.holes[target] = hole_builder
            return
        if construction := _parse_construction_create_input(value, self.feature_collections, self.construction_policy):
            self.constructions[target] = construction
            return
        if _parse_fillet_create_input(value, self.feature_collections):
            self.fillets[target] = {}
            return
        if _parse_chamfer_create_input(value, self.feature_collections):
            self.chamfers[target] = {}
            return
        if combine := _parse_combine_create_input(value, self.feature_collections, self.object_collections, self):
            self.combines[target] = combine
            return
        if mirror := _parse_mirror_create_input(value, self.feature_collections, self.object_collections, self):
            self.mirrors[target] = mirror
            return
        if circular_pattern := _parse_circular_pattern_create_input(
            value,
            self.feature_collections,
            self.object_collections,
            self,
        ):
            self.circular_patterns[target] = circular_pattern
            return
        if rectangular_pattern := _parse_rectangular_pattern_create_input(
            value,
            self.feature_collections,
            self.object_collections,
            self,
        ):
            self.rectangular_patterns[target] = rectangular_pattern
            return
        translated = self._translate_runtime_call(value, assign_target=target)
        if translated is not None:
            if translated:
                self._emit(translated)
            return
        passthrough = self._rewrite_expr(value)
        if passthrough is not None:
            self._emit_assignment(target, passthrough)
            return
        raise SampleConversionError(f"Unsupported assignment in official sample: {ast.unparse(statement).strip()}")

    def _translate_expr(self, value: ast.expr) -> None:
        if _is_documents_add(value):
            return
        if _parse_object_collection_add(value, self.object_collections, self):
            return
        translated = self._translate_runtime_call(value, assign_target=None)
        if translated is not None:
            if translated:
                self._emit(translated)
            return
        passthrough = self._rewrite_expr(value)
        if passthrough is not None:
            self._emit(passthrough)
            return
        raise SampleConversionError(f"Unsupported expression in official sample: {ast.unparse(value).strip()}")

    def _translate_attribute_assign(self, target: ast.Attribute, value: ast.expr) -> bool:
        if not isinstance(target.value, ast.Name):
            return False
        builder_name = target.value.id

        combine = self.combines.get(builder_name)
        if combine is not None:
            return _parse_combine_attribute_assign(target.attr, value, combine, self.feature_ops, self.bools)

        extrude = self.builders.get(builder_name)
        if extrude is not None:
            return _parse_extrude_builder_attribute_assign(target.attr, value, extrude, self.bools)

        sweep = self.sweeps.get(builder_name)
        if sweep is not None:
            return _parse_sweep_attribute_assign(
                target.attr,
                value,
                sweep,
                self.value_inputs,
                self.bools,
                self,
            )

        loft = self.lofts.get(builder_name)
        if loft is not None:
            return _parse_loft_attribute_assign(
                target.attr,
                value,
                loft,
                self.bools,
            )

        shell = self.shells.get(builder_name)
        if shell is not None:
            return _parse_shell_attribute_assign(
                target.attr,
                value,
                shell,
                self.value_inputs,
                self,
            )

        draft = self.drafts.get(builder_name)
        if draft is not None:
            return _parse_draft_attribute_assign(target.attr, value, draft, self.bools)

        matrix = self.matrices.get(builder_name)
        if matrix is not None:
            return _parse_matrix_attribute_assign(target.attr, value, matrix, self.vectors)

        scale = self.scales.get(builder_name)
        if scale is not None:
            return _parse_scale_attribute_assign(target.attr, value, scale, self.value_inputs)

        thread = self.threads.get(builder_name)
        if thread is not None:
            return _parse_thread_attribute_assign(target.attr, value, thread, self.bools, self.value_inputs)

        trim_cell_ref = self.trim_cell_refs.get(builder_name)
        if trim_cell_ref is not None:
            return _parse_trim_cell_attribute_assign(target.attr, value, trim_cell_ref, self.trims, self.bools)

        text = self.texts.get(builder_name)
        if text is not None:
            return _parse_text_attribute_assign(
                target.attr,
                value,
                text,
                self.bools,
                self.scalars,
                self.text_policy,
            )

        circular = self.circular_patterns.get(builder_name)
        if circular is not None:
            return _parse_circular_pattern_attribute_assign(
                target.attr,
                value,
                circular,
                self.value_inputs,
                self.scalars,
                self.bools,
            )

        rectangular = self.rectangular_patterns.get(builder_name)
        if rectangular is not None:
            return _parse_rectangular_pattern_attribute_assign(
                target.attr,
                value,
                rectangular,
                self.bools,
            )

        return False

    def _translate_runtime_call(self, value: ast.expr, *, assign_target: str | None) -> str | None:
        if shape := _parse_sketch_shape_call(
            value,
            self.collection_targets,
            self.points,
            self.value_inputs,
            self.scalars,
            self.object_collections,
            self.sketch_policy,
        ):
            return self._wrap_assignment(assign_target, f"{shape['sketch']}.{shape['method']}({', '.join(shape['args'])})")
        if update := _parse_text_mutation(
            value,
            self.texts,
            self.bools,
            self.value_inputs,
            self.scalars,
            self.text_horizontal_values,
            self.text_vertical_values,
            self.text_horizontal_aliases,
            self.text_vertical_aliases,
            self,
        ):
            return "" if update else None
        if build := _parse_text_build(value, self.collection_targets, self.texts):
            return self._wrap_assignment(assign_target, build)
        if simple := _parse_add_simple_call(value, self.value_inputs, self.feature_ops):
            expr = _component_extrude(simple["profile"], simple["operation"], simple["distance"])
            return self._wrap_assignment(assign_target, expr)
        if update := _parse_extrude_builder_mutation(value, self.extents, self.value_inputs, self.bools):
            builder = self.builders.get(update["builder"])
            if builder is None:
                raise SampleConversionError(f"Unknown extrude builder variable: {update['builder']}")
            builder.append(update["fragment"])
            return ""
        if build := _parse_extrude_builder_build(value, self.feature_collections):
            builder = self.builders.pop(build["builder"], None)
            if builder is None:
                raise SampleConversionError(f"Unknown extrude builder variable: {build['builder']}")
            return self._wrap_assignment(assign_target, f"{builder.render()}.build()")
        if update := _parse_revolve_builder_mutation(value, self.revolves, self.value_inputs, self.bools):
            return "" if update else None
        if build := _parse_revolve_builder_build(value, self.feature_collections, self.revolves):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_sweep_mutation(value, self.sweeps, self.value_inputs, self.bools, self):
            return "" if update else None
        if build := _parse_sweep_build(value, self.feature_collections, self.sweeps):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_loft_mutation(value, self.lofts, self):
            return "" if update else None
        if build := _parse_loft_build(value, self.feature_collections, self.lofts):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_patch_build(value, self.feature_collections, self.patches):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_shell_build(value, self.feature_collections, self.shells):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_draft_mutation(value, self.drafts, self.value_inputs, self.bools):
            return "" if update else None
        if build := _parse_draft_build(value, self.feature_collections, self.drafts):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_move_mutation(value, self.moves, self.matrices):
            return "" if update else None
        if build := _parse_move_build(value, self.feature_collections, self.moves):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_offset_build(value, self.feature_collections, self.offsets):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_replace_face_build(value, self.feature_collections, self.replace_faces):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_scale_mutation(value, self.scales, self.value_inputs):
            return "" if update else None
        if build := _parse_scale_build(value, self.feature_collections, self.scales):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_split_body_build(value, self.feature_collections, self.split_bodies):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_thread_build(value, self.feature_collections, self.threads):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_trim_build(value, self.feature_collections, self.trims):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_hole_builder_mutation(value, self.holes, self.value_inputs, self.object_collections, self):
            return "" if update else None
        if build := _parse_hole_builder_build(value, self.feature_collections, self.holes):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_construction_builder_mutation(value, self.constructions, self):
            return "" if update else None
        if build := _parse_construction_builder_build(value, self.feature_collections, self.constructions):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_fillet_builder_mutation(value, self.fillets, self.object_collections, self.value_inputs, self.bools, self):
            return "" if update else None
        if build := _parse_fillet_builder_build(value, self.feature_collections, self.fillets):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_chamfer_builder_mutation(
            value,
            self.chamfers,
            self.object_collections,
            self.value_inputs,
            self.bools,
            self,
        ):
            return "" if update else None
        if build := _parse_chamfer_builder_build(value, self.feature_collections, self.chamfers):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_combine_build(value, self.feature_collections, self.combines):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_mirror_build(value, self.feature_collections, self.mirrors):
            return self._wrap_assignment(assign_target, build)
        if build := _parse_circular_pattern_build(value, self.feature_collections, self.circular_patterns):
            return self._wrap_assignment(assign_target, build)
        if update := _parse_rectangular_pattern_mutation(value, self.rectangular_patterns, self):
            return "" if update else None
        if build := _parse_rectangular_pattern_build(value, self.feature_collections, self.rectangular_patterns):
            return self._wrap_assignment(assign_target, build)
        if _is_signature_call(value):
            self.signature_emitted = True
            return "print_design_signature(design.raw)"
        return None

    def _wrap_assignment(self, assign_target: str | None, expr: str) -> str:
        if assign_target and assign_target in self.used_names:
            return f"{assign_target} = {expr}"
        return expr

    def _emit_assignment(self, target: str, expr: str) -> None:
        self._emit(self._wrap_assignment(target, expr))

    def _emit(self, line: str) -> None:
        self.lines.append(f"    {line}")

    def _rewrite_expr(self, value: ast.expr) -> str | None:
        rewritten = _ExpressionRewriter(self.name_aliases).visit(ast.parse(ast.unparse(value), mode="eval").body)
        text = ast.unparse(ast.fix_missing_locations(rewritten)).strip()
        if "adsk." in text:
            return None
        return text

    def sample_expr(self, value: ast.expr, *, point=False) -> str:
        if isinstance(value, ast.Name) and value.id in self.planes:
            return json.dumps(self.planes[value.id])
        if plane := _parse_plane_alias(value):
            return json.dumps(plane)
        if point:
            parsed_point = _parse_point(value, self.points)
            if parsed_point is not None:
                return parsed_point[0]
        parsed = _parse_value_input(value, self.value_inputs) or _parse_scalar(value, self.scalars)
        if parsed is not None:
            return parsed
        rewritten = self._rewrite_expr(value)
        if rewritten is None:
            raise SampleConversionError(f"Unsupported expression in official sample: {ast.unparse(value).strip()}")
        return rewritten


def _is_boilerplate_assign(value: ast.expr) -> bool:
    if isinstance(value, ast.Constant) and value.value is None:
        return True
    if isinstance(value, ast.Call):
        return _dotted(value.func) in {
            "adsk.core.Application.get",
            "adsk.fusion.Design.cast",
            "app.documents.add",
        }
    dotted = _dotted(value)
    return dotted in {
        "app.activeProduct",
        "app.userInterface",
        "design.rootComponent",
        "root_comp.features.extrudeFeatures",
        "rootComp.features.extrudeFeatures",
    }


def _is_documents_add(value: ast.expr) -> bool:
    return isinstance(value, ast.Call) and _dotted(value.func) == "app.documents.add"


def _parse_root_alias(value: ast.expr) -> str | None:
    return "root" if _dotted(value) == "design.rootComponent" else None


def _parse_plane_alias(value: ast.expr) -> str | None:
    if isinstance(value, ast.Name):
        return PLANE_ALIASES.get(value.id)
    return PLANE_ALIASES.get(_attr_name(value))


def _is_sketches_alias(value: ast.expr) -> bool:
    return _dotted(value) in {"root_comp.sketches", "rootComp.sketches"}


def _parse_feature_collection(value: ast.expr) -> str | None:
    return FEATURE_COLLECTION_ALIASES.get(_dotted(value))


def _parse_sketch_plane(
    value: ast.expr,
    planes: dict[str, str],
    sketch_collections: set[str],
    state: _ConversionState,
) -> tuple[str, bool] | None:
    if not isinstance(value, ast.Call):
        return None
    if not isinstance(value.func, ast.Attribute) or value.func.attr != "add":
        return None
    if len(value.args) != 1:
        return None
    if isinstance(value.func.value, ast.Attribute):
        if value.func.value.attr != "sketches":
            return None
    elif not (isinstance(value.func.value, ast.Name) and value.func.value.id in sketch_collections):
        return None

    if isinstance(value.args[0], ast.Name):
        plane = planes.get(value.args[0].id)
        if plane is not None:
            return plane, True
    plane = PLANE_ALIASES.get(_attr_name(value.args[0]))
    if plane is not None:
        return plane, True
    return state.sample_expr(value.args[0]), False


def _parse_sketch_collection(value: ast.expr) -> tuple[str, str] | None:
    dotted = _dotted(value)
    if ".sketchCurves." in dotted:
        sketch, _, collection = dotted.partition(".sketchCurves.")
        if not sketch or not collection or "." in collection or not collection.startswith("sketch"):
            return None
        return sketch, collection
    for suffix in ("sketchPoints", "sketchTexts"):
        token = f".{suffix}"
        if dotted.endswith(token):
            sketch = dotted[: -len(token)]
            if sketch and "." not in suffix:
                return sketch, suffix
    return None


def _is_object_collection_create(value: ast.expr) -> bool:
    return isinstance(value, ast.Call) and _dotted(value.func) == "adsk.core.ObjectCollection.create" and not value.args


def _parse_object_collection_add(
    value: ast.expr,
    object_collections: dict[str, list[str]],
    state: _ConversionState,
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    target = value.func.value.id
    if value.func.attr != "add" or target not in object_collections or len(value.args) != 1:
        return False
    object_collections[target].append(state.sample_expr(value.args[0], point=True))
    return True


def _parse_point(value: ast.expr, points: dict[str, tuple[str, str]]) -> tuple[str, str] | None:
    if isinstance(value, ast.Name):
        return points.get(value.id)
    if isinstance(value, ast.Attribute):
        if value.attr in {"startSketchPoint", "endSketchPoint", "centerSketchPoint"}:
            expression = ast.unparse(value)
            return expression, expression
        return None
    if not isinstance(value, ast.Call):
        return None
    if _dotted(value.func) != "adsk.core.Point3D.create" or len(value.args) != 3:
        return None
    x, y, z = (_literal_number(arg) for arg in value.args)
    if None in {x, y, z}:
        return None
    if z == "0":
        return f"({x}, {y})", f"({x}, {y}, 0)"
    return f"({x}, {y}, {z})", f"({x}, {y}, {z})"


def _parse_vector(value: ast.expr, vectors: dict[str, str]) -> str | None:
    if isinstance(value, ast.Name):
        return vectors.get(value.id)
    if not isinstance(value, ast.Call):
        return None
    if _dotted(value.func) != "adsk.core.Vector3D.create" or len(value.args) != 3:
        return None
    x, y, z = (_literal_number(arg) for arg in value.args)
    if None in {x, y, z}:
        return None
    if z == "0":
        return f"({x}, {y})"
    return f"({x}, {y}, {z})"


def _is_matrix_create(value: ast.expr) -> bool:
    return isinstance(value, ast.Call) and _dotted(value.func) == "adsk.core.Matrix3D.create" and not value.args


def _parse_profile(value: ast.expr) -> tuple[str, int] | None:
    if not isinstance(value, ast.Call):
        return None
    if not isinstance(value.func, ast.Attribute) or value.func.attr != "item":
        return None
    if not isinstance(value.func.value, ast.Attribute) or value.func.value.attr != "profiles":
        return None
    if not isinstance(value.func.value.value, ast.Name):
        return None
    if len(value.args) != 1 or not isinstance(value.args[0], ast.Constant) or not isinstance(value.args[0].value, int):
        return None
    return value.func.value.value.id, value.args[0].value


def _parse_value_input(value: ast.expr, value_inputs: dict[str, str]) -> str | None:
    if isinstance(value, ast.Name):
        return value_inputs.get(value.id)
    if not isinstance(value, ast.Call):
        return None
    dotted = _dotted(value.func)
    if dotted == "adsk.core.ValueInput.createByReal" and len(value.args) == 1:
        return _literal_number(value.args[0]) or ast.unparse(value.args[0]).strip()
    if dotted == "adsk.core.ValueInput.createByString" and len(value.args) == 1:
        if isinstance(value.args[0], ast.Constant) and isinstance(value.args[0].value, str):
            return json.dumps(value.args[0].value)
    return None


def _parse_scalar(value: ast.expr, scalars: dict[str, str]) -> str | None:
    if isinstance(value, ast.Name):
        return scalars.get(value.id)
    if isinstance(value, ast.Constant):
        if isinstance(value.value, (int, float)) and not isinstance(value.value, bool):
            literal = value.value
            if isinstance(literal, float) and literal.is_integer():
                literal = int(literal)
            return repr(literal)
        if isinstance(value.value, str):
            return json.dumps(value.value)
    return None


def _parse_bool(value: ast.expr, bools: dict[str, bool]) -> bool | None:
    if isinstance(value, ast.Name):
        return bools.get(value.id)
    if isinstance(value, ast.Constant) and isinstance(value.value, bool):
        return value.value
    return None


def _parse_feature_operation(value: ast.expr, feature_ops: dict[str, str]) -> str | None:
    if isinstance(value, ast.Name):
        return feature_ops.get(value.id)
    dotted = _dotted(value)
    prefix = "adsk.fusion.FeatureOperations."
    if dotted.startswith(prefix):
        return FEATURE_OPERATION_ALIASES.get(dotted[len(prefix) :])
    return None


def _parse_direction(value: ast.expr) -> str | None:
    dotted = _dotted(value)
    prefix = "adsk.fusion.ExtentDirections."
    if dotted.startswith(prefix):
        return DIRECTION_ALIASES.get(dotted[len(prefix) :])
    return None


def _parse_hole_edge_position(value: ast.expr) -> str | None:
    dotted = _dotted(value)
    prefix = "adsk.fusion.HoleEdgePositions."
    if dotted == prefix + "EdgeStartPointPosition":
        return "start"
    if dotted == prefix + "EdgeMidPointPosition":
        return "mid"
    if dotted == prefix + "EdgeEndPointPosition":
        return "end"
    return None


def _parse_extent_definition(value: ast.expr, value_inputs: dict[str, str]) -> tuple[str, str | None] | None:
    if not isinstance(value, ast.Call):
        return None
    dotted = _dotted(value.func)
    if dotted == "adsk.fusion.DistanceExtentDefinition.create" and len(value.args) == 1:
        distance = _parse_value_input(value.args[0], value_inputs)
        if distance is None:
            raise SampleConversionError(f"Unsupported distance extent value: {ast.unparse(value.args[0]).strip()}")
        return "distance", distance
    if dotted == "adsk.fusion.ThroughAllExtentDefinition.create" and not value.args:
        return "through_all", None
    return None


def _parse_move_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    object_collections: dict[str, list[str]],
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput2" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "move":
        return None
    if not isinstance(value.args[0], ast.Name):
        raise SampleConversionError("Move createInput2 expects a named ObjectCollection.")
    items = object_collections.get(value.args[0].id)
    if not items:
        raise SampleConversionError(f"Unknown move input collection: {value.args[0].id}")
    return {
        "entities": items[0] if len(items) == 1 else "[" + ", ".join(items) + "]",
        "translation": None,
        "transform": None,
    }


def _parse_offset_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    object_collections: dict[str, list[str]],
    value_inputs: dict[str, str],
    feature_ops: dict[str, str],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) not in {3, 4}:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "offset":
        return None
    distance = _parse_value_input(value.args[1], value_inputs)
    operation = _parse_feature_operation(value.args[2], feature_ops)
    if distance is None or operation is None:
        raise SampleConversionError(f"Unsupported offset input: {ast.unparse(value).strip()}")
    chain = _parse_bool(value.args[3], state.bools) if len(value.args) == 4 else True
    if chain is None:
        raise SampleConversionError(f"Unsupported offset chain flag: {ast.unparse(value.args[3]).strip()}")
    return {
        "entities": _collection_argument_expr(value.args[0], object_collections, state),
        "distance": distance,
        "operation": operation,
        "chain": chain,
    }


def _parse_replace_face_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    object_collections: dict[str, list[str]],
    bools: dict[str, bool],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 3:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "replace_face":
        return None
    tangent_chain = _parse_bool(value.args[1], bools)
    if tangent_chain is None:
        raise SampleConversionError(f"Unsupported replace-face tangent chain flag: {ast.unparse(value.args[1]).strip()}")
    return {
        "source_faces": _collection_argument_expr(value.args[0], object_collections, state),
        "tangent_chain": tangent_chain,
        "target": state.sample_expr(value.args[2]),
    }


def _parse_scale_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    object_collections: dict[str, list[str]],
    value_inputs: dict[str, str],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 3:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "scale":
        return None
    factor = _parse_value_input(value.args[2], value_inputs)
    if factor is None:
        raise SampleConversionError(f"Unsupported scale factor: {ast.unparse(value.args[2]).strip()}")
    return {
        "entities": _collection_argument_expr(value.args[0], object_collections, state),
        "origin": state.sample_expr(value.args[1], point=True),
        "factor": factor,
        "xyz": None,
    }


def _parse_split_body_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 3:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "split_body":
        return None
    extend = _parse_bool(value.args[2], state.bools)
    if extend is None:
        raise SampleConversionError(f"Unsupported split-body extend flag: {ast.unparse(value.args[2]).strip()}")
    return {
        "bodies": state.sample_expr(value.args[0]),
        "tool": state.sample_expr(value.args[1]),
        "extend": extend,
    }


def _parse_thread_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    object_collections: dict[str, list[str]],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 2:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "thread":
        return None
    return {
        "faces": _collection_argument_expr(value.args[0], object_collections, state),
        "internal": False,
        "length": None,
        "full_length": True,
    }


def _parse_trim_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "trim":
        return None
    return {"tool": state.sample_expr(value.args[0]), "cell": 0}


def _parse_thread_query_alias(
    value: ast.expr,
    feature_collections: dict[str, str],
    thread_queries: set[str],
) -> bool:
    if not isinstance(value, ast.Attribute) or value.attr != "threadDataQuery":
        return False
    if not isinstance(value.value, ast.Name):
        return False
    return feature_collections.get(value.value.id) == "thread"


def _parse_thread_query_value(value: ast.expr, thread_queries: set[str], state: _ConversionState) -> bool:
    if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name) and value.value.id in thread_queries:
        return True
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
        if isinstance(value.func.value, ast.Name) and value.func.value.id in thread_queries:
            return True
    if isinstance(value, ast.Subscript):
        base = value.value
        if isinstance(base, ast.Name) and base.id in state.scalars:
            return True
    return False


def _parse_thread_info_create(
    value: ast.expr,
    feature_collections: dict[str, str],
    thread_queries: set[str],
) -> bool:
    if not isinstance(value, ast.Call):
        return False
    dotted = _dotted(value.func)
    if dotted == "adsk.fusion.ThreadInfo.create":
        return True
    if isinstance(value.func, ast.Attribute) and isinstance(value.func.value, ast.Name):
        return feature_collections.get(value.func.value.id) == "thread" and value.func.attr == "createThreadInfo"
    return False


def _parse_trim_cells_alias(value: ast.expr, trims: dict[str, dict[str, object]]) -> str | None:
    if not isinstance(value, ast.Attribute) or value.attr != "bRepCells":
        return None
    if not isinstance(value.value, ast.Name):
        return None
    return value.value.id if value.value.id in trims else None


def _parse_trim_cell_ref(value: ast.expr, trim_cells: dict[str, str]) -> tuple[str, int] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "item" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    trim_name = trim_cells.get(value.func.value.id)
    if trim_name is None:
        return None
    index = _literal_number(value.args[0])
    if index is None:
        raise SampleConversionError(f"Unsupported trim cell index: {ast.unparse(value.args[0]).strip()}")
    return trim_name, int(index)


def _parse_extrude_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    feature_ops: dict[str, str],
) -> dict[str, str] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 2:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "extrude":
        return None
    if not isinstance(value.args[0], ast.Name):
        raise SampleConversionError("createInput profile argument must be a named profile variable.")
    operation = _parse_feature_operation(value.args[1], feature_ops)
    if operation is None:
        raise SampleConversionError(f"Unsupported createInput operation: {ast.unparse(value.args[1]).strip()}")
    return {"profile": value.args[0].id, "operation": operation}


def _parse_revolve_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    feature_ops: dict[str, str],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 3:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "revolve":
        return None
    operation = _parse_feature_operation(value.args[2], feature_ops)
    if operation is None:
        raise SampleConversionError(f"Unsupported revolve operation: {ast.unparse(value.args[2]).strip()}")
    return {
        "profile": state.sample_expr(value.args[0]),
        "axis": state.sample_expr(value.args[1]),
        "operation": operation,
        "angle": None,
        "symmetric": False,
    }


def _parse_sweep_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    feature_ops: dict[str, str],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 3:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "sweep":
        return None
    operation = _parse_feature_operation(value.args[2], feature_ops)
    if operation is None:
        raise SampleConversionError(f"Unsupported sweep operation: {ast.unparse(value.args[2]).strip()}")
    return {
        "profile": state.sample_expr(value.args[0]),
        "path": state.sample_expr(value.args[1]),
        "operation": operation,
        "guide": None,
        "taper": None,
        "twist": None,
        "scale": None,
        "flip": False,
    }


def _parse_loft_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    feature_ops: dict[str, str],
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "loft":
        return None
    operation = _parse_feature_operation(value.args[0], feature_ops)
    if operation is None:
        raise SampleConversionError(f"Unsupported loft operation: {ast.unparse(value.args[0]).strip()}")
    return {
        "sections": [],
        "operation": operation,
        "solid": False,
        "closed": False,
        "merge_tangent_edges": True,
        "start_alignment": "free",
        "end_alignment": "free",
        "rails": None,
    }


def _parse_patch_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    feature_ops: dict[str, str],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 2:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "patch":
        return None
    operation = _parse_feature_operation(value.args[1], feature_ops)
    if operation is None:
        raise SampleConversionError(f"Unsupported patch operation: {ast.unparse(value.args[1]).strip()}")
    return {
        "boundary": state.sample_expr(value.args[0]),
        "operation": operation,
    }


def _parse_shell_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    bools: dict[str, bool],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 2:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "shell":
        return None
    tangent_chain = _parse_bool(value.args[1], bools)
    if tangent_chain is None:
        raise SampleConversionError(f"Unsupported shell tangent-chain flag: {ast.unparse(value.args[1]).strip()}")
    return {
        "entities": _collection_argument_expr(value.args[0], state.object_collections, state),
        "inside": None,
        "outside": None,
        "tangent_chain": tangent_chain,
        "shell_type": "sharp",
    }


def _parse_draft_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    bools: dict[str, bool],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 3:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "draft":
        return None
    tangent_chain = _parse_bool(value.args[2], bools)
    if tangent_chain is None:
        raise SampleConversionError(f"Unsupported draft tangent-chain flag: {ast.unparse(value.args[2]).strip()}")
    return {
        "faces": state.sample_expr(value.args[0]),
        "plane": state.sample_expr(value.args[1]),
        "tangent_chain": tangent_chain,
        "flip": False,
        "symmetric": True,
        "angle": None,
    }


def _parse_hole_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    value_inputs: dict[str, str],
) -> BuilderState | None:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "hole":
        return None
    method = value.func.attr
    if method == "createSimpleInput" and len(value.args) == 1:
        diameter = _parse_value_input(value.args[0], value_inputs)
        if diameter is None:
            raise SampleConversionError(f"Unsupported hole diameter: {ast.unparse(value.args[0]).strip()}")
        return BuilderState(base_expr=f"root.hole({diameter})")
    if method == "createCounterboreInput" and len(value.args) == 3:
        values = [_parse_value_input(arg, value_inputs) for arg in value.args]
        if any(item is None for item in values):
            raise SampleConversionError(f"Unsupported counterbore input: {ast.unparse(value).strip()}")
        builder = BuilderState(base_expr=f"root.hole({values[0]})")
        builder.append(f".counterbore({values[1]}, {values[2]})")
        return builder
    if method == "createCountersinkInput" and len(value.args) == 3:
        values = [_parse_value_input(arg, value_inputs) for arg in value.args]
        if any(item is None for item in values):
            raise SampleConversionError(f"Unsupported countersink input: {ast.unparse(value).strip()}")
        builder = BuilderState(base_expr=f"root.hole({values[0]})")
        builder.append(f".countersink({values[1]}, {values[2]})")
        return builder
    return None


def _parse_combine_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    object_collections: dict[str, list[str]],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 2:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "combine":
        return None
    return {
        "target": state.sample_expr(value.args[0]),
        "tools": _collection_argument_expr(value.args[1], object_collections, state),
        "operation": "join",
        "keep_tools": False,
        "new_component": False,
    }


def _parse_mirror_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    object_collections: dict[str, list[str]],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 2:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "mirror":
        return None
    return {
        "entities": _collection_argument_expr(value.args[0], object_collections, state),
        "plane": state.sample_expr(value.args[1]),
    }


def _parse_circular_pattern_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    object_collections: dict[str, list[str]],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 2:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "circular_pattern":
        return None
    return {
        "entities": _collection_argument_expr(value.args[0], object_collections, state),
        "axis": state.sample_expr(value.args[1]),
        "quantity": None,
        "angle": None,
        "symmetric": False,
    }


def _parse_rectangular_pattern_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    object_collections: dict[str, list[str]],
    state: _ConversionState,
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or len(value.args) != 5:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "rectangular_pattern":
        return None
    quantity_one = state.sample_expr(value.args[2])
    distance_one = state.sample_expr(value.args[3])
    distance_type = _parse_pattern_distance_type(value.args[4])
    if distance_type is None:
        raise SampleConversionError(f"Unsupported pattern distance type: {ast.unparse(value.args[4]).strip()}")
    return {
        "entities": _collection_argument_expr(value.args[0], object_collections, state),
        "direction_one": state.sample_expr(value.args[1]),
        "quantity_one": quantity_one,
        "distance_one": distance_one,
        "direction_two": None,
        "quantity_two": None,
        "distance_two": None,
        "distance_type": distance_type,
        "symmetric_one": False,
        "symmetric_two": False,
    }


def _parse_construction_create_input(
    value: ast.expr,
    feature_collections: dict[str, str],
    construction_policy: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "createInput" or value.args:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    family = feature_collections.get(value.func.value.id)
    if not family or not family.startswith("construction:"):
        return None
    _, helper_name = family.split(":", 1)
    policy = next((data for data in construction_policy.values() if data["helper_name"] == helper_name), None)
    if policy is None:
        raise SampleConversionError(f"Unsupported construction helper: {helper_name}")
    return {"helper": helper_name, "policy": policy, "method": None, "args": []}


def _parse_fillet_create_input(value: ast.expr, feature_collections: dict[str, str]) -> bool:
    return (
        isinstance(value, ast.Call)
        and _attr_name(value.func) == "createInput"
        and isinstance(value.func, ast.Attribute)
        and isinstance(value.func.value, ast.Name)
        and feature_collections.get(value.func.value.id) == "fillet"
    )


def _parse_chamfer_create_input(value: ast.expr, feature_collections: dict[str, str]) -> bool:
    return (
        isinstance(value, ast.Call)
        and _attr_name(value.func) == "createInput2"
        and isinstance(value.func, ast.Attribute)
        and isinstance(value.func.value, ast.Name)
        and feature_collections.get(value.func.value.id) == "chamfer"
    )


def _parse_add_simple_call(
    value: ast.expr,
    value_inputs: dict[str, str],
    feature_ops: dict[str, str],
) -> dict[str, str] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "addSimple" or len(value.args) != 3:
        return None
    if not isinstance(value.args[0], ast.Name):
        raise SampleConversionError("addSimple profile argument must be a named profile variable.")
    distance = _parse_value_input(value.args[1], value_inputs)
    operation = _parse_feature_operation(value.args[2], feature_ops)
    if distance is None or operation is None:
        raise SampleConversionError(f"Unsupported addSimple call: {ast.unparse(value).strip()}")
    return {"profile": value.args[0].id, "distance": distance, "operation": operation}


def _parse_sketch_shape_call(
    value: ast.expr,
    collection_targets: dict[str, tuple[str, str]],
    points: dict[str, tuple[str, str]],
    value_inputs: dict[str, str],
    scalars: dict[str, str],
    object_collections: dict[str, list[str]],
    sketch_policy: dict[tuple[str, str, int], dict[str, object]],
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return None
    if not isinstance(value.func.value, ast.Name):
        return None
    target = collection_targets.get(value.func.value.id)
    if target is None:
        return None
    sketch, raw_collection = target
    spec = sketch_policy.get((raw_collection, value.func.attr, len(value.args)))
    if spec is None:
        return None
    args = []
    for coercer, argument in zip(spec["coercers"], value.args, strict=True):
        parsed = _parse_shape_argument(coercer, argument, points, value_inputs, scalars, object_collections)
        if parsed is None:
            raise SampleConversionError(f"Unsupported sketch call: {ast.unparse(value).strip()}")
        if coercer == "point_collection":
            args.extend(parsed)
        else:
            args.append(parsed)
    return {"sketch": sketch, "method": spec["compact_method"], "args": args}


def _parse_shape_argument(
    coercer: str,
    value: ast.expr,
    points: dict[str, tuple[str, str]],
    value_inputs: dict[str, str],
    scalars: dict[str, str],
    object_collections: dict[str, list[str]],
) -> str | list[str] | None:
    if coercer == "point":
        point = _parse_point(value, points)
        return point[0] if point is not None else None
    if coercer == "point_collection":
        if isinstance(value, ast.Name) and value.id in object_collections:
            return list(object_collections[value.id])
        if isinstance(value, (ast.List, ast.Tuple)):
            items = []
            for element in value.elts:
                point = _parse_point(element, points)
                if point is None:
                    return None
                items.append(point[0])
            return items
        return None
    if coercer in {"length_cm", "identity"}:
        return _parse_value_input(value, value_inputs) or _parse_scalar(value, scalars) or _literal_number(value) or ast.unparse(value).strip()
    raise SampleConversionError(f"Unsupported sketch argument coercer in sample conversion: {coercer}")


def _parse_text_create_input(
    value: ast.expr,
    collection_targets: dict[str, tuple[str, str]],
    value_inputs: dict[str, str],
    scalars: dict[str, str],
    text_policy: dict[str, object],
) -> dict[str, object] | None:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return None
    if not isinstance(value.func.value, ast.Name):
        return None
    target = collection_targets.get(value.func.value.id)
    if target is None or target[1] != text_policy.get("collection_attr"):
        return None
    if value.func.attr != text_policy.get("builder_input") or len(value.args) != 2:
        return None
    if not isinstance(value.args[0], ast.Constant) or not isinstance(value.args[0].value, str):
        raise SampleConversionError("Sketch text input must use a string literal for text.")
    height = (
        _parse_value_input(value.args[1], value_inputs)
        or _parse_scalar(value.args[1], scalars)
        or _literal_number(value.args[1])
    )
    if height is None:
        raise SampleConversionError(f"Unsupported sketch text height: {ast.unparse(value.args[1]).strip()}")
    return {
        "sketch": target[0],
        "text": json.dumps(value.args[0].value),
        "height": height,
        "font": None,
        "hflip": False,
        "vflip": False,
        "mode": None,
    }


def _parse_text_attribute_assign(
    attr_name: str,
    value: ast.expr,
    text: dict[str, object],
    bools: dict[str, bool],
    scalars: dict[str, str],
    text_policy: dict[str, object],
) -> bool:
    attrs = text_policy.get("input_attrs", {})
    if attr_name == attrs.get("horizontal_flip"):
        flag = _parse_bool(value, bools)
        if flag is None:
            raise SampleConversionError(f"Unsupported sketch text horizontal flip: {ast.unparse(value).strip()}")
        text["hflip"] = flag
        return True
    if attr_name == attrs.get("vertical_flip"):
        flag = _parse_bool(value, bools)
        if flag is None:
            raise SampleConversionError(f"Unsupported sketch text vertical flip: {ast.unparse(value).strip()}")
        text["vflip"] = flag
        return True
    if attr_name == attrs.get("font_name"):
        font_name = _parse_scalar(value, scalars)
        if font_name is None:
            raise SampleConversionError(f"Unsupported sketch text font: {ast.unparse(value).strip()}")
        text["font"] = font_name
        return True
    return False


def _parse_text_mutation(
    value: ast.expr,
    texts: dict[str, dict[str, object]],
    bools: dict[str, bool],
    value_inputs: dict[str, str],
    scalars: dict[str, str],
    horizontal_values: dict[str, str],
    vertical_values: dict[str, str],
    horizontal_aliases: dict[str, str],
    vertical_aliases: dict[str, str],
    state: _ConversionState,
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    text = texts.get(value.func.value.id)
    if text is None:
        return False
    method = value.func.attr
    if method == "setAsMultiLine" and len(value.args) == 5:
        h_align = _parse_alignment(value.args[2], horizontal_aliases, "HorizontalAlignments", horizontal_values)
        v_align = _parse_alignment(value.args[3], vertical_aliases, "VerticalAlignments", vertical_values)
        spacing = _parse_scalar(value.args[4], scalars) or _parse_value_input(value.args[4], value_inputs) or _literal_number(value.args[4])
        if h_align is None or v_align is None or spacing is None:
            raise SampleConversionError(f"Unsupported sketch text multiline call: {ast.unparse(value).strip()}")
        text["mode"] = {
            "kind": "multiline",
            "corner": state.sample_expr(value.args[0], point=True),
            "diagonal": state.sample_expr(value.args[1], point=True),
            "h_align": h_align,
            "v_align": v_align,
            "spacing": spacing,
        }
        return True
    if method == "setAsAlongPath" and len(value.args) == 4:
        above = _parse_bool(value.args[1], bools)
        align = _parse_alignment(value.args[2], horizontal_aliases, "HorizontalAlignments", horizontal_values)
        spacing = _parse_scalar(value.args[3], scalars) or _parse_value_input(value.args[3], value_inputs) or _literal_number(value.args[3])
        if above is None or align is None or spacing is None:
            raise SampleConversionError(f"Unsupported sketch text along-path call: {ast.unparse(value).strip()}")
        text["mode"] = {
            "kind": "along_path",
            "path": state.sample_expr(value.args[0]),
            "above": above,
            "align": align,
            "spacing": spacing,
        }
        return True
    if method == "setAsFitOnPath" and len(value.args) == 2:
        above = _parse_bool(value.args[1], bools)
        if above is None:
            raise SampleConversionError(f"Unsupported sketch text fit-path call: {ast.unparse(value).strip()}")
        text["mode"] = {
            "kind": "fit_path",
            "path": state.sample_expr(value.args[0]),
            "above": above,
        }
        return True
    return False


def _parse_text_build(
    value: ast.expr,
    collection_targets: dict[str, tuple[str, str]],
    texts: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute) or value.func.attr != "add":
        return None
    if not isinstance(value.func.value, ast.Name):
        return None
    target = collection_targets.get(value.func.value.id)
    if target is None or target[1] != "sketchTexts" or len(value.args) != 1:
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    text = texts.pop(value.args[0].id, None)
    if text is None:
        return None
    return _render_text_call(text)


def _render_text_call(text: dict[str, object]) -> str:
    mode = text.get("mode")
    if not isinstance(mode, dict):
        raise SampleConversionError("Sketch text input was never configured with a mode.")
    if mode["kind"] == "multiline":
        parts = [
            text["text"],
            mode["corner"],
            mode["diagonal"],
            text["height"],
        ]
        kwargs: list[str] = []
        _append_kwarg(kwargs, "h_align", mode["h_align"], default=json.dumps("left"))
        _append_kwarg(kwargs, "v_align", mode["v_align"], default=json.dumps("top"))
        _append_kwarg(kwargs, "spacing", mode["spacing"], default="0")
        _append_kwarg(kwargs, "font", text["font"])
        _append_kwarg(kwargs, "hflip", "True" if text["hflip"] else None)
        _append_kwarg(kwargs, "vflip", "True" if text["vflip"] else None)
        rendered = ", ".join(parts + kwargs)
        return f"{text['sketch']}.text({rendered})"
    if mode["kind"] == "along_path":
        parts = [text["text"], mode["path"], text["height"]]
        kwargs = []
        _append_kwarg(kwargs, "above", "True" if mode["above"] else None)
        _append_kwarg(kwargs, "align", mode["align"], default=json.dumps("center"))
        _append_kwarg(kwargs, "spacing", mode["spacing"], default="0")
        _append_kwarg(kwargs, "font", text["font"])
        _append_kwarg(kwargs, "hflip", "True" if text["hflip"] else None)
        _append_kwarg(kwargs, "vflip", "True" if text["vflip"] else None)
        rendered = ", ".join(parts + kwargs)
        return f"{text['sketch']}.text_path({rendered})"
    if mode["kind"] == "fit_path":
        parts = [text["text"], mode["path"], text["height"]]
        kwargs = []
        _append_kwarg(kwargs, "above", "True" if mode["above"] else None)
        _append_kwarg(kwargs, "font", text["font"])
        _append_kwarg(kwargs, "hflip", "True" if text["hflip"] else None)
        _append_kwarg(kwargs, "vflip", "True" if text["vflip"] else None)
        rendered = ", ".join(parts + kwargs)
        return f"{text['sketch']}.text_fit({rendered})"
    raise SampleConversionError(f"Unsupported sketch text mode: {mode['kind']}")


def _append_kwarg(items: list[str], key: str, value: str | None, *, default: str | None = None) -> None:
    if value is None or value == default:
        return
    items.append(f"{key}={value}")


def _parse_alignment(
    value: ast.expr,
    reverse_aliases: dict[str, str],
    prefix: str,
    named_values: dict[str, str],
) -> str | None:
    if isinstance(value, ast.Name):
        return named_values.get(value.id)
    dotted = _dotted(value)
    enum_prefix = f"adsk.core.{prefix}."
    if dotted.startswith(enum_prefix):
        alias = reverse_aliases.get(dotted[len(enum_prefix) :])
        if alias is None:
            return None
        return json.dumps(alias)
    return None


def _parse_extrude_builder_mutation(
    value: ast.expr,
    extents: dict[str, tuple[str, str | None]],
    value_inputs: dict[str, str],
    bools: dict[str, bool],
) -> dict[str, str] | None:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return None
    if not isinstance(value.func.value, ast.Name):
        return None
    builder = value.func.value.id
    method = value.func.attr

    if method == "setOneSideExtent" and len(value.args) in {2, 3}:
        kind, distance = _parse_extent_argument(value.args[0], extents, value_inputs)
        direction = _parse_direction(value.args[1])
        if direction is None:
            raise SampleConversionError(f"Unsupported one-side direction: {ast.unparse(value.args[1]).strip()}")
        taper = _parse_value_input(value.args[2], value_inputs) if len(value.args) == 3 else None
        fragment = _one_side_fragment(distance, direction) if kind == "distance" else _through_all_fragment(direction)
        if taper is not None:
            fragment += f".taper({taper})"
        return {"builder": builder, "fragment": fragment}

    if method == "setSymmetricExtent" and len(value.args) in {2, 3}:
        distance = _parse_value_input(value.args[0], value_inputs)
        if distance is None:
            raise SampleConversionError(f"Unsupported symmetric distance: {ast.unparse(value.args[0]).strip()}")
        full_length = _parse_bool(value.args[1], bools)
        if full_length is None:
            raise SampleConversionError(f"Unsupported symmetric full-length flag: {ast.unparse(value.args[1]).strip()}")
        taper = _parse_value_input(value.args[2], value_inputs) if len(value.args) == 3 else None
        fragment = f".symmetric({distance}" + ("" if full_length else ", full_length=False") + ")"
        if taper is not None:
            fragment += f".taper({taper})"
        return {"builder": builder, "fragment": fragment}

    return None


def _parse_extrude_builder_build(value: ast.expr, feature_collections: dict[str, str]) -> dict[str, str] | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "extrude":
        return None
    if isinstance(value.args[0], ast.Name):
        return {"builder": value.args[0].id}
    return None


def _parse_extrude_builder_attribute_assign(
    attr_name: str,
    value: ast.expr,
    builder: BuilderState,
    bools: dict[str, bool],
) -> bool:
    if attr_name != "isSolid":
        return False
    solid = _parse_bool(value, bools)
    if solid is None:
        raise SampleConversionError(f"Unsupported extrude isSolid assignment: {ast.unparse(value).strip()}")
    if not solid:
        builder.append(".surface()")
    return True


def _parse_revolve_builder_mutation(
    value: ast.expr,
    revolves: dict[str, dict[str, object]],
    value_inputs: dict[str, str],
    bools: dict[str, bool],
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    builder = revolves.get(value.func.value.id)
    if builder is None or value.func.attr != "setAngleExtent" or len(value.args) != 2:
        return False
    symmetric = _parse_bool(value.args[0], bools)
    angle = _parse_value_input(value.args[1], value_inputs)
    if symmetric is None or angle is None:
        raise SampleConversionError(f"Unsupported revolve extent: {ast.unparse(value).strip()}")
    builder["symmetric"] = symmetric
    builder["angle"] = angle
    return True


def _parse_revolve_builder_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    revolves: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "revolve":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    builder = revolves.pop(value.args[0].id, None)
    if builder is None:
        return None
    angle = builder.get("angle")
    if angle is None:
        raise SampleConversionError("Revolve builder must set an angle before add(...).")
    if builder["symmetric"]:
        expr = _component_revolve(builder["profile"], builder["axis"], None, builder["operation"])
        return f"{expr}.angle({angle}, symmetric=True).build()"
    return _component_revolve(builder["profile"], builder["axis"], angle, builder["operation"])


def _parse_sweep_mutation(
    value: ast.expr,
    sweeps: dict[str, dict[str, object]],
    value_inputs: dict[str, str],
    bools: dict[str, bool],
    state: _ConversionState,
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    sweep = sweeps.get(value.func.value.id)
    if sweep is None:
        return False
    if value.func.attr == "setPath" and len(value.args) == 1:
        sweep["path"] = state.sample_expr(value.args[0])
        return True
    if value.func.attr == "setGuideRail" and len(value.args) == 1:
        sweep["guide"] = state.sample_expr(value.args[0])
        return True
    return False


def _parse_sweep_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    sweeps: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "sweep":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    sweep = sweeps.pop(value.args[0].id, None)
    if sweep is None:
        return None
    return _component_sweep(
        str(sweep["profile"]),
        str(sweep["path"]),
        str(sweep["operation"]),
        guide=sweep["guide"],
        taper=sweep["taper"],
        twist=sweep["twist"],
        scale=sweep["scale"],
        flip=bool(sweep["flip"]),
    )


def _parse_loft_mutation(
    value: ast.expr,
    lofts: dict[str, dict[str, object]],
    state: _ConversionState,
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    target_name, method_name = _call_target(value.func)
    if target_name is None or target_name not in lofts or method_name != "add" or len(value.args) != 1:
        return False
    if not (isinstance(value.func.value, ast.Attribute) and value.func.value.attr == "loftSections"):
        return False
    lofts[target_name]["sections"].append(state.sample_expr(value.args[0]))
    return True


def _parse_loft_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    lofts: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "loft":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    loft = lofts.pop(value.args[0].id, None)
    if loft is None:
        return None
    if len(loft["sections"]) < 2:
        raise SampleConversionError("Loft input must define at least two sections before add(...).")
    return _component_loft(
        list(loft["sections"]),
        str(loft["operation"]),
        bool(loft["solid"]),
        bool(loft["closed"]),
        bool(loft["merge_tangent_edges"]),
        str(loft["start_alignment"]),
        str(loft["end_alignment"]),
        loft["rails"],
    )


def _parse_patch_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    patches: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "patch":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    patch = patches.pop(value.args[0].id, None)
    if patch is None:
        return None
    return _component_patch(str(patch["boundary"]), str(patch["operation"]))


def _parse_shell_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    shells: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "shell":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    shell = shells.pop(value.args[0].id, None)
    if shell is None:
        return None
    return _component_shell(
        str(shell["entities"]),
        shell["inside"],
        shell["outside"],
        bool(shell["tangent_chain"]),
        str(shell["shell_type"]),
    )


def _parse_draft_mutation(
    value: ast.expr,
    drafts: dict[str, dict[str, object]],
    value_inputs: dict[str, str],
    bools: dict[str, bool],
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    draft = drafts.get(value.func.value.id)
    if draft is None or value.func.attr != "setSingleAngle" or len(value.args) != 2:
        return False
    symmetric = _parse_bool(value.args[0], bools)
    angle = _parse_value_input(value.args[1], value_inputs)
    if symmetric is None or angle is None:
        raise SampleConversionError(f"Unsupported draft single angle call: {ast.unparse(value).strip()}")
    draft["symmetric"] = symmetric
    draft["angle"] = angle
    return True


def _parse_draft_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    drafts: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "draft":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    draft = drafts.pop(value.args[0].id, None)
    if draft is None:
        return None
    if draft["angle"] is None:
        raise SampleConversionError("Draft input must define setSingleAngle(...) before add(...).")
    return _component_draft(
        str(draft["faces"]),
        str(draft["plane"]),
        str(draft["angle"]),
        bool(draft["tangent_chain"]),
        bool(draft["symmetric"]),
        bool(draft["flip"]),
    )


def _parse_hole_builder_mutation(
    value: ast.expr,
    holes: dict[str, BuilderState],
    value_inputs: dict[str, str],
    object_collections: dict[str, list[str]],
    state: _ConversionState,
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    builder = holes.get(value.func.value.id)
    if builder is None:
        return False
    method = value.func.attr
    if method == "setDistanceExtent" and len(value.args) == 1:
        depth = _parse_value_input(value.args[0], value_inputs)
        if depth is None:
            raise SampleConversionError(f"Unsupported hole depth: {ast.unparse(value.args[0]).strip()}")
        builder.append(f".depth({depth})")
        return True
    if method == "setPositionByPlaneAndOffsets" and len(value.args) == 6:
        args = [
            state.sample_expr(value.args[0]),
            state.sample_expr(value.args[1], point=True),
            state.sample_expr(value.args[2]),
            state.sample_expr(value.args[3]),
            state.sample_expr(value.args[4]),
            state.sample_expr(value.args[5]),
        ]
        builder.append(f".by_offsets({', '.join(args)})")
        return True
    if method == "setPositionOnEdge" and len(value.args) == 3:
        position = _parse_hole_edge_position(value.args[2])
        if position is None:
            raise SampleConversionError(f"Unsupported hole edge position: {ast.unparse(value.args[2]).strip()}")
        fragment = f".on_edge({state.sample_expr(value.args[0])}, {state.sample_expr(value.args[1])}"
        if position != "mid":
            fragment += f", position={json.dumps(position)}"
        fragment += ")"
        builder.append(fragment)
        return True
    if method == "setPositionAtCenter" and len(value.args) == 2:
        builder.append(f".at_center({state.sample_expr(value.args[0])}, {state.sample_expr(value.args[1])})")
        return True
    if method == "setPositionBySketchPoints" and len(value.args) == 1 and isinstance(value.args[0], ast.Name):
        items = object_collections.get(value.args[0].id)
        if not items:
            raise SampleConversionError(f"Unknown sketch-point collection: {value.args[0].id}")
        builder.append(f".by_points({', '.join(items)})")
        return True
    return False


def _parse_hole_builder_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    holes: dict[str, BuilderState],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "hole":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    builder = holes.pop(value.args[0].id, None)
    if builder is None:
        return None
    return f"{builder.render()}.build()"


def _parse_combine_attribute_assign(
    attr_name: str,
    value: ast.expr,
    combine: dict[str, object],
    feature_ops: dict[str, str],
    bools: dict[str, bool],
) -> bool:
    if attr_name == "operation":
        operation = _parse_feature_operation(value, feature_ops)
        if operation is None:
            raise SampleConversionError(f"Unsupported combine operation: {ast.unparse(value).strip()}")
        combine["operation"] = operation
        return True
    if attr_name == "isKeepToolBodies":
        keep_tools = _parse_bool(value, bools)
        if keep_tools is None:
            raise SampleConversionError(f"Unsupported combine keep-tools flag: {ast.unparse(value).strip()}")
        combine["keep_tools"] = keep_tools
        return True
    if attr_name == "isNewComponent":
        new_component = _parse_bool(value, bools)
        if new_component is None:
            raise SampleConversionError(f"Unsupported combine new-component flag: {ast.unparse(value).strip()}")
        combine["new_component"] = new_component
        return True
    return False


def _parse_sweep_attribute_assign(
    attr_name: str,
    value: ast.expr,
    sweep: dict[str, object],
    value_inputs: dict[str, str],
    bools: dict[str, bool],
    state: _ConversionState,
) -> bool:
    if attr_name == "guideRail":
        sweep["guide"] = state.sample_expr(value)
        return True
    if attr_name == "profileScaling":
        scaling = _parse_sweep_profile_scaling(value)
        if scaling is None:
            raise SampleConversionError(f"Unsupported sweep profile scaling: {ast.unparse(value).strip()}")
        sweep["scale"] = scaling
        return True
    if attr_name == "isDirectionFlipped":
        flipped = _parse_bool(value, bools)
        if flipped is None:
            raise SampleConversionError(f"Unsupported sweep direction flip: {ast.unparse(value).strip()}")
        sweep["flip"] = flipped
        return True
    if attr_name == "taperAngle":
        taper = _parse_value_input(value, value_inputs)
        if taper is None:
            raise SampleConversionError(f"Unsupported sweep taper angle: {ast.unparse(value).strip()}")
        sweep["taper"] = taper
        return True
    if attr_name == "twistAngle":
        twist = _parse_value_input(value, value_inputs)
        if twist is None:
            raise SampleConversionError(f"Unsupported sweep twist angle: {ast.unparse(value).strip()}")
        sweep["twist"] = twist
        return True
    return False


def _parse_loft_attribute_assign(
    attr_name: str,
    value: ast.expr,
    loft: dict[str, object],
    bools: dict[str, bool],
) -> bool:
    if attr_name == "isSolid":
        solid = _parse_bool(value, bools)
        if solid is None:
            raise SampleConversionError(f"Unsupported loft solid flag: {ast.unparse(value).strip()}")
        loft["solid"] = solid
        return True
    if attr_name == "isClosed":
        closed = _parse_bool(value, bools)
        if closed is None:
            raise SampleConversionError(f"Unsupported loft closed flag: {ast.unparse(value).strip()}")
        loft["closed"] = closed
        return True
    if attr_name == "isTangentEdgesMerged":
        merged = _parse_bool(value, bools)
        if merged is None:
            raise SampleConversionError(f"Unsupported loft tangent-edge merge flag: {ast.unparse(value).strip()}")
        loft["merge_tangent_edges"] = merged
        return True
    if attr_name == "startLoftEdgeAlignment":
        alignment = _parse_loft_edge_alignment(value)
        if alignment is None:
            raise SampleConversionError(f"Unsupported loft start alignment: {ast.unparse(value).strip()}")
        loft["start_alignment"] = alignment
        return True
    if attr_name == "endLoftEdgeAlignment":
        alignment = _parse_loft_edge_alignment(value)
        if alignment is None:
            raise SampleConversionError(f"Unsupported loft end alignment: {ast.unparse(value).strip()}")
        loft["end_alignment"] = alignment
        return True
    return False


def _parse_shell_attribute_assign(
    attr_name: str,
    value: ast.expr,
    shell: dict[str, object],
    value_inputs: dict[str, str],
    state: _ConversionState,
) -> bool:
    if attr_name == "insideThickness":
        inside = _parse_value_input(value, value_inputs)
        if inside is None:
            raise SampleConversionError(f"Unsupported shell inside thickness: {ast.unparse(value).strip()}")
        shell["inside"] = inside
        return True
    if attr_name == "outsideThickness":
        outside = _parse_value_input(value, value_inputs)
        if outside is None:
            raise SampleConversionError(f"Unsupported shell outside thickness: {ast.unparse(value).strip()}")
        shell["outside"] = outside
        return True
    if attr_name == "shellType":
        shell_kind = _parse_shell_type(value)
        if shell_kind is None:
            raise SampleConversionError(f"Unsupported shell type: {ast.unparse(value).strip()}")
        shell["shell_type"] = shell_kind
        return True
    if attr_name == "inputEntities":
        shell["entities"] = state.sample_expr(value)
        return True
    return False


def _parse_draft_attribute_assign(
    attr_name: str,
    value: ast.expr,
    draft: dict[str, object],
    bools: dict[str, bool],
) -> bool:
    if attr_name != "isDirectionFlipped":
        return False
    flipped = _parse_bool(value, bools)
    if flipped is None:
        raise SampleConversionError(f"Unsupported draft direction flip: {ast.unparse(value).strip()}")
    draft["flip"] = flipped
    return True


def _parse_matrix_attribute_assign(
    attr_name: str,
    value: ast.expr,
    matrix: dict[str, object],
    vectors: dict[str, str],
) -> bool:
    if attr_name != "translation":
        return False
    translation = _parse_vector(value, vectors)
    if translation is None:
        raise SampleConversionError(f"Unsupported Matrix3D translation assignment: {ast.unparse(value).strip()}")
    matrix["translation"] = translation
    return True


def _parse_scale_attribute_assign(
    attr_name: str,
    value: ast.expr,
    scale: dict[str, object],
    value_inputs: dict[str, str],
) -> bool:
    return False


def _parse_thread_attribute_assign(
    attr_name: str,
    value: ast.expr,
    thread: dict[str, object],
    bools: dict[str, bool],
    value_inputs: dict[str, str],
) -> bool:
    if attr_name == "isFullLength":
        full_length = _parse_bool(value, bools)
        if full_length is None:
            raise SampleConversionError(f"Unsupported thread full-length flag: {ast.unparse(value).strip()}")
        thread["full_length"] = full_length
        return True
    if attr_name == "threadLength":
        length = _parse_value_input(value, value_inputs)
        if length is None:
            raise SampleConversionError(f"Unsupported thread length: {ast.unparse(value).strip()}")
        thread["length"] = length
        return True
    return False


def _parse_trim_cell_attribute_assign(
    attr_name: str,
    value: ast.expr,
    trim_cell_ref: tuple[str, int],
    trims: dict[str, dict[str, object]],
    bools: dict[str, bool],
) -> bool:
    if attr_name != "isSelected":
        return False
    selected = _parse_bool(value, bools)
    if selected is None:
        raise SampleConversionError(f"Unsupported trim cell selection flag: {ast.unparse(value).strip()}")
    if selected:
        trim_name, index = trim_cell_ref
        trims[trim_name]["cell"] = index
    return True


def _parse_combine_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    combines: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "combine":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    combine = combines.pop(value.args[0].id, None)
    if combine is None:
        return None
    return _component_combine(
        combine["target"],
        combine["tools"],
        str(combine["operation"]),
        bool(combine["keep_tools"]),
        bool(combine["new_component"]),
    )


def _parse_move_mutation(
    value: ast.expr,
    moves: dict[str, dict[str, object]],
    matrices: dict[str, dict[str, object]],
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    move = moves.get(value.func.value.id)
    if move is None or value.func.attr != "defineAsFreeMove" or len(value.args) != 1:
        return False
    arg = value.args[0]
    if isinstance(arg, ast.Name) and arg.id in matrices:
        matrix = matrices[arg.id]
        move["translation"] = matrix.get("translation")
        if move["translation"] is None:
            move["transform"] = arg.id
        return True
    move["transform"] = ast.unparse(arg).strip()
    return True


def _parse_move_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    moves: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "move":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    move = moves.pop(value.args[0].id, None)
    if move is None:
        return None
    if move["translation"] is None and move["transform"] is None:
        raise SampleConversionError("Move input must define defineAsFreeMove(...) before add(...).")
    return _component_move(str(move["entities"]), move["translation"], move["transform"])


def _parse_offset_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    offsets: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "offset":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    offset = offsets.pop(value.args[0].id, None)
    if offset is None:
        return None
    return _component_offset(
        str(offset["entities"]),
        str(offset["distance"]),
        str(offset["operation"]),
        bool(offset["chain"]),
    )


def _parse_replace_face_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    replace_faces: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "replace_face":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    replace_face = replace_faces.pop(value.args[0].id, None)
    if replace_face is None:
        return None
    return _component_replace_face(
        str(replace_face["source_faces"]),
        str(replace_face["target"]),
        bool(replace_face["tangent_chain"]),
    )


def _parse_scale_mutation(
    value: ast.expr,
    scales: dict[str, dict[str, object]],
    value_inputs: dict[str, str],
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    scale = scales.get(value.func.value.id)
    if scale is None or value.func.attr != "setToNonUniform" or len(value.args) != 3:
        return False
    xyz = tuple(_parse_value_input(arg, value_inputs) for arg in value.args)
    if any(item is None for item in xyz):
        raise SampleConversionError(f"Unsupported scale factors: {ast.unparse(value).strip()}")
    scale["xyz"] = xyz
    return True


def _parse_scale_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    scales: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "scale":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    scale = scales.pop(value.args[0].id, None)
    if scale is None:
        return None
    return _component_scale(
        str(scale["entities"]),
        str(scale["origin"]),
        str(scale["factor"]),
        scale["xyz"],
    )


def _parse_split_body_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    split_bodies: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "split_body":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    split_body = split_bodies.pop(value.args[0].id, None)
    if split_body is None:
        return None
    return _component_split_body(
        str(split_body["bodies"]),
        str(split_body["tool"]),
        bool(split_body["extend"]),
    )


def _parse_thread_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    threads: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "thread":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    thread = threads.pop(value.args[0].id, None)
    if thread is None:
        return None
    return _component_thread(str(thread["faces"]), bool(thread["internal"]), thread["length"])


def _parse_trim_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    trims: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "trim":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    trim = trims.pop(value.args[0].id, None)
    if trim is None:
        return None
    return _component_trim(str(trim["tool"]), int(trim["cell"]))


def _parse_mirror_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    mirrors: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "mirror":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    mirror = mirrors.pop(value.args[0].id, None)
    if mirror is None:
        return None
    return _component_mirror(str(mirror["entities"]), str(mirror["plane"]))


def _parse_circular_pattern_attribute_assign(
    attr_name: str,
    value: ast.expr,
    circular_pattern: dict[str, object],
    value_inputs: dict[str, str],
    scalars: dict[str, str],
    bools: dict[str, bool],
) -> bool:
    if attr_name == "quantity":
        quantity = _parse_value_input(value, value_inputs) or _parse_scalar(value, scalars)
        if quantity is None:
            raise SampleConversionError(f"Unsupported circular-pattern quantity: {ast.unparse(value).strip()}")
        circular_pattern["quantity"] = quantity
        return True
    if attr_name == "totalAngle":
        angle = _parse_value_input(value, value_inputs) or _parse_scalar(value, scalars)
        if angle is None:
            raise SampleConversionError(f"Unsupported circular-pattern angle: {ast.unparse(value).strip()}")
        circular_pattern["angle"] = angle
        return True
    if attr_name == "isSymmetric":
        symmetric = _parse_bool(value, bools)
        if symmetric is None:
            raise SampleConversionError(f"Unsupported circular-pattern symmetry flag: {ast.unparse(value).strip()}")
        circular_pattern["symmetric"] = symmetric
        return True
    return False


def _parse_circular_pattern_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    circular_patterns: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "circular_pattern":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    circular_pattern = circular_patterns.pop(value.args[0].id, None)
    if circular_pattern is None:
        return None
    if circular_pattern["quantity"] is None or circular_pattern["angle"] is None:
        raise SampleConversionError("Circular pattern input must define quantity and totalAngle before add(...).")
    return _component_circular_pattern(
        str(circular_pattern["entities"]),
        str(circular_pattern["axis"]),
        str(circular_pattern["quantity"]),
        str(circular_pattern["angle"]),
        bool(circular_pattern["symmetric"]),
    )


def _parse_rectangular_pattern_attribute_assign(
    attr_name: str,
    value: ast.expr,
    rectangular_pattern: dict[str, object],
    bools: dict[str, bool],
) -> bool:
    if attr_name == "isSymmetricInDirectionOne":
        symmetric = _parse_bool(value, bools)
        if symmetric is None:
            raise SampleConversionError(f"Unsupported rectangular-pattern direction-one symmetry: {ast.unparse(value).strip()}")
        rectangular_pattern["symmetric_one"] = symmetric
        return True
    if attr_name == "isSymmetricInDirectionTwo":
        symmetric = _parse_bool(value, bools)
        if symmetric is None:
            raise SampleConversionError(f"Unsupported rectangular-pattern direction-two symmetry: {ast.unparse(value).strip()}")
        rectangular_pattern["symmetric_two"] = symmetric
        return True
    if attr_name == "patternDistanceType":
        distance_type = _parse_pattern_distance_type(value)
        if distance_type is None:
            raise SampleConversionError(f"Unsupported rectangular-pattern distance type: {ast.unparse(value).strip()}")
        rectangular_pattern["distance_type"] = distance_type
        return True
    return False


def _parse_rectangular_pattern_mutation(
    value: ast.expr,
    rectangular_patterns: dict[str, dict[str, object]],
    state: _ConversionState,
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    rectangular_pattern = rectangular_patterns.get(value.func.value.id)
    if rectangular_pattern is None or value.func.attr != "setDirectionTwo" or len(value.args) != 3:
        return False
    rectangular_pattern["direction_two"] = state.sample_expr(value.args[0])
    rectangular_pattern["quantity_two"] = state.sample_expr(value.args[1])
    rectangular_pattern["distance_two"] = state.sample_expr(value.args[2])
    return True


def _parse_rectangular_pattern_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    rectangular_patterns: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "rectangular_pattern":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    rectangular_pattern = rectangular_patterns.pop(value.args[0].id, None)
    if rectangular_pattern is None:
        return None
    return _component_rect_pattern(
        str(rectangular_pattern["entities"]),
        str(rectangular_pattern["direction_one"]),
        str(rectangular_pattern["quantity_one"]),
        str(rectangular_pattern["distance_one"]),
        rectangular_pattern["direction_two"],
        rectangular_pattern["quantity_two"],
        rectangular_pattern["distance_two"],
        str(rectangular_pattern["distance_type"]),
        bool(rectangular_pattern["symmetric_one"]),
        bool(rectangular_pattern["symmetric_two"]),
    )


def _parse_construction_builder_mutation(
    value: ast.expr,
    constructions: dict[str, dict[str, object]],
    state: _ConversionState,
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    if not isinstance(value.func.value, ast.Name):
        return False
    builder = constructions.get(value.func.value.id)
    if builder is None:
        return False
    method_name = builder["policy"]["reverse_methods"].get(value.func.attr)
    if method_name is None:
        return False
    builder["method"] = method_name
    builder["args"] = _construction_args(builder["helper"], method_name, value.args, state)
    return True


def _parse_construction_builder_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    constructions: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    family = feature_collections.get(value.func.value.id)
    if not family or not family.startswith("construction:"):
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    builder = constructions.pop(value.args[0].id, None)
    if builder is None:
        return None
    if builder["method"] is None:
        raise SampleConversionError(f"Construction input {value.args[0].id} has no defining setBy... call.")
    return f"root.{builder['helper']}.{builder['method']}({', '.join(builder['args'])})"


def _parse_fillet_builder_mutation(
    value: ast.expr,
    fillets: dict[str, dict[str, object]],
    object_collections: dict[str, list[str]],
    value_inputs: dict[str, str],
    bools: dict[str, bool],
    state: _ConversionState,
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    target_name, method_name = _call_target(value.func)
    if method_name != "addConstantRadiusEdgeSet" or target_name not in fillets:
        return False
    if len(value.args) != 3:
        raise SampleConversionError(f"Unsupported fillet edge set: {ast.unparse(value).strip()}")
    radius = _parse_value_input(value.args[1], value_inputs)
    tangent_chain = _parse_bool(value.args[2], bools)
    if radius is None or tangent_chain is None:
        raise SampleConversionError(f"Unsupported fillet edge set: {ast.unparse(value).strip()}")
    edge_expr = _collection_argument_expr(value.args[0], object_collections, state)
    fillets[target_name] = {"expr": _component_fillet(edge_expr, radius, tangent_chain)}
    return True


def _parse_fillet_builder_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    fillets: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "fillet":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    builder = fillets.pop(value.args[0].id, None)
    if builder is None:
        return None
    return builder["expr"]


def _parse_chamfer_builder_mutation(
    value: ast.expr,
    chamfers: dict[str, dict[str, object]],
    object_collections: dict[str, list[str]],
    value_inputs: dict[str, str],
    bools: dict[str, bool],
    state: _ConversionState,
) -> bool:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return False
    target_name, method_name = _call_target(value.func)
    if method_name != "addEqualDistanceChamferEdgeSet" or target_name not in chamfers:
        return False
    if len(value.args) != 3:
        raise SampleConversionError(f"Unsupported chamfer edge set: {ast.unparse(value).strip()}")
    distance = _parse_value_input(value.args[1], value_inputs)
    tangent_chain = _parse_bool(value.args[2], bools)
    if distance is None or tangent_chain is None:
        raise SampleConversionError(f"Unsupported chamfer edge set: {ast.unparse(value).strip()}")
    edge_expr = _collection_argument_expr(value.args[0], object_collections, state)
    chamfers[target_name] = {"expr": _component_chamfer(edge_expr, distance, tangent_chain)}
    return True


def _parse_chamfer_builder_build(
    value: ast.expr,
    feature_collections: dict[str, str],
    chamfers: dict[str, dict[str, object]],
) -> str | None:
    if not isinstance(value, ast.Call) or _attr_name(value.func) != "add" or len(value.args) != 1:
        return None
    if not isinstance(value.func, ast.Attribute) or not isinstance(value.func.value, ast.Name):
        return None
    if feature_collections.get(value.func.value.id) != "chamfer":
        return None
    if not isinstance(value.args[0], ast.Name):
        return None
    builder = chamfers.pop(value.args[0].id, None)
    if builder is None:
        return None
    return builder["expr"]


def _construction_args(helper: str, method_name: str, args: list[ast.expr], state: _ConversionState) -> list[str]:
    if helper == "plane":
        mapping = {
            "offset": [False, False],
            "angle": [False, False, False],
            "between": [False, False],
            "tangent": [False, False, False],
            "edges": [False, False],
            "three_points": [True, True, True],
            "tangent_at": [False, True],
            "on_path": [False, False],
        }
    elif helper == "axis":
        mapping = {
            "circular_face": [False],
            "perpendicular": [False, True],
            "between_planes": [False, False],
            "between_points": [True, True],
            "edge": [False],
            "normal": [False, True],
        }
    else:
        mapping = {
            "edges": [False, False],
            "planes": [False, False, False],
            "edge_plane": [False, False],
            "center": [False],
            "at": [False],
        }
    point_flags = mapping[method_name]
    return [state.sample_expr(arg, point=is_point) for arg, is_point in zip(args, point_flags, strict=True)]


def _parse_extent_argument(
    value: ast.expr,
    extents: dict[str, tuple[str, str | None]],
    value_inputs: dict[str, str],
) -> tuple[str, str | None]:
    if isinstance(value, ast.Name) and value.id in extents:
        return extents[value.id]
    extent = _parse_extent_definition(value, value_inputs)
    if extent is None:
        raise SampleConversionError(f"Unsupported extent argument: {ast.unparse(value).strip()}")
    return extent


def _is_signature_call(value: ast.expr) -> bool:
    return isinstance(value, ast.Call) and _dotted(value.func) == "print_design_signature"


def _component_extrude(profile: str, operation: str, distance: str | None = None) -> str:
    args = [profile]
    if distance is not None:
        args.append(distance)
    if operation != "new_body":
        args.append(f'op={json.dumps(operation)}')
    return f"root.extrude({', '.join(args)})"


def _component_revolve(profile: str, axis: str, angle: str | None, operation: str) -> str:
    args = [profile, axis]
    if angle is not None:
        args.append(angle)
    if operation != "new_body":
        args.append(f'op={json.dumps(operation)}')
    return f"root.revolve({', '.join(args)})"


def _component_sweep(
    profile: str,
    path: str,
    operation: str,
    *,
    guide: object,
    taper: object,
    twist: object,
    scale: object,
    flip: bool,
) -> str:
    args = [profile, path]
    if operation != "new_body":
        args.append(f'op={json.dumps(operation)}')
    if guide is not None:
        args.append(f"guide={guide}")
    if taper is not None:
        args.append(f"taper={taper}")
    if twist is not None:
        args.append(f"twist={twist}")
    if scale is not None:
        args.append(f"scale={json.dumps(str(scale))}")
    if flip:
        args.append("flip=True")
    return f"root.sweep({', '.join(args)})"


def _component_loft(
    sections: list[str],
    operation: str,
    solid: bool,
    closed: bool,
    merge_tangent_edges: bool,
    start_alignment: str,
    end_alignment: str,
    rails: object,
) -> str:
    args = list(sections)
    if operation != "new_body":
        args.append(f'op={json.dumps(operation)}')
    if solid:
        args.append("solid=True")
    if closed:
        args.append("closed=True")
    if not merge_tangent_edges:
        args.append("merge_tangent_edges=False")
    if start_alignment != "free":
        args.append(f"start_alignment={json.dumps(start_alignment)}")
    if end_alignment != "free":
        args.append(f"end_alignment={json.dumps(end_alignment)}")
    if rails is not None:
        args.append(f"rails={rails}")
    return f"root.loft({', '.join(args)})"


def _component_patch(boundary: str, operation: str) -> str:
    args = [boundary]
    if operation != "new_body":
        args.append(f'op={json.dumps(operation)}')
    return f"root.patch({', '.join(args)})"


def _component_shell(entities: str, inside: object, outside: object, tangent_chain: bool, shell_type: str) -> str:
    args = [entities]
    if inside is not None:
        args.append(f"inside={inside}")
    if outside is not None:
        args.append(f"outside={outside}")
    if not tangent_chain:
        args.append("tangent_chain=False")
    if shell_type != "sharp":
        args.append(f"shell_type={json.dumps(shell_type)}")
    return f"root.shell({', '.join(args)})"


def _component_draft(
    faces: str,
    plane: str,
    angle: str,
    tangent_chain: bool,
    symmetric: bool,
    flip: bool,
) -> str:
    args = [faces, plane, angle]
    if not tangent_chain:
        args.append("tangent_chain=False")
    if not symmetric:
        args.append("symmetric=False")
    if flip:
        args.append("flip=True")
    return f"root.draft({', '.join(args)})"


def _component_move(entities: str, translation: object, transform: object) -> str:
    args = [entities]
    if translation is not None:
        args.append(f"translation={translation}")
    elif transform is not None:
        args.append(f"transform={transform}")
    else:
        raise SampleConversionError("Move translation or transform is required.")
    return f"root.move({', '.join(args)})"


def _component_offset(entities: str, distance: str, operation: str, chain: bool) -> str:
    args = [entities, distance]
    if operation != "new_body":
        args.append(f'op={json.dumps(operation)}')
    if not chain:
        args.append("chain=False")
    return f"root.offset({', '.join(args)})"


def _component_replace_face(source_faces: str, target: str, tangent_chain: bool) -> str:
    args = [source_faces, target]
    if tangent_chain:
        args.append("tangent_chain=True")
    return f"root.replace_face({', '.join(args)})"


def _component_scale(entities: str, origin: str, factor: str, xyz: object) -> str:
    args = [entities, origin, factor]
    if xyz is not None:
        args.append("xyz=(" + ", ".join(str(value) for value in xyz) + ")")
    return f"root.scale({', '.join(args)})"


def _component_split_body(bodies: str, tool: str, extend: bool) -> str:
    args = [bodies, tool]
    if not extend:
        args.append("extend=False")
    return f"root.split_body({', '.join(args)})"


def _component_thread(faces: str, internal: bool, length: object) -> str:
    args = [faces]
    if internal:
        args.append("internal=True")
    if length is not None:
        args.append(f"length={length}")
    return f"root.thread({', '.join(args)})"


def _component_trim(tool: str, cell: int) -> str:
    if cell == 0:
        return f"root.trim({tool})"
    return f"root.trim({tool}, cell={cell})"


def _component_combine(target: str, tools: str, operation: str, keep_tools: bool, new_component: bool) -> str:
    args = [target, tools]
    if operation != "join":
        args.append(f'op={json.dumps(operation)}')
    if keep_tools:
        args.append("keep_tools=True")
    if new_component:
        args.append("new_component=True")
    return f"root.combine({', '.join(args)})"


def _component_mirror(entities: str, plane: str) -> str:
    return f"root.mirror({entities}, {plane})"


def _component_circular_pattern(entities: str, axis: str, quantity: str, angle: str, symmetric: bool) -> str:
    args = [entities, axis, quantity, angle]
    if symmetric:
        args.append("symmetric=True")
    return f"root.circular_pattern({', '.join(args)})"


def _component_rect_pattern(
    entities: str,
    direction_one: str,
    quantity_one: str,
    distance_one: str,
    direction_two: object,
    quantity_two: object,
    distance_two: object,
    distance_type: str,
    symmetric_one: bool,
    symmetric_two: bool,
) -> str:
    args = [entities, direction_one, quantity_one, distance_one]
    if direction_two is not None or quantity_two is not None or distance_two is not None:
        if direction_two is None or quantity_two is None or distance_two is None:
            raise SampleConversionError("Rectangular pattern second direction is incomplete.")
        args.extend([str(direction_two), str(quantity_two), str(distance_two)])
    if distance_type != "spacing":
        args.append(f'distance_type={json.dumps(distance_type)}')
    if symmetric_one:
        args.append("symmetric_one=True")
    if symmetric_two:
        args.append("symmetric_two=True")
    return f"root.rect_pattern({', '.join(args)})"


def _component_fillet(edges: str, radius: str, tangent_chain: bool) -> str:
    if tangent_chain:
        return f"root.fillet({edges}, {radius})"
    return f"root.fillet({edges}, {radius}, tangent_chain=False)"


def _component_chamfer(edges: str, distance: str, tangent_chain: bool) -> str:
    if tangent_chain:
        return f"root.chamfer({edges}, {distance})"
    return f"root.chamfer({edges}, {distance}, tangent_chain=False)"


def _collection_argument_expr(value: ast.expr, object_collections: dict[str, list[str]], state: _ConversionState) -> str:
    if isinstance(value, ast.Name) and value.id in object_collections:
        items = object_collections[value.id]
        if len(items) == 1:
            return items[0]
        return "[" + ", ".join(items) + "]"
    return state.sample_expr(value)


def _one_side_fragment(distance: str | None, direction: str) -> str:
    if distance is None:
        raise SampleConversionError("Distance extent requires a distance value.")
    if direction == "positive":
        return f".one_side({distance})"
    return f".one_side({distance}, direction={json.dumps(direction)})"


def _through_all_fragment(direction: str) -> str:
    if direction == "positive":
        return ".through_all()"
    return f".through_all({json.dumps(direction)})"


def _call_target(node: ast.Attribute) -> tuple[str | None, str]:
    if isinstance(node.value, ast.Name):
        return node.value.id, node.attr
    if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
        return node.value.value.id, node.attr
    return None, node.attr


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        return f"{_dotted(node.func)}()"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _attr_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _literal_number(node: ast.expr) -> str | None:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _literal_number(node.operand)
        if operand is None:
            return None
        if isinstance(node.op, ast.USub):
            return operand[1:] if operand.startswith("-") else f"-{operand}"
        return operand[1:] if operand.startswith("+") else operand
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        value = node.value
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return repr(value)
    return None


def _parse_pattern_distance_type(value: ast.expr) -> str | None:
    dotted = _dotted(value)
    prefix = "adsk.fusion.PatternDistanceType."
    if dotted.startswith(prefix):
        return PATTERN_DISTANCE_TYPE_ALIASES.get(dotted[len(prefix) :])
    return None


def _parse_sweep_profile_scaling(value: ast.expr) -> str | None:
    dotted = _dotted(value)
    prefix = "adsk.fusion.SweepProfileScalingOptions."
    if dotted.startswith(prefix):
        return SWEEP_PROFILE_SCALING_ALIASES.get(dotted[len(prefix) :])
    return None


def _parse_loft_edge_alignment(value: ast.expr) -> str | None:
    dotted = _dotted(value)
    prefix = "adsk.fusion.LoftEdgeAlignments."
    if dotted.startswith(prefix):
        return LOFT_EDGE_ALIGNMENT_ALIASES.get(dotted[len(prefix) :])
    return None


def _parse_shell_type(value: ast.expr) -> str | None:
    dotted = _dotted(value)
    prefix = "adsk.fusion.ShellTypes."
    if dotted.startswith(prefix):
        return SHELL_TYPE_ALIASES.get(dotted[len(prefix) :])
    return None


class _ExpressionRewriter(ast.NodeTransformer):
    def __init__(self, aliases: dict[str, str]) -> None:
        self.aliases = aliases

    def visit_Name(self, node: ast.Name) -> ast.AST:
        alias = self.aliases.get(node.id)
        if alias is None:
            return node
        return ast.copy_location(ast.Name(id=alias, ctx=node.ctx), node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        node = self.generic_visit(node)
        dotted = _dotted(node.func)
        if dotted == "adsk.core.Point3D.create":
            return ast.copy_location(
                ast.Call(func=ast.Attribute(value=ast.Name(id="fx", ctx=ast.Load()), attr="p", ctx=ast.Load()), args=node.args, keywords=[]),
                node,
            )
        if dotted == "adsk.core.ValueInput.createByReal" and len(node.args) == 1:
            return node.args[0]
        if dotted == "adsk.core.ValueInput.createByString" and len(node.args) == 1:
            return node.args[0]
        return node
