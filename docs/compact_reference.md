# Compact Reference

Generated from FusionSparse metadata and compact reference rules.

## Public Helpers

### `app`

- Raw Autodesk mapping: `adsk.core.Application.get`
- Implementation: `fusion_sparse.compact.app.app`
- Arguments: `none`
- Example:

```python
app = fs.app()
```

- Escape hatch: Returns a wrapped Autodesk Application. Use `.raw` for the original object.

### `ui`

- Raw Autodesk mapping: `adsk.core.Application.userInterface`
- Implementation: `fusion_sparse.compact.app.ui`
- Arguments: `none`
- Example:

```python
ui = fs.ui()
```

- Escape hatch: Returns a wrapped Autodesk UserInterface. Use `.raw` for the original object.

### `ctx`

- Raw Autodesk mapping: `adsk.core.Application active context`
- Implementation: `fusion_sparse.compact.app.ctx`
- Arguments: `strict=True`
- Example:

```python
context = fs.ctx()
root = context.root
```

- Escape hatch: The fields on the returned context are wrapped Autodesk objects; each field supports `.raw`.

### `new_design`

- Raw Autodesk mapping: `adsk.core.Documents.add(FusionDesignDocumentType)`
- Implementation: `fusion_sparse.compact.app.new_design`
- Arguments: `visible=True`, `options=None`
- Example:

```python
design = fs.new_design()
```

- Escape hatch: Returns a wrapped Design. Use `.raw` to drop to Autodesk APIs directly.

### `new_or_active_design`

- Raw Autodesk mapping: `adsk.core.Application.activeProduct or adsk.core.Documents.add(FusionDesignDocumentType)`
- Implementation: `fusion_sparse.compact.app.new_or_active_design`
- Arguments: `none`
- Example:

```python
design = fs.new_or_active_design()
```

- Escape hatch: Returns a wrapped Design. Use `.raw` to drop to Autodesk APIs directly.

### `p`

- Raw Autodesk mapping: `adsk.core.Point3D.create`
- Implementation: `fusion_sparse.runtime.geom.p`
- Arguments: `x`, `y=None`, `z=0`
- Example:

```python
center = fs.p(0, 0, 0)
```

- Escape hatch: Pass an Autodesk Point3D directly to keep it unchanged.

### `vec`

- Raw Autodesk mapping: `adsk.core.Vector3D.create`
- Implementation: `fusion_sparse.runtime.geom.vec`
- Arguments: `x`, `y=None`, `z=0`
- Example:

```python
axis = fs.vec(0, 0, 1)
```

- Escape hatch: Pass an Autodesk Vector3D directly to keep it unchanged.

### `oc`

- Raw Autodesk mapping: `adsk.core.ObjectCollection.create`
- Implementation: `fusion_sparse.runtime.geom.oc`
- Arguments: `*items`
- Example:

```python
bodies = fs.oc(body_a, body_b)
```

- Escape hatch: Wrapped FusionSparse refs are unwrapped automatically when inserted.

### `u`

- Raw Autodesk mapping: `adsk.core.ValueInput.createByString via fs.v`
- Implementation: `fusion_sparse.runtime.values.u`
- Arguments: `none`
- Example:

```python
depth = fs.u.mm(10)
```

- Escape hatch: `u` only builds expressions; call `v(...)` to create a ValueInput.

### `v`

- Raw Autodesk mapping: `adsk.core.ValueInput.createByString/createByReal/createByBoolean/createByObject`
- Implementation: `fusion_sparse.runtime.values.v`
- Arguments: `value`
- Example:

```python
depth = fs.v("10 mm")
```

- Escape hatch: Existing Autodesk ValueInput objects pass through unchanged.

### `op`

- Raw Autodesk mapping: `adsk.fusion.FeatureOperations`
- Implementation: `fusion_sparse.runtime.enums.op`
- Arguments: `none`
- Example:

