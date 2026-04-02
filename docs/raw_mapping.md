# Raw Mapping

Generated compact-to-Autodesk mapping table.

| Compact Surface | Raw Autodesk Mapping |
| --- | --- |
| `app` | `adsk.core.Application.get` |
| `ui` | `adsk.core.Application.userInterface` |
| `ctx` | `adsk.core.Application active context` |
| `new_design` | `adsk.core.Documents.add(FusionDesignDocumentType)` |
| `new_or_active_design` | `adsk.core.Application.activeProduct or adsk.core.Documents.add(FusionDesignDocumentType)` |
| `p` | `adsk.core.Point3D.create` |
| `vec` | `adsk.core.Vector3D.create` |
| `oc` | `adsk.core.ObjectCollection.create` |
| `u` | `adsk.core.ValueInput.createByString via fs.v` |
| `v` | `adsk.core.ValueInput.createByString/createByReal/createByBoolean/createByObject` |
| `op` | `adsk.fusion.FeatureOperations` |
| `dir` | `adsk.fusion.ExtentDirections` |
| `DesignRef.root` | `adsk.fusion.Design.rootComponent` |
| `ComponentRef.sketch` | `adsk.fusion.Sketches.add` |
| `ComponentRef.extrude` | `adsk.fusion.ExtrudeFeatures.addSimple or createInput + add` |
| `SketchRef.line` | `adsk.fusion.SketchLines.addByTwoPoints` |
| `SketchRef.point` | `adsk.fusion.SketchPoints.add` |
| `SketchRef.circle` | `adsk.fusion.SketchCircles.addByCenterRadius` |
| `SketchRef.arc` | `adsk.fusion.SketchArcs.addByCenterStartSweep` |
| `SketchRef.arc3p` | `adsk.fusion.SketchArcs.addByThreePoints` |
| `SketchRef.ellipse` | `adsk.fusion.SketchEllipses.add` |
| `SketchRef.spline` | `adsk.fusion.SketchFittedSplines.add` |
| `SketchRef.rect` | `adsk.fusion.SketchLines.addTwoPointRectangle` |
| `SketchRef.rect_center` | `adsk.fusion.SketchLines.addCenterPointRectangle` |
| `SketchRef.rect3p` | `adsk.fusion.SketchLines.addThreePointRectangle` |
| `SketchRef.circle2p` | `adsk.fusion.SketchCircles.addByTwoPoints` |
| `SketchRef.circle3p` | `adsk.fusion.SketchCircles.addByThreePoints` |
| `SketchRef.text` | `adsk.fusion.SketchTexts.createInput2 + SketchTextInput.setAsMultiLine + SketchTexts.add` |
| `SketchRef.text_path` | `adsk.fusion.SketchTexts.createInput2 + SketchTextInput.setAsAlongPath + SketchTexts.add` |
| `SketchRef.text_fit` | `adsk.fusion.SketchTexts.createInput2 + SketchTextInput.setAsFitOnPath + SketchTexts.add` |
| `SketchRef.profile` | `adsk.fusion.Sketch.profiles.item` |
| `SketchRef.profiles` | `adsk.fusion.Sketch.profiles` |
| `ExtrudeBuilder.one_side` | `adsk.fusion.ExtrudeFeatureInput.setOneSideExtent` |
| `ExtrudeBuilder.symmetric` | `adsk.fusion.ExtrudeFeatureInput.setSymmetricExtent` |
| `ExtrudeBuilder.solid` | `adsk.fusion.ExtrudeFeatureInput.isSolid` |
| `ExtrudeBuilder.surface` | `adsk.fusion.ExtrudeFeatureInput.isSolid = False` |
| `ExtrudeBuilder.taper` | `taper angle argument on Autodesk extent setters` |
| `ExtrudeBuilder.participant_bodies` | `adsk.fusion.ExtrudeFeatureInput.participantBodies` |
| `ExtrudeBuilder.build` | `adsk.fusion.ExtrudeFeatures.add` |
| `ComponentRef.revolve` | `adsk.fusion.RevolveFeatures.createInput + setAngleExtent + add` |
| `ComponentRef.sweep` | `adsk.fusion.Features.createPath + adsk.fusion.SweepFeatures.createInput + add` |
| `ComponentRef.loft` | `adsk.fusion.LoftFeatures.createInput + LoftSections.add + add` |
| `ComponentRef.patch` | `adsk.fusion.PatchFeatures.createInput + add` |
| `ComponentRef.shell` | `adsk.fusion.ShellFeatures.createInput + add` |
| `ComponentRef.draft` | `adsk.fusion.DraftFeatures.createInput + setSingleAngle + add` |
| `ComponentRef.move` | `adsk.fusion.MoveFeatures.createInput2 + defineAsFreeMove + add` |
| `ComponentRef.offset` | `adsk.fusion.OffsetFeatures.createInput + add` |
| `ComponentRef.replace_face` | `adsk.fusion.ReplaceFaceFeatures.createInput + add` |
| `ComponentRef.scale` | `adsk.fusion.ScaleFeatures.createInput + setToNonUniform + add` |
| `ComponentRef.split_body` | `adsk.fusion.SplitBodyFeatures.createInput + add` |
| `ComponentRef.thread` | `adsk.fusion.ThreadFeatures.threadDataQuery + ThreadInfo.create + createInput + add` |
| `ComponentRef.trim` | `adsk.fusion.TrimFeatures.createInput + TrimFeatureInput.bRepCells + add` |
