"""FusionSpace kit: discipline targets.

embedded/   OLED, e-paper and TFT boot logos as C headers (Adafruit GFX, U8g2/XBM, SSD1306 pages, RGB565) + previews
pcb/        KiCad silkscreen footprints of the mark (several sizes, front and back) + SVG/PNG for other EDA tools
3d-print/   STL, STEP and 3MF: extruded mark and lockups, badges, magnet, desk stand, cable tags, stencils, lithophane, cookie
            cutter; sketches and parametric templates (geometry and solids in kit_cad.py)
software/   terminal color schemes, braille/ASCII banners (plain and 24-bit ANSI), CLI banner snippets
games/      studio splash screens, Steam and itch.io template art
video/      logo animation (MP4, WebM, GIF, alpha WebM), YouTube watermark, thumbnail template
wallpapers/ desktop and phone wallpapers, video-call backgrounds
merch/      t-shirt, hoodie and mug print files (300 dpi), poster"""
import os, io, json, math, shutil, subprocess, struct, re
import numpy as np
from PIL import Image
import geo, build, kit, kit_cad
from kit import (KIT, note, out, save_svg, png, pdf, cmyk, svg_open, layer, text, background, theme, gradient, art_mark, art_horizontal,
                 art_stacked, PIECES, TAGLINE, WARN, f)
from build import VOID, PAPER, WHITE, ION, EMBER, M_ORANGE, O_BLUE, STOPS
ABYSS, GRAPHITE, SLATE, HAZE, MIST = kit.ABYSS, kit.GRAPHITE, kit.SLATE, kit.HAZE, kit.MIST

def raster(svg, w, h):
    r = subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h)], input=svg.encode(), capture_output=True, check=True)
    return np.asarray(Image.open(io.BytesIO(r.stdout)).convert("RGBA"))

def plain_svg(w, h, body, defs="", bg=None):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(w)}" height="{f(h)}" viewBox="0 0 {f(w)} {f(h)}"><defs>{defs}</defs>'
            + (f'<rect width="{f(w)}" height="{f(h)}" fill="{bg}"/>' if bg else "") + body + "</svg>")

def fit(art, w, h, frac=0.8, mode="white", prefix="z", cx=None, cy=None):
    k = frac * min(w / art.w, h / art.h)
    cx = w / 2 if cx is None else cx; cy = h / 2 if cy is None else cy
    return art.place(mode, prefix, cx - art.w * k / 2, cy - art.h * k / 2, k)

# ================================================================ embedded displays
DISPLAYS = [  # (name, w, h, kind, piece) kind: mono | rgb565
    ("oled-128x64", 128, 64, "mono", "stacked"), ("oled-128x32", 128, 32, "mono", "horizontal"), ("oled-128x64-mark", 128, 64, "mono", "mark"),
    ("oled-72x40-mark", 72, 40, "mono", "mark"), ("epaper-296x128", 296, 128, "mono", "horizontal"), ("epaper-250x122", 250, 122, "mono", "horizontal"),
    ("tft-240x240", 240, 240, "rgb565", "stacked"), ("tft-320x240", 320, 240, "rgb565", "stacked"), ("tft-160x128", 160, 128, "rgb565", "horizontal"),
    ("tft-135x240", 135, 240, "rgb565", "stacked"), ("tft-480x320", 480, 320, "rgb565", "stacked"),
    ("tft-240x240-round", 240, 240, "rgb565", "mark"),              # GC9A01 1.28" round: art inside the visible circle
    ("epaper-200x200", 200, 200, "mono", "stacked"), ("epaper-400x300", 400, 300, "mono", "stacked")]   # 1.54" and 4.2" e-paper

def c_array(name, data, per_line=16, ctype="uint8_t", fmt="0x{:02X}"):
    lines = []
    for i in range(0, len(data), per_line):
        lines.append("  " + ", ".join(fmt.format(v) for v in data[i:i + per_line]) + ",")
    return f"const {ctype} {name}[{len(data)}] PROGMEM = {{\n" + "\n".join(lines) + "\n};\n"

