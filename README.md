<picture>
  <source media="(prefers-color-scheme: dark)" srcset="kit/github/readme-banner-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="kit/github/readme-banner-light.png">
  <img alt="FusionSpace" src="kit/github/readme-banner-dark.png" width="100%">
</picture>

# FusionSpace: brand system, Rev C

Everything I make, under one name. This is the identity for my own projects: software and embedded systems, games, electronics, mechanical and machined parts, and aerospace. I rebuilt it in 2026 using only free tools (Inkscape, FreeCAD, GIMP) and open-source fonts. It keeps the original 2023 idea, a loose cluster of four shapes with the soft orange-to-blue gradient and Cascadia Mono. Rev C turns the four stars into four nose cones and redraws everything with exact geometry.

Open `guide/index.html` in a browser for the full guide.

## The idea

Stars run on nuclear fusion, so the brand is *FusionSpace*.

The mark is four nose cones in a diamond, each a real rocketry profile. Von Kármán is the main cone, at the north; the conical is west, the elliptical east, and a tangent ogive tail south. The profiles follow the standard nose-cone equations. Each is 3.50× as long as its base radius, with a notch 1.00 of the base radius deep. Its feet are cut flat where the wall is 0.05 of the base radius wide. With *r* as the Von Kármán base radius, the others are 0.4 *r* (conical), 0.3 *r* (elliptical) and 0.5 *r* (ogive).

Spacing is measured on a grid leaned 45°. The ogive sits on the Von Kármán axis, with its tip 0.2 *r* below the Von Kármán foot line. The wings' centroids share a line 0.47 *r* below it. The conical sits 0.19 *r* and the elliptical 0.23 *r* out from the Von Kármán feet. The exact values are in `color/fusion-space-tokens.json`.

One gradient sweeps left to right across the whole mark, from M-class orange `#DA7C30` through rose and lavender to O-class blue `#768DF5`. The end colors start from the M- and O-class star colors of the Harvard stellar classification. I deepened them so the whole gradient holds at least 3:1 on white and 6:1 on Void. It's the same gradient on dark and light backgrounds.

The wordmark is `FusionSpace`, one word, in Cascadia Mono SemiBold with the same gradient.

Each project takes a constellation (Lyra, `FS-LYR`). Each of its products takes one of that constellation's IAU-approved stars as its internal name (Vega, `FS-VEGA`). Its drawings are numbered from there (`FS-VEGA-001`), with revisions A, B, C… The name customers see can be the star's or a different one. This repository is project Ara (`FS-ARA`): Callsign's internal name is Cervantes (`FS-CERVANTES`), and the Mark Tuner's is Inquill (`FS-INQUILL`).

## Folder map

| Folder | Contents | Opens in |
|---|---|---|
| `logo/mark` | The four-cone mark: `fusion-space-mark` (gradient), `-void` and `-white` (one color), `-twotone-on-dark` and `-twotone-on-light` (flat two-tone), plus `fusion-space-mark-50mm.dxf` (lines and arcs only) for laser/CNC | Inkscape, FreeCAD, CAM |
| `logo/lockup` | Horizontal and stacked lockups, each as `color`, `twotone-on-dark`, `twotone-on-light`, `void` and `white` | Inkscape |
| `logo/wordmark` | Wordmark alone | Inkscape |
| `logo/png` | Transparent PNG exports of all the above | anything |
| `logo/favicon` | `favicon.svg` (full cluster, framed for 16–48 px), `icon.svg` (full cluster), `app-icon.svg` (square tile for iOS/Android), `.ico`, PNGs, `apple-touch-icon.png` | web |
| `color` | `fusion-space.gpl` palette (includes the gradient stops), CSS and JSON tokens | Inkscape, GIMP, code |
| `type/fonts` | Cascadia Mono and Archivo (SIL OFL) | install once |
| `graphics` | Mark construction drawing, gradient strip, spectral bar | Inkscape |
| `templates` | GitHub social card (1280×640), plus FreeCAD TechDraw sheets in ANSI A, ANSI B and A4 | Inkscape, FreeCAD |
| `tools/callsign` | Callsign, the star name tool: `callsign.html` (any browser, phones included) and `callsign.py` (terminal, Python 3.8+), with the IAU star list as JSON and CSV | browser, terminal |
| `tools/mark-tuner` | `index.html`: tune the mark and both lockups in the browser and export SVGs | browser |
| `product` | The product system: how FusionSpace sites, tools, PWAs, CLIs, iOS, Android, watch, macOS, Windows and Linux apps, flight computers, boards and rockets are designed. Rules (start with `product/README.md`), tokens for every platform, a web stylesheet with a specimen and example screens, icons, phone screens on iOS and Android with Live Activity, widget and Live Update mock-ups and SwiftUI and Compose parts, watch screens, complications and tiles for Apple Watch and Wear OS, device-screen mock-ups, a KiCad board title block, livery sheets, desktop packaging | anything |
| `tools/build` | The scripts that build every file here (`python3 tools/build/build.py`); see `tools/build/README.md` | terminal |
| `guide` | Brand guide | browser |
| `kit` | Asset kit, ready for any project: every logo in every color mode and size; web/app icons; GitHub and social images (dark and light); letterhead, covers, business cards, email signature, slides; boot logos for OLED/TFT displays; KiCad PCB logos; 3D-print files (STL, STEP, two-color 3MF, sketches, a parametric badge); terminal themes and CLI banners; game splash and store art; logo animation; wallpapers; merch and posters; cut files, stickers, engraving and embroidery. Open `kit/index.html` to browse, `kit/README.md` for the list | everything |
| `tools/build/project.py` | Per-project images: `python3 tools/build/project.py --name Vega --tag EMB --desc "..."` makes a project's social preview, README banners, OG image, YouTube thumbnail, title slides, report covers and starter README | terminal |