```python
operation = fs.op.new_body
```

- Escape hatch: Use the Autodesk enum directly if you need a member that does not have a compact alias.

### `dir`

- Raw Autodesk mapping: `adsk.fusion.ExtentDirections`
- Implementation: `fusion_sparse.runtime.enums.dir`
- Arguments: `none`
- Example:

```python
direction = fs.dir.symmetric
```

- Escape hatch: Use the Autodesk enum directly if you need a member that does not have a compact alias.

## Compact Methods

### `DesignRef.root`

- Raw Autodesk mapping: `adsk.fusion.Design.rootComponent`
- Arguments: `none`
- Example:

```python
root = fs.new_design().root
```

- Escape hatch: The returned Component wrapper exposes `.raw` for the Autodesk Component.

### `ComponentRef.sketch`

- Raw Autodesk mapping: `adsk.fusion.Sketches.add`
- Arguments: `plane`
- Example:

```python
sk = root.sketch("xy")
```

- Escape hatch: Pass a raw construction plane or planar face instead of an alias to bypass plane lookup.

### `ComponentRef.extrude`

- Raw Autodesk mapping: `adsk.fusion.ExtrudeFeatures.addSimple or createInput + add`
- Arguments: `profile`, `distance=None`, `op="new_body"`
- Example:

```python
ext = root.extrude(sk.profile(), "10 mm")
```

- Escape hatch: Use `root.raw.features.extrudeFeatures` for direct Autodesk feature creation.

### `SketchRef.line`

- Raw Autodesk mapping: `adsk.fusion.SketchLines.addByTwoPoints`
- Arguments: `a`, `b`
- Example:

```python
sk.line((0, 0), (5, 0))
```

- Escape hatch: Points are passed through unchanged if they are already Autodesk sketch points or Point3D values.

### `SketchRef.point`

- Raw Autodesk mapping: `adsk.fusion.SketchPoints.add`
- Arguments: `at`
- Example:

```python
pt = sk.point((5, 4))
```

- Escape hatch: Pass a raw Autodesk Point3D or SketchPoint directly to bypass coordinate coercion.

### `SketchRef.circle`

- Raw Autodesk mapping: `adsk.fusion.SketchCircles.addByCenterRadius`
- Arguments: `center`, `r`
- Example:

```python
sk.circle((0, 0), "20 mm")
```

- Escape hatch: Radius strings are parsed into Fusion internal length units; pass a numeric radius directly to skip parsing.

### `SketchRef.arc`

- Raw Autodesk mapping: `adsk.fusion.SketchArcs.addByCenterStartSweep`
- Arguments: `center`, `start`, `sweep`
- Example:

```python
sk.arc((0, 0), (5, 0), "90 deg")
```

- Escape hatch: Pass Autodesk points directly if you already have them.

### `SketchRef.arc3p`

- Raw Autodesk mapping: `adsk.fusion.SketchArcs.addByThreePoints`
- Arguments: `a`, `b`, `c`
- Example:

```python
sk.arc3p((-10, 0), (-5, 3), (0, 0))
```

- Escape hatch: Pass Autodesk points directly if you already have them.

### `SketchRef.ellipse`

- Raw Autodesk mapping: `adsk.fusion.SketchEllipses.add`
- Arguments: `center`, `major`, `through`
- Example:

```python
sk.ellipse((0, 0), (10, 0), (5, 4))
```

- Escape hatch: Pass Autodesk points directly if you already have them.

### `SketchRef.spline`

- Raw Autodesk mapping: `adsk.fusion.SketchFittedSplines.add`
- Arguments: `*fit_points`
- Example:

```python
sk.spline((0, 0), (5, 1), (7, 6), (0, 1))
```

- Escape hatch: Pass an Autodesk ObjectCollection or any iterable of point-like values.

### `SketchRef.rect`

