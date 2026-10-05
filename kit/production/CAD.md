# The mark in CAD

Which kit file to use for logos on parts and drawings. All sizes are in millimeters.

| Job | Fusion | Onshape | FreeCAD | SolidWorks |
|---|---|---|---|---|
| **Emboss or engrave** the mark into a face | Insert → Insert DXF → `kit/production/cut/fusion-space-mark-<size>mm.dxf` onto a sketch plane, then Emboss / Extrude | Sketch → Import DXF (same file), then Extrude add/remove | Import the DXF (Draft), Part → Extrude | Sketch → Insert DXF (same file), Extruded Boss/Cut |
| **Decal** (color image on a face, for renders) | Insert → Decal → `kit/logo/png/fusion-space-mark-color-1024.png` (transparent) | Insert → Decal (same PNG) | Appearance texture, or skip | Appearances → Decals (same PNG) |
| **Drawing title block** | use `templates/freecad/` as the pattern, or the one-color SVG | Drawing template logo: `kit/logo/svg/fusion-space-horizontal-void.svg` | `templates/freecad/FusionSpace_*.svg` | Sheet format: insert `kit/logo/png/fusion-space-horizontal-void-1000w.png` |

- The DXF is lines and true arcs only (no splines), so every CAD package imports it cleanly. Its feet are trimmed to at least
  0.5 mm; for a smaller logo on a part, check the tool size first (a 0.5 mm foot needs a 0.4 mm or smaller cutter).
- Pick the DXF closest to the size you need and scale in the sketch; the outlines are exact at any scale.
- For two-color prints, model the mark as a separate body (see `kit/3d-print/`).
- `kit/3d-print/` also has STEP solids with the mark as exact curves (lines, arcs, the ellipse, Béziers) in named, colored
  bodies, sketches with exact ARC/ELLIPSE/SPLINE entities (`sketch/`), and a parametric badge for FreeCAD and Fusion (`parametric/`).
