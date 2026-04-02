"""Generated compact behavior policy. Do not edit by hand."""

from __future__ import annotations

import json as _json

DESIGN_WORKSPACE_POLICY = _json.loads('{"adjacent":["Sketches","SketchLines","SketchCircles","SketchArcs","SketchPoints","SketchEllipses","SketchFittedSplines","SketchTexts","ExtrudeFeatures","ConstructionPlanes","ConstructionAxes","ConstructionPoints","RevolveFeatures","HoleFeatures","FilletFeatures","ChamferFeatures","CombineFeatures","MirrorFeatures","RectangularPatternFeatures","CircularPatternFeatures","LoftFeatures","SweepFeatures","ShellFeatures","DraftFeatures","PatchFeatures","MoveFeatures","OffsetFeatures","ReplaceFaceFeatures","ScaleFeatures","SplitBodyFeatures","ThreadFeatures","TrimFeatures"],"scope_namespaces":["adsk.fusion"],"waves":{"deferred":["Occurrences","Joints","AsBuiltJoints"],"wave_four":["MoveFeatures","OffsetFeatures","ReplaceFaceFeatures","ScaleFeatures","SplitBodyFeatures","ThreadFeatures","TrimFeatures"],"wave_one":["ConstructionPlanes","ConstructionAxes","ConstructionPoints","SketchArcs","RevolveFeatures","HoleFeatures","FilletFeatures","ChamferFeatures"],"wave_three":["LoftFeatures","SweepFeatures","ShellFeatures","DraftFeatures","PatchFeatures"],"wave_two":["CombineFeatures","MirrorFeatures","RectangularPatternFeatures","CircularPatternFeatures"]}}')

PLANE_ALIASES = _json.loads('{"xy":"xYConstructionPlane","xz":"xZConstructionPlane","yz":"yZConstructionPlane"}')

SKETCH_TARGETS = _json.loads('{"point":["sketchPoints"]}')

SKETCH_COLLECTIONS = _json.loads('{"arc":"sketchArcs","arc3p":"sketchArcs","circle":"sketchCircles","circle2p":"sketchCircles","circle3p":"sketchCircles","ellipse":"sketchEllipses","line":"sketchLines","point":"sketchPoints","rect":"sketchLines","rect3p":"sketchLines","rect_center":"sketchLines","spline":"sketchFittedSplines"}')

SKETCH_METHODS = _json.loads('{"arc":"addByCenterStartSweep","arc3p":"addByThreePoints","circle":"addByCenterRadius","circle2p":"addByTwoPoints","circle3p":"addByThreePoints","ellipse":"add","line":"addByTwoPoints","point":"add","rect":"addTwoPointRectangle","rect3p":"addThreePointRectangle","rect_center":"addCenterPointRectangle","spline":"add"}')

SKETCH_COERCERS = _json.loads('{"arc":["point","point","identity"],"arc3p":["point","point","point"],"circle":["point","length_cm"],"circle2p":["point","point"],"circle3p":["point","point","point"],"ellipse":["point","point","point"],"line":["point","point"],"point":["point"],"rect":["point","point"],"rect3p":["point","point","point"],"rect_center":["point","point"],"spline":["point_collection"]}')

SKETCH_LENGTH_UNITS_CM = _json.loads('{"cm":1.0,"in":2.54,"inch":2.54,"inches":2.54,"m":100.0,"mm":0.1}')

SKETCH_LENGTH_PATTERN = _json.loads('"^\\\\s*(?P<value>[+-]?(?:\\\\d+(?:\\\\.\\\\d*)?|\\\\.\\\\d+))\\\\s*(?P<unit>inches|inch|cm|in|mm|m)\\\\s*$"')

TEXT_POLICY = _json.loads('{"builder_input":"createInput2","builder_terminal":"add","collection_attr":"sketchTexts","family_id":"adsk.fusion.SketchTexts","horizontal_alignments":{"center":"CenterHorizontalAlignment","left":"LeftHorizontalAlignment","right":"RightHorizontalAlignment"},"input_attrs":{"font_name":"fontName","horizontal_flip":"isHorizontalFlip","vertical_flip":"isVerticalFlip"},"input_methods":{"along_path":"setAsAlongPath","fit_path":"setAsFitOnPath","multiline":"setAsMultiLine"},"vertical_alignments":{"bottom":"BottomVerticalAlignment","center":"MiddleVerticalAlignment","middle":"MiddleVerticalAlignment","top":"TopVerticalAlignment"}}')

EXTRUDE_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","compact_method":"extrude","extent_types":{"distance":"DistanceExtentDefinition","through_all":"ThroughAllExtentDefinition"},"family_id":"adsk.fusion.ExtrudeFeatures","input_attrs":{"participant_bodies":"participantBodies","solid":"isSolid"},"input_methods":{"one_side":"setOneSideExtent","symmetric":"setSymmetricExtent"},"simple_method":"addSimple"}')