def build_embedded():
    D = f"{KIT}/embedded"; G = "Embedded & electronics"
    os.makedirs(out(D), exist_ok=True)
    readme = ["# FusionSpace boot logos for small displays", "",
              "Each header has the logo as C arrays, ready for a splash screen. Monochrome logos are white-on-black (lit pixels =",
              "logo), drawn pixel-hinted so small sizes stay crisp. `PROGMEM` is defined away on non-AVR targets.", "",
              "| Array suffix | Layout | Use with |", "|---|---|---|",
              "| `_gfx` | 1 bit/pixel, rows top to bottom, MSB = leftmost pixel, rows padded to whole bytes | Adafruit GFX `drawBitmap(x, y, bmp, w, h, WHITE)` |",
              "| `_xbm` | 1 bit/pixel, rows, LSB = leftmost pixel (XBM) | U8g2 `drawXBM(x, y, w, h, bmp)`, also saved as `.xbm` |",
              "| `_pages` | SSD1306 native: 8-pixel vertical bytes, page by page | Write straight to the SSD1306/SH1106 frame buffer |",
              "| `_rgb565` | 16-bit RGB565, big-endian words, row-major, background Void | TFT_eSPI `pushImage(x, y, w, h, img)`, ST7789/ILI9341 |", "",
              "| File | Size | Display |", "|---|---|---|"]
    for name, w, h, kind, piece in DISPLAYS:
        a = PIECES[piece](); ident = "fs_logo_" + re.sub(r"[^a-z0-9]+", "_", name)
        if kind == "mono":
            ss = 8
            defs, g = fit(a, w * ss, h * ss, 0.88, "white")
            cov = raster(plain_svg(w * ss, h * ss, g, defs), w * ss, h * ss)[..., 3].astype(float) / 255
            bits = cov.reshape(h, ss, w, ss).mean((1, 3)) >= 0.5
            Image.fromarray((bits * 255).astype(np.uint8)).save(out(f"{D}/{name}.png"))
            Image.fromarray((bits * 255).astype(np.uint8)).resize((w * 4, h * 4), Image.NEAREST).save(out(f"{D}/{name}-preview@4x.png"))
            bw = (w + 7) // 8
            gfx = [sum((1 << (7 - b)) for b in range(8) if x0 * 8 + b < w and bits[y, x0 * 8 + b]) for y in range(h) for x0 in range(bw)]
            xbm = [sum((1 << b) for b in range(8) if x0 * 8 + b < w and bits[y, x0 * 8 + b]) for y in range(h) for x0 in range(bw)]
            pages = [sum((1 << b) for b in range(8) if p * 8 + b < h and bits[p * 8 + b, x]) for p in range((h + 7) // 8) for x in range(w)]
            hdr = (f"// FusionSpace {piece} logo, {w} x {h}, monochrome. Generated by tools/build/kit_targets.py.\n#pragma once\n#include <stdint.h>\n"
                   "#ifndef PROGMEM\n#define PROGMEM\n#endif\n"
                   f"#define {ident.upper()}_W {w}\n#define {ident.upper()}_H {h}\n\n// Adafruit GFX drawBitmap (MSB first)\n" + c_array(ident + "_gfx", gfx)
                   + "\n// XBM / U8g2 drawXBM (LSB first)\n" + c_array(ident + "_xbm", xbm)
                   + "\n// SSD1306 page format (vertical bytes)\n" + c_array(ident + "_pages", pages))
            build.wr(f"{D}/{name}.h", hdr)
            build.wr(f"{D}/{name}.xbm", f"#define {ident}_width {w}\n#define {ident}_height {h}\nstatic unsigned char {ident}_bits[] = {{\n"
                     + ",".join(f"0x{v:02x}" for v in xbm) + " };\n")
        else:
            S = 4
            t = theme(True)
            round_ = name.endswith("-round")
            defs, g = fit(a, w * S, h * S, build.app_frac() * 1.1 if round_ else 0.8, "color")   # round: farthest point at 0.44 of the width, inside the glass
            img = Image.fromarray(raster(plain_svg(w * S, h * S, g, defs, bg=VOID), w * S, h * S)).convert("RGB").resize((w, h), Image.LANCZOS)
            img.save(out(f"{D}/{name}.png"))
            pv = img.resize((w * 2, h * 2), Image.NEAREST)
            if round_:                                                  # preview shows the round glass
                mask = Image.new("L", pv.size, 0); __import__("PIL.ImageDraw", fromlist=["Draw"]).Draw(mask).ellipse((0, 0, pv.width - 1, pv.height - 1), fill=255)
                pv = pv.convert("RGBA"); pv.putalpha(mask)
            pv.save(out(f"{D}/{name}-preview@2x.png"))
            px = np.asarray(img).astype(np.uint16)
            rgb = ((px[..., 0] >> 3) << 11) | ((px[..., 1] >> 2) << 5) | (px[..., 2] >> 3)
            hdr = (f"// FusionSpace {piece} logo, {w} x {h}, RGB565 on Void (0x{(0x0B >> 3) << 11 | (0x0F >> 2) << 5 | (0x1C >> 3):04X}). "
                   "Generated by tools/build/kit_targets.py.\n#pragma once\n#include <stdint.h>\n#ifndef PROGMEM\n#define PROGMEM\n#endif\n"
                   f"#define {ident.upper()}_W {w}\n#define {ident.upper()}_H {h}\n\n"
                   + c_array(ident + "_rgb565", [int(v) for v in rgb.flatten()], per_line=12, ctype="uint16_t", fmt="0x{:04X}"))
            build.wr(f"{D}/{name}.h", hdr)
            le = b"".join(int(v).to_bytes(2, "little") for v in rgb.flatten())      # LVGL v9 image: RGB565, little-endian, stride w*2
            build.wr(f"{D}/{name}-lvgl.c", f"""// FusionSpace {piece} logo, {w} x {h}, LVGL v9 image (RGB565 on Void). Generated by tools/build/kit_targets.py.
// Use: LV_IMAGE_DECLARE({ident}); lv_obj_t * img = lv_image_create(lv_screen_active()); lv_image_set_src(img, &{ident});
#include "lvgl.h"
#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif
""" + c_array(ident + "_map", list(le), ctype="LV_ATTRIBUTE_MEM_ALIGN uint8_t").replace(" PROGMEM", "") + f"""
const lv_image_dsc_t {ident} = {{
  .header = {{ .magic = LV_IMAGE_HEADER_MAGIC, .cf = LV_COLOR_FORMAT_RGB565, .flags = 0, .w = {w}, .h = {h}, .stride = {w * 2} }},
  .data_size = sizeof({ident}_map),
  .data = {ident}_map,
}};
""")
        readme.append(f"| `{name}.h` | {w} × {h} | {'monochrome OLED / e-paper' if kind == 'mono' else 'color TFT (RGB565' + (', round GC9A01' if name.endswith('-round') else '') + '; LVGL v9 image in `' + name + '-lvgl.c`)'} |")
    readme += ["", "Previews: `*-preview@4x.png` (mono) and `*-preview@2x.png` (color). Regenerate with the build to change sizes",
               "(`DISPLAYS` in `tools/build/kit_targets.py`). Color logos also come as LVGL v9 images (`*-lvgl.c`, `lv_image_dsc_t`, RGB565):",
               "add the file to your project, then `LV_IMAGE_DECLARE(fs_logo_tft_240x240); lv_image_set_src(img, &fs_logo_tft_240x240);`.",
               "The round 240 × 240 logo keeps the art inside the visible circle of a GC9A01 display."]
    build.wr(f"{D}/README.md", "\n".join(readme) + "\n")
    note(f"{D}/*.h, *.xbm, *.png", G, "boot logos as C arrays: OLED 128×64/128×32/72×40, e-paper 296×128/250×122 (1-bit; GFX, XBM, SSD1306 pages), e-paper 200×200/400×300, TFT 240×240/320×240/160×128/135×240/480×320 and round 240×240 (RGB565, plus LVGL v9 images)",
         "", "Splash screens on microcontrollers (Arduino, ESP32, STM32, RP2040)")

# ================================================================ PCB silkscreen (KiCad)
SILK_MM = [4, 6, 8, 12, 20]
def mark_polys_mm(height_mm, min_wall_mm, tol=0.01):
    cl, A, bb = build.dxf_geometry(float(height_mm), min_wall_mm)
    polys = []
    for n in geo.ORDER:
        pts = geo.sample(cl[n], 60)
        clean = [pts[0]]
        for p in pts[1:]:
            if math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > tol: clean.append(p)
        polys.append(clean)
    return polys, bb

def kicad_footprint(name, polys, bb, layer_name, mirror=False):
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    def P(x, y):
        x, y = x - cx, y - cy
        return (-x if mirror else x, y)
    body = []
    for ly in ([layer_name, layer_name[0] + ".Mask"] if layer_name.endswith(".Cu") else [layer_name]):   # copper logos get a matching mask opening
        for poly in polys:
            pts = " ".join(f"(xy {P(x, y)[0]:.4f} {P(x, y)[1]:.4f})" for x, y in poly)
            body.append(f'  (fp_poly (pts {pts}) (stroke (width 0) (type solid)) (fill solid) (layer "{ly}"))')
    h = bb[3] - bb[1]
    return (f'(footprint "{name}" (version 20240108) (generator "fusionspace-kit") (layer "F.Cu")\n'
            f'  (descr "FusionSpace mark, {h:.1f} mm tall, {layer_name}")\n  (attr board_only exclude_from_pos_files exclude_from_bom)\n'
            f'  (property "Reference" "G***" (at 0 {-h / 2 - 1:.2f}) (layer "{"F" if layer_name.startswith("F") else "B"}.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))\n'
            f'  (property "Value" "{name}" (at 0 {h / 2 + 1:.2f}) (layer "{"F" if layer_name.startswith("F") else "B"}.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))\n'
            + "\n".join(body) + "\n)\n")

def build_pcb():
    D = f"{KIT}/pcb"; G = "Embedded & electronics"
    lib = f"{D}/FusionSpace.pretty"
    for z in SILK_MM:
        polys, bb = mark_polys_mm(z, 0.15)
        for side, lay, mir in (("F", "F.SilkS", False), ("B", "B.SilkS", True), ("FCu", "F.Cu", False)):
            nm = f"FusionSpace_Mark_{z}mm_{side}"
            build.wr(f"{lib}/{nm}.kicad_mod", kicad_footprint(nm, polys, bb, lay, mir))
        cl, A, b2 = build.dxf_geometry(float(z), 0.15)
        build.wr(f"{D}/svg/fusion-space-mark-{z}mm-silk.svg",
                 f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(b2[2])}mm" height="{f(b2[3])}mm" viewBox="0 0 {f(b2[2])} {f(b2[3])}">'
                 + "".join(f'<path fill="#000000" d="{geo.seg_to_d(cl[n])}"/>' for n in geo.ORDER) + "</svg>\n")
    for piece in ("mark", "horizontal", "stacked"):          # 1-bit PNGs at 1200 dpi for KiCad's Image Converter / other EDA tools
        a = PIECES[piece](); hmm = 10.0 if piece == "mark" else (6.0 if piece == "horizontal" else 14.0)
        hp = int(hmm / 25.4 * 1200); wp = int(hp * a.w / a.h)
        defs, g = a.place("void", "p", 0, 0, hp / a.h)
        al = raster(plain_svg(wp, hp, g, defs), wp, hp)[..., 3]
        os.makedirs(out(f"{D}/png"), exist_ok=True)
        Image.fromarray(np.where(al >= 128, 0, 255).astype(np.uint8)).convert("1").save(out(f"{D}/png/fusion-space-{piece}-{f(hmm)}mm-1200dpi.png"), dpi=(1200, 1200))
    build.wr(f"{D}/README.md", f"""# FusionSpace logo for PCBs

- **KiCad**: add `FusionSpace.pretty` as a footprint library (Preferences → Manage Footprint Libraries → Add existing).
  Footprints: `FusionSpace_Mark_<size>mm_F` (front silkscreen), `_B` (back silkscreen, mirrored as KiCad expects), and `_FCu`
  (exposed copper with a matching F.Mask opening, so it comes out bare and takes the board finish: gold on ENIG, silver on HASL). Sizes: {", ".join(map(str, SILK_MM))} mm tall.
- Feet are trimmed so every feature is at least 0.15 mm wide, the usual silkscreen minimum. Below 6 mm many fabs blur the
  tips; 8 mm and up is safest.
- **Other EDA tools** (EasyEDA, Altium, Fusion Electronics): import `svg/fusion-space-mark-<size>mm-silk.svg`, or use the
  1200 dpi 1-bit PNGs in `png/` (mark 10 mm, horizontal lockup 6 mm, stacked 14 mm tall) with KiCad's Image Converter.
- The wordmark has thin strokes: keep the cap height at least 1 mm (horizontal lockup at least 1.7 mm tall).
""")
    note(f"{D}/FusionSpace.pretty/", G, f"KiCad footprints: mark on F.SilkS, B.SilkS (mirrored) and F.Cu", ", ".join(map(str, SILK_MM)) + " mm tall", "PCB logos (KiCad 7/8)")
    note(f"{D}/svg/, {D}/png/", G, "silkscreen SVGs in mm and 1-bit 1200 dpi PNGs", "", "EasyEDA, Altium, KiCad Image Converter")

# ================================================================ 3D printing (STL)
def tri_stl(triangles):
    triangles = [t for t in triangles if np.linalg.norm(np.cross(np.subtract(t[1], t[0]), np.subtract(t[2], t[0]))) > 1e-9]
    buf = io.BytesIO(); buf.write(b"FusionSpace kit".ljust(80, b" ")); buf.write(struct.pack("<I", len(triangles)))
    for a, b, c in triangles:
        n = np.cross(np.subtract(b, a), np.subtract(c, a)); l = np.linalg.norm(n); n = n / l if l else n
        buf.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
    return buf.getvalue()

def _earclip(poly):
    """Triangulate a polygon (with holes) by ear clipping. Fallback for shapely < 2.1 (no constrained_delaunay_triangles,
    e.g. on Python 3.9)."""
    from shapely.geometry import LineString
    ext = [tuple(p) for p in list(poly.exterior.coords)[:-1]]            # CCW (poly is oriented by the caller)
    for hole in poly.interiors:                                           # bridge each hole into the outer ring
        h = [tuple(p) for p in list(hole.coords)[:-1]]                    # CW
        j = max(range(len(h)), key=lambda k: h[k][0])
        order = sorted(range(len(ext)), key=lambda k: (ext[k][0] - h[j][0]) ** 2 + (ext[k][1] - h[j][1]) ** 2)
        i = next(k for k in order if poly.buffer(1e-9).contains(LineString([h[j], ext[k]])))
        ext = ext[:i + 1] + h[j:] + h[:j + 1] + [ext[i]] + ext[i + 1:]
    P = np.array(ext, dtype=float); idx = list(range(len(P))); tris = []
    def cross(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    guard = 0
    while len(idx) > 3 and guard < 10 * len(P) * len(P):
        n = len(idx); found = False
        for k in range(n):
            ia, ib, ic = idx[(k - 1) % n], idx[k], idx[(k + 1) % n]
            a, b, c = P[ia], P[ib], P[ic]
            if cross(a, b, c) <= 1e-12: continue
            Q = P[idx]
            d1 = (b[0] - a[0]) * (Q[:, 1] - a[1]) - (b[1] - a[1]) * (Q[:, 0] - a[0])
            d2 = (c[0] - b[0]) * (Q[:, 1] - b[1]) - (c[1] - b[1]) * (Q[:, 0] - b[0])
            d3 = (a[0] - c[0]) * (Q[:, 1] - c[1]) - (a[1] - c[1]) * (Q[:, 0] - c[0])
            inside = (d1 > 1e-12) & (d2 > 1e-12) & (d3 > 1e-12)
            same = np.all(np.isclose(Q[:, None, :], np.array([a, b, c])[None]), axis=2).any(1)
            if (inside & ~same).any(): continue
            tris.append((tuple(a), tuple(b), tuple(c))); idx.pop(k); found = True; break
        guard += 1
        if not found: idx.pop(0)                                          # degenerate leftover; skip a vertex
    if len(idx) == 3: tris.append(tuple(tuple(P[i]) for i in idx))
    return tris

def extrude(poly, z0, z1):
    """Triangles for a shapely polygon (with holes) extruded from z0 to z1, outward normals."""
    import shapely
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient
    poly = orient(poly.simplify(1e-5, preserve_topology=True), 1.0)       # drop collinear/near-duplicate vertices
    tris = []
    if hasattr(shapely, "constrained_delaunay_triangles"):
        faces = [list(t.exterior.coords)[:3] for t in shapely.constrained_delaunay_triangles(poly).geoms]
    else:
        faces = [list(t) for t in _earclip(poly)]
    for c in faces:
        area = (c[1][0] - c[0][0]) * (c[2][1] - c[0][1]) - (c[2][0] - c[0][0]) * (c[1][1] - c[0][1])
        if area < 0: c = [c[0], c[2], c[1]]
        tris.append(([c[0][0], c[0][1], z1], [c[1][0], c[1][1], z1], [c[2][0], c[2][1], z1]))
        tris.append(([c[0][0], c[0][1], z0], [c[2][0], c[2][1], z0], [c[1][0], c[1][1], z0]))
    for ring in [poly.exterior] + list(poly.interiors):
        pts = list(ring.coords)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            tris.append(([x0, y0, z0], [x1, y1, z0], [x1, y1, z1]))
            tris.append(([x0, y0, z0], [x1, y1, z1], [x0, y0, z1]))
    return tris

def stl_preview(parts, dest, S=900, elev=50.0):
    """Oblique view of extruded layers: y is foreshortened by sin(elev), z lifts by cos(elev). Each part's side wall is the
    exact sweep of its outline along the lift (edge quads + both ends); tops go over it. Parts are drawn bottom to top."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from shapely import affinity
    se, ce = math.sin(math.radians(elev)), math.cos(math.radians(elev))
    proj = lambda p, z: affinity.translate(affinity.scale(p, 1, se, origin=(0, 0)), 0, z * ce)
    col = {"base": ("#141A2B", "#2A3248"), "cone": ("#4F64C2", O_BLUE)}   # cone: side (O blue, darker), top (O blue)
    layers = []
    for poly, z0, z1, role in sorted(parts, key=lambda t: t[1]):
        lo, hi = proj(poly, z0), proj(poly, z1)
        quads = []
        for ring in [lo.exterior] + list(lo.interiors):
            c = list(ring.coords)
            for (x0, y0), (x1, y1) in zip(c[:-1], c[1:]):
                q = Polygon([(x0, y0), (x1, y1), (x1, y1 + (z1 - z0) * ce), (x0, y0 + (z1 - z0) * ce)])
                if q.is_valid and q.area > 1e-9: quads.append(q)
        side = unary_union([lo, hi] + quads)
        layers.append((side, col[role][0])); layers.append((hi, col[role][1]))
    allp = unary_union([g for g, _ in layers]); x0, y0, x1, y1 = allp.bounds
    pad = 0.12 * max(x1 - x0, y1 - y0); W = max(x1 - x0, y1 - y0) + 2 * pad
    ox, oy = x0 - pad - (W - (x1 - x0) - 2 * pad) / 2, y0 - pad - (W - (y1 - y0) - 2 * pad) / 2
    def d(g):
        geoms = getattr(g, "geoms", [g]); out_ = []
        for pg in geoms:
            for ring in [pg.exterior] + list(pg.interiors):
                out_.append("M" + " L".join(f"{x - ox:.3f},{W - (y - oy):.3f}" for x, y in ring.coords) + "Z")
        return " ".join(out_)
    body = "".join(f'<path d="{d(g)}" fill="{c}" fill-rule="evenodd" stroke="{c}" stroke-width="{W / 2000:.4f}" stroke-linejoin="round"/>' for g, c in layers if not g.is_empty)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.3f} {W:.3f}"><rect width="{W:.3f}" height="{W:.3f}" fill="{PAPER}"/>{body}</svg>'
    Image.fromarray(raster(svg, S, S)).convert("RGB").save(dest)

class Layer:
    """One printed layer of a model: poly (shapely, mm, y up) from z0 to z1. role: "base" or "cone" (the preview color of
    stl_preview), tone: the body it belongs to in STEP and 3MF (base / warm / cool / name / part), exact: the Outline when
    the piece is a cone (STEP uses its true curves)."""
    def __init__(self, poly, z0, z1, role="cone", tone="part", exact=None):
        self.poly, self.z0, self.z1, self.role, self.tone, self.exact = poly, z0, z1, role, tone, exact
    def __iter__(self): return iter((self.poly, self.z0, self.z1, self.role))      # old (poly, z0, z1, role) unpacking

# bodies in STEP and 3MF: label, color in the file (the two-tone mode on dark: Void base, M orange and O blue cones, white name),
# extruder in the 3MF (1 base, 2 everything raised: a two-color print; give "cones, O blue" filament 3 for three colors)
TONES = {"base": ("base", VOID, 1), "warm": ("cones, M orange", M_ORANGE, 2), "cool": ("cones, O blue", O_BLUE, 2),
         "name": ("name", WHITE, 2), "part": ("part", O_BLUE, 1), "context": ("", "#C9CDD8", 0)}
PREVIEW = {"base": "#2A3248", "warm": M_ORANGE, "cool": O_BLUE, "name": "#F3F4F7", "part": O_BLUE, "context": "#C9CDD8"}
SIDE = build.twotone_side()
FINCAN = [(38, 16), (54, 22), (75, 30), (98, 40)]      # (body tube outer diameter, mark height) in mm; mark ≈ 0.4 × the tube
STAND = dict(w=120.0, h=66.0, t=3.0, relief=1.2, lockup_w=106.0, slot_depth=8.2, lean=15.0)   # desk stand and lithophane
SKETCH_SIZES = {"mark": [20, 30, 40, 50, 80, 100], "horizontal": [80, 100, 120, 150, 200], "stacked": [60, 80, 100, 150],
                "wordmark": [80, 100, 120, 150, 200]}     # mm: mark tall, the others wide

def _rrect(x0, y0, x1, y1, r):
    from shapely.geometry import box
    return box(x0, y0, x1, y1).buffer(-r, join_style=2).buffer(r, resolution=32)

def _contour(polys, h, off, simp=0.0):
    """The die-cut contour (the sticker outline): the cones merged by a closing, then offset by off mm."""
    from shapely.ops import unary_union
    U = unary_union(polys); R = kit.STICKER_CLOSE * h
    C = U.buffer(R, resolution=32).buffer(-R, resolution=32).buffer(off, resolution=32)
    return C.simplify(simp) if simp else C

def mark_layers(h, z0, z1, dx=0.0, dy=0.0, center=True, mirror=False):
    ols, (w, hh) = kit_cad.mark_outlines(h, kit_cad.FOOT_MM, center=center, mirror=mirror)
    ols = [o.moved(dx, dy) for o in ols]
    return [Layer(o.poly(40), z0, z1, "cone", SIDE[o.name], o) for o in ols]

def piece_layers(piece, z0, z1, width=None, height=None, dx=0.0, dy=0.0):
    """Layers for the stacked/horizontal lockup or the wordmark, width (or height) in mm, bottom left at (dx, dy), y up:
    exact cones (feet floored at FOOT_MM at the printed size) and the name as its filled region (nonzero rule)."""
    from shapely import affinity
    a = PIECES[piece](); k = (width / a.w) if width else (height / a.h); Hh = a.h * k
    out_ = []
    if a.mark_bb is not None:
        mb = a.mark_bb
        ols, _ = kit_cad.mark_outlines((mb[3] - mb[1]) * k, kit_cad.FOOT_MM)
        out_ += [Layer(o.moved(mb[0] * k + dx, Hh - mb[3] * k + dy).poly(40), z0, z1, "cone", SIDE[o.name],
                       o.moved(mb[0] * k + dx, Hh - mb[3] * k + dy)) for o in ols]
    wd = [d for d, role, cone in a.parts if role == "wm"]
    if wd:
        wm = affinity.translate(affinity.scale(kit_cad.nonzero_region(wd[0]), k, -k, origin=(0, 0)), dx, Hh + dy)
        out_ += [Layer(q, z0, z1, "cone", "name") for q in kit_cad.polys_of(wm)]
    return out_, a.w * k, Hh

class Model:
    """A print: either layers (STL from extrude(), no OCP needed) or OCP bodies [(tone, shape)]. pieces: for prints in
    several pieces, {suffix: [(tone, shape)]} in print orientation (one STL each, one object each in the 3MF), with
    bodies being the assembled view for STEP and the preview."""
    def __init__(self, fn, what, layers=None, bodies=None, pieces=None, mf=False, step=True, elev=50.0, azim=0.0, context=None, preview=None):
        self.fn, self.what, self.layers, self.bodies, self.pieces, self.preview = fn, what, layers, bodies, pieces, preview
        self.mf, self.step, self.elev, self.azim, self.context = mf, step, elev, azim, context
        self.check, self.info = [], {}

def _bodies_from_layers(layers):
    """[(tone, OCP shape)] from layers, one body per tone (exact cones where known)."""
    by = {}
    for L in layers:
        by.setdefault(L.tone, []).append(kit_cad.prism(L.exact if L.exact is not None else L.poly, L.z0, L.z1))
    return [(t, kit_cad.compound(s)) for t, s in by.items()]

def _meshes_from_layers(layers):
    by = {}
    for L in layers:
        by.setdefault(L.tone, []).extend(extrude(L.poly, L.z0, L.z1))
    return [(t, kit_cad.mesh_from_tris(tr)) for t, tr in by.items()]

def _ocp_models():
    """The prints that need Open CASCADE: pockets, slots, curved backs, engraving, cutters. Their plates and the name are
    fitted within 0.005 mm (STEP_TOL is 0.002): far below what a printer can show, and a quarter of the file size."""
    with kit_cad.fit_tolerance(0.005):
        return _ocp_models_()

def _ocp_models_():
    from shapely.geometry import Point, Polygon, box
    from shapely.ops import unary_union, polylabel
    from shapely import affinity
    P = kit_cad; M = []
    def tone_shapes(layers): return _bodies_from_layers(layers)

    # fridge magnet: the 40 mm mark raised on the die-cut base, a pocket for a 10 x 3 mm disc magnet under the thickest point
    dmag = P.MAGNET[0] + 2 * P.MAGNET_CLEAR; hmag = P.MAGNET[1] + 0.2
    for hidden in (False, True):
        cones = mark_layers(40, 0, 1)
        base = _contour([L.poly for L in cones], 40, 3.0, 0.002)
        c = polylabel(base, 0.05)
        zb = 4.6 if hidden else 4.0; pz = 0.6 if hidden else 0.0
        if base.exterior.distance(c) < dmag / 2 + P.MIN_WALL: raise ValueError("magnet: pocket too close to the edge")
        plate = P.cut(P.prism(base, 0, zb), P.cylinder(dmag / 2, pz, pz + hmag, c.x, c.y))
        cones = mark_layers(40, zb, zb + 1.2)
        fn = "fusion-space-magnet-40mm" + ("-hidden" if hidden else "")
        M.append(Model(fn, ("fridge magnet, hidden magnet (pause at %.1f mm)" % (pz + hmag)) if hidden else "fridge magnet",
                       bodies=[("base", plate)] + tone_shapes(cones), mf=True))
        M[-1].check = [base] + [L.poly for L in cones]
        M[-1].info = dict(base=zb, top=zb + 1.2, pocket=(dmag, hmag, pz), center=(c.x, c.y))

    # fin-can badges: a chamfered plaque curved to the body tube, the mark raised 0.8 mm; printed standing on its bottom edge
    for D, H in FINCAN:
        R = D / 2; t = 1.6; rel = 0.8; m = max(2.5, round(0.1 * H * 2) / 2); S = H + 2 * m; ch = round(0.22 * S, 1)
        octa = Polygon([(-S / 2 + ch, 0), (S / 2 - ch, 0), (S / 2, ch), (S / 2, S - ch), (S / 2 - ch, S), (-S / 2 + ch, S), (-S / 2, S - ch), (-S / 2, ch)])
        ols, _ = P.mark_outlines(H, P.FOOT_MM, center=True); ols = [o.moved(0, S / 2) for o in ols]
        far = R + t + rel + 2
        shell = P.cut(P.cylinder(R + t, -1, S + 1), P.cylinder(R, -2, S + 2))
        skin = P.cut(P.cylinder(R + t + rel, -1, S + 1), P.cylinder(R + t - 1e-3, -2, S + 2))
        plaque = P.common(shell, P.prism_along(octa, "y", -far, 0))
        bodies = [("base", plaque)]
        for tone in ("warm", "cool"):
            sel = [o for o in ols if SIDE[o.name] == tone]
            bodies.append((tone, P.common(skin, P.prism_along(sel, "y", -far, 0))))
        tube = P.cut(P.cylinder(R, -6, S + 6), P.cylinder(R - 1.2, -7, S + 7))
        tube = P.common(tube, P.box(-R - 1, -R - 1, -7, R + 1, 0, S + 7))
        md = Model(f"fusion-space-fincan-badge-{D}mm", f"fin-can badge for a {D} mm body tube", bodies=bodies, mf=True,
                   elev=22.0, azim=-28.0, context=tube)
        md.check = [octa] + [o.poly(40) for o in ols]; md.info = dict(D=D, H=H, S=S, t=t, rel=rel, ch=ch)
        M.append(md)

    # desk stand: the stacked lockup raised on a plate (filament swap), and a foot with a slot that leans it back 15 degrees
    s = STAND; plate = _rrect(-s["w"] / 2, 0, s["w"] / 2, s["h"], 6.0)
    lay, w_, h_ = piece_layers("stacked", s["t"], s["t"] + s["relief"], width=s["lockup_w"])
    vis0 = s["slot_depth"]; cy = (vis0 + s["h"]) / 2
    lay = [Layer(affinity.translate(L.poly, -w_ / 2, cy - h_ / 2), L.z0, L.z1, L.role, L.tone,
                 L.exact.moved(-w_ / 2, cy - h_ / 2) if L.exact is not None else None) for L in lay]
    plaque_bodies = [("base", P.prism(plate, 0, s["t"]))] + tone_shapes(lay)
    Lf, Df, Hf, chf = s["w"] + 12, 32.0, 14.0, 4.0
    top = P.prism(_rrect(-Lf / 2, 0, Lf / 2, Df, 6.0), 0, Hf)
    prof = Polygon([(0, 0), (Df, 0), (Df, Hf - chf), (Df - chf, Hf), (chf, Hf), (0, Hf - chf)])
    foot = P.common(top, P.prism_along(prof, "x", -Lf / 2 - 1, Lf / 2 + 1))
    gap = s["t"] + 2 * P.CLEAR; ls = s["w"] + 2 * P.CLEAR
    yf, zf = 14.0, Hf - s["slot_depth"] * math.cos(math.radians(s["lean"]))
    def place(shape):       # slot frame (x, t, s) -> world: lean back by s["lean"] about x, floor center at (0, yf, zf)
        return P.transformed(shape, rot=((0, 0, 0), (1, 0, 0), -s["lean"]), move=(0, yf, zf))
    slot = place(P.box(-ls / 2, -gap / 2, 0, ls / 2, gap / 2, 40))
    foot = P.cut(foot, slot)
    def stand_up(shape):    # plaque as printed (x, y up the plate, z out of it) -> slot frame: back face at t = +t/2
        sh = P.transformed(shape, rot=((0, 0, 0), (1, 0, 0), 90.0), move=(0, s["t"] / 2, 0))
        return place(sh)
    # rotate +90 about x: (y, z) -> (-z, y): the plate's thickness points to -t (the front), its height up the slot
    md = Model("fusion-space-desk-stand-120mm", "desk stand: stacked lockup plaque and foot",
               bodies=[(t_, stand_up(sh), "plaque" if t_ == "base" else f"plaque: {TONES[t_][0]}") for t_, sh in plaque_bodies] + [("base", foot, "foot")],
               pieces={"plaque": plaque_bodies, "foot": [("base", foot)]}, mf=True, elev=24.0, azim=-30.0)
    md.check = [plate] + [L.poly for L in lay]; md.info = dict(gap=gap, slot=ls, zf=zf)
    M.append(md)

    # cable tag for a zip tie (two slots), the 12 mm mark raised 0.6 mm (filament swap at 2.0 mm)
    tag = _rrect(-22, -8, 22, 8, 3.0)
    slots = [box(x - 0.9, -2.2, x + 0.9, 2.2) for x in (-18.5, 18.5)]
    plate_s = P.cut(P.prism(tag, 0, 2.0), *[P.prism(sl, -1, 3) for sl in slots])
    cones = mark_layers(12, 2.0, 2.6, dx=-9.0)
    md = Model("fusion-space-cable-tag-44mm", "cable tag for a zip tie", bodies=[("base", plate_s)] + tone_shapes(cones), mf=True)
    md.check = [tag.difference(unary_union(slots))] + [L.poly for L in cones]
    M.append(md)

    # snap-on cable clips (cable 4, 6, 8 mm; kept next to the zip-tie tag, Neer's choice), the mark engraved on the flag; printed on their side, no supports
    for d in (4, 6, 8):
        ri = d / 2 + 0.15; ro = ri + 1.6; wid = 12.0
        prof = (Point(0, 0).buffer(ro, resolution=64).union(box(0, ro - 2.0, ro + 18, ro))
                .difference(Point(0, 0).buffer(ri, resolution=64)).difference(box(-0.4 * d, -ro - 1, 0.4 * d, -0.3 * ri)))
        body = P.prism(prof, 0, wid)
        ols, _ = P.mark_outlines(9, P.FOOT_MM, center=True, mirror=True)       # mirrored: read from the flag's face (+y)
        ols = [o.moved(ro + 9.5, wid / 2) for o in ols]
        body = P.cut(body, P.prism_along(ols, "y", ro - 0.6, ro + 1))
        md = Model(f"fusion-space-cable-clip-{d}mm", f"snap-on cable clip for a {d} mm cable", bodies=[("part", body)], elev=35.0, azim=200.0)
        md.check = [prof]; M.append(md)

    # stencils: the mark cut out of a 1.2 mm sheet (the cones have no islands, so no bridges are needed)
    for H, mg in ((50, 13.0), (100, 20.0)):
        S = H + 2 * mg
        ols, _ = P.mark_outlines(H, P.FOOT_MM, center=True)
        sheet = P.cut(P.prism(_rrect(-S / 2, -S / 2, S / 2, S / 2, 6.0), 0, 1.2), P.prism(ols, -1, 2.2))
        md = Model(f"fusion-space-stencil-mark-{H}mm", f"stencil, {H} mm mark", bodies=[("part", sheet)])
        md.check = [_rrect(-S / 2, -S / 2, S / 2, S / 2, 6.0).difference(unary_union([o.poly(40) for o in ols]))]
        M.append(md)

    # nose-cone badges: thin and flexible (TPU) so they follow a nose cone's double curve
    for H in (20, 30):
        cones = mark_layers(H, 0.6, 1.2)
        base = _contour([L.poly for L in cones], H, 1.5, 0.002)
        md = Model(f"fusion-space-nosecone-badge-{H}mm", f"nose-cone badge, {H} mm, flexible (TPU)",
                   bodies=[("base", P.prism(base, 0, 0.6))] + tone_shapes(cones))
        md.check = [base] + [L.poly for L in cones]; M.append(md)

    # cookie cutter and stamp, 80 mm mark, mirrored (both are used upside down)
    H = 80
    cones = mark_layers(H, 3.0, 6.0, mirror=True)
    C = _contour([L.poly for L in cones], H, 3.0, 0.002)
    wall = C.buffer(0.8, resolution=32).simplify(0.002).difference(C); flange = C.buffer(4.8, resolution=32).simplify(0.002).difference(C)
    cutter = P.fuse(P.prism(wall, 0, 14.0), P.prism(flange, 0, 2.0))
    stamp = P.fuse(P.prism(C.buffer(-1.0, resolution=32).simplify(0.002), 0, 3.0), *[P.prism(L.exact, L.z0, L.z1) for L in cones])
    dx = C.bounds[2] - C.bounds[0] + 14
    md = Model("fusion-space-cookie-80mm", "cookie cutter and stamp, 80 mm mark",
               bodies=[("part", cutter, "cutter"), ("cool", P.transformed(stamp, move=(dx, 0, 0)), "stamp")],
               pieces={"cutter": [("part", cutter)], "stamp": [("part", stamp)]}, elev=42.0,
               preview=[("part", cutter), ("base", P.transformed(P.prism(C.buffer(-1.0, resolution=32).simplify(0.002), 0, 3.0), move=(dx, 0, 0)))]
                       + [(L.tone, P.transformed(P.prism(L.exact, L.z0, L.z1), move=(dx, 0, 0))) for L in cones])
    md.check = [wall, C.buffer(-1.0)] + [L.poly for L in cones]
    M.append(md)
    return M

def lithophane(fn):
    """The stacked lockup as a lithophane, 120 x 75 mm: 0.8 mm where the lockup is (light shines through), 3.0 mm elsewhere,
    with a 10 mm frame at the bottom that fits the desk stand's slot. A height field on a 0.4 mm grid; STL only."""
    W, Hh, px, tmin, tmax = STAND["w"], 75.0, 0.4, 0.8, 3.0
    fl, fr, fb, ft = 4.0, 4.0, 10.0, 4.0
    nx = int(round(W / px)) + 1; ny = int(round(Hh / px)) + 1
    a = art_stacked(); vw, vh = W - fl - fr, Hh - fb - ft
    k = 0.86 * min(vw / a.w, vh / a.h)
    x0 = fl + (vw - a.w * k) / 2; y0 = ft + (vh - a.h * k) / 2       # y down in the SVG
    defs, body = a.place("white", "li", x0, y0, k)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="{-px / 2} {-px / 2} {W + px} {Hh + px}">'
           f'<defs>{defs}</defs><rect x="-1" y="-1" width="{W + 2}" height="{Hh + 2}" fill="#000"/>{body}</svg>')
    img = raster(svg, nx, ny)[..., :3].astype(float) / 255
    Lum = img @ np.array([0.2126, 0.7152, 0.0722])
    yy, xx = np.mgrid[0:ny, 0:nx]; X = xx * W / (nx - 1); Y = Hh - yy * Hh / (ny - 1)        # y up
    inside = (X > fl) & (X < W - fr) & (Y > fb) & (Y < Hh - ft)
    T = np.where(inside, tmax - (tmax - tmin) * Lum, tmax)
    # mesh: top height field, flat bottom, side walls
    top = np.stack([X, Y, T], -1).reshape(-1, 3); idx = np.arange(nx * ny).reshape(ny, nx)
    a_, b_, c_, d_ = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]          # rows go down in y
    Ft = np.concatenate([np.stack([a_, c_, b_], -1).reshape(-1, 3), np.stack([b_, c_, d_], -1).reshape(-1, 3)])
    ring = list(idx[-1, :]) + list(idx[-2::-1, -1]) + list(idx[0, -2::-1]) + list(idx[1:-1, 0])   # bottom edge (y=0) left to right, up the right, back along the top, down the left
    nb = len(top); ringb = [nb + i for i in range(len(ring))]
    bot = top[ring].copy(); bot[:, 2] = 0.0
    from shapely.geometry import Polygon
    import shapely
    poly = Polygon(bot[:, :2]); lut = {(round(p[0], 6), round(p[1], 6)): i for i, p in zip(ringb, bot)}
    Fb = []
    for tri in shapely.constrained_delaunay_triangles(poly).geoms:
        q = [lut[(round(x, 6), round(y, 6))] for x, y in list(tri.exterior.coords)[:3]]
        pa, pb, pc = (bot[i - nb] for i in q)
        if (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pc[0] - pa[0]) * (pb[1] - pa[1]) > 0: q = [q[0], q[2], q[1]]     # bottom faces down
        Fb.append(q)
    Fs = []
    n = len(ring)
    for i in range(n):
        t0, t1, b0, b1 = ring[i], ring[(i + 1) % n], ringb[i], ringb[(i + 1) % n]
        Fs += [[t0, b0, b1], [t0, b1, t1]]
    V = np.concatenate([top, bot]); F = np.concatenate([Ft, np.array(Fb), np.array(Fs)])
    ok, msg = kit_cad.mesh_check(V, F)
    if not ok:                                   # the ring may run the other way round: flip the walls and try again
        F = np.concatenate([Ft, np.array(Fb), np.array(Fs)[:, [0, 2, 1]]]); ok, msg = kit_cad.mesh_check(V, F)
    if not ok: raise ValueError(f"lithophane mesh: {msg}")
    return (V, F), T, dict(W=W, H=Hh, px=px, tmin=tmin, tmax=tmax)