## Palette

| Role | Name | Hex |
|---|---|---|
| Gradient | M orange 0% · Rose 35% · Lavender 65% · O blue 100% | `#DA7C30` `#D07D7A` `#A188CB` `#768DF5` |
| Core | Void · Abyss · Graphite · Slate · Haze · Mist · Paper · White | `#0B0F1C` `#141A2B` `#2A3248` `#566079` `#98A1B8` `#D6DAE4` `#F3F4F7` `#FFFFFF` |
| Signal | Ion (links/UI on light) · Ember (highlights on light) | `#3350D6` `#B34F0C` |
| Spectral | O · B · A · F · G · K · M | `#768DF5` `#AABFFF` `#CAD7FF` `#F8F7FF` `#FFF4EA` `#FFD2A1` `#DA7C30` |

## Type

The wordmark and display type are Cascadia Mono SemiBold, the same face as the original logo. Text is Archivo Regular. Technical type, for part numbers, dimensions and title blocks, is Cascadia Mono Regular.

## Setup

1. Install every font in `type/fonts`.
2. Copy `color/fusion-space.gpl` to `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/palettes/`, then restart Inkscape.
3. For FreeCAD, open TechDraw → *Insert Page using Template* and pick a file from `templates/freecad`. The title-block fields are editable, and on FreeCAD 1.0+ some fill themselves in (author, date, scale, sheet). The sheets are transparent; with a dark TechDraw page color use the `-dark` ones, and print from the light ones.
4. The wordmark is outlined in every logo file. Each file also has a hidden, locked "live text" layer for when you want to retype it.

## Rules

- Keep 0.25 H clear space around the logo, where H is the cluster height. The minimum cluster height is 24 px (8 mm). Below 24 px, as in favicons, use the favicon files. They're the full cluster, hinted for 16 px, where the two wing cones become small arrows.
- In the horizontal lockup the mark comes before the wordmark and is 1.92× its cap height. The gap is 0.35 × the cap height (0.183 × the mark height). In the stacked lockup the mark sits above the wordmark with a gap of 0.10 H (to the cap line). These are the only approved arrangements; don't put the mark after or below the wordmark.
- The gradient always runs left to right, M orange to O blue. It's the same on dark and light backgrounds. Don't reverse it, recolor it, or add outlines, shadows or glows.
- Where gradients can't be reproduced (spot-color print, vinyl, embroidery), use the flat two-tone versions. The cones are the same on every background: M orange `#DA7C30` (warm) and O blue `#768DF5` (cool). Only the wordmark changes, white on dark and Void on light (`twotone-on-dark`, `twotone-on-light`). Each cone takes the nearer end of the gradient.
- On light backgrounds, a horizontal lockup under 32 px tall uses the one-color Void lockup (`fusion-space-horizontal-void`). At that size the thin gradient details are too faint on light.
- Ion `#3350D6` and Ember `#B34F0C` are text and UI colors on light (links, warnings), not logo colors.
- Don't stretch the cluster, change the 45° lean, or move, add or drop cones.
- The gradient logo works on Void, white and Paper. For single-color production (engraving, laser, vinyl, stamps), use the `void` or `white` files, or the DXF.
- Mind the minimum feature size in cut files. In the master artwork the feet are cut where the wall is 0.05 of each cone's base radius wide. That's only 0.18 mm on the elliptical cone at 50 mm. The DXF trims the feet so every foot is at least 0.5 mm wide, then scales the trimmed outline to exactly 50 mm tall. Nothing else changes. Laser vendors typically need features of about half the material thickness. So for stock thicker than about 1 mm, scale the DXF up or ask the vendor. The cone tips are true points: ask the vendor to apply their usual tip radius.

## License and trademarks

The build scripts and the mark tuner in `tools/` are licensed under the Apache License 2.0 (`tools/LICENSE`). The license covers the code, not the FusionSpace name or logo, including the artwork the code draws.

The code-like files in `product/` are Apache-2.0 too, so any project can copy them in. They're the tokens (`product/tokens/`), `fusionspace.css`, the Tailwind and mdBook themes, the CLI styles, the LVGL styles and the Linux desktop templates. Each file says so in an SPDX line.

The FusionSpace name, the four-cone mark, both lockups and every brand file here are © 2026 Neer Patel, all rights reserved. The brand files are `logo/`, `kit/`, `guide/`, `graphics/`, `color/`, `templates/`, `source/` and the rest of `product/`. They're published to show the work. `TRADEMARKS.md` says what's fine, such as linking to my projects and showing the logo unchanged when you mention them.

Archivo and Cascadia Mono in `type/fonts/` are under the SIL Open Font License, with the license files next to them.

See `LICENSE` for the full terms.