- Raw Autodesk mapping: `adsk.fusion.SketchLines.addTwoPointRectangle`
- Arguments: `a`, `b`
- Example:

```python
sk.rect((0, 0), (10, 5))
```

- Escape hatch: Pass Autodesk points directly if you already have them.

### `SketchRef.rect_center`

- Raw Autodesk mapping: `adsk.fusion.SketchLines.addCenterPointRectangle`
- Arguments: `center`, `corner`
- Example:

```python
sk.rect_center((5, 5), (25, 25))
```

- Escape hatch: Pass Autodesk points directly if you already have them.

### `SketchRef.rect3p`

- Raw Autodesk mapping: `adsk.fusion.SketchLines.addThreePointRectangle`
- Arguments: `a`, `b`, `c`
- Example:

```python
sk.rect3p((0, 0), (5, 15), (-5, -6))
```

- Escape hatch: Pass Autodesk points directly if you already have them.

### `SketchRef.circle2p`

- Raw Autodesk mapping: `adsk.fusion.SketchCircles.addByTwoPoints`
- Arguments: `a`, `b`
- Example:

```python
sk.circle2p((1, 1), (8, 8))
```

- Escape hatch: Pass Autodesk points directly if you already have them.

### `SketchRef.circle3p`

- Raw Autodesk mapping: `adsk.fusion.SketchCircles.addByThreePoints`
- Arguments: `a`, `b`, `c`
- Example:

```python
sk.circle3p((0, 0), (5, 5), (9, 14))
```

- Escape hatch: Pass Autodesk points directly if you already have them.

### `SketchRef.text`

- Raw Autodesk mapping: `adsk.fusion.SketchTexts.createInput2 + SketchTextInput.setAsMultiLine + SketchTexts.add`
- Arguments: `text`, `corner`, `diagonal`, `height`
- Example:

```python
sk.text("Autodesk", (0, 0), (10, 5), 0.5)
```

- Escape hatch: Use `sk.raw.sketchTexts` directly for advanced text-input options not exposed compactly.

### `SketchRef.text_path`

- Raw Autodesk mapping: `adsk.fusion.SketchTexts.createInput2 + SketchTextInput.setAsAlongPath + SketchTexts.add`
- Arguments: `text`, `path`, `height`
- Example:

```python
sk.text_path("Autodesk", arc, 0.5)
```

- Escape hatch: Use `sk.raw.sketchTexts` directly for advanced text-input options not exposed compactly.

### `SketchRef.text_fit`

- Raw Autodesk mapping: `adsk.fusion.SketchTexts.createInput2 + SketchTextInput.setAsFitOnPath + SketchTexts.add`
- Arguments: `text`, `path`, `height`
- Example:

```python
sk.text_fit("Autodesk", arc, 0.5)
```

- Escape hatch: Use `sk.raw.sketchTexts` directly for advanced text-input options not exposed compactly.

### `SketchRef.profile`

- Raw Autodesk mapping: `adsk.fusion.Sketch.profiles.item`
- Arguments: `i=0`
- Example:

```python
profile = sk.profile()
```

- Escape hatch: Use `sk.raw.profiles` for direct access to the Autodesk Profiles collection.

### `SketchRef.profiles`

- Raw Autodesk mapping: `adsk.fusion.Sketch.profiles`
- Arguments: `none`
- Example:

```python
profiles = sk.profiles()
```

- Escape hatch: Use `sk.raw.profiles` for direct access to the Autodesk Profiles collection.

### `ExtrudeBuilder.one_side`

- Raw Autodesk mapping: `adsk.fusion.ExtrudeFeatureInput.setOneSideExtent`
- Arguments: `distance`, `direction="positive"`
- Example:

```python
ext = root.extrude(sk.profile()).one_side("5 mm")
```

- Escape hatch: Use `builder.raw` to call Autodesk extent setters directly.

### `ExtrudeBuilder.symmetric`