def lithophane_preview(T, dest, info, mu=1.5, S=900):
    """How it looks lit from behind: light through PLA falls off about exp(-mu * thickness)."""
    I = np.exp(-mu * (T - info["tmin"]))
    light = np.array(kit_cad._hex("#FFF1D6")); dark = np.array(kit_cad._hex("#1C1A17"))
    rgb = dark + (light - dark) * I[..., None]
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    w = int(S * 0.86); h = int(w * info["H"] / info["W"]); im = im.resize((w, h), Image.LANCZOS)
    can = Image.new("RGB", (S, S), PAPER); can.paste(im, ((S - w) // 2, (S - h) // 2)); can.save(dest)

def write_sketch_dxf_exact(outlines, region, path, layer="OUTLINE"):
    """Like kit_cad.write_sketch_dxf, but the cones are their true curves: LINE, ARC, ELLIPSE and SPLINE (each Bézier as
    an exact cubic). region: the rest (the name) as closed polylines."""
    import ezdxf
    try: ezdxf.options.write_fixed_meta_data_for_testing = True
    except Exception: pass
    doc = ezdxf.new("R2010", setup=False); doc.units = 4; doc.layers.add(layer); msp = doc.modelspace(); at = {"layer": layer}
    def ang(p, c): return math.degrees(math.atan2(p[1] - c[1], p[0] - c[0]))
    for ol in outlines:
        for c in ol.curves():
            if c[0] == "line": msp.add_line(c[1], c[2], dxfattribs=at)
            elif c[0] == "circle":
                _, p0, pm, p1, cen, r = c; a0, am, a1 = ang(p0, cen), ang(pm, cen), ang(p1, cen)
                ccw = (am - a0) % 360 < (a1 - a0) % 360
                msp.add_arc(cen, r, a0 if ccw else a1, a1 if ccw else a0, dxfattribs=at)
            elif c[0] == "ellipse":
                _, p0, pm, p1, cen, d, A, B = c; nrm = np.array([-d[1], d[0]])
                pa = lambda p: math.atan2((np.subtract(p, cen) @ nrm) / B, (np.subtract(p, cen) @ np.array(d)) / A)
                t0, tm, t1 = pa(p0), pa(pm), pa(p1)
                ccw = (tm - t0) % (2 * math.pi) < (t1 - t0) % (2 * math.pi)
                s0, s1 = (t0, t1) if ccw else (t1, t0)
                msp.add_ellipse(cen, (d[0] * A, d[1] * A), B / A, s0 % (2 * math.pi), s1 % (2 * math.pi), dxfattribs=at)
            else:
                msp.add_open_spline(c[1], degree=3, knots=[0, 0, 0, 0, 1, 1, 1, 1], dxfattribs=at)
    if region is not None:
        for p in kit_cad.polys_of(region):
            for r in [p.exterior] + list(p.interiors):
                msp.add_lwpolyline([(round(x, 4), round(y, 4)) for x, y in list(r.coords)[:-1]], close=True, dxfattribs=at)
    doc.saveas(path)

def sketch_svg_exact(outlines, region, h, title, margin=2.0):
    """Hairline SVG in mm, y down: the cones as exact paths (lines, arcs, Béziers), the name as polylines."""
    from shapely import affinity
    flip = [o.affine(((1, 0), (0, -1)), (0, h)) for o in outlines]
    rg = affinity.scale(region, 1, -1, origin=(0, h / 2)) if region is not None else None
    pts = [p for o in flip for p in o.points(12)]
    if rg is not None and not rg.is_empty:
        bx = rg.bounds; pts += [(bx[0], bx[1]), (bx[2], bx[3])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]; x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    d = "".join(o.svg_d() for o in flip)
    if rg is not None:
        for p in kit_cad.polys_of(rg):
            for r in [p.exterior] + list(p.interiors):
                d += "M" + " L".join(f"{x:.4f},{y:.4f}" for x, y in list(r.coords)[:-1]) + "Z"
    w, hh = x1 - x0 + 2 * margin, y1 - y0 + 2 * margin
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}mm" height="{hh:.3f}mm" '
            f'viewBox="{x0 - margin:.3f} {y0 - margin:.3f} {w:.3f} {hh:.3f}">\n<title>{title}</title>\n'
            f'<path d="{d}" fill="none" stroke="#000000" stroke-width="0.01" fill-rule="evenodd"/>\n</svg>\n')

