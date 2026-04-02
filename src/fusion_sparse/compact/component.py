"""Compact component wrappers."""

from __future__ import annotations

from fusion_sparse.compact._surface import invoke_generated_method
from fusion_sparse.compact._helpers import (
    feature_operation,
    feature_path,
    loft_edge_alignment,
    object_collection,
    pattern_distance_type,
    plane_or_entity,
    raw_list,
    shell_type_value,
    sweep_profile_scaling,
)
from fusion_sparse.compact.construction import AxisHelper, PlaneHelper, PointHelper
from fusion_sparse.compact.extrude import ExtrudeBuilder
from fusion_sparse.compact.hole import HoleBuilder
from fusion_sparse.compact.modify import (
    move_entities,
    offset_entities,
    replace_faces,
    scale_entities,
    split_bodies,
    thread_faces,
    trim_tool,
)
from fusion_sparse.compact.revolve import RevolveBuilder
from fusion_sparse.generated.compact_policy import (
    CHAMFER_POLICY,
    CIRCULAR_PATTERN_POLICY,
    COMBINE_POLICY,
    CONSTRUCTION_POLICY,
    DRAFT_POLICY,
    EXTRUDE_POLICY,
    FILLET_POLICY,
    HOLE_POLICY,
    LOFT_POLICY,
    MIRROR_POLICY,
    MOVE_POLICY,
    OFFSET_POLICY,
    PATCH_POLICY,
    PLANE_ALIASES,
    REPLACE_FACE_POLICY,
    RECTANGULAR_PATTERN_POLICY,
    REVOLVE_POLICY,
    SCALE_POLICY,
    SHELL_POLICY,
    SWEEP_POLICY,
    SPLIT_BODY_POLICY,
    THREAD_POLICY,
    TRIM_POLICY,
)
from fusion_sparse.runtime.adapter import unwrap, wrap
from fusion_sparse.runtime.values import v
from fusion_sparse.runtime.refs import Ref