CONSTRUCTION_POLICY = _json.loads('{"axis":{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.ConstructionAxes","methods":{"between_planes":"setByTwoPlanes","between_points":"setByTwoPoints","circular_face":"setByCircularFace","edge":"setByEdge","normal":"setByNormalToFaceAtPoint","perpendicular":"setByPerpendicularAtPoint"}},"plane":{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.ConstructionPlanes","methods":{"angle":"setByAngle","between":"setByTwoPlanes","edges":"setByTwoEdges","offset":"setByOffset","on_path":"setByDistanceOnPath","tangent":"setByTangent","tangent_at":"setByTangentAtPoint","three_points":"setByThreePoints"}},"point":{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.ConstructionPoints","methods":{"at":"setByPoint","center":"setByCenter","edge_plane":"setByEdgePlane","edges":"setByTwoEdges","planes":"setByThreePlanes"}}}')

REVOLVE_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.RevolveFeatures","input_methods":{"angle":"setAngleExtent"}}')

HOLE_POLICY = _json.loads('{"builder_terminal":"add","create_methods":{"counterbore":"createCounterboreInput","countersink":"createCountersinkInput","simple":"createSimpleInput"},"edge_positions":{"end":"end","mid":"mid","start":"start"},"family_id":"adsk.fusion.HoleFeatures","input_methods":{"at_center":"setPositionAtCenter","by_offsets":"setPositionByPlaneAndOffsets","by_points":"setPositionBySketchPoints","depth":"setDistanceExtent","on_edge":"setPositionOnEdge"}}')

FILLET_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.FilletFeatures","input_attrs":{"edge_sets":"edgeSetInputs"},"input_methods":{"constant_radius":"addConstantRadiusEdgeSet"}}')

CHAMFER_POLICY = _json.loads('{"builder_input":"createInput2","builder_terminal":"add","family_id":"adsk.fusion.ChamferFeatures","input_attrs":{"edge_sets":"chamferEdgeSets"},"input_methods":{"equal_distance":"addEqualDistanceChamferEdgeSet"}}')

COMBINE_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.CombineFeatures","input_attrs":{"keep_tools":"isKeepToolBodies","new_component":"isNewComponent","operation":"operation"}}')

MIRROR_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.MirrorFeatures"}')

CIRCULAR_PATTERN_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.CircularPatternFeatures","input_attrs":{"quantity":"quantity","symmetric":"isSymmetric","total_angle":"totalAngle"}}')

RECTANGULAR_PATTERN_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","distance_types":{"extent":"extent","spacing":"spacing"},"family_id":"adsk.fusion.RectangularPatternFeatures","input_attrs":{"distance_type":"patternDistanceType","symmetric_one":"isSymmetricInDirectionOne","symmetric_two":"isSymmetricInDirectionTwo"},"input_methods":{"direction_two":"setDirectionTwo"}}')

SWEEP_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.SweepFeatures","input_attrs":{"direction_flipped":"isDirectionFlipped","guide_rail":"guideRail","profile_scaling":"profileScaling","taper_angle":"taperAngle","twist_angle":"twistAngle"}}')

LOFT_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.LoftFeatures","input_attrs":{"closed":"isClosed","end_alignment":"endLoftEdgeAlignment","merge_tangent_edges":"isTangentEdgesMerged","rails":"centerLineOrRails","sections":"loftSections","solid":"isSolid","start_alignment":"startLoftEdgeAlignment"},"input_methods":{"add_section":"add"}}')

PATCH_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.PatchFeatures"}')

SHELL_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.ShellFeatures","input_attrs":{"inside_thickness":"insideThickness","outside_thickness":"outsideThickness","shell_type":"shellType"}}')

DRAFT_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.DraftFeatures","input_attrs":{"direction_flipped":"isDirectionFlipped"},"input_methods":{"single_angle":"setSingleAngle"}}')

MOVE_POLICY = _json.loads('{"builder_input":"createInput2","builder_terminal":"add","family_id":"adsk.fusion.MoveFeatures","input_methods":{"free_move":"defineAsFreeMove"}}')

OFFSET_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.OffsetFeatures"}')

REPLACE_FACE_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.ReplaceFaceFeatures"}')

SCALE_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.ScaleFeatures","input_methods":{"non_uniform":"setToNonUniform"}}')

SPLIT_BODY_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.SplitBodyFeatures"}')

THREAD_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.ThreadFeatures","input_attrs":{"full_length":"isFullLength","length":"threadLength"}}')

TRIM_POLICY = _json.loads('{"builder_input":"createInput","builder_terminal":"add","family_id":"adsk.fusion.TrimFeatures","input_attrs":{"cells":"bRepCells"},"input_methods":{"item":"item"}}')