def build_3d():
    from shapely.geometry import Polygon, Point, box
    from shapely.ops import unary_union
    from shapely import affinity
    D = f"{KIT}/3d-print"; G = "Mechanical & fabrication"
    os.makedirs(out(D), exist_ok=True); models = {}
    problems = []
    def cone_polys(hmm, wall):
        cl, A, bb = build.dxf_geometry(float(hmm), wall)
        ps = [Polygon(geo.sample(cl[n], 40)).buffer(0) for n in geo.ORDER]
        return [affinity.scale(p, 1, -1, origin=(0, bb[3] / 2)) for p in ps], bb     # y up for STL
    def cone_exact(hmm, wall, dx=0.0, dy=0.0):
        ols, _ = kit_cad.mark_outlines(hmm, wall)
        return [o.moved(dx, dy) for o in ols]
    def cones(ps, ols, z0, z1, role="cone"):
        return [Layer(p, z0, z1, role, SIDE[o.name], o) for p, o in zip(ps, ols)]
    FW = kit_cad.FOOT_MM
    # 1. plain extruded mark (inlays, signs)
    for hmm in (40, 80):
        ps, bb = cone_polys(hmm, FW)
        models[f"fusion-space-mark-{hmm}mm-extruded-3mm"] = cones(ps, cone_exact(hmm, FW), 0, 3.0)
    # 2. desk badge: rounded base plate (the sticker contour) with the cones raised on top
    hmm = 50
    ps, bb = cone_polys(hmm, FW)
    base = _contour(ps, hmm, 3.0)
    models[f"fusion-space-badge-{hmm}mm"] = [Layer(base, 0, 2.0, "base", "base")] + cones(ps, cone_exact(hmm, FW), 2.0, 3.6)
    # 3. keychain: circle tag, mark raised, hole at the top
    Dm = 40.0; ps, bb = cone_polys(0.55 * Dm, FW)
    tag = Point(0, 0).buffer(Dm / 2, resolution=64).union(Point(0, Dm / 2).buffer(5.5, resolution=48)).difference(Point(0, Dm / 2 + 1.0).buffer(2.4, resolution=48))
    cx, cy = (bb[0] + bb[2]) / 2, bb[3] / 2
    ps = [affinity.translate(p, -cx, -cy) for p in ps]
    models[f"fusion-space-keychain-{int(Dm)}mm"] = [Layer(tag, 0, 2.4, "base", "base")] + cones(ps, cone_exact(0.55 * Dm, FW, -cx, -cy), 2.4, 3.6)
    # 4. the lockups and the name as solid pieces, a sign and a coaster (design review, October 2026). The name's thinnest stroke is
    # 0.0058 x the name's width (0.0047 x a horizontal lockup's), so every piece with the name is sized to keep it at
    # kit_cad.MIN_FEATURE (0.6 mm) or more: name and stacked lockup at least 104 mm wide, horizontal lockup 130 mm
    def part_layers(piece, width, z0, z1, dx=0.0, dy=0.0):
        lay, w_, h_ = piece_layers(piece, z0, z1, width=width, dx=dx, dy=dy); return lay, w_, h_
    lay, _, _ = part_layers("horizontal", 130, 0, 2.0); models["fusion-space-horizontal-130mm-extruded-2mm"] = lay
    lay, _, _ = part_layers("stacked", 110, 0, 2.0); models["fusion-space-stacked-110mm-extruded-2mm"] = lay
    lay, _, _ = part_layers("wordmark", 120, 0, 2.0); models["fusion-space-wordmark-120mm-extruded-2mm"] = lay
    # sign: 150 mm rounded plate, the horizontal lockup raised 1.2 mm (filament swap at 3.0 mm)
    lay, w_, h_ = part_layers("horizontal", 130, 3.0, 4.2)
    pad = 10.0; plate = box(-pad, -pad, w_ + pad, h_ + pad).buffer(-4, join_style=1).buffer(4, resolution=32)
    models["fusion-space-sign-horizontal-150mm"] = [Layer(plate, 0, 3.0, "base", "base")] + lay
    # coaster: 95 mm disc, the mark raised 0.8 mm (filament swap at 4.0 mm); keep the raised part low so a cup sits flat
    ps, bb = cone_polys(52.0, FW); cx, cy = (bb[0] + bb[2]) / 2, bb[3] / 2
    disc = Point(0, 0).buffer(47.5, resolution=96)
    models["fusion-space-coaster-95mm"] = [Layer(disc, 0, 4.0, "base", "base")] + cones([affinity.translate(q, -cx, -cy) for q in ps], cone_exact(52.0, FW, -cx, -cy), 4.0, 4.8)
    TWO = {"fusion-space-badge-50mm", "fusion-space-keychain-40mm", "fusion-space-sign-horizontal-150mm", "fusion-space-coaster-95mm"}
    for fn, layers in models.items():
        tris = [t for L in layers for t in extrude(L.poly, L.z0, L.z1)]
        open(out(f"{D}/{fn}.stl"), "wb").write(tri_stl(tris))
        raised = [L.poly for L in layers if L.role == "cone"]
        problems += kit_cad.check_print(fn, unary_union(raised))
    # STEP (every model; the cones exact), 3MF (the two-color ones), and the prints that need OCP
    ocp = []
    if kit_cad.HAVE_OCC:
        for fn, layers in models.items():
            kit_cad.write_step_bodies([(TONES[t][0], sh, TONES[t][1]) for t, sh in _bodies_from_layers(layers)], out(f"{D}/{fn}.step"), fn)
            if fn in TWO:
                kit_cad.write_3mf([(TONES[t][0], m, TONES[t][1], TONES[t][2]) for t, m in _meshes_from_layers(layers)], out(f"{D}/{fn}.3mf"), fn)
        ocp = _ocp_models()
        for md in ocp:
            for g in md.check: problems += kit_cad.check_print(md.fn, g)
            pv = [(kit_cad.mesh_of(b[1], 0.04, 0.2), PREVIEW[b[0]]) for b in (md.preview or md.bodies)]   # coarse mesh for the preview first
            if md.context is not None: pv = [(kit_cad.mesh_of(md.context, 0.05, 0.2), PREVIEW["context"])] + pv
            kit_cad.render_preview(pv, out(f"{D}/{md.fn}-preview.png"), elev=md.elev, azim=md.azim)
            meshes = [(b[0], kit_cad.mesh_of(b[1])) for b in md.bodies]
            if md.pieces:
                for suf, bl in md.pieces.items():
                    open(out(f"{D}/{md.fn}-{suf}.stl"), "wb").write(kit_cad.stl_bytes([kit_cad.mesh_of(sh) for _, sh in bl]))
            else:
                open(out(f"{D}/{md.fn}.stl"), "wb").write(kit_cad.stl_bytes([m for _, m in meshes]))
            kit_cad.write_step_bodies([(b[2] if len(b) > 2 else TONES[b[0]][0], b[1], TONES[b[0]][1]) for b in md.bodies], out(f"{D}/{md.fn}.step"), md.fn)
            if md.mf:
                if md.pieces:
                    objs = [[(f"{suf}: {TONES[t][0]}", kit_cad.mesh_of(sh), TONES[t][1], TONES[t][2]) for t, sh in bl] for suf, bl in md.pieces.items()]
                    kit_cad.write_3mf(None, out(f"{D}/{md.fn}.3mf"), md.fn, objects=objs)
                else:
                    kit_cad.write_3mf([(TONES[t][0], m, TONES[t][1], TONES[t][2]) for t, m in meshes], out(f"{D}/{md.fn}.3mf"), md.fn)
    else:
        WARN.append("step"); print(f"WARN kit: STEP, 3MF and the prints that need OCP (magnet, fin-can and nose-cone badges, desk stand, cable tag and clips, stencils, cookie cutter) skipped: OCP (cadquery-ocp) couldn't be loaded ({kit_cad.OCC_ERROR}). pip install cadquery-ocp")
    # lithophane (mesh only)
    (V, F), T, li = lithophane("fusion-space-lithophane-stacked-120mm")
    open(out(f"{D}/fusion-space-lithophane-stacked-120mm.stl"), "wb").write(kit_cad.stl_bytes([(V, F)]))
    lithophane_preview(T, out(f"{D}/fusion-space-lithophane-stacked-120mm-preview.png"), li)
    if problems:
        raise ValueError("3D prints fail the FDM rules (kit_cad.MIN_FEATURE / MIN_GAP):\n  " + "\n  ".join(problems))
    # sketches to import into CAD (or a slicer) and extrude or cut: the mark, the lockups and the name as closed outlines,
    # 1:1 mm, at several sizes. The cones are exact (LINE, ARC, ELLIPSE, SPLINE in the DXF; arcs and Béziers in the SVG)
    os.makedirs(out(f"{D}/sketch"), exist_ok=True)
    for piece, sizes in SKETCH_SIZES.items():
        for mm in sizes:
            if piece == "mark":
                ols, (w_, h_) = kit_cad.mark_outlines(mm, FW); wm = None; tag_ = f"{mm}mm"
            else:
                lay, w_, h_ = piece_layers(piece, 0, 1, width=mm)
                ols = [L.exact for L in lay if L.exact is not None]
                nm = [L.poly for L in lay if L.tone == "name"]; wm = unary_union(nm) if nm else None; tag_ = f"{mm}mm"
            write_sketch_dxf_exact(ols, wm, out(f"{D}/sketch/fusion-space-{piece}-{tag_}.dxf"))
            build.wr(f"{D}/sketch/fusion-space-{piece}-{tag_}.svg", sketch_svg_exact(ols, wm, h_,
                     f"FusionSpace {piece}, outline for CAD, {mm} mm {'tall' if piece == 'mark' else 'wide'}"))
    # previews of the layered models: oblique 3/4 view drawn as vector layers (side walls swept, then tops)
    for fn, layers in models.items():
        stl_preview([tuple(L) for L in layers], out(f"{D}/{fn}-preview.png"))
    # parametric templates (FreeCAD macro, Fusion script) with the exact mark in them
    os.makedirs(out(f"{D}/parametric"), exist_ok=True)
    build.wr(f"{D}/parametric/FusionSpace_Badge.FCMacro", kit_cad.freecad_macro())
    # Fusion runs a script from a folder of the same name, with a .manifest next to it (a bare .py can't be picked)
    os.makedirs(out(f"{D}/parametric/FusionSpace_Badge_Fusion"), exist_ok=True)
    build.wr(f"{D}/parametric/FusionSpace_Badge_Fusion/FusionSpace_Badge_Fusion.py", kit_cad.fusion_script())
    build.wr(f"{D}/parametric/FusionSpace_Badge_Fusion/FusionSpace_Badge_Fusion.manifest", json.dumps({
        "autodeskProduct": "Fusion360", "type": "script", "author": "FusionSpace",
        "description": {"": "FusionSpace badge: a parametric badge with the exact mark, driven by user parameters"},
        "supportedOS": "windows|mac", "editEnabled": True}, indent=1) + "\n")
    build.wr(f"{D}/README.md", README_3D(ocp))
    note(f"{D}/*.stl", G, "STL: extruded mark (40, 80 mm), desk badge, keychain, lockups and name, sign, coaster, fridge magnet, fin-can and nose-cone badges, desk stand, cable tag and clips, stencils, lithophane, cookie cutter and stamp", "", "3D printing (0.4 mm nozzle, 0.2 mm layers; settings in the README)")
    note(f"{D}/*.step", G, "STEP solids of every model (the mark's true lines, arcs, ellipse and Béziers; named, colored bodies)", "", "Fusion, Onshape, FreeCAD, SolidWorks")
    note(f"{D}/*.3mf", G, "3MF with one part per color (base, M orange cones, O blue cones, name) for two-color printers", "", "PrusaSlicer, OrcaSlicer, Bambu Studio")
    note(f"{D}/sketch/*.dxf/.svg", G, "outlines of the mark (exact curves), the lockups and the name to import and extrude or cut", "mark 20–100 mm, lockups and name 60–200 mm", "CAD sketches, slicer SVG import")
    note(f"{D}/parametric/", G, "parametric badge template: FreeCAD macro (spreadsheet-driven) and Fusion script (user parameters)", "", "resize, re-thicken, add a magnet pocket")

