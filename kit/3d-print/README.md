# FusionSpace 3D-print and CAD files (millimetres)

Every model comes as `.stl` (mesh, for slicers) and `.step` (solid, for CAD: Fusion, Onshape, FreeCAD, SolidWorks). In the STEP
files the mark is exact: its lines, circular arcs, the elliptical wing's ellipse and the Von Kármán's Bézier curves, the same
curves as the master SVG (no fitting); the name and the plates are smooth B-splines within 0.002 mm. Each STEP has named,
coloured bodies (base, cones in M orange and O blue, name). Two-colour models also come as `.3mf` with one part per colour
(see *Two colours* below). `sketch/` has outlines to import and extrude or cut; `parametric/` has a badge you can resize in
FreeCAD or Fusion.

Everything is made for a normal FDM printer: **0.4 mm nozzle, 0.2 mm layers** (first layer 0.2 mm), and checked by the build:
no raised stroke under 0.6 mm, no gap under 0.5 mm, cone feet trimmed to 0.6 mm, heights in whole layers,
no supports needed anywhere. Every STL was sliced (PrusaSlicer 2.7, 0.4 mm nozzle, 0.2 mm layers, no supports) without an overhang
or support warning; the two-colour 3MFs slice with their parts on two filaments. Use a slicer with variable-width walls (Arachne: PrusaSlicer 2.6+, OrcaSlicer, Bambu Studio; in
Cura turn on *Print Thin Walls*) so the 0.6 mm feet and the name's thinnest strokes print as one line.

## The models

| File | What | Size (mm) |
|---|---|---|
| `fusion-space-mark-40mm-extruded-3mm`, `-80mm-` | the four cones, 3 mm thick | 40 / 80 tall |
| `fusion-space-badge-50mm` | die-cut base 2.0 mm, cones raised 1.6 mm | 56 × 56 × 3.6 |
| `fusion-space-keychain-40mm` | round tag with a 4.8 mm keyring hole, cones raised 1.2 mm | Ø40 × 3.6 |
| `fusion-space-horizontal-130mm-extruded-2mm` | the horizontal lockup, mark and letters as separate pieces (was 120 mm: its thinnest strokes were 0.56 mm) | 130 wide × 2 |
| `fusion-space-stacked-110mm-extruded-2mm` | the stacked lockup (was 80 mm: its thinnest strokes were 0.46 mm) | 110 wide × 2 |
| `fusion-space-wordmark-120mm-extruded-2mm` | the name alone | 120 wide × 2 |
| `fusion-space-sign-horizontal-150mm` | 3 mm plate, horizontal lockup raised 1.2 mm | 150 × 42 × 4.2 |
| `fusion-space-coaster-95mm` | 4 mm disc, mark raised 0.8 mm | Ø95 × 4.8 |
| `fusion-space-magnet-40mm` | fridge magnet: die-cut base 4.0 mm with a 10.3 × 3.2 mm pocket from the back, cones raised 1.2 mm | 46 × 46 × 5.2 |
| `fusion-space-magnet-40mm-hidden` | the same magnet sealed inside (pause the print to drop it in): no glue, clean back | 46 × 46 × 5.8 |
| `fusion-space-fincan-badge-{38, 54, 75, 98}mm` | a chamfered plaque curved to fit a body tube of that outer diameter, mark raised 0.8 mm | mark 16 / 22 / 30 / 40 |
| `fusion-space-nosecone-badge-20mm`, `-30mm` | thin flexible badge (TPU) that follows a nose cone's double curve | 23 / 33 wide, 1.2 thick |
| `fusion-space-desk-stand-120mm` (`-plaque`, `-foot`) | stacked lockup plaque and a foot that holds it leaning back 15° | 120 × 66 plaque |
| `fusion-space-cable-tag-44mm` | tag for a zip tie (two slots for ties up to 4.0 × 1.4 mm), mark raised 0.6 mm, room to write a label | 44 × 16 × 2.6 |
| `fusion-space-cable-clip-4mm`, `-6mm`, `-8mm` | snap-on clip for that cable diameter (no zip tie needed), the mark engraved on the flag | 26–30 × 12 |
| `fusion-space-stencil-mark-50mm`, `-100mm` | the mark cut out of a 1.2 mm sheet (the cones have no islands, so no bridges) | 76 / 140 square |
| `fusion-space-lithophane-stacked-120mm` | the stacked lockup as a lithophane (STL only); its 10 mm bottom frame fits the desk stand's foot | 120 × 75 × 3.0 |
| `fusion-space-cookie-80mm` (`-cutter`, `-stamp`) | cookie cutter (die-cut outline) and a stamp that presses the cones in; both mirrored, because both are used upside down | cutter 96 × 96 × 14, stamp 84 × 84 × 6 |
| `fusion-space-remove-before-flight-140mm` | remove-before-flight tag in one piece: 2.0 mm red tag with a 5.5 mm hole for a split ring, REMOVE BEFORE FLIGHT raised 0.8 mm in tall condensed capitals, the mark engraved 0.6 mm into the back (the name would be too fine to engrave at this size; to have it made as a woven tag instead: `production/remove-before-flight/`) | 140 × 32 × 2.8 |
| `fusion-space-remove-before-flight-160mm-2part` (`-front`, `-back`) | the same tag in two halves glued back to back, so the back has the full logo raised in white; two 1.75 mm filament pieces as dowels line them up | 160 × 36 × 4.4 |

