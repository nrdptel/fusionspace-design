# FusionSpace: brand system, Rev B

The identity for my aerospace engineering projects, rebuilt in 2026 using only free tools (Inkscape, FreeCAD, GIMP) and open-source fonts. It keeps the original 2023 idea, with the four-star cluster, the soft orange-to-blue gradient and Cascadia Mono, but redraws everything with exact geometry. The old Illustrator and SolidWorks files are kept in `_archive/`.

Open `guide/index.html` in a browser for the full guide.

## The idea

- **Name.** Stars run on nuclear fusion, so the brand is *FusionSpace*.
- **Mark.** Four stars in the original arrangement. Each star is the space left between four touching circles of radius *a*, so the tips are true points. The companion stars are 0.45, 0.40 and 0.32 the size of the main star (exact positions are in `color/fusion-space-tokens.json`).
- **Color.** One soft gradient sweeps left to right across the whole mark, from M-class orange `#FFB56C` through rose and lavender to O-class blue `#9BB0FF`. The end colors come from the Harvard stellar classification.
- **Wordmark.** `FusionSpace`, one word, in Cascadia Mono SemiBold with the same gradient.
- **Projects.** Each project is named after an IAU-approved star, which becomes its code: `FS-VEGA`, then drawings `FS-VEGA-001`, with revisions A, B, C…

## Folder map

| Folder | Contents | Opens in |
|---|---|---|
| `logo/mark` | The four-star mark: `fusion-space-mark` (gradient), `-void` and `-white` (one color), plus `fusion-space-mark-50mm.dxf` with exact arcs for laser/CNC | Inkscape, FreeCAD, CAM |
| `logo/lockup` | Horizontal and stacked lockups, each as `color`, `void` and `white` | Inkscape |
| `logo/wordmark` | Wordmark alone | Inkscape |
| `logo/png` | Transparent PNG exports of all the above | anything |
| `logo/favicon` | `favicon.svg` (main star, for small sizes), `icon.svg` (full cluster), `app-icon.svg` (square tile for iOS/Android), `.ico`, PNGs, `apple-touch-icon.png` | web |
| `color` | `fusion-space.gpl` palette (includes the gradient stops), CSS and JSON tokens | Inkscape, GIMP, code |
| `type/fonts` | Cascadia Mono and Archivo (SIL OFL) | install once |
| `graphics` | Mark construction drawing, gradient strip, spectral bar | Inkscape |
| `templates` | GitHub social card (1280×640), plus FreeCAD TechDraw sheets in ANSI A, ANSI B and A4 | Inkscape, FreeCAD |
| `tools/callsign` | Callsign, the star name tool: `callsign.html` (any browser, phones included) and `callsign.py` (terminal, Python 3.8+), with the IAU star list as JSON and CSV | browser, terminal |
| `guide` | Brand guide | browser |

## Palette

| Role | Name | Hex |
|---|---|---|
| Gradient | M orange 0% · Rose 35% · Lavender 65% · O blue 100% | `#FFB56C` `#F2B3A0` `#C3B3E0` `#9BB0FF` |
| Core | Void · Abyss · Graphite · Slate · Haze · Mist · Paper · White | `#0B0F1C` `#141A2B` `#2A3248` `#566079` `#98A1B8` `#D6DAE4` `#F3F4F7` `#FFFFFF` |
| Signal | Ion (links/UI on light) · Ember (highlights on light) | `#3350D6` `#B34F0C` |
| Spectral | O · B · A · F · G · K · M | `#9BB0FF` `#AABFFF` `#CAD7FF` `#F8F7FF` `#FFF4EA` `#FFD2A1` `#FFB56C` |

## Type

- **Wordmark / display.** Cascadia Mono SemiBold, the same face as the original logo.
- **Text.** Archivo Regular.
- **Technical.** Cascadia Mono Regular, for part numbers, dimensions and title blocks.

## Setup

1. Install every font in `type/fonts`.
2. Copy `color/fusion-space.gpl` to `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/palettes/`, then restart Inkscape.
3. For FreeCAD, open TechDraw → *Insert Page using Template* and pick a file from `templates/freecad`. The title-block fields are editable, and on FreeCAD 1.0+ some fill themselves in (author, date, scale, sheet).
4. The wordmark is outlined in every logo file. Each file also has a hidden, locked "live text" layer for when you want to retype it.

## Rules

- Keep 0.25 H clear space around the logo, where H is the cluster height. The minimum cluster height is 24 px (8 mm). Below 48 px, use the main star on its own.
- The gradient always runs left to right, M orange to O blue. Don't reverse it, recolor it, or add outlines, shadows or glows.
- Don't stretch the cluster or move, add or drop stars.
- The gradient logo is strongest on Void. For single-color production (engraving, laser, vinyl, stamps), use the `void` or `white` files, or the DXF.
- The star tips are true points. Most cutters handle that, but if a vendor needs a minimum feature size, ask them to apply their usual tip radius at production size.