- Raw Autodesk mapping: `adsk.fusion.ExtrudeFeatureInput.setSymmetricExtent`
- Arguments: `distance`
- Example:

```python
ext = root.extrude(sk.profile()).symmetric("10 mm")
```

- Escape hatch: Use `builder.raw` to call Autodesk extent setters directly.

### `ExtrudeBuilder.solid`

- Raw Autodesk mapping: `adsk.fusion.ExtrudeFeatureInput.isSolid`
- Arguments: `flag=True`
- Example:

```python
ext = root.extrude(sk.profile()).solid()
```

- Escape hatch: Use `builder.raw.isSolid` for direct Autodesk access.

### `ExtrudeBuilder.surface`

- Raw Autodesk mapping: `adsk.fusion.ExtrudeFeatureInput.isSolid = False`
- Arguments: `none`
- Example:

```python
ext = root.extrude(sk.profile()).surface()
```

- Escape hatch: Use `builder.raw.isSolid` for direct Autodesk access.

### `ExtrudeBuilder.taper`

- Raw Autodesk mapping: `taper angle argument on Autodesk extent setters`
- Arguments: `angle`
- Example:

```python
ext = root.extrude(sk.profile()).one_side("5 mm").taper("2 deg")
```

- Escape hatch: Use `builder.raw` and Autodesk extent setters directly for advanced taper control.

### `ExtrudeBuilder.participant_bodies`

- Raw Autodesk mapping: `adsk.fusion.ExtrudeFeatureInput.participantBodies`
- Arguments: `*bodies`
- Example:

```python
ext = root.extrude(sk.profile()).participant_bodies(body)
```

- Escape hatch: Use `builder.raw.participantBodies` for direct Autodesk access.

### `ExtrudeBuilder.build`

- Raw Autodesk mapping: `adsk.fusion.ExtrudeFeatures.add`
- Arguments: `none`
- Example:

```python
ext = root.extrude(sk.profile()).one_side("5 mm").build()
```

- Escape hatch: Call `builder.raw` with Autodesk feature collections directly if you need unsupported setup.

### `ComponentRef.revolve`

- Raw Autodesk mapping: `adsk.fusion.RevolveFeatures.createInput + setAngleExtent + add`
- Arguments: `profile`, `axis`, `angle=None`, `op="new_body"`
- Example:

```python
rev = root.revolve(sk.profile(), axis, "180 deg")
```

- Escape hatch: Use `root.raw.features.revolveFeatures` for direct Autodesk revolve configuration.

### `ComponentRef.sweep`

- Raw Autodesk mapping: `adsk.fusion.Features.createPath + adsk.fusion.SweepFeatures.createInput + add`
- Arguments: `profile`, `path`, `op="new_body"`, `guide=None`, `taper=None`, `twist=None`, `scale=None`, `flip=False`
- Example:

```python
swp = root.sweep(sk.profile(), path, taper="5 deg", twist="10 deg")
```

- Escape hatch: Use `root.raw.features.sweepFeatures` and raw Path objects for unsupported sweep options.

### `ComponentRef.loft`

- Raw Autodesk mapping: `adsk.fusion.LoftFeatures.createInput + LoftSections.add + add`
- Arguments: `*sections`, `op="new_body"`, `solid=False`, `closed=False`, `merge_tangent_edges=True`, `start_alignment="free"`, `end_alignment="free"`, `rails=None`
- Example:

```python
loft = root.loft(profile0, profile1, profile2)
```

- Escape hatch: Use `root.raw.features.loftFeatures` when you need unsupported section or rail behavior.

### `ComponentRef.patch`

- Raw Autodesk mapping: `adsk.fusion.PatchFeatures.createInput + add`
- Arguments: `boundary`, `op="new_body"`
- Example:

```python
patch = root.patch(boundary_edge)
```

- Escape hatch: Use `root.raw.features.patchFeatures` for direct Autodesk patch setup.