## Print settings

Defaults for every part: 0.4 mm nozzle, 0.2 mm layers, 3 walls, 4 top and 4 bottom layers, 15 % gyroid infill, no supports,
no brim unless the table says so, printed as exported (the files are already in print orientation, flat side on the bed).
"Colour change at Z" means the first layer of the new colour (PrusaSlicer/Orca: add the colour change on the layer at that height;
Bambu: *Add pause/filament change* on that layer).

| Model | Material | Orientation | Settings | Colour |
|---|---|---|---|---|
| mark 40/80, extruded | PLA | flat | defaults; a 3 mm brim keeps the small wing cones down | one colour |
| badge 50 | PLA | flat (base down) | defaults | colour change at 2.2 mm (Void base, cones in a light colour), or the 3MF |
| keychain 40 | PETG (takes the pull of a key ring) | flat | 4 walls | colour change at 2.6 mm, or the 3MF |
| horizontal 130, stacked 110, name 120 | PLA | flat | 2 walls, 100 % infill (the strokes are walls only); 3 mm brim (the i's dot and the wing cones are small) | one colour; glue onto a sign or a case |
| sign 150 | PLA | flat | defaults | colour change at 3.2 mm, or the 3MF |
| coaster 95 | PETG (PLA softens under a hot mug) | flat | 5 bottom layers | colour change at 4.2 mm, or the 3MF |
| magnet 40 | PLA | flat, pocket on the bed | defaults (the pocket's 0.8 mm roof bridges 10 mm cleanly) | colour change at 4.2 mm, or the 3MF. Press a 10 × 3 mm disc magnet in with a drop of CA glue |
| magnet 40 hidden | PLA | flat | **pause at 3.8 mm** (insert the pause before the 4.0 mm layer), drop the magnet in, resume. Use a brass nozzle: a steel one is pulled toward the magnet | colour change at 4.8 mm |
| fin-can badges | PETG or ASA (sun and motor heat) | **standing on its flat bottom edge**, as exported | 5 mm brim, 4 walls (the 1.6 mm shell is solid walls), 0.2 mm layers; the cones stand 0.8 mm proud of the curve and print without support | one colour, or the 3MF on a multi-material printer; or paint the cones. Glue with epoxy; each fits its tube up to about 3 mm larger in diameter |
| nose-cone badges | TPU 95A | flat | 20–30 mm/s, 100 % infill | one colour (or paint). Glue with contact cement or flexible CA |
| desk stand plaque | PLA | flat | defaults | colour change at 3.2 mm, or the 3MF (the plaque's parts) |
| desk stand foot | PLA | upright, as exported | 15 % infill; the slot is 3.4 mm for the 3.0 mm plaque (0.2 mm each side), 8.2 mm deep | one colour (Void) |
| cable tag | PLA or PETG | flat | defaults | colour change at 2.2 mm, or the 3MF |
| cable clips | PETG (PLA cracks when it snaps) | on its side, as exported (the clip's profile on the bed) | 4 walls, 100 % infill, 3 mm brim | one colour. Fits cables within about 0.5 mm of the size |
| stencils | PLA or PETG | flat | 100 % infill (the 1.2 mm sheet is 6 solid layers) | one colour. Tape it down and spray light coats |
| lithophane | white PLA | upright (rotate it so the 120 mm edge with the 10 mm frame is on the bed) with a 5 mm brim, or flat | 100 % infill, 0.12–0.2 mm layers, slow outer walls | white only. Light it from behind (a window, an LED strip) |
| cookie cutter / stamp | a food-safe PLA or PETG | cutter flange down, stamp face up, as exported | defaults; the cutting wall is 0.8 mm (2 lines) | one colour. Wash by hand; prints are porous, so keep them for dry dough or line them with cling film |
| remove-before-flight tag | red and white PLA or PETG | flat, front up (the back's engraving prints on the bed) | defaults; smooth (textured PEI shows in the engraving) | colour change at 2.2 mm (red tag, white text), or the 3MF |
| remove-before-flight tag, two-part | red and white PLA or PETG | both halves flat, art up, as exported | defaults | colour change at 1.6 mm on both, or the 3MF (both halves, two colours). Push 1.4 mm lengths of 1.75 mm filament into the holes of one half, glue the halves (CA or epoxy), press together; the split ring goes through both |

## Fits and tolerances

| Where | Gap | Why |
|---|---|---|
| magnet pocket | 10.3 × 3.2 mm for a 10 × 3 mm disc | 0.15 mm each side on the diameter, 0.2 mm on the depth: a snug push fit, glue to be sure |
| desk stand slot | 3.4 mm for a 3.0 mm plaque (or the lithophane) | 0.2 mm each side: slides in, held by the 15° lean |
| cookie stamp | 1.0 mm inside the cutter's wall | the stamp drops into the cut cookie |
| cable clip | hole 0.3 mm over the cable, opening 0.8 × the cable | snaps over and holds |

If your printer runs tight or loose, scale only the part with the hole in the slicer (the foot, or the clip), or change the values
in `parametric/`.

## Two colours

Badge, keychain, sign, coaster, magnet, fin-can badges, desk stand and cable tag have a `.3mf` with one object whose parts are the
colours: **base** (Void), **cones, M orange**, **cones, O blue** and **name** (white), as in the two-tone logo on dark. Each part
already has its filament set for a two-colour print: base filament 1, everything raised filament 2. For three colours give
“cones, O blue” filament 3. PrusaSlicer, OrcaSlicer and Bambu Studio read the parts and filaments; other programs see one
coloured mesh. On a one-nozzle printer without a changer, print the STL with a colour change at the height in the table.

## Sketches (`sketch/`)

Closed outlines at 1:1 to import onto a sketch plane and extrude (emboss) or cut (engrave). In the DXF the cones are true LINE,
ARC, ELLIPSE and SPLINE entities (each Bézier as an exact cubic), the name is closed polylines; the SVG has the same curves as
paths (hairline, y down). Feet are trimmed to 0.6 mm at each size.

| Sketch | Sizes (mm) | Smallest to print with a 0.4 mm nozzle |
|---|---|---|
| `fusion-space-mark-<size>mm` | 20, 30, 40, 50, 80, 100 tall | any (raised or cut) |
| `fusion-space-horizontal-<size>mm` | 80, 100, 120, 150, 200 wide | 130 mm (the name's thinnest stroke is 0.0058 × the name's width, 0.0047 × this lockup's) |
| `fusion-space-stacked-<size>mm` | 60, 80, 100, 150 wide | 105 mm |
| `fusion-space-wordmark-<size>mm` | 80, 100, 120, 150, 200 wide | 105 mm |

Smaller sizes are fine for engraving, laser or CNC. For cutting the mark from sheet, `production/cut/` has DXFs from 25 to
300 mm (feet at 0.5 mm, as a laser or water-jet needs).

## Parametric template (`parametric/`)

- `FusionSpace_Badge.FCMacro`: FreeCAD 0.21 or 1.x. *Macro → Macros… → Execute*. It makes a document with a spreadsheet
  **Params** (mark height, margin, plate diameter (follows the mark and the margin unless you type a number), thickness, relief,
  magnet pocket); change a value, recompute (Ctrl+R; after
  reopening the file use Ctrl+Shift+R, recompute all) and the badge follows. The mark is the exact outline (lines, arcs, ellipse, Bézier), scaled from the spreadsheet. Export
  **Badge** (no pocket) or **BadgeMagnet** with *File → Export*.
- `FusionSpace_Badge_Fusion/`: Autodesk Fusion. *Utilities → Add-Ins → Scripts and Add-Ins → +* → *Script or add-in from
  device*, pick the `FusionSpace_Badge_Fusion` **folder** (not the .py inside it), then select it in the list and *Run*. It makes a parametric design driven by user parameters (*Modify → Change Parameters*): the same values. Lines and
  arcs are exact; the elliptical wing and the Von Kármán flanks are splines through the exact curve.

## Notes

- The mark's feet are cut flat where the wall is 0.6 mm (the master is sharper; at 40 mm its feet would be 0.15 mm, too thin
  to print), then the mark is scaled back to its full height, like the DXF.
- Everything here is built by `tools/build/kit_targets.py` (`build_3d`) and `kit_cad.py` from the master geometry; the FDM
  limits are constants in `kit_cad.py` (`MIN_FEATURE`, `MIN_GAP`, `FOOT_MM`, `CLEAR`, `MAGNET`). Without Open CASCADE
  (`pip install cadquery-ocp`) the STEP and 3MF files and the models that need it are skipped.