def README_3D(ocp):
    K = kit_cad
    pocket = f"{K.MAGNET[0] + 2 * K.MAGNET_CLEAR:.1f} × {K.MAGNET[1] + 0.2:.1f} mm"
    fc = ", ".join(f"{d}" for d, _ in FINCAN)
    return f"""# FusionSpace 3D-print and CAD files (millimeters)

Every model comes as `.stl` (mesh, for slicers) and `.step` (solid, for CAD: Fusion, Onshape, FreeCAD, SolidWorks). In the STEP
files the mark is exact: its lines, circular arcs, the elliptical wing's ellipse and the Von Kármán's Bézier curves, the same
curves as the master SVG (no fitting); the name and the plates are smooth B-splines within 0.002 mm. Each STEP has named,
colored bodies (base, cones in M orange and O blue, name). Two-color models also come as `.3mf` with one part per color
(see *Two colors* below). `sketch/` has outlines to import and extrude or cut; `parametric/` has a badge you can resize in
FreeCAD or Fusion.

Everything is made for a normal FDM printer: **0.4 mm nozzle, 0.2 mm layers** (first layer 0.2 mm), and checked by the build:
no raised stroke under {K.MIN_FEATURE} mm, no gap under {K.MIN_GAP} mm, cone feet trimmed to {K.FOOT_MM} mm, heights in whole layers,
no supports needed anywhere. Every STL was sliced (PrusaSlicer 2.7, 0.4 mm nozzle, 0.2 mm layers, no supports) without an overhang
or support warning; the two-color 3MFs slice with their parts on two filaments. Use a slicer with variable-width walls (Arachne: PrusaSlicer 2.6+, OrcaSlicer, Bambu Studio; in
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
| `fusion-space-magnet-40mm` | fridge magnet: die-cut base 4.0 mm with a {pocket} pocket from the back, cones raised 1.2 mm | 46 × 46 × 5.2 |
| `fusion-space-magnet-40mm-hidden` | the same magnet sealed inside (pause the print to drop it in): no glue, clean back | 46 × 46 × 5.8 |
| `fusion-space-fincan-badge-{{{fc}}}mm` | a chamfered plaque curved to fit a body tube of that outer diameter, mark raised 0.8 mm | mark 16 / 22 / 30 / 40 |
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
"Color change at Z" means the first layer of the new color (PrusaSlicer/Orca: add the color change on the layer at that height;
Bambu: *Add pause/filament change* on that layer).

| Model | Material | Orientation | Settings | Color |
|---|---|---|---|---|
| mark 40/80, extruded | PLA | flat | defaults; a 3 mm brim keeps the small wing cones down | one color |
| badge 50 | PLA | flat (base down) | defaults | color change at 2.2 mm (Void base, cones in a light color), or the 3MF |
| keychain 40 | PETG (takes the pull of a key ring) | flat | 4 walls | color change at 2.6 mm, or the 3MF |
| horizontal 130, stacked 110, name 120 | PLA | flat | 2 walls, 100 % infill (the strokes are walls only); 3 mm brim (the i's dot and the wing cones are small) | one color; glue onto a sign or a case |
| sign 150 | PLA | flat | defaults | color change at 3.2 mm, or the 3MF |
| coaster 95 | PETG (PLA softens under a hot mug) | flat | 5 bottom layers | color change at 4.2 mm, or the 3MF |
| magnet 40 | PLA | flat, pocket on the bed | defaults (the pocket's 0.8 mm roof bridges 10 mm cleanly) | color change at 4.2 mm, or the 3MF. Press a 10 × 3 mm disc magnet in with a drop of CA glue |
| magnet 40 hidden | PLA | flat | **pause at 3.8 mm** (insert the pause before the 4.0 mm layer), drop the magnet in, resume. Use a brass nozzle: a steel one is pulled toward the magnet | color change at 4.8 mm |
| fin-can badges | PETG or ASA (sun and motor heat) | **standing on its flat bottom edge**, as exported | 5 mm brim, 4 walls (the 1.6 mm shell is solid walls), 0.2 mm layers; the cones stand 0.8 mm proud of the curve and print without support | one color, or the 3MF on a multi-material printer; or paint the cones. Glue with epoxy; each fits its tube up to about 3 mm larger in diameter |
| nose-cone badges | TPU 95A | flat | 20–30 mm/s, 100 % infill | one color (or paint). Glue with contact cement or flexible CA |
| desk stand plaque | PLA | flat | defaults | color change at 3.2 mm, or the 3MF (the plaque's parts) |
| desk stand foot | PLA | upright, as exported | 15 % infill; the slot is {STAND['t'] + 2 * K.CLEAR:.1f} mm for the 3.0 mm plaque ({K.CLEAR} mm each side), 8.2 mm deep | one color (Void) |
| cable tag | PLA or PETG | flat | defaults | color change at 2.2 mm, or the 3MF |
| cable clips | PETG (PLA cracks when it snaps) | on its side, as exported (the clip's profile on the bed) | 4 walls, 100 % infill, 3 mm brim | one color. Fits cables within about 0.5 mm of the size |
| stencils | PLA or PETG | flat | 100 % infill (the 1.2 mm sheet is 6 solid layers) | one color. Tape it down and spray light coats |
| lithophane | white PLA | upright (rotate it so the 120 mm edge with the 10 mm frame is on the bed) with a 5 mm brim, or flat | 100 % infill, 0.12–0.2 mm layers, slow outer walls | white only. Light it from behind (a window, an LED strip) |
| cookie cutter / stamp | a food-safe PLA or PETG | cutter flange down, stamp face up, as exported | defaults; the cutting wall is 0.8 mm (2 lines) | one color. Wash by hand; prints are porous, so keep them for dry dough or line them with cling film |
| remove-before-flight tag | red and white PLA or PETG | flat, front up (the back's engraving prints on the bed) | defaults; smooth (textured PEI shows in the engraving) | color change at 2.2 mm (red tag, white text), or the 3MF |
| remove-before-flight tag, two-part | red and white PLA or PETG | both halves flat, art up, as exported | defaults | color change at 1.6 mm on both, or the 3MF (both halves, two colors). Push 1.4 mm lengths of 1.75 mm filament into the holes of one half, glue the halves (CA or epoxy), press together; the split ring goes through both |

## Fits and tolerances

| Where | Gap | Why |
|---|---|---|
| magnet pocket | {pocket} for a 10 × 3 mm disc | 0.15 mm each side on the diameter, 0.2 mm on the depth: a snug push fit, glue to be sure |
| desk stand slot | 3.4 mm for a 3.0 mm plaque (or the lithophane) | 0.2 mm each side: slides in, held by the 15° lean |
| cookie stamp | 1.0 mm inside the cutter's wall | the stamp drops into the cut cookie |
| cable clip | hole 0.3 mm over the cable, opening 0.8 × the cable | snaps over and holds |

If your printer runs tight or loose, scale only the part with the hole in the slicer (the foot, or the clip), or change the values
in `parametric/`.

## Two colors

Badge, keychain, sign, coaster, magnet, fin-can badges, desk stand and cable tag have a `.3mf` with one object whose parts are the
colors: **base** (Void), **cones, M orange**, **cones, O blue** and **name** (white), as in the two-tone logo on dark. Each part
already has its filament set for a two-color print: base filament 1, everything raised filament 2. For three colors give
“cones, O blue” filament 3. PrusaSlicer, OrcaSlicer and Bambu Studio read the parts and filaments; other programs see one
colored mesh. On a one-nozzle printer without a changer, print the STL with a color change at the height in the table.

## Sketches (`sketch/`)

Closed outlines at 1:1 to import onto a sketch plane and extrude (emboss) or cut (engrave). In the DXF the cones are true LINE,
ARC, ELLIPSE and SPLINE entities (each Bézier as an exact cubic), the name is closed polylines; the SVG has the same curves as
paths (hairline, y down). Feet are trimmed to 0.6 mm at each size.

| Sketch | Sizes (mm) | Smallest to print with a 0.4 mm nozzle |
|---|---|---|
| `fusion-space-mark-<size>mm` | {", ".join(str(v) for v in SKETCH_SIZES["mark"])} tall | any (raised or cut) |
| `fusion-space-horizontal-<size>mm` | {", ".join(str(v) for v in SKETCH_SIZES["horizontal"])} wide | 130 mm (the name's thinnest stroke is 0.0058 × the name's width, 0.0047 × this lockup's) |
| `fusion-space-stacked-<size>mm` | {", ".join(str(v) for v in SKETCH_SIZES["stacked"])} wide | 105 mm |
| `fusion-space-wordmark-<size>mm` | {", ".join(str(v) for v in SKETCH_SIZES["wordmark"])} wide | 105 mm |

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
"""

# ================================================================ software: terminal themes, banners
TERM = {  # red, green, yellow and magenta are the product system's signal inks on dark (Flare, Aurora, Sodium, Nebula), so a
          # CLI's error:, ok, warning: and predicted values match the screens; blue is O blue (product/cli.md). Decided 5 October 2026.
    "background": VOID, "foreground": "#E6E8EF", "cursor": O_BLUE, "selection": GRAPHITE,
    "black": ABYSS, "red": "#FB8083", "green": "#6AD5B6", "yellow": "#F5AF20", "blue": O_BLUE, "magenta": "#ED89D2", "cyan": "#8FD3E8", "white": "#D6DAE4",
    "brightBlack": SLATE, "brightRed": "#FFA9AB", "brightGreen": "#9BE8D0", "brightYellow": "#FFCB66", "brightBlue": "#CAD7FF",
    "brightMagenta": "#F5B4E3", "brightCyan": "#B9E8F5", "brightWhite": "#FFFFFF"}

def hex2rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

BLANK = "⠀"      # empty braille cell: used for the gaps inside the art, so every cell comes from the same font and has the same width

def term_art(piece, min_wall):
    """The piece for text art: the same layout, but each cone's feet are cut where the wall is at least min_wall wide (in the
    piece's units), the way the DXF gets its production floor (build.dxf_geometry). At banner sizes the master feet are far
    thinner than one braille dot and came out as stray dots or spikes (the conical wing's left foot read as a tail); cut at one
    dot they end cleanly. Cone positions, the wordmark and the gradient sweeps are unchanged."""
    a = PIECES[piece]()
    if piece == "mark": cl, _, bb = geo.fit_cluster(height=a.h); d = None
    elif piece == "horizontal": cl, bb, d, *_ = build.horizontal_geometry()
    elif piece == "stacked": cl, bb, d, *_ = build.stacked_geometry()
    else: return a
    b0 = geo.bbox(geo.cluster()); A = (bb[3] - bb[1]) / (b0[3] - b0[1]); org = (bb[0] - A * b0[0], bb[1] - A * b0[1])
    cones = {n: geo.cone_segments(n, A, org, min_wall=min_wall / A) for n in geo.ORDER}
    parts = [(geo.seg_to_d(cones[n]), "mark", n) for n in geo.DRAW_ORDER] + ([(d, "wm", None)] if d else [])
    return kit.Art(a.w, a.h, parts, mark_bb=a.mark_bb, wm_bb=a.wm_bb)