class ComponentRef(Ref):
    """High-value component helpers for sketching and extrusion."""

    @property
    def plane(self):
        return PlaneHelper(self.raw, self.raw.constructionPlanes, CONSTRUCTION_POLICY["plane"])

    @property
    def axis(self):
        return AxisHelper(self.raw, self.raw.constructionAxes, CONSTRUCTION_POLICY["axis"])

    @property
    def point(self):
        return PointHelper(self.raw, self.raw.constructionPoints, CONSTRUCTION_POLICY["point"])

    def sketch(self, plane):
        return invoke_generated_method(self.raw, "ComponentRef.sketch", plane)

    def extrude(self, profile, distance=None, op="new_body"):
        extrude_features = self.raw.features.extrudeFeatures
        profile_raw = unwrap(profile)
        operation = feature_operation(op)
        if distance is not None:
            simple_method = getattr(extrude_features, EXTRUDE_POLICY["simple_method"])
            return wrap(simple_method(profile_raw, v(distance), operation))
        return ExtrudeBuilder(extrude_features, profile_raw, operation, EXTRUDE_POLICY)

    def revolve(self, profile, axis, angle=None, op="new_body"):
        revolve_features = self.raw.features.revolveFeatures
        builder = RevolveBuilder(
            revolve_features,
            unwrap(profile),
            unwrap(axis),
            feature_operation(op),
            REVOLVE_POLICY,
        )
        if angle is not None:
            return builder.angle(angle).build()
        return builder

    def sweep(self, profile, path, op="new_body", guide=None, taper=None, twist=None, scale=None, flip=False, chain=True):
        sweep_features = self.raw.features.sweepFeatures
        input_obj = getattr(sweep_features, SWEEP_POLICY["builder_input"])(
            unwrap(profile),
            feature_path(self.raw.features, path, chain=chain),
            feature_operation(op),
        )
        if guide is not None:
            setattr(input_obj, SWEEP_POLICY["input_attrs"]["guide_rail"], feature_path(self.raw.features, guide, chain=chain))
        if taper is not None:
            setattr(input_obj, SWEEP_POLICY["input_attrs"]["taper_angle"], v(taper))
        if twist is not None:
            setattr(input_obj, SWEEP_POLICY["input_attrs"]["twist_angle"], v(twist))
        if scale is not None:
            setattr(input_obj, SWEEP_POLICY["input_attrs"]["profile_scaling"], sweep_profile_scaling(scale))
        if flip:
            setattr(input_obj, SWEEP_POLICY["input_attrs"]["direction_flipped"], True)
        return wrap(getattr(sweep_features, SWEEP_POLICY["builder_terminal"])(input_obj))

    def loft(
        self,
        *sections,
        op="new_body",
        solid=False,
        closed=False,
        merge_tangent_edges=True,
        start_alignment="free",
        end_alignment="free",
        rails=None,
    ):
        if len(sections) < 2:
            raise ValueError("loft requires at least two sections.")
        loft_features = self.raw.features.loftFeatures
        input_obj = getattr(loft_features, LOFT_POLICY["builder_input"])(feature_operation(op))
        loft_sections = getattr(input_obj, LOFT_POLICY["input_attrs"]["sections"])
        add_section = LOFT_POLICY["input_methods"]["add_section"]
        for section in sections:
            getattr(loft_sections, add_section)(unwrap(section))
        if rails is not None:
            rails_value = unwrap(rails)
            rails_target = getattr(input_obj, LOFT_POLICY["input_attrs"]["rails"])
            if hasattr(rails_target, "add"):
                for rail in (rails_value if isinstance(rails_value, (list, tuple, set, frozenset)) else [rails_value]):
                    rails_target.add(unwrap(rail))
            else:
                setattr(input_obj, LOFT_POLICY["input_attrs"]["rails"], unwrap(rails))
        setattr(input_obj, LOFT_POLICY["input_attrs"]["solid"], bool(solid))
        setattr(input_obj, LOFT_POLICY["input_attrs"]["closed"], bool(closed))
        setattr(input_obj, LOFT_POLICY["input_attrs"]["merge_tangent_edges"], bool(merge_tangent_edges))
        setattr(input_obj, LOFT_POLICY["input_attrs"]["start_alignment"], loft_edge_alignment(start_alignment))
        setattr(input_obj, LOFT_POLICY["input_attrs"]["end_alignment"], loft_edge_alignment(end_alignment))
        return wrap(getattr(loft_features, LOFT_POLICY["builder_terminal"])(input_obj))

    def patch(self, boundary, op="new_body"):
        patch_features = self.raw.features.patchFeatures
        input_obj = getattr(patch_features, PATCH_POLICY["builder_input"])(unwrap(boundary), feature_operation(op))
        return wrap(getattr(patch_features, PATCH_POLICY["builder_terminal"])(input_obj))

    def shell(self, entities, inside=None, outside=None, tangent_chain=True, shell_type="sharp"):
        shell_features = self.raw.features.shellFeatures
        input_obj = getattr(shell_features, SHELL_POLICY["builder_input"])(object_collection(entities), bool(tangent_chain))
        if inside is not None:
            setattr(input_obj, SHELL_POLICY["input_attrs"]["inside_thickness"], v(inside))
        if outside is not None:
            setattr(input_obj, SHELL_POLICY["input_attrs"]["outside_thickness"], v(outside))
        if shell_type is not None:
            setattr(input_obj, SHELL_POLICY["input_attrs"]["shell_type"], shell_type_value(shell_type))
        return wrap(getattr(shell_features, SHELL_POLICY["builder_terminal"])(input_obj))

    def draft(self, faces, plane, angle, tangent_chain=True, symmetric=True, flip=False):
        draft_features = self.raw.features.draftFeatures
        input_obj = getattr(draft_features, DRAFT_POLICY["builder_input"])(
            raw_list(faces),
            plane_or_entity(self.raw, plane, PLANE_ALIASES),
            bool(tangent_chain),
        )
        setattr(input_obj, DRAFT_POLICY["input_attrs"]["direction_flipped"], bool(flip))
        getattr(input_obj, DRAFT_POLICY["input_methods"]["single_angle"])(bool(symmetric), v(angle))
        return wrap(getattr(draft_features, DRAFT_POLICY["builder_terminal"])(input_obj))

    def hole(self, diameter, depth=None):
        return HoleBuilder(self.raw.features.holeFeatures, diameter, depth, HOLE_POLICY)

    def fillet(self, edges, radius, tangent_chain=True):
        fillets = self.raw.features.filletFeatures
        input_obj = getattr(fillets, FILLET_POLICY["builder_input"])()
        edge_sets = getattr(input_obj, FILLET_POLICY["input_attrs"]["edge_sets"], input_obj)
        getattr(edge_sets, FILLET_POLICY["input_methods"]["constant_radius"])(
            object_collection(edges),
            v(radius),
            bool(tangent_chain),
        )
        return wrap(getattr(fillets, FILLET_POLICY["builder_terminal"])(input_obj))

    def chamfer(self, edges, distance, tangent_chain=True):
        chamfers = self.raw.features.chamferFeatures
        input_obj = getattr(chamfers, CHAMFER_POLICY["builder_input"])()
        edge_sets = getattr(input_obj, CHAMFER_POLICY["input_attrs"]["edge_sets"], input_obj)
        getattr(edge_sets, CHAMFER_POLICY["input_methods"]["equal_distance"])(
            object_collection(edges),
            v(distance),
            bool(tangent_chain),
        )
        return wrap(getattr(chamfers, CHAMFER_POLICY["builder_terminal"])(input_obj))

    def combine(self, target, tools, op="join", keep_tools=False, new_component=False):
        combines = self.raw.features.combineFeatures
        input_obj = getattr(combines, COMBINE_POLICY["builder_input"])(unwrap(target), object_collection(tools))
        setattr(input_obj, COMBINE_POLICY["input_attrs"]["operation"], feature_operation(op))
        setattr(input_obj, COMBINE_POLICY["input_attrs"]["keep_tools"], bool(keep_tools))
        setattr(input_obj, COMBINE_POLICY["input_attrs"]["new_component"], bool(new_component))
        return wrap(getattr(combines, COMBINE_POLICY["builder_terminal"])(input_obj))

    def mirror(self, entities, plane):
        mirrors = self.raw.features.mirrorFeatures
        input_obj = getattr(mirrors, MIRROR_POLICY["builder_input"])(
            object_collection(entities),
            plane_or_entity(self.raw, plane, PLANE_ALIASES),
        )
        return wrap(getattr(mirrors, MIRROR_POLICY["builder_terminal"])(input_obj))

    def move(self, entities, *, translation=None, transform=None):
        return move_entities(
            self.raw,
            MOVE_POLICY,
            entities,
            translation=translation,
            transform=transform,
        )

    def offset(self, entities, distance, op="new_body", chain=True):
        return offset_entities(
            self.raw,
            OFFSET_POLICY,
            entities,
            distance,
            op=op,
            chain=chain,
        )

    def replace_face(self, source_faces, target, tangent_chain=False):
        return replace_faces(
            self.raw,
            REPLACE_FACE_POLICY,
            source_faces,
            target,
            tangent_chain=tangent_chain,
        )

    def scale(self, entities, origin, factor, xyz=None):
        return scale_entities(self.raw, SCALE_POLICY, entities, origin, factor, xyz=xyz)

    def split_body(self, bodies, tool, extend=True):
        return split_bodies(self.raw, SPLIT_BODY_POLICY, bodies, tool, extend=extend)

    def thread(
        self,
        faces,
        *,
        internal=False,
        length=None,
        thread_type=None,
        designation=None,
        thread_class=None,
    ):
        return thread_faces(
            self.raw,
            THREAD_POLICY,
            faces,
            internal=internal,
            length=length,
            thread_type=thread_type,
            designation=designation,
            thread_class=thread_class,
        )

    def trim(self, tool, cell=0):
        return trim_tool(self.raw, TRIM_POLICY, tool, cell=cell)

    def circular_pattern(self, entities, axis, quantity, angle="360 deg", symmetric=False):
        patterns = self.raw.features.circularPatternFeatures
        input_obj = getattr(patterns, CIRCULAR_PATTERN_POLICY["builder_input"])(
            object_collection(entities),
            unwrap(axis),
        )
        setattr(input_obj, CIRCULAR_PATTERN_POLICY["input_attrs"]["quantity"], v(quantity))
        setattr(input_obj, CIRCULAR_PATTERN_POLICY["input_attrs"]["total_angle"], v(angle))
        setattr(input_obj, CIRCULAR_PATTERN_POLICY["input_attrs"]["symmetric"], bool(symmetric))
        return wrap(getattr(patterns, CIRCULAR_PATTERN_POLICY["builder_terminal"])(input_obj))

    def rect_pattern(
        self,
        entities,
        direction_one,
        quantity_one,
        distance_one,
        direction_two=None,
        quantity_two=None,
        distance_two=None,
        distance_type="spacing",
        symmetric_one=False,
        symmetric_two=False,
    ):
        patterns = self.raw.features.rectangularPatternFeatures
        distance_kind = pattern_distance_type(distance_type)
        input_obj = getattr(patterns, RECTANGULAR_PATTERN_POLICY["builder_input"])(
            object_collection(entities),
            unwrap(direction_one),
            v(quantity_one),
            v(distance_one),
            distance_kind,
        )
        needs_direction_two = any(value is not None for value in (direction_two, quantity_two, distance_two))
        if needs_direction_two:
            if quantity_two is None or distance_two is None:
                raise ValueError("rect_pattern direction_two requires quantity_two and distance_two.")
            getattr(input_obj, RECTANGULAR_PATTERN_POLICY["input_methods"]["direction_two"])(
                unwrap(direction_two) if direction_two is not None else None,
                v(quantity_two),
                v(distance_two),
            )
        setattr(input_obj, RECTANGULAR_PATTERN_POLICY["input_attrs"]["distance_type"], distance_kind)
        setattr(input_obj, RECTANGULAR_PATTERN_POLICY["input_attrs"]["symmetric_one"], bool(symmetric_one))
        if needs_direction_two:
            setattr(input_obj, RECTANGULAR_PATTERN_POLICY["input_attrs"]["symmetric_two"], bool(symmetric_two))
        return wrap(getattr(patterns, RECTANGULAR_PATTERN_POLICY["builder_terminal"])(input_obj))

__all__ = ["ComponentRef"]
