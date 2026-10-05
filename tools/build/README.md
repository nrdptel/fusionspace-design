# FusionSpace build scripts (Rev C)

These scripts generate every Rev C brand file from a handful of numbers: logos, PNGs, favicons, DXF, construction drawing, tokens, templates, guide and README.

## Files

| File | What it does |
|---|---|
| `geo.py` | The mark geometry. All the parameters live here (see below). It turns each cone into exact SVG path data (lines, circular arcs, one elliptical arc, and cubic Béziers for Von Kármán) and lays out the cluster on the leaned grid. |
| `build.py` | Builds every output file. `build_all()` wipes the output folder and rebuilds it from scratch. |
| `construction.py` | Draws the construction drawing (`graphics/mark-construction.svg`): 1 cone, 2 spacing on the leaned grid, 3 cluster, 4 profiles, 5 feet (detail of the foot cut). The guide embeds the same drawing. |
| `../mark-tuner/index.html` | Interactive tuner. A JavaScript port of `geo.py` and the lockup/icon geometry, for trying values before a rebuild. Keep it in step with `geo.py`. |
| `kit.py` | The asset kit (`<OUT>/kit`): the logo color-mode matrix (SVG, PDF, PNG sizes), web/app icons, GitHub and social images, documents, production files, `kit/README.md` and the guide's Kit sheet. `build_all()` runs it. |
| `kit_github.py` | GitHub extras for the kit: profile README, labels, badges, how-to, and the example project. |
| `kit_targets.py` | Discipline targets: embedded boot logos (C headers), KiCad footprints, 3D prints (`build_3d()`: every model in `kit/3d-print/`, its STL, STEP, 3MF, preview and print settings in the folder's README; sketches at `SKETCH_SIZES`; fin-can tube sizes in `FINCAN`; desk stand in `STAND`), terminal themes and CLI banners (`braille()`: the whole piece, name included, as braille text art; `term_art()` cuts the feet at one dot for it), game art, logo animation (needs ffmpeg), wallpapers, merch, posters. |
| `kit_review.py` | A sign-off page, `_build/rev-c/review.html` (not committed; also runs on its own, `python3 tools/build/kit_review.py`, from the last build's manifest): every output grouped into items (one piece of artwork in all its formats) with Keep / Change / Remove, notes, export/import, audit flags (placeholders, PNG sizes vs file names, SVG/JSON parse) and a per-item content hash so changed items come back for a re-check. Office and DXF previews go in `_build/rev-c/review-previews/` (needs LibreOffice + pdftoppm; skipped otherwise). |
| `kit_review.py` scope | `REPS`, `COVER`, `CORE` in `kit_review.py` decide which items the review page shows under Focus (one representative per design, with the items it covers) and which are Covered (settled, copies, text). |
| `kit_site.py` | `kit/web/site/`: drop-in Rev C files for fusionspace.co (Next.js file names), one name constant (`NAME`, FusionSpace, one word; the build stops on a space) and the brand link preview. |
| `kit_picker.py` | `tools/star-name-picker/` from `source/star-name-picker/`: puts the current horizontal lockup in the header and loads Cascadia Mono and Archivo from `type/fonts/`. |
| `kit_apps.py` | `kit/apps/`: iOS (1024 and Icon Composer layers), macOS, Android adaptive icon layers, Google Play icon and feature graphic. |
| `kit_docs.py` | `kit/software/docs-theme/`: MkDocs Material and Docusaurus themes, with a drawn preview. |
| `kit_decals.py` | `kit/production/rocket-decals/`: A4 rocket decal sheets (print-and-cut dark/light, one-color vinyl). Sizes in `DECALS`. |
| `kit_cad.py` | Solids and files for `kit/3d-print/` (Open CASCADE via `pip install cadquery-ocp`): `Outline` (the cones as exact curves from `geo.cone_segments`: lines, circular arcs, the ellipse, cubic Béziers) and `mark_outlines()`; prisms, booleans, `mesh_of()` (BRepMesh, welded, watertight); STEP with named, colored bodies (`write_step_bodies`, XCAF) where the mark is exact and other outlines are B-splines between corners within `STEP_TOL` 0.002 mm; two-color 3MF (`write_3mf`: one object, one part per color, extruders set for PrusaSlicer/Orca/Bambu); a small z-buffer renderer for previews; the FDM rules (`MIN_FEATURE` 0.6, `MIN_GAP` 0.5, `FOOT_MM` 0.6, `CLEAR` 0.2, `MAGNET` 10 × 3) and `check_print()`, which the build runs on every printed outline; the FreeCAD macro and Fusion script (`freecad_macro()`, `fusion_script()`); and `nonzero_region()`, the area an SVG path fills under the nonzero rule (the outlined wordmark is built from overlapping contours, so its subpaths can't be used one by one as faces or cut lines). The models themselves are in `kit_targets.build_3d()`. Without OCP the STEP and 3MF files and the OCP-built prints are skipped with a warning. |
| `kit_product.py` | `product/`: the product system. Semantic color roles for light, dark and field themes, the four signal colors, type, space, lines, motion (one place: the constants at the top); `check_contrast()` and `check_cvd()` stop the build if any pair the rules rely on falls short (WCAG contrast, and distance under simulated protan/deutan/tritan vision); token files (DTCG JSON, CSS, Swift, Kotlin, C); the web stylesheet (`source/product/web/components.css` plus the tokens), WOFF2 font subsets, Tailwind and mdBook themes, the specimen and four example screens with Playwright screenshots; a made-up example flight (`example_flight()`) and the chart drawing (`chart_svg()`); CLI styles for Rust and Python with a rendered sample; device-screen mock-ups drawn with Spleen bitmap fonts (`source/product/embedded/fonts`, BSD-2); a KiCad board title block; livery wrap sheets; the rule documents, rendered from `source/product/*.md` with every `{{…}}` filled in from these values; and the guide's Products sheet. Runs on its own too: `python3 tools/build/kit_product.py` (needs a built `_build/rev-c` for the logos). |
| `kit_icons.py` | The product icon set: 60 icons on a 24 px grid (1.5 px stroke, square caps, 0/45/90°), drawn in code; the nose cone uses the Von Kármán profile. `GROUPS` orders them. |
| `kit_shot.py` | Screenshots an HTML file for a review preview (Playwright or headless Chrome; skipped if neither is installed). |
| `project.py` | Per-project images (`--name`, `--tag`, `--desc`): social preview, README banners, OG image, YouTube thumbnail, title slides, report covers, starter README. Writes to `projects/<name>/` or `--out`. |
| `kit_office.js` | Office templates for the kit (slides .pptx, letterhead .docx). Needs node with `pptxgenjs` and `docx` (`npm i -g pptxgenjs docx`); skipped with a warning otherwise. |
| `verify.py` | Renders a contact sheet (`verify.png`) of the lockups, icons and DXF, for checking by eye, and checks that no mark spills out of an icon tile, that every apparel print file keeps its transparent margin (`MERCH_MARGIN_IN`), that no output spells the name as two words, and that every 3D file is sound: each STL shell closed and consistently wound, each STEP read back as valid solids, each 3MF opened with closed objects. |

## Run

```
# on a Linux VM without root: bash tools/build/setup-linux-vm.sh, then use the export line it prints (rsvg-convert
# from _build/vm/, TMPDIR in _build/tmp, for a VM with a small, shared home disk)
pip install numpy scipy pillow svgpathtools ezdxf shapely cadquery-ocp   # cadquery-ocp: STEP files only
# product system: pip install fonttools brotli playwright && python3 -m playwright install chromium   (WOFF2 fonts, page screenshots)
# plus rsvg-convert (librsvg): brew install librsvg  /  apt install librsvg2-bin
# kit extras: Ghostscript for CMYK PDFs (brew install ghostscript), ffmpeg for the logo animation (brew install ffmpeg),
# matplotlib for STL previews (pip install matplotlib), node + npm i -g pptxgenjs docx for Office files,
# and the brand fonts from type/fonts installed (text in the kit is rendered with them)
python3 tools/build/build.py      # writes <repo>/_build/rev-c
python3 tools/build/verify.py     # writes <repo>/_build/rev-c/verify.png
python3 tools/mark-tuner/test/parity.py   # checks the tuner's geo.js draws exactly what the build draws (needs node)
python3 tools/mark-tuner/src/assemble.py  # rebuilds tools/mark-tuner/index.html from src/
```

The mark tuner (`tools/mark-tuner/index.html`) is a JavaScript port of `geo.py` and the lockup/icon geometry in `build.py`. Its source is in `tools/mark-tuner/src/` (`app.html` page, `geo.js` geometry, `wm-*.txt` wordmark paths). Any change to the geometry or lockup rules must be made in both places; `parity.py` fails if they drift.

- **Inputs:** the Rev B files in `source/`. The build takes the outlined wordmark paths, the templates, the guide HTML and the README text from there.
- **Output:** `_build/rev-c/`, which mirrors the repo layout. After checking it, copy its contents over the repo root (not `verify.png`, `review.html` or `review-previews/`, which stay local).
- **Paths:** override the input and output folders with the `FS_SRC` and `FS_OUT` environment variables.
- **Reproducible:** `build.py` sets `SOURCE_DATE_EPOCH` (PDF dates), runs with `PYTHONHASHSEED=0` (DXF object order), writes DXFs with
  fixed metadata, strips Ghostscript's IDs, gives Office and 3MF files fixed zip dates and STEP files a fixed date, and renumbers
  the STEP color entities, which Open CASCADE writes in hash order (`kit_cad._canonical_colors`). Two builds on the same machine are byte-identical
  apart from the build time in the sign-off page, so a commit only shows files whose content changed. (A different machine's rsvg,
  Ghostscript or LibreOffice can still produce different bytes.)

## Parameters (current values, all in `geo.py` or `build.py`)

*r* is the Von Kármán base radius. Internally the code uses *a*, where r = `W_K` × a = 0.40 a.

| Parameter | Value | Where |
|---|---|---|
| Lean of the whole cluster (degrees, clockwise) | 45 | `geo.TILT` |
| Profiles | main (north) Von Kármán (LD-Haack, C = 0), west conical, east elliptical, south (tail) tangent ogive | `geo.KINDS` |
| Base radii (in r) | main 1.0, west 0.4, east 0.3, south 0.5 | `geo.SIZE` |
| Cone length / base radius (all cones) | 3.50 (`H_K / W_K` = 1.40 / 0.40) | `geo.H_K`, `geo.W_K` |
| Tip above cone center (fraction of length) | 0.58 | `geo.TIP_K` |
| Notch depth / base radius | 1.00 (circular arc through both base corners, a half circle) | `geo.SAG_K` |
| Foot width / base radius: each foot is cut flat, parallel to the base line, where the wall between flank and notch is this wide | 0.05 | `geo.FOOT_K` |
| West wing gap: left Von Kármán foot corner to the conical's inner foot corner, horizontal (in r) | 0.19 | `geo.GAP_W_R` |
| East wing gap: right Von Kármán foot corner to the elliptical's inner foot corner, horizontal (in r) | 0.23 | `geo.GAP_E_R` |
| Wing centroid line (area centroids of the conical and elliptical) relative to the Von Kármán foot line (in r, + = below) | 0.47 | `geo.WING_R` |
| Tail (ogive) tip relative to the Von Kármán foot line (in r, + = below, − = up into the notch) | 0.21 | `geo.TAIL_R` |
| Stacked lockup: cluster height, gap, mark position | 125, 0.10 × cluster height (to the cap line when the mark is above, from the descenders when below), above | `build.STACK_H`, `build.STACK_GAP`, `build.STACK_POS` |
| Horizontal lockup: mark height, gap, mark position | 115 units (1.92 × cap height), 0.35 × cap height (21 units, mark's bounding box to the F; `H_GAP_K` = 0.183 × mark height is derived from it), before. Until October 3, 2026: 100 units and 0.375 × mark height; see `reviews/horizontal-gap-mockups/DECISION.md` | `build.H_MARK`, `build.H_GAP_CAP`, `build.H_POS` |

## Spacing rule

1. Lay the cluster out upright on a grid, then rotate the whole grid by `TILT`.
2. Each foot is cut flat where the wall between flank and notch is `FOOT_K` × that cone's base radius wide (`geo.foot()`). This also removes the sliver where the notch arc runs outside a straight conical flank.
3. Diamond: with the lean at 0, the Von Kármán is north and the ogive is the tail, south on the same axis. Its tip sits `TAIL_R` × r from the Von Kármán foot line, and it is drawn behind the Von Kármán (`geo.DRAW_ORDER`).
4. The area centroids of the conical (west) and elliptical (east) wings sit on one line, `WING_R` × r from the Von Kármán foot line (`geo.centroid_y()`).
5. The west wing's inner foot corner is `GAP_W_R` × r out from the left Von Kármán foot corner, and the east wing's is `GAP_E_R` × r out from the right one.

`geo.layout()` implements the rule. It returns the rotated cone centers (`POS`) and the upright ones (`POS_UPRIGHT`).

## Profile equations

Each profile uses the standard nose-cone equation, where x is measured from the tip, L is the length, R is the base radius and y is the radius at x:

- **Conical:** y = x R / L
- **Tangent ogive:** ρ = (R² + L²) / (2R), and y = √(ρ² − (L − x)²) + R − ρ. Drawn as a single circular arc of radius ρ.
- **Elliptical:** y = R √(1 − (L − x)² / L²). Drawn as a quarter-ellipse arc.
- **Von Kármán:** θ = arccos(1 − 2x/L), and y = (R/√π) √(θ − sin 2θ / 2). Drawn as five C1-continuous cubic Béziers that stay within 0.2% of the true curve (`geo.VK_BREAKS`, `geo.VK_ERR`).

## DXF

The DXF is 50 mm tall (`build.DXF_H_MM`). Every curve is converted to lines and arcs within 0.0005 mm (LWPOLYLINE bulges), so it works for laser and CNC. It is written with `ezdxf.new(setup=False)`, so it carries no default arrow or linetype blocks (FreeCAD imports those as stray objects).

**Minimum foot width.** At 50 mm the master feet (`FOOT_K` = 0.05) are 0.18–0.60 mm wide, too thin for most cutters. The DXF alone applies a production floor, `build.DXF_MIN_WALL_MM` = 0.5: each foot is cut where the wall is at least that wide (`geo.foot(..., min_wall)` / `geo.cone_segments(..., min_wall)`), then the trimmed outline is scaled to exactly 50 mm tall (at 45° the feet are the outermost points). `build.dxf_geometry()` does this and `build_dxf()` writes its result. Cone positions come from the master layout, which always uses `min_wall = 0`, so every SVG is unchanged. The tuner ports this (`minWall`, `dxfGeometry()` in `geo.js`), and `parity.py` checks it at 50 mm / 0.5 mm and at random sizes and floors.

Checked October 2026: LibreCAD 2.2 prints the file at 1:1 as 50.0 × 50.0 mm, and FreeCAD 26.3 (`Import.readDXF`) imports exactly 4 closed outlines with true arcs.

## Favicons and app icon

- `favicon.svg`: the cluster's bounding box fills `FAV_FILL` = 0.87 of the tile (corner radius `FAV_RX` = 96 of 512), and the cluster is moved from bbox-centered by `FAV_SHIFT` = (−10.72, +10.07) (of 512) so the gap to the tile edge is even: the main cone's tip (to the rounded corner), the west cone (left edge) and the east cone (bottom edge) are all 23.2 from it. `fav_balance()` finds the shift (it maximizes the cluster's least distance to the edge, `cone_gaps()`); rerun it and update `FAV_SHIFT` after changing the geometry, `FAV_FILL` or `FAV_RX`. `build_favicons()` stops if the three gaps differ by more than `FAV_GAP_TOL` = 0.05 or any is under `FAV_INSET` = 8, and `verify.py` checks every built icon tile for marks outside it. The tuner's `geo.js` mirrors `FAV_SHIFT`. (Until October 3, 2026 the fill was 0.92 and the cluster bbox-centered, which put the main cone's tip outside the top-right corner.) The 16 px PNG and .ico image are pixel-hinted by `hinted_favicon()`: the main and south cones from their outlines, the wing cones (`FAV_ARROWS`) as 2 × 2 arrows pointing up and right (top left, top right, bottom right pixels) in the 2 × 2 box where plain hinting puts each, since their outlines are too small to hint at 16 px.
- `favicon-16.png` (and the 16 px image in `favicon.ico`) is pixel-hinted by `hinted_favicon()`: each pixel is either cone (its average gradient color) or tile, with no half-tone fringe. 32 and 48 px are plain renders.
- `app-icon.svg` / `apple-touch-icon.png`: the cluster is scaled so its farthest point sits on a circle of radius `APP_SAFE_R` = 0.40 × the tile (the W3C maskable-icon safe zone), computed by `app_frac()`. It therefore also works as an Android/PWA maskable icon.
- The tuner's `geo.js` mirrors these values (`FAV_FILL`, `FAV_RX`, `APP_SAFE_R`, `appFrac`), and `parity.py` checks them. The tuner also previews the hinted 16 px favicon (`drawHinted()` in `app.html`, a port of `hinted_favicon()`; browser and rsvg anti-aliasing differ slightly, so a few pixels can differ by a shade).

## Mark tuner extras

- **Production · minimum feature sizes**: every foot at the DXF size (master and trimmed, with a magnified thumbnail), the height at which every master foot reaches the floor, and foot widths in px at 16/32 px favicons and a 24 px cluster. `DXF_H_MM` and `DXF_MIN_WALL_MM` are tuner controls and are included in the copied values.
- **Export SVG**: the mark, stacked and horizontal lockups (gradient, Void or white) and the cut outline in mm, from the current tuning. They download directly from the browser. They are previews; the build's files stay the reference.

## 3D print and CAD (`kit_targets.build_3d`, `kit_cad.py`)

- **Rules** for a 0.4 mm nozzle and 0.2 mm layers, in `kit_cad.py`: raised strokes at least `MIN_FEATURE` 0.6 mm, gaps at least
  `MIN_GAP` 0.5 mm, cone feet cut at `FOOT_MM` 0.6 mm (the mark is then scaled back to its full height, as for the DXF),
  heights in whole layers, `CLEAR` 0.2 mm a side for slip fits, magnet pockets for a 10 × 3 mm disc (`MAGNET`, +0.15 mm a side,
  +0.2 mm deep). `check_print()` shrinks each printed outline by half the minimum stroke (a piece that splits has a stroke too
  thin; tips only shrink) and grows it by half the minimum gap (pieces that merge or holes that fill are too close); the build
  stops if any model fails. The name's thinnest stroke is 0.0058 × its width, so prints with the name are sized from that
  (name and stacked lockup ≥ 104 mm wide, horizontal lockup ≥ 130 mm).
- **Exact mark.** `kit_cad.Outline` carries a cone's own segments (`geo.cone_segments`) through a similarity transform, so the
  STEP files hold true lines, circles, the elliptical wing's ellipse and the Von Kármán's cubic Béziers (written by OCCT as
  B-spline entities with Bézier knots: the same curve, not a fit), and the sketch DXFs hold LINE, ARC, ELLIPSE and SPLINE
  entities. The wordmark and shapely-built plates are B-splines within `STEP_TOL`.
- **Two kinds of model.** Layered prints (lists of `Layer`: an outline extruded between two heights) get their STL from
  `extrude()` without OCP, so their STLs stay byte-identical when OCP is missing; STEP and 3MF need OCP. Prints with pockets,
  slots, curved backs or engraving are `Model`s built with OCP booleans and meshed with `mesh_of()`. Without OCP those are
  skipped with a warning (and a copy of such a build over the repo would delete them: build where OCP loads).
- **3MF**: one object per piece, one part per color (base, cones M orange, cones O blue, name) with `displaycolor` from the
  two-tone-on-dark mode and `Metadata/Slic3r_PE_model.config` setting each part's extruder (base 1, raised 2). Checked by slicing
  with PrusaSlicer 2.7 on two extruders. Zip dates are fixed, so 3MFs are reproducible.
- **Previews**: layered models keep `stl_preview()`; the others use `kit_cad.render_preview()` (orthographic, flat shaded, crease
  lines), and the lithophane shows how it looks lit from behind.
- **Templates**: `freecad_macro()` writes a FreeCAD macro (spreadsheet-driven Draft clone of the exact mark, extruded, on a round
  plate with a magnet pocket; run headless in FreeCAD 26.3 when it was added) and `fusion_script()` a Fusion script with user
  parameters (not run in Fusion).

## Asset kit (`kit.py`)

`build_all()` ends with `kit.build_kit()`, which writes `<OUT>/kit`. Everything is generated from the master geometry and the five color modes in `build.MODES`:

| Mode | Fills |
|---|---|
| `color` | Fusion gradient (mark and wordmark each get their own sweep); the same on dark and light |
| `twotone-on-dark` | flat: warm cones M orange `#DA7C30`, cool cones O blue `#768DF5`, white wordmark |
| `twotone-on-light` | flat: the same cones, Void wordmark |
| `void`, `white` | one color |

Warm or cool comes from `build.twotone_side()`: each cone takes the gradient end nearest its area centroid along the sweep (now: west and south warm, main and east cool). Light composites use `kit.LIGHT_MODE` (`color`, the gradient, as approved; set `FS_LIGHT_MODE=twotone-on-light` to try the alternative).

## Colors

The palette lives in `build.py`: `GRADIENT` (stops, decided October 2, 2026), `M_ORANGE` /
`O_BLUE` (the gradient ends: accents on dark, two-tone cones `WARM` / `COOL`, Spectral O and M), `ION` / `EMBER` (text and UI on light,
not logo colors). The archived Rev B inputs carry the old pastel colors; `rd()` maps them through `OLD_COLORS`. `build_tokens()`
writes the JSON, then `build_color_files()` writes `color/fusion-space-tokens.css` and `color/fusion-space.gpl` from it;
`build_graphics()` writes the gradient strip and spectral bar; `build_wordmarks()` the standalone wordmarks. The guide's contrast table
is computed by `contrast()`. `SMALL_RULE` / `SMALL_H_PX` hold the small-size rule (horizontal lockup under 32 px on light → Void; 28 px until October 3, 2026).

To add a target: write a function that returns an SVG string (use `Art.place()` for logos, `background()` for the grid and strip, `text()` for editable text), save it with `save_svg()`, export with `png()` / `pdf()` / `cmyk()`, and `note()` it so it appears in `kit/README.md`. Platform sizes live in `SOCIAL`, `AVATARS`, `PAGES`, `CARDS`, `CUT_MM` (kit.py) and `DISPLAYS`, `SILK_MM`, `STEAM`, `WALL` (kit_targets.py). Brand words live in `TAGLINE`, `SCOPE`, `ROLE` and `DISCIPLINES` (kit.py).