def braille(piece, cols, mode="color", thr=0.5, foot_dots=1.0):
    """Text art: braille cells (2 × 4 dots; a terminal cell is about twice as tall as wide, so the dots are square). The whole
    piece is drawn, wordmark included, at the lockup's own proportions: at 48 columns and up the name is legible in braille.
    Returns (plain lines, ANSI 24-bit lines), all the same width (padded with the empty braille cell U+2800, not spaces: a
    font without braille draws it with a fallback font whose cells can be wider than a space, which shifted whole rows).
    A dot is set where at least thr of it is covered; feet are cut at foot_dots dots wide (term_art). Each cell takes the
    average color of its dots."""
    a = PIECES[piece](); W = cols * 2; H = int(round(W * a.h / a.w / 2)) * 2
    H = max(4, (H + 3) // 4 * 4); ss = 6
    k = min(W * ss / a.w, H * ss / a.h)
    a = term_art(piece, foot_dots * ss / k)
    defs, g = a.place(mode, "b", (W * ss - a.w * k) / 2, (H * ss - a.h * k) / 2, k)
    img = raster(plain_svg(W * ss, H * ss, g, defs), W * ss, H * ss).astype(float)
    al = img[..., 3].reshape(H, ss, W, ss).mean((1, 3)) / 255
    col = (img[..., :3] * img[..., 3:4] / 255).reshape(H, ss, W, ss, 3).sum((1, 3)) / np.maximum((img[..., 3] / 255).reshape(H, ss, W, ss).sum((1, 3)), 1e-6)[..., None]
    bitmap = [[0, 3], [1, 4], [2, 5], [6, 7]]
    plain, ansi = [], []
    for r in range(H // 4):
        line, aline = "", ""
        for c in range(W // 2):
            code = 0; cs = []
            for dy in range(4):
                for dx in range(2):
                    y, x = r * 4 + dy, c * 2 + dx
                    if al[y, x] >= thr: code |= 1 << bitmap[dy][dx]; cs.append(col[y, x])
            ch = chr(0x2800 + code)
            line += ch
            if code:
                rgb = np.mean(cs, axis=0).round().astype(int)
                aline += f"\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{ch}"
            else:
                aline += ch
        plain.append(line); ansi.append(aline + "\x1b[0m")
    while plain and not plain[-1].strip(BLANK): plain.pop(); ansi.pop()
    while plain and not plain[0].strip(BLANK): plain.pop(0); ansi.pop(0)
    while plain and all(ln[-1] == BLANK for ln in plain):        # trim empty columns, keep every row the same width
        plain = [ln[:-1] for ln in plain]; ansi = [re.sub(BLANK + r"(\x1b\[0m)$", r"\1", ln) for ln in ansi]
    while plain and all(ln[0] == BLANK for ln in plain):
        plain = [ln[1:] for ln in plain]; ansi = [ln[1:] for ln in ansi]
    return plain, ansi

def term_preview(ansi_lines, dest, cw=12, ch=24, pad=16):
    """PNG of ANSI text as a terminal draws it (Void background, cells cw × ch, Cascadia Mono): braille cells as dots on
    the cell's 2 × 4 grid, text in the font. Browsers borrow braille from whatever font has it, so the review page shows
    this picture rather than the raw text (kit_review.make_previews calls this for every .ans file)."""
    from PIL import ImageDraw, ImageFont
    fdir = os.path.join(build.ROOT, "type", "fonts")
    reg = ImageFont.truetype(os.path.join(fdir, "CascadiaMono-Regular.ttf"), round(cw / 0.6))
    bold = ImageFont.truetype(os.path.join(fdir, "CascadiaMono-SemiBold.ttf"), round(cw / 0.6))
    rows = []
    for ln in ansi_lines:
        cells, fg, b = [], (230, 232, 239), False
        for tok in re.findall(r"\x1b\[[0-9;]*m|.", ln):
            if tok.startswith("\x1b["):
                codes = tok[2:-1].split(";")
                if codes == ["0"] or codes == [""]: fg, b = (230, 232, 239), False
                elif codes == ["1"]: b = True
                elif codes[:2] == ["38", "2"]: fg = tuple(int(v) for v in codes[2:5])
            else: cells.append((tok, fg, b))
        rows.append(cells)
    W = max(len(r) for r in rows) * cw + 2 * pad; H = len(rows) * ch + 2 * pad
    im = Image.new("RGB", (W, H), hex2rgb(VOID)); dr = ImageDraw.Draw(im)
    dots = [(0, 0, 0), (1, 0, 1), (2, 0, 2), (3, 1, 0), (4, 1, 1), (5, 1, 2), (6, 0, 3), (7, 1, 3)]     # bit, column, row
    rr = cw * 0.2
    for y, row in enumerate(rows):
        for x, (c, fg, b) in enumerate(row):
            X, Y = pad + x * cw, pad + y * ch
            o = ord(c)
            if 0x2800 <= o <= 0x28FF:
                for bit, dx, dy in dots:
                    if (o - 0x2800) >> bit & 1:
                        cx, cy = X + cw * (0.27 + 0.46 * dx), Y + ch * (0.125 + 0.25 * dy)
                        dr.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=fg)
            elif c.strip():
                dr.text((X, Y + ch * 0.5), c, font=bold if b else reg, fill=fg, anchor="lm")
    im.save(out(dest) if not os.path.isabs(dest) else dest)

BANNERS = [("mark", 16), ("mark", 24), ("horizontal", 48), ("horizontal", 72), ("horizontal", 96), ("stacked", 40)]   # (piece, columns wide)

def build_software():
    D = f"{KIT}/software"; G = "Software"
    t = TERM
    # Windows Terminal
    wt = {"name": "FusionSpace", "background": t["background"], "foreground": t["foreground"], "cursorColor": t["cursor"], "selectionBackground": t["selection"]}
    for k in ("black", "red", "green", "yellow", "blue", "white", "cyan"): wt[k] = t[k]
    wt["purple"] = t["magenta"]; wt["brightPurple"] = t["brightMagenta"]
    for k in ("brightBlack", "brightRed", "brightGreen", "brightYellow", "brightBlue", "brightWhite", "brightCyan"): wt[k] = t[k]
    build.wr(f"{D}/terminal/windows-terminal.json", json.dumps(wt, indent=2) + "\n")
    # iTerm2
    def it_color(h):
        r, g, b = hex2rgb(h)
        return ("<dict><key>Color Space</key><string>sRGB</string>"
                f"<key>Red Component</key><real>{r / 255:.6f}</real><key>Green Component</key><real>{g / 255:.6f}</real>"
                f"<key>Blue Component</key><real>{b / 255:.6f}</real><key>Alpha Component</key><real>1</real></dict>")
    order = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "brightBlack", "brightRed", "brightGreen", "brightYellow",
             "brightBlue", "brightMagenta", "brightCyan", "brightWhite"]
    items = [(f"Ansi {i} Color", t[k]) for i, k in enumerate(order)] + [("Background Color", t["background"]), ("Foreground Color", t["foreground"]),
             ("Cursor Color", t["cursor"]), ("Selection Color", t["selection"]), ("Bold Color", "#FFFFFF"), ("Link Color", t["blue"])]
    build.wr(f"{D}/terminal/FusionSpace.itermcolors", '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
             '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0"><dict>\n'
             + "\n".join(f"<key>{k}</key>{it_color(v)}" for k, v in items) + "\n</dict></plist>\n")
    # Alacritty, kitty, Ghostty, VS Code terminal
    norm = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
    build.wr(f"{D}/terminal/alacritty.toml", "# FusionSpace\n[colors.primary]\n" + f'background = "{t["background"]}"\nforeground = "{t["foreground"]}"\n'
             + "[colors.cursor]\n" + f'cursor = "{t["cursor"]}"\n' + "[colors.selection]\n" + f'background = "{t["selection"]}"\n'
             + "[colors.normal]\n" + "".join(f'{k} = "{t[k]}"\n' for k in norm)
             + "[colors.bright]\n" + "".join(f'{k} = "{t["bright" + k.capitalize()]}"\n' for k in norm))
    build.wr(f"{D}/terminal/kitty.conf", "# FusionSpace\n" + f"background {t['background']}\nforeground {t['foreground']}\ncursor {t['cursor']}\nselection_background {t['selection']}\n"
             + "".join(f"color{i} {t[k]}\n" for i, k in enumerate(order)))
    build.wr(f"{D}/terminal/ghostty", "# FusionSpace (save as ~/.config/ghostty/themes/FusionSpace)\n" + f"background = {t['background']}\nforeground = {t['foreground']}\n"
             f"cursor-color = {t['cursor']}\nselection-background = {t['selection']}\n" + "".join(f"palette = {i}={t[k]}\n" for i, k in enumerate(order)))
    vs = {"terminal.background": t["background"], "terminal.foreground": t["foreground"], "terminalCursor.foreground": t["cursor"],
          "terminal.selectionBackground": t["selection"]}
    vs.update({f"terminal.ansi{k[0].upper()}{k[1:]}": t[k] for k in order})
    build.wr(f"{D}/terminal/vscode-settings.json", json.dumps({"workbench.colorCustomizations": vs}, indent=2) + "\n")
    # preview of the scheme
    rows = []
    for i, k in enumerate(order):
        x = 40 + (i % 8) * 110; y = 120 + (i // 8) * 90
        rows.append(f'<rect x="{x}" y="{y}" width="96" height="56" rx="6" fill="{t[k]}"/>' + f'<text x="{x}" y="{y + 76}" fill="{HAZE}" font-family="Cascadia Mono" font-size="13">{k}</text>')
    prev = plain_svg(940, 330, f'<text x="40" y="70" fill="{t["foreground"]}" font-family="Cascadia Mono" font-size="22">FusionSpace terminal <tspan fill="{O_BLUE}">~/vega</tspan> <tspan fill="{t["green"]}">$</tspan> make flash</text>' + "".join(rows), bg=VOID)
    save_svg(f"{D}/terminal/preview.svg", prev); png(out(f"{D}/terminal/preview.svg"), f"{D}/terminal/preview.png", 940, 330); os.remove(out(f"{D}/terminal/preview.svg"))
    # banners
    banners = {}
    for piece, cols in BANNERS:
        plain, ansi = braille(piece, cols)
        build.wr(f"{D}/banner/{piece}-{cols}.txt", "\n".join(plain) + "\n")
        build.wr(f"{D}/banner/{piece}-{cols}.ans", "\n".join(ansi) + "\n")
        banners[(piece, cols)] = (plain, ansi)
    wide = sorted((c for p, c in BANNERS if p == "horizontal"), reverse=True)
    py_banners = ",\n".join(f"    {c}: ({json.dumps(chr(10).join(banners[('horizontal', c)][0]))},\n        {json.dumps(chr(10).join(banners[('horizontal', c)][1]))})" for c in wide)
    mk = banners[("mark", 16)]
    blue = ";".join(str(v) for v in hex2rgb(O_BLUE))
    build.wr(f"{D}/banner/cli_banner.py", f'''"""FusionSpace CLI banner: the logo for a terminal program's start-up or --version output.

    from cli_banner import banner
    banner()            # the widest logo that fits the terminal ({", ".join(str(c) for c in wide)} columns), then the tagline

Color when stdout is a terminal: 24-bit where the terminal says it supports it (COLORTERM=truecolor or 24bit, Windows
Terminal), otherwise the nearest 256-color codes. NO_COLOR turns color off, FORCE_COLOR turns it on. Under {min(wide)} columns
it prints the mark alone ({len(mk[0][0])} columns) and the name as text. Needs a font with braille (most have it, or the terminal borrows it).
"""
import os, re, shutil, sys

NAME = "FusionSpace"
TAGLINE = "{TAGLINE}"
BANNERS = {{  # columns: (plain, 24-bit ANSI)
{py_banners},
}}
MARK = ({json.dumps(chr(10).join(mk[0]))},
        {json.dumps(chr(10).join(mk[1]))})
BLUE = "\\x1b[38;2;{blue}m"

def _to256(m):
    r, g, b = (int(v) for v in m.groups())
    q = lambda v: 0 if v < 48 else 1 if v < 115 else (v - 35) // 40
    lv = [0, 95, 135, 175, 215, 255]
    cube = (lv[q(r)], lv[q(g)], lv[q(b)]); k = min(23, max(0, (r + g + b) // 3 - 3) // 10); gray = 8 + 10 * k
    d = lambda c: sum((u - v) ** 2 for u, v in zip(c, (r, g, b)))
    return f"\\x1b[38;5;{{232 + k if d((gray,) * 3) < d(cube) else 16 + 36 * q(r) + 6 * q(g) + q(b)}}m"

def banner(tagline=TAGLINE, file=None):
    out = file or sys.stdout
    try: out.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError): pass
    color = bool(os.environ.get("FORCE_COLOR")) or (out.isatty() and not os.environ.get("NO_COLOR"))
    if color and os.name == "nt": os.system("")          # turns on ANSI escapes in the Windows console
    truecolor = os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit") or "WT_SESSION" in os.environ
    cols = shutil.get_terminal_size((80, 24)).columns
    fit = [c for c in BANNERS if c <= cols]
    plain, ansi = BANNERS[max(fit)] if fit else MARK
    text = ansi if color else plain
    if not fit: text += "\\n" + ("\\x1b[1m" + NAME + "\\x1b[0m" if color else NAME)
    if tagline: text += "\\n" + (BLUE + tagline + "\\x1b[0m" if color else tagline)
    if color and not truecolor: text = re.sub(r"\\x1b\\[38;2;(\\d+);(\\d+);(\\d+)m", _to256, text)
    print(text, file=out)

if __name__ == "__main__":
    banner()
''')
    c_plain, c_ansi = banners[("horizontal", 72)]
    cesc = lambda ln: ln.replace("\x1b", "\\033")          # C: octal escape (a hex escape would swallow following hex digits)
    resc = lambda ln: ln.replace("\x1b", "\\u{1b}")        # Rust
    h_plain = "\n".join('    "' + ln + '\\n"' for ln in c_plain); h_ansi = "\n".join('    "' + cesc(ln) + '\\n"' for ln in c_ansi)
    r_plain = "\n".join('    "' + ln + '\\n",' for ln in c_plain); r_ansi = "\n".join('    "' + resc(ln) + '\\n",' for ln in c_ansi)
    build.wr(f"{D}/banner/cli_banner.h", f'''// FusionSpace CLI banner, 72 columns (UTF-8 braille; fits an 80-column terminal or serial console).
//   printf("%s", FS_BANNER);         plain
//   printf("%s", FS_BANNER_ANSI);    24-bit color
#pragma once
static const char FS_BANNER[] =
{h_plain};
static const char FS_BANNER_ANSI[] =
{h_ansi};
''')
    build.wr(f"{D}/banner/cli_banner.rs", f'''// FusionSpace CLI banner, 72 columns (UTF-8 braille; fits an 80-column terminal).
//   print!("{{}}", FS_BANNER);         plain
//   print!("{{}}", FS_BANNER_ANSI);    24-bit color
pub const FS_BANNER: &str = concat!(
{r_plain}
);
pub const FS_BANNER_ANSI: &str = concat!(
{r_ansi}
);
''')
    # ASCII-only fallback (for terminals without braille): the wordmark in a box
    build.wr(f"{D}/banner/ascii.txt", "+-----------------+\n|   FusionSpace   |\n+-----------------+\n" + f"  {TAGLINE}\n".replace("·", "-"))
    build.wr(f"{D}/README.md", f"""# FusionSpace for software projects

## Terminal color scheme
`terminal/`: Windows Terminal (`windows-terminal.json`, paste into `schemes`), iTerm2 (`FusionSpace.itermcolors`, double-click),
Alacritty (`alacritty.toml`, import it), kitty (`kitty.conf`, `include` it), Ghostty (`ghostty`), VS Code integrated terminal
(`vscode-settings.json`). Background Void, blue O, yellow M orange; red, green and cyan are terminal-only additions picked to sit
with the palette. Preview: `terminal/preview.png`.

## CLI banners
`banner/`: the logo as braille text art in the Fusion gradient: the mark alone (`mark-16`, `mark-24`: 16 and 24 columns wide),
the horizontal lockup (`horizontal-48`, `horizontal-72`, `horizontal-96`: 48, 72 and 96 columns; 72 fits an 80-column terminal)
and the stacked lockup (`stacked-40`), plain (`.txt`) and with 24-bit color (`.ans`, `cat` it). The name is drawn too, at the
lockup's own proportions, so the banner is the logo, not the mark next to a line of text. The art pads with the empty braille
cell (U+2800), so rows stay aligned even where the font has no braille and the terminal borrows it from another font.
To print it from a program: `cli_banner.py` (`from cli_banner import banner; banner()`: picks the widest banner that fits,
color on a terminal with a 256-color fallback, honors `NO_COLOR` and `FORCE_COLOR`), `cli_banner.h` (C/C++) and
`cli_banner.rs` (Rust) with the 72-column banner plain and in color (`FS_BANNER`, `FS_BANNER_ANSI`), `ascii.txt` (pure ASCII
fallback). Use them for `--version` output, firmware serial-console boot messages, or tool start-up.

## Docs sites
Colors: `color/fusion-space-tokens.css`. Icons: `kit/web/`. Fonts: Cascadia Mono (code, headings), Archivo (body).
""")
    note(f"{D}/terminal/", G, "terminal color schemes: Windows Terminal, iTerm2, Alacritty, kitty, Ghostty, VS Code terminal", "", "Your terminal, screenshots, demos")
    note(f"{D}/banner/", G, "CLI banners: the mark and both lockups as braille text art (plain and 24-bit ANSI) at 16–96 columns, Python/C/Rust snippets, ASCII fallback", "", "--version output, serial consoles, tool start-up")

# ================================================================ games
STEAM = [("header-capsule", 920, 430), ("small-capsule", 462, 174), ("main-capsule", 1232, 706), ("vertical-capsule", 748, 896),
         ("library-capsule", 600, 900), ("library-header", 920, 430)]
def game_card(w, h, title="Game Title", studio=False):
    """Game art template. Steam capsules (studio=False) carry the game's title and art only: Steamworks asks for no text
    beyond the title, and for the small capsule a title that nearly fills it. itch.io covers (studio=True) also carry the
    studio lockup and a "A FUSIONSPACE GAME" line."""
    bdefs, bg = background(w, h, True, "gc", cell=min(w, h) / 6, strip="bottom", strip_h=max(3, h / 70))
    m = art_mark(200); km = 0.55 * min(w, h) / max(m.w, m.h)
    mdefs, mg = m.place("white", "gm", w - m.w * km - 0.06 * w, h - m.h * km - 0.1 * h, km)
    mx = 0.07 * min(w, h) if w / h < 2 else 0.05 * w                    # left margin
    adv = 0.6 * len(title)                                              # Cascadia Mono advance (em) of the title
    small = h < 200
    size = min((0.86 if small else 0.62 if w > h else 0.8) * (w - 2 * mx) / adv * (1 if small else 1), (0.42 if small else 0.16) * h)
    base = h * (0.5 + 0.35 * size / h) if small else h * (0.6 if w > h else 0.62)
    s = svg_open(w, h, f"{title} · {w} x {h} template", page=VOID)
    defs = bdefs + mdefs; brand = f'<g opacity="0.06">{mg}</g>\n'
    txt = text(mx, base, title, size, PAPER, weight=600, label="Game title (edit me)")
    if studio:
        a = art_horizontal(); k = min(0.16 * h, 0.36 * w * a.h / a.w) / a.h; k = min(k, 0.3 * w / a.w)
        ldefs, lg = a.place("color", "gl", mx, mx, k); defs += ldefs; brand = lg + brand
        txt += text(mx + 2, base + size * 0.75, "A FUSIONSPACE GAME", max(10, size * 0.22), O_BLUE, label="Subtitle", spacing=size * 0.02)
    s += f'<defs id="defs">{defs}</defs>\n' + bg + layer("Brand", brand) + layer("Text (edit me)", txt)
    return s + "</svg>\n"

def splash(w, h, dark=True):
    t = theme(dark)
    a = art_stacked(); k = 0.36 * h / a.h
    defs, g = a.place("color", "sp", (w - a.w * k) / 2, (h - a.h * k) / 2 - 0.03 * h, k)
    bdefs, bg = background(w, h, dark, "sb", cell=h / 9, strip="bottom", strip_h=h / 90, grid=False)
    s = svg_open(w, h, "FusionSpace splash", page=t["bg"]) + f'<defs id="defs">{bdefs}{defs}</defs>\n' + bg + layer("Brand", g + "\n")
    return s + "</svg>\n"

def build_games():
    D = f"{KIT}/games"; G = "Games"
    for (w, h) in ((1920, 1080), (3840, 2160), (1280, 720)):
        for dark in (True, False):
            tone = "dark" if dark else "light"
            src = save_svg(f"{D}/splash/splash-{w}x{h}-{tone}.svg", splash(w, h, dark)); png(src, f"{D}/splash/splash-{w}x{h}-{tone}.png", w, h)
    for name, w, h in STEAM:
        src = save_svg(f"{D}/steam/{name}-{w}x{h}.svg", game_card(w, h)); png(src, f"{D}/steam/{name}-{w}x{h}.png", w, h)
    # library hero: background only (Steam asks for no text or logos), library logo: transparent title placeholder
    bdefs, bg = background(3840, 1240, True, "lh", cell=1240 / 6, strip=None)
    m = art_mark(200); km = 1.1 * 1240 / m.h
    mdefs, mg = m.place("white", "lhm", 3840 * 0.62, -0.12 * 1240, km)
    s = svg_open(3840, 1240, "Library hero background", page=VOID) + f'<defs id="defs">{bdefs}{mdefs}</defs>\n' + bg + layer("Brand", f'<g opacity="0.05">{mg}</g>\n') + "</svg>\n"
    src = save_svg(f"{D}/steam/library-hero-3840x1240.svg", s); png(src, f"{D}/steam/library-hero-3840x1240.png", 3840, 1240)
    # store page background (optional): ambient, low contrast, so it doesn't compete with the page
    bdefs, bg = background(1438, 810, True, "pb", cell=810 / 6, strip=None)
    km = 0.95 * 810 / m.h; mdefs, mg = m.place("white", "pbm", 1438 * 0.55, 0.02 * 810, km)
    s = svg_open(1438, 810, "Store page background", page=VOID) + f'<defs id="defs">{bdefs}{mdefs}</defs>\n' + bg + layer("Brand", f'<g opacity="0.04">{mg}</g>\n') + "</svg>\n"
    src = save_svg(f"{D}/steam/page-background-1438x810.svg", s); png(src, f"{D}/steam/page-background-1438x810.png", 1438, 810)
    s = svg_open(1280, 720, "Library logo (title placeholder, transparent)", page=VOID) + layer("Text (edit me)", text(640, 400, "Game Title", 150, PAPER, weight=600, anchor="middle", label="Game title (edit me)")) + "</svg>\n"
    src = save_svg(f"{D}/steam/library-logo-1280x720.svg", s); png(src, f"{D}/steam/library-logo-1280x720.png", 1280, 720)
    for name, w, h in (("itch-cover", 630, 500), ("itch-cover@2x", 1260, 1000)):
        src = save_svg(f"{D}/itch/{name}.svg", game_card(w, h, studio=True)); png(src, f"{D}/itch/{name}.png", w, h)
    a = art_mark(200)                                         # app/shortcut icons from the web set
    shutil.copy(out(f"{KIT}/web/icon-256.png"), out(f"{D}/steam/shortcut-icon-256.png"))
    # community/app icon: square and full bleed (a JPG has no transparency, so the rounded tile would get black corners)
    img = Image.open(out(f"{KIT}/web/icon-maskable-512.png")).convert("RGB").resize((184, 184), Image.LANCZOS); img.save(out(f"{D}/steam/app-icon-184.jpg"), quality=92)
    build.wr(f"{D}/README.md", """# FusionSpace for games

- `splash/`: studio splash screens (stacked lockup) at 1280×720, 1920×1080 and 3840×2160, dark and light. Show for 2–3 s at start-up,
  or use the animated version in `kit/video/`.
- `steam/`: templates at the current Steamworks sizes (checked October 2026: header 920×430, small 462×174, main 1232×706,
  vertical 748×896, optional page background 1438×810; library capsule 600×900, library header 920×430, library hero 3840×1240,
  transparent library logo 1280×720). Each has a "Game title (edit me)" text layer. Steam allows only the game's title on capsules
  (no studio logo, taglines or quotes) and wants the title to nearly fill the small capsule, so the templates carry just the title
  and a faint mark. Put key art on the Background layer. Keep anything important in the hero's center (Steam crops it). `shortcut-icon-256.png` and `app-icon-184.jpg` are ready as-is.
- `itch/`: itch.io cover template (630×500, and 2×).
- Engines: use `kit/logo/png/` for in-game logos (transparent PNG at many sizes) and `kit/web/icon-*.png` for app icons.
""")
    note(f"{D}/splash/", G, "studio splash screens (stacked lockup)", "1280×720, 1920×1080, 3840×2160; dark, light", "Game start-up, engine splash")
    note(f"{D}/steam/", G, "Steam store and library templates (edit the title), shortcut and app icons", "920×430, 462×174, 1232×706, 748×896, 1438×810, 600×900, 3840×1240, 1280×720", "Steamworks")
    note(f"{D}/itch/", G, "itch.io cover template", "630×500 (+2×)", "itch.io")

# ================================================================ video
def build_video():
    D = f"{KIT}/video"; G = "Video"
    os.makedirs(out(D), exist_ok=True)
    # YouTube branding watermark: 150 × 150, transparent
    a = art_mark(200); defs, g = fit(a, 600, 600, 0.86, "white")
    src = save_svg(f"{D}/youtube-watermark.svg", plain_svg(600, 600, g, defs)); png(src, f"{D}/youtube-watermark-150.png", 150, 150)
    png(src, f"{D}/youtube-watermark-600.png", 600, 600); os.remove(src)
    note(f"{D}/youtube-watermark-150.png", G, "white mark, transparent", "150 × 150 (and 600)", "YouTube branding watermark, video corner bug")
    if not shutil.which("ffmpeg"):
        WARN.append("ffmpeg"); print("WARN kit: ffmpeg not found, logo animation skipped"); return
    import tempfile
    W, H, FPS = 1920, 1080, 30
    st = art_stacked(); k = 0.36 * H / st.h; ox, oy = (W - st.w * k) / 2, (H - st.h * k) / 2
    mf, wf, _ = build.mode_fills("color", "url(#mg)", "url(#wg)")
    defs = gradient("mg", st.mark_bb[0], st.mark_bb[2]) + gradient("wg", st.wm_bb[0], st.wm_bb[2])
    order = {"south": 0, "west": 1, "east": 2, "main": 3}
    ang = math.radians(geo.TILT); ux, uy = math.sin(ang), -math.cos(ang)          # flight direction (up the leaned axis)
    ease = lambda x: 1 - (1 - max(0.0, min(1.0, x))) ** 3
    N = int(3.6 * FPS)
    tmp = tempfile.mkdtemp(prefix="fs-anim-")
    for alpha in (False, True):
        for i in range(N):
            tt = i / FPS; parts = []
            for d, role, cone in st.parts:
                if role == "mark":
                    p = ease((tt - 0.15 - 0.16 * order[cone]) / 0.9)
                    dist = (1 - p) * 0.55 * H
                    parts.append(f'<g opacity="{p:.3f}" transform="translate({-ux * dist:.2f} {-uy * dist:.2f})"><path fill="{mf}" d="{d}"/></g>')
                else:
                    p = ease((tt - 1.5) / 0.8)
                    parts.append(f'<g opacity="{p:.3f}" transform="translate(0 {(1 - p) * 18:.2f})"><path fill="{wf}" d="{d}"/></g>')
            body = f'<g transform="translate({ox:.2f} {oy:.2f}) scale({k:.5f})">{"".join(parts)}</g>'
            sp = 1 if tt > 2.3 else 0
            strip = f'<rect x="0" y="{H - 12}" width="{W * ease((tt - 2.2) / 0.8):.1f}" height="12" fill="url(#sg)"/>' if not alpha else ""
            svg = plain_svg(W, H, body + strip, defs + gradient("sg", 0, W), bg=None if alpha else VOID)
            open(f"{tmp}/f.svg", "w").write(svg)
            subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), f"{tmp}/f.svg", "-o", f"{tmp}/{'a' if alpha else 'o'}{i:04d}.png"], check=True)
        hold = 1.2
    q = ["-hide_banner", "-loglevel", "error", "-y"]
    subprocess.run(["ffmpeg", *q, "-framerate", str(FPS), "-i", f"{tmp}/o%04d.png", "-vf", f"tpad=stop_mode=clone:stop_duration={hold}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", out(f"{D}/logo-intro-1080p.mp4")], check=True)
    subprocess.run(["ffmpeg", *q, "-framerate", str(FPS), "-i", f"{tmp}/o%04d.png", "-vf", f"tpad=stop_mode=clone:stop_duration={hold}",
                    "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32", "-fflags", "+bitexact", out(f"{D}/logo-intro-1080p.webm")], check=True)
    subprocess.run(["ffmpeg", *q, "-framerate", str(FPS), "-i", f"{tmp}/a%04d.png", "-vf", f"tpad=stop_mode=clone:stop_duration={hold}",
                    "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "30", "-fflags", "+bitexact", out(f"{D}/logo-intro-alpha.webm")], check=True)
    subprocess.run(["ffmpeg", *q, "-framerate", str(FPS), "-i", f"{tmp}/o%04d.png", "-vf",
                    f"tpad=stop_mode=clone:stop_duration={hold},fps=20,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4",
                    out(f"{D}/logo-intro-640.gif")], check=True)
    Image.open(f"{tmp}/o{N - 1:04d}.png").save(out(f"{D}/logo-intro-last-frame.png"))
    shutil.rmtree(tmp)
    note(f"{D}/logo-intro-1080p.mp4 / .webm", G, "logo animation: the four cones fly in along the 45° lean, then the wordmark and strip", f"1920 × 1080, {N / FPS + 1.2:.1f} s",
         "Video intros and outros, talks, game splash")
    note(f"{D}/logo-intro-alpha.webm", G, "same animation with a transparent background (VP9 alpha)", "1920 × 1080", "Overlay in video editors (DaVinci, Premiere, OBS)")
    note(f"{D}/logo-intro-640.gif", G, "animated GIF", "640 wide", "READMEs, chat, slides")

# ================================================================ wallpapers and call backgrounds
# Checked Oct 2, 2026: iPhone 17 / 17 Pro 1206 x 2622, iPhone 17 Pro Max 1320 x 2868 (iOS scales a wallpaper to other models),
# iPad Pro 13" (M4/M5) 2064 x 2752, MacBook Air 13" 2560 x 1664, MacBook Pro 14"/16" 3024 x 1964 / 3456 x 2234.
WALL = [("desktop-2560x1440", 2560, 1440), ("desktop-3840x2160", 3840, 2160), ("desktop-5120x2880", 5120, 2880), ("ultrawide-3440x1440", 3440, 1440),
        ("macbook-air-2560x1664", 2560, 1664), ("macbook-3024x1964", 3024, 1964), ("macbook-3456x2234", 3456, 2234),
        ("phone-1320x2868", 1320, 2868), ("phone-1206x2622", 1206, 2622), ("phone-1440x3200", 1440, 3200), ("tablet-2064x2752", 2064, 2752)]
def wallpaper(w, h, dark):
    t = theme(dark); u = min(w, h)
    bdefs, bg = background(w, h, dark, "wp", cell=u / 8, strip="bottom", strip_h=u / 180)
    m = art_mark(200); km = (0.42 if w > h else 0.55) * u / max(m.w, m.h)
    cx = w * (0.5 if h > w else 0.5); cy = h * (0.44 if h > w else 0.48)
    mdefs, mg = m.place(t["mode"], "wpm", cx - m.w * km / 2, cy - m.h * km / 2, km)
    s = svg_open(w, h, "FusionSpace wallpaper", page=t["bg"]) + f'<defs id="defs">{bdefs}{mdefs}</defs>\n' + bg + layer("Brand", mg + "\n")
    s += layer("Text", text(w / 2, h - u * 0.06, TAGLINE.upper(), u * 0.018, t["muted"], anchor="middle", label="Tagline", spacing=u * 0.003))
    return s + "</svg>\n"

def call_bg(w, h, dark):
    t = theme(dark)
    bdefs, bg = background(w, h, dark, "cb", cell=h / 9, strip="bottom", strip_h=h / 120)
    a = art_horizontal(); k = 0.065 * h / a.h
    ldefs, lg = a.place(t["mode"], "cbl", w - a.w * k - 0.04 * w, 0.06 * h, k)
    s = svg_open(w, h, "FusionSpace video-call background", page=t["bg"]) + f'<defs id="defs">{bdefs}{ldefs}</defs>\n' + bg + layer("Brand", lg + "\n")
    return s + "</svg>\n"

def build_wallpapers():
    D = f"{KIT}/wallpapers"; G = "Wallpapers & backgrounds"
    for name, w, h in WALL:
        for dark in (True, False):
            tone = "dark" if dark else "light"
            src = save_svg(f"{D}/{name}-{tone}.svg", wallpaper(w, h, dark)); png(src, f"{D}/{name}-{tone}.png", w, h); os.remove(src)
    for dark in (True, False):
        tone = "dark" if dark else "light"
        src = save_svg(f"{D}/call-background-1920x1080-{tone}.svg", call_bg(1920, 1080, dark)); png(src, f"{D}/call-background-1920x1080-{tone}.png", 1920, 1080); os.remove(src)
    note(f"{D}/{{desktop,ultrawide,macbook,macbook-air,phone,tablet}}-*-{{dark,light}}.png", G, "wallpapers", ", ".join(f"{w}×{h}" for _, w, h in WALL), "Desktop, laptop, phone, tablet lock and home screens")
    note(f"{D}/call-background-1920x1080-{{dark,light}}.png", G, "video-call background, logo top right (mirrored views flip it)", "1920 × 1080", "Zoom, Teams, Meet")

# ================================================================ merch and posters
MERCH_MARGIN_IN = 0.1   # transparent margin around apparel art (design review: the mark's tip touched the top right edge)

def build_merch():
    D = f"{KIT}/merch"; G = "Merch & print"
    DPI = 300
    jobs = [("tshirt-front-chest", "mark", 4.0, None), ("tshirt-front-center", "stacked", 10.0, None), ("tshirt-back", "stacked", 12.0, None),
            ("hoodie-front", "horizontal", 10.0, None), ("cap-front", "mark", 2.5, None)]
    for name, piece, width_in, _ in jobs:
        a = PIECES[piece]()
        for mode in ("color", "white", "void", "twotone-on-dark", "twotone-on-light"):
            wp = int(width_in * DPI); hp = int(wp * a.h / a.w); mg = int(MERCH_MARGIN_IN * DPI)
            defs, g = a.place(mode, "mc", mg, mg, wp / a.w)
            src = save_svg(f"{D}/{name}-{mode}.svg", plain_svg(wp + 2 * mg, hp + 2 * mg, g, defs))
            png(src, f"{D}/{name}-{mode}-{width_in:g}in-300dpi.png", wp + 2 * mg, hp + 2 * mg)
            Image.open(out(f"{D}/{name}-{mode}-{width_in:g}in-300dpi.png")).save(out(f"{D}/{name}-{mode}-{width_in:g}in-300dpi.png"), dpi=(DPI, DPI))
            os.remove(src)
    note(f"{D}/{{tshirt,hoodie,cap}}-*-{{mode}}-*in-300dpi.png", G, "apparel print files, transparent, 300 dpi, every color mode (white or twotone-on-dark for dark garments)",
         f"art width: chest 4 in, front 10 in, back 12 in, hoodie 10 in, cap 2.5 in, plus {MERCH_MARGIN_IN:g} in of transparent margin on every side", "Print-on-demand (DTG, DTF, screen print)")
    # 11 oz mug wrap: 8.5 x 3.5 in, logo on both sides
    W, H = int(8.5 * DPI), int(3.5 * DPI)
    for tone, bgc, mode in (("white", WHITE, "color"), ("dark", VOID, "color")):
        a = art_stacked(); k = min(0.62 * H / a.h, 0.4 * W / a.w)
        d1, g1 = a.place(mode, "m1", W * 0.25 - a.w * k / 2, (H - a.h * k) / 2, k)
        m = art_mark(200); km = 0.62 * H / m.h
        d2, g2 = m.place(mode, "m2", W * 0.75 - m.w * km / 2, (H - m.h * km) / 2, km)
        src = save_svg(f"{D}/mug-11oz-wrap-{tone}.svg", plain_svg(W, H, g1 + g2, d1 + d2, bg=bgc))
        png(src, f"{D}/mug-11oz-wrap-{tone}-300dpi.png", W, H); os.remove(src)
        Image.open(out(f"{D}/mug-11oz-wrap-{tone}-300dpi.png")).save(out(f"{D}/mug-11oz-wrap-{tone}-300dpi.png"), dpi=(300, 300))   # print shops read the DPI
    note(f"{D}/mug-11oz-wrap-{{white,dark}}-300dpi.png", G, "mug wrap: stacked lockup one side, mark the other", "8.5 × 3.5 in at 300 dpi", "11 oz mugs (print-on-demand)")
    # posters: construction drawing poster and a mark poster
    for (pname, wmm, hmm) in (("a3", 297, 420), ("a2", 420, 594), ("18x24in", 457.2, 609.6)):
        bdefs, bg = background(wmm, hmm, True, "po", cell=wmm / 12, strip="bottom", strip_h=hmm / 120)
        m = art_mark(200); km = 0.66 * wmm / m.w
        mdefs, mg = m.place("color", "pm", (wmm - m.w * km) / 2, hmm * 0.17, km)
        # the name alone under the big mark (Neer: not the logo twice, just the words), 0.3 × the poster
        # width, with the tagline under it
        w = kit.art_wordmark(); kw = 0.30 * wmm / w.w; ny = hmm * 0.79
        ldefs, lg = w.place("color", "pl", (wmm - w.w * kw) / 2, ny, kw)
        s = svg_open(wmm, hmm, f"FusionSpace poster ({pname})", units="mm", page=VOID) + f'<defs id="defs">{bdefs}{mdefs}{ldefs}</defs>\n' + bg
        s += layer("Brand", mg + lg + "\n")
        s += layer("Text (edit me)", text(wmm / 2, ny + w.h * kw + hmm * 0.035, TAGLINE.upper(), hmm * 0.012, O_BLUE, anchor="middle", label="Tagline", spacing=hmm * 0.002))
        s += "</svg>\n"
        src = save_svg(f"{D}/poster-mark-{pname}.svg", s); pdf(src, f"{D}/poster-mark-{pname}.pdf"); cmyk(f"{D}/poster-mark-{pname}.pdf", f"{D}/poster-mark-{pname}-cmyk.pdf")
        png(src, f"{D}/poster-mark-{pname}-preview.png", w=900)
        # construction poster: the construction drawing centered on Paper
        cons = open(out("graphics/mark-construction.svg"), encoding="utf-8").read()
        cw = float(re.search(r'width="([\d.]+)"', cons).group(1)); ch = float(re.search(r'height="([\d.]+)"', cons).group(1))
        inner = cons[cons.index(">", cons.index("<svg")) + 1:cons.rindex("</svg>")]
        inner = re.sub(r"<title>.*?</title>|<sodipodi:namedview.*?/>|<metadata>.*?</metadata>", "", inner, flags=re.S)
        sc = min(0.86 * wmm / cw, 0.78 * hmm / ch)
        a = art_horizontal(); k = 0.022 * hmm / a.h
        ldefs, lg = a.place("color", "cl", wmm * 0.07, hmm * 0.045, k)
        s = svg_open(wmm, hmm, f"FusionSpace construction poster ({pname})", units="mm", page=PAPER)
        s += f'<defs id="defs">{ldefs}</defs>\n<rect width="{f(wmm)}" height="{f(hmm)}" fill="{PAPER}"/>' + lg
        s += f'<g transform="translate({f((wmm - cw * sc) / 2)} {f(max(hmm * 0.12, (hmm - ch * sc) / 2))}) scale({sc:.6f})">{inner}</g>\n'
        s += text(wmm * 0.93, hmm * 0.045 + 0.022 * hmm * 0.75, "MARK CONSTRUCTION · REV C", hmm * 0.011, SLATE, anchor="end", label="Title", spacing=hmm * 0.001) + "</svg>\n"
        src = save_svg(f"{D}/poster-construction-{pname}.svg", s); pdf(src, f"{D}/poster-construction-{pname}.pdf"); cmyk(f"{D}/poster-construction-{pname}.pdf", f"{D}/poster-construction-{pname}-cmyk.pdf")
        png(src, f"{D}/poster-construction-{pname}-preview.png", w=900)
    note(f"{D}/poster-{{mark,construction}}-{{a3,a2,18x24in}}.pdf", G, "posters: big mark on Void with the name and tagline under it, and the construction drawing on Paper", "A3, A2, 18 × 24 in", "Workshop, office, events; -cmyk.pdf for print shops")

# ================================================================ remove-before-flight tag (3D print and made-to-order)
RBF_RED = "#C8102E"          # the safety red every RBF tag uses (Pantone 186 C); the brand has no red, and this tag must read as one
RBF = dict(w=140.0, h=32.0, r=4.0, hole_x=9.0, hole_d=5.0, text_x0=17.0, text_x1=136.0, lockup_w=116.0)   # 5.5 × 1.25 in keychain size
RBF2 = dict(w=160.0, h=36.0, r=4.5, hole_x=10.0, hole_d=5.0, text_x0=19.0, text_x1=155.0, lockup_w=134.0)  # two-part print, same proportions
RBF_TEXT = "REMOVE BEFORE FLIGHT"
RBF_FONT = "Archivo-ExtraCondensedExtraBold.ttf"   # the brand's Archivo at its narrowest width (62) and weight 800, from the OFL variable font
RBF_STRETCH = 1.35           # drawn 1.35 × taller than wide, for the tall condensed lettering real tags have

def text_outline(s, font="Archivo-SemiBold.ttf", tracking=0.04, sy=1.0, word=0.0):
    """SVG path data for s in a brand font, in em units (1 = the font's em), y down, baseline at y = 0, starting at x = 0,
    sy × as tall as the font draws it, word em added to each space. Returns (d, width, cap height)."""
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    ft = TTFont(os.path.join(build.ROOT, "type", "fonts", font)); gs = ft.getGlyphSet(); cmap = ft.getBestCmap()
    upm = ft["head"].unitsPerEm; cap = ft["OS/2"].sCapHeight / upm * sy
    x = 0.0; d = ""
    for ch in s:
        g = cmap[ord(ch)]
        pen = SVGPathPen(gs); gs[g].draw(TransformPen(pen, (1 / upm, 0, 0, -sy / upm, x, 0)))
        d += pen.getCommands() + " "
        x += gs[g].width / upm + (tracking if ch != " " else word)
    return d.strip(), x - tracking, cap

def rbf_layout(s=RBF):
    """REMOVE BEFORE FLIGHT filling the text area of tag s: (d in em, mm per em, x, baseline y (y down), cap height mm)."""
    d, w, cap = text_outline(RBF_TEXT, RBF_FONT, tracking=0.03, sy=RBF_STRETCH, word=0.12)   # wider word gaps, as on real tags
    k = (s["text_x1"] - s["text_x0"]) / w
    return d, k, s["text_x0"], s["h"] / 2 + cap * k / 2, cap * k

def _rbf_text_poly(s):
    from shapely import affinity
    d, k, tx, ty, _ = rbf_layout(s)
    return affinity.translate(affinity.scale(kit_cad.nonzero_region(d), k, -k, origin=(0, 0)), tx, s["h"] - ty)   # y up

def _rbf_lockup(s, z0, z1):
    """The horizontal lockup centered in the tag's text area, y up: layers (exact cones, the name)."""
    lx = s["text_x0"] + (s["text_x1"] - s["text_x0"] - s["lockup_w"]) / 2
    a = art_horizontal(); lh = a.h * s["lockup_w"] / a.w
    lay, _, _ = piece_layers("horizontal", z0, z1, width=s["lockup_w"], dx=lx, dy=(s["h"] - lh) / 2)
    return lay

def build_rbf():
    """Remove-before-flight tag: prints (kit/3d-print) and art to have it made (kit/production/remove-before-flight)."""
    from shapely import affinity
    from shapely.geometry import Point
    from shapely.ops import unary_union
    s = RBF; d, k, tx, ty, capmm = rbf_layout(s)
    P = f"{KIT}/production/remove-before-flight"; os.makedirs(out(P), exist_ok=True); G = "Mechanical & fabrication"
    a = art_horizontal(); lk = s["lockup_w"] / a.w; lh = a.h * lk
    lx = s["text_x0"] + (s["text_x1"] - s["text_x0"] - s["lockup_w"]) / 2; ly = (s["h"] - lh) / 2
    def side(back, guides=True):
        W, H = s["w"], s["h"]
        body = f'<rect width="{f(W)}" height="{f(H)}" rx="{f(s["r"])}" fill="{RBF_RED}"/>'
        if back:
            defs, g = a.place("white", "rb", lx, ly, lk); body = f"<defs>{defs}</defs>" + body + g
        else:
            body += f'<path fill="#FFFFFF" d="{d}" transform="translate({f(tx)} {f(ty)}) scale({k:.6f})"/>'
        if guides:
            body += (f'<g id="grommet-not-printed"><circle cx="{f(s["hole_x"])}" cy="{f(H / 2)}" r="{f(s["hole_d"] / 2)}" fill="none" '
                     f'stroke="#9AA3B5" stroke-width="0.2" stroke-dasharray="0.6 0.4"/></g>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(W)}mm" height="{f(H)}mm" viewBox="0 0 {f(W)} {f(H)}">'
                f'<title>FusionSpace remove-before-flight tag, {"back" if back else "front"}, {f(W)} × {f(H)} mm</title>{body}</svg>\n')
    for nm, back in (("front", False), ("back", True)):
        base = f"{P}/remove-before-flight-140x32mm-{nm}"
        sv = save_svg(f"{base}.svg", side(back))
        pdf(sv, f"{base}.pdf"); cmyk(f"{base}.pdf", f"{base}-cmyk.pdf")
        png(sv, f"{base}.png", w=1400)
    fr = Image.open(out(f"{P}/remove-before-flight-140x32mm-front.png")).convert("RGBA"); bk = Image.open(out(f"{P}/remove-before-flight-140x32mm-back.png")).convert("RGBA")
    cv = Image.new("RGB", (1600, 2 * fr.height + 300), PAPER); cv.paste(fr, (100, 100), fr); cv.paste(bk, (100, fr.height + 200), bk)
    cv.save(out(f"{P}/remove-before-flight-140x32mm-preview.png"))
    build.wr(f"{P}/README.md", f"""# Remove-before-flight tag: files to have it made

The classic red streamer tag, FusionSpace version: **REMOVE BEFORE FLIGHT** on the front in tall condensed capitals, the
horizontal lockup on the back, both in white on safety red. For rocket arming pins, switch covers, payload bay keys, keychains.

| File | What |
|---|---|
| `remove-before-flight-140x32mm-front.svg` / `.pdf` / `-cmyk.pdf` / `.png` | front, 140 × 32 mm (5.5 × 1.25 in), text in outlines |
| `remove-before-flight-140x32mm-back.svg` / `.pdf` / `-cmyk.pdf` / `.png` | back, the horizontal lockup in white |
| `remove-before-flight-140x32mm-preview.png` | both sides |

The lettering is the brand's Archivo at its narrowest and boldest (ExtraCondensed ExtraBold, `type/fonts/`), drawn
{RBF_STRETCH:g} × taller, the tall condensed look of a real tag; capitals are {capmm:.1f} mm tall. It is outlined in the files, so the
maker needs no font.

## What to order

- **Woven tag, double-sided** (the usual “remove before flight keychain”): best at this size, the letters stay sharp.
  Embroidered also works (capitals {capmm:.1f} mm, well above the usual 5 mm minimum for embroidered text).
- Size 140 × 32 mm, corners as drawn (4 mm radius) or square with a merrowed (overlocked) edge, whichever the maker offers.
- Colors: red **Pantone 186 C** (`{RBF_RED}`), white. Two colors, no gradient. Give the vendor the PDFs (vector, text already
  outlined); the CMYK PDFs are for a printed (dye-sublimated) tag.
- A **5 mm metal grommet** at the left end, centered, 9 mm from the edge (dashed circle in the files, layer “grommet-not-printed”;
  it is not printed), and a 25 mm split ring.
- Printed tags: ask whether they want bleed; the red is a plain rectangle, so it can be extended without touching the art.

The 3D-print versions are in `kit/3d-print/`: `fusion-space-remove-before-flight-140mm` (one piece, the mark engraved on the
back) and `fusion-space-remove-before-flight-160mm-2part` (two halves glued back to back, the full logo raised on the back).
""")
    note(f"{P}/*", G, "remove-before-flight tag artwork (front text, back lockup, white on safety red) and what to order", "140 × 32 mm", "woven or embroidered tags, keychains")
    if not kit_cad.HAVE_OCC: return
    D = f"{KIT}/3d-print"; os.makedirs(out(D), exist_ok=True)
    import tempfile
    flip = lambda sh, h: kit_cad.transformed(sh, rot=((0, h / 2, 0.0), (1, 0, 0), 180.0))     # turned over its long edge
    def tag_poly(s): return _rrect(0, 0, s["w"], s["h"], s["r"]).difference(Point(s["hole_x"], s["h"] / 2).buffer(s["hole_d"] / 2 + 0.25, resolution=48))
    def preview(rows, dest, hs):
        """rows: [[(shape, color)]] stacked top to bottom, each drawn on its own and cropped to its height."""
        with tempfile.TemporaryDirectory() as td:
            ims = []
            for i, row in enumerate(rows):
                p = os.path.join(td, f"{i}.png")
                kit_cad.render_preview([(kit_cad.mesh_of(sh, 0.04, 0.2), c) for sh, c in row], p, elev=55.0); ims.append(Image.open(p))
            cv = Image.new("RGB", (900, 900), PAPER); band = 900 // len(ims)
            for i, im in enumerate(ims):
                cv.paste(im.crop((0, 450 - band // 2, 900, 450 + band // 2)), (0, i * band))
            cv.save(dest)
    # one piece: 2.0 mm tag, the text raised 0.8 mm, the mark engraved 0.6 mm into the back (the name's grooves would be 0.43 mm)
    fn = "fusion-space-remove-before-flight-140mm"
    tag = tag_poly(s); txt = _rbf_text_poly(s)
    mh = 26.0; mo, (mw, _) = kit_cad.mark_outlines(mh, kit_cad.FOOT_MM)
    mx = (s["text_x0"] + s["text_x1"]) / 2 - mw / 2; my = (s["h"] - mh) / 2
    # seen from the back after turning the tag over its long edge, (x, y) shows at (x, h - y): mirror the engraving that way
    eng = [o.moved(mx, my).affine(((1, 0), (0, -1)), (0, s["h"])) for o in mo]
    with kit_cad.fit_tolerance(0.005):
        plate = kit_cad.cut(kit_cad.prism(tag, 0, 2.0), kit_cad.prism(eng, -1, 0.6))
        text = kit_cad.prism(txt, 2.0, 2.8)
    probs = kit_cad.check_print(fn, txt) + kit_cad.check_print(fn + " (back)", tag.difference(unary_union([o.poly(40) for o in eng])))
    m_plate, m_text = kit_cad.mesh_of(plate, 0.05, 0.2), kit_cad.mesh_of(text, 0.05, 0.2)    # 0.05 mm: well under a layer, a third the file
    open(out(f"{D}/{fn}.stl"), "wb").write(kit_cad.stl_bytes([m_plate, m_text]))
    kit_cad.write_step_bodies([("tag, red", plate, RBF_RED), ("text, white", text, WHITE)], out(f"{D}/{fn}.step"), fn)
    kit_cad.write_3mf([("tag, red", m_plate, RBF_RED, 1), ("text, white", m_text, WHITE, 2)], out(f"{D}/{fn}.3mf"), fn)
    fill = flip(kit_cad.prism(eng, 0.05, 0.6), s["h"])                    # the engraving's floor shaded darker, so it shows
    preview([[(plate, RBF_RED), (text, "#F3F4F7")], [(flip(plate, s["h"]), RBF_RED), (fill, "#7A0A1C")]], out(f"{D}/{fn}-preview.png"), s["h"])
    # two parts: a front half and a back half, each printed face up (1.4 mm, the art raised 0.8 mm in white), glued back to back.
    # Two blind holes in each glue face take 1.75 mm filament as dowels (2.0 mm, 0.8 mm deep), so the halves line up.
    s2 = RBF2; fn2 = "fusion-space-remove-before-flight-160mm-2part"; tb, rel = 1.4, 0.8
    tag2 = tag_poly(s2); txt2 = _rbf_text_poly(s2)
    pins = [(s2["text_x0"] + 1.0, 5.0), (s2["w"] - 5.0, s2["h"] - 5.0)]                 # front half's glue face, as seen from below
    pins_back = [(x, s2["h"] - y) for x, y in pins]                                       # the back half's, mirrored over the long edge
    lay = _rbf_lockup(s2, tb, tb + rel)
    with kit_cad.fit_tolerance(0.005):
        holes = lambda ps: [kit_cad.cylinder(1.0, -1, 0.8, x, y) for x, y in ps]
        front = kit_cad.cut(kit_cad.prism(tag2, 0, tb), *holes(pins)); ftext = kit_cad.prism(txt2, tb, tb + rel)
        back = kit_cad.cut(kit_cad.prism(tag2, 0, tb), *holes(pins_back))
        bart = [(t_, sh) for t_, sh in _bodies_from_layers(lay)]
    probs += kit_cad.check_print(fn2 + " (front)", txt2) + kit_cad.check_print(fn2 + " (back)", unary_union([L.poly for L in lay]))
    if probs: raise ValueError("\n".join(probs))
    bart_shape = kit_cad.compound([sh for _, sh in bart])
    for suf, bodies in (("front", [(front, RBF_RED), (ftext, WHITE)]), ("back", [(back, RBF_RED), (bart_shape, WHITE)])):
        open(out(f"{D}/{fn2}-{suf}.stl"), "wb").write(kit_cad.stl_bytes([kit_cad.mesh_of(sh, 0.05, 0.2) for sh, _ in bodies]))
    # STEP: assembled (the back half turned over under the front half); 3MF: both halves on the plate, red + white each
    under = lambda sh: kit_cad.transformed(flip(sh, s2["h"]), move=(0, 0, 0))
    kit_cad.write_step_bodies([("front half, red", front, RBF_RED), ("front text, white", ftext, WHITE),
                               ("back half, red", under(back), RBF_RED), ("back logo, white", under(bart_shape), WHITE)], out(f"{D}/{fn2}.step"), fn2)
    kit_cad.write_3mf(None, out(f"{D}/{fn2}.3mf"), fn2, objects=[
        [("front: half, red", kit_cad.mesh_of(front, 0.05, 0.2), RBF_RED, 1), ("front: text, white", kit_cad.mesh_of(ftext, 0.05, 0.2), WHITE, 2)],
        [("back: half, red", kit_cad.mesh_of(back, 0.05, 0.2), RBF_RED, 1), ("back: logo, white", kit_cad.mesh_of(bart_shape, 0.05, 0.2), WHITE, 2)]])
    preview([[(front, RBF_RED), (ftext, "#F3F4F7")], [(back, RBF_RED), (bart_shape, "#F3F4F7")]], out(f"{D}/{fn2}-preview.png"), s2["h"])

def build_targets():
    build_embedded(); build_pcb(); build_3d(); build_rbf(); build_software(); build_games(); build_video(); build_wallpapers(); build_merch()