### `ComponentRef.shell`

- Raw Autodesk mapping: `adsk.fusion.ShellFeatures.createInput + add`
- Arguments: `entities`, `inside=None`, `outside=None`, `tangent_chain=True`, `shell_type="sharp"`
- Example:

```python
shell = root.shell(face, inside=0.5, tangent_chain=False)
```

- Escape hatch: Use `root.raw.features.shellFeatures` for Autodesk shell options not exposed compactly.

### `ComponentRef.draft`

- Raw Autodesk mapping: `adsk.fusion.DraftFeatures.createInput + setSingleAngle + add`
- Arguments: `faces`, `plane`, `angle`, `tangent_chain=True`, `symmetric=True`, `flip=False`
- Example:

```python
draft = root.draft([side_face], neutral_face, "10 deg")
```

- Escape hatch: Use `root.raw.features.draftFeatures` for Autodesk draft setups beyond the single-angle path.

### `ComponentRef.move`

- Raw Autodesk mapping: `adsk.fusion.MoveFeatures.createInput2 + defineAsFreeMove + add`
- Arguments: `entities`, `translation=None`, `transform=None`
- Example:

```python
moved = root.move(body, translation=(2, 1, 0))
```

- Escape hatch: Pass a raw `Matrix3D` as `transform=` to bypass the compact translation helper.

### `ComponentRef.offset`

- Raw Autodesk mapping: `adsk.fusion.OffsetFeatures.createInput + add`
- Arguments: `entities`, `distance`, `op="new_body"`, `chain=True`
- Example:

```python
offset = root.offset(face, "2 mm")
```

- Escape hatch: Use `root.raw.features.offsetFeatures` if you need Autodesk-only offset options.

### `ComponentRef.replace_face`

- Raw Autodesk mapping: `adsk.fusion.ReplaceFaceFeatures.createInput + add`
- Arguments: `source_faces`, `target`, `tangent_chain=False`
- Example:

```python
replaced = root.replace_face(end_face, offset_plane)
```

- Escape hatch: Use `root.raw.features.replaceFaceFeatures` for Autodesk replace-face options not surfaced compactly.

### `ComponentRef.scale`

- Raw Autodesk mapping: `adsk.fusion.ScaleFeatures.createInput + setToNonUniform + add`
- Arguments: `entities`, `origin`, `factor`, `xyz=None`
- Example:

```python
scaled = root.scale(body, (0, 0, 0), 1, xyz=(1.5, 0.75, 0.5))
```

- Escape hatch: Pass a raw Autodesk point for `origin` or use `root.raw.features.scaleFeatures` for advanced scaling behavior.

### `ComponentRef.split_body`

- Raw Autodesk mapping: `adsk.fusion.SplitBodyFeatures.createInput + add`
- Arguments: `bodies`, `tool`, `extend=True`
- Example:

```python
split = root.split_body(body, "xz")
```

- Escape hatch: Use `root.raw.features.splitBodyFeatures` for Autodesk split-body control beyond the direct helper.

### `ComponentRef.thread`

- Raw Autodesk mapping: `adsk.fusion.ThreadFeatures.threadDataQuery + ThreadInfo.create + createInput + add`
- Arguments: `faces`, `internal=False`, `length=None`, `thread_type=None`, `designation=None`, `thread_class=None`
- Example:

```python
thread = root.thread(side_face, length=2.5)
```

- Escape hatch: Use `root.raw.features.threadFeatures` if you need to manage Autodesk thread-query data directly.

### `ComponentRef.trim`

- Raw Autodesk mapping: `adsk.fusion.TrimFeatures.createInput + TrimFeatureInput.bRepCells + add`
- Arguments: `tool`, `cell=0`
- Example:

```python
trimmed = root.trim(surface_body)
```

- Escape hatch: Use `root.raw.features.trimFeatures` if you need to inspect or select Autodesk trim cells manually.
