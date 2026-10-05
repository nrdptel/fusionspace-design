"""FusionSpace kit: rocket decal sheets (kit/production/rocket-decals/).

A4 sheets of decals sized for model and high-power rockets: horizontal lockups for body tubes, marks for fins and nose
cones. Three versions:
  print-and-cut-{dark,light}  color art on a Void or white backing, each piece with a CutContour line (Silhouette, Cricut,
                              Roland print-and-cut; or any sticker printer that takes a CutContour layer)
  vinyl-cut                   one color: the art's own outline is the cut line (plotter-cut vinyl, then weed), with a
                              weeding box around each piece. Feet are floored at VINYL_MIN_WALL so they don't tear.
Sizes are in DECALS; the lockup height is the mark height (the cap height is 0.6 of it).
"""
import os
import geo, build, kit
from kit import KIT, note, out, save_svg, png, pdf, cmyk, PIECES, polygons, f, VOID, WHITE, PAPER, theme, LIGHT_MODE

PAGE = (210.0, 297.0)          # A4 portrait, mm
MARGIN = 13.0                  # room for print-and-cut registration marks (Silhouette and Cricut need about 10-13 mm)
GAP = 4.0
VINYL_MIN_WALL = 0.4           # mm, narrowest foot on the vinyl sheet
# (piece, height mm, count, what for)
DECALS = [("horizontal", 25, 1, "98 mm airframe"), ("horizontal", 20, 2, "75 mm airframe"), ("horizontal", 16, 2, "54 mm airframe"),
          ("horizontal", 12, 2, "38 mm airframe"), ("mark", 30, 4, "fins"), ("mark", 20, 4, "fins, nose cone"),
          ("mark", 15, 4, "small fins, rail buttons")]

def _shapes(piece, h, vinyl):
    """(w, h, art paths (d, fill-role, cone), union polygon) in mm, origin top left."""
    from shapely.ops import unary_union
    from shapely import affinity
    a = PIECES[piece](); k = h / a.h
    parts = []
    if vinyl:   # mark with floored feet, from the production geometry, scaled to the same height
        cl, A, bb = build.dxf_geometry(float(h), VINYL_MIN_WALL)
        parts += [(geo.seg_to_d(cl[n]), "mark", n, 1.0, 0.0) for n in geo.DRAW_ORDER]
        parts += [(d, role, cone, k, 0.0) for d, role, cone in a.parts if role != "mark"]
    else:
        parts += [(d, role, cone, k, 0.0) for d, role, cone in a.parts]
    polys = []
    for d, role, cone, s, _ in parts:
        polys += [affinity.scale(p, s, s, origin=(0, 0)) for p in polygons(d)]
    return a.w * k, h, parts, unary_union(polys), a, k

def _pack(items):
    """First-fit decreasing-height shelf packing: each piece goes on the first shelf with room, else on a new shelf.
    items: (w, h, payload). Returns [(x, y, payload)]; raises if the page overflows."""
    shelves = []                                         # [y, height, x_next]
    outp, y_next, avail, last = [], MARGIN, PAGE[0] - MARGIN, None
    for w, h, p in sorted(items, key=lambda t: (t[2][0] != "horizontal", -t[1], -t[0])):   # lockups first, then marks
        if p[0] != last: shelves, last = [], p[0]                                          # marks start on their own shelves
        sh = next((s_ for s_ in shelves if s_[2] + w <= avail + 1e-6 and h <= s_[1] + 1e-6), None)
        if sh is None:
            if y_next + h > PAGE[1] - MARGIN + 1e-6: raise ValueError("decal sheet overflows the page")
            sh = [y_next, h, MARGIN]; shelves.append(sh); y_next += h + GAP
        outp.append((sh[2], sh[0] + (sh[1] - h) / 2, p)); sh[2] += w + GAP
    return outp

def rings(g, dx, dy):
    """Path data for a (multi)polygon with its holes, offset by (dx, dy)."""
    out_ = ""
    for p in getattr(g, "geoms", [g]):
        for r in [p.exterior] + list(p.interiors):
            out_ += "M" + " L".join(f"{f(px + dx)},{f(py + dy)}" for px, py in list(r.coords)[:-1]) + " Z"
    return out_

def sheet(kind):
    """kind: print-dark | print-light | vinyl. Returns (svg, labels svg fragment for the preview)."""
    from shapely.geometry import box
    vinyl = kind == "vinyl"; dark = kind == "print-dark"
    items = []
    for piece, h, n, what in DECALS:
        w, hh, parts, U, a, k = _shapes(piece, float(h), vinyl)
        if vinyl:
            pad = 1.5; cut = box(-pad, -pad, w + pad, hh + pad)          # weeding box
        elif piece == "mark":
            R = kit.STICKER_CLOSE * hh; cut = U.buffer(R, resolution=32).buffer(-R, resolution=32).buffer(1.5, resolution=32)
        else:
            cut = box(*U.bounds).buffer(2.0, resolution=32)
        bx = cut.buffer(0 if vinyl else 1.0).bounds                     # footprint incl. 1 mm bleed
        for i in range(n):
            items.append((bx[2] - bx[0], bx[3] - bx[1], (piece, h, what, parts, U, cut, a, k, bx, i)))
    placed = _pack(items)
    W, H = PAGE
    title = {"print-dark": "print-and-cut, Void backing", "print-light": "print-and-cut, white backing", "vinyl": "one-color vinyl cut"}[kind]
    s = kit.svg_open(W, H, f"FusionSpace rocket decals, A4, {title}", units="mm", page=WHITE)
    defs, back, art, cutl, labels = "", "", "", "", ""
    for j, (x, y, (piece, h, what, parts, U, cut, a, k, bx, i)) in enumerate(placed):
        ox, oy = x - bx[0], y - bx[1]
        def ring(g, dx=ox, dy=oy):
            return "".join("M" + " L".join(f"{f(px + dx)},{f(py + dy)}" for px, py in p.exterior.coords) + " Z" for p in getattr(g, "geoms", [g]))
        if vinyl:
            # the mark cones as their exact curves; the wordmark as one merged outline per letter. The outlined wordmark is
            # built from overlapping contours, and cutting those would slice the letters into pieces (design review: the
            # preview showed them as slivers where the contours cross).
            art += "".join(f'<path class="art" d="{d}" transform="translate({f(ox)} {f(oy)}) scale({sc:.6f})" fill="none" stroke="#000000" stroke-width="{f(0.01 / sc)}"/>'
                           for d, role, cone, sc, _ in parts if role == "mark")
            wm = [(d, sc) for d, role, cone, sc, _ in parts if role != "mark"]
            if wm:
                from shapely.ops import unary_union
                from shapely import affinity
                import kit_cad                      # the area the wordmark fills (nonzero rule), so the counters stay open
                W_ = unary_union([affinity.scale(kit_cad.nonzero_region(d, 48), sc, sc, origin=(0, 0)) for d, sc in wm]).simplify(0.003)
                art += f'<path class="art" d="{rings(W_, ox, oy)}" fill="none" stroke="#000000" stroke-width="0.01"/>'

            cutl += f'<path d="{ring(cut)}" fill="none" stroke="#000000" stroke-width="0.01"/>'
        else:
            back += f'<path d="{ring(cut.buffer(1.0, resolution=32))}" fill="{VOID if dark else WHITE}"/>'
            d_, g_ = a.place("color" if dark else LIGHT_MODE, f"d{j}", ox, oy, k); defs += d_; art += g_
            cutl += f'<path d="{ring(cut)}" fill="none" stroke="#FF00FF" stroke-width="0.25"/>'
        if i == 0:
            labels += kit.text(x, y + (bx[3] - bx[1]) + 3.2, f"{h} mm · {what}", 2.4, "#566079", family="sans")
    s += f'<defs id="defs">{defs}</defs>\n'
    if vinyl:
        s += kit.layer("Cut (art outlines)", art + "\n") + kit.layer("Weeding boxes", cutl + "\n")
    else:
        s += kit.layer("Backing (print, 1 mm bleed)", back + "\n") + kit.layer("Art", art + "\n") + kit.layer("CutContour", cutl + "\n", lid="layer-CutContour")
    return s + "</svg>\n", labels

def build_decals():
    D = f"{KIT}/production/rocket-decals"; G = "Physical production"
    for kind, name in (("print-dark", "decal-sheet-a4-print-and-cut-dark"), ("print-light", "decal-sheet-a4-print-and-cut-light"), ("vinyl", "decal-sheet-a4-vinyl-cut")):
        svg, labels = sheet(kind)
        src = save_svg(f"{D}/{name}.svg", svg); pdf(src, f"{D}/{name}.pdf")
        if kind != "vinyl": cmyk(f"{D}/{name}.pdf", f"{D}/{name}-cmyk.pdf")
        # preview: the sheet with size labels (labels are not in the print/cut file), and the vinyl shown as cut Void vinyl
        pv = svg.replace("</svg>\n", f'<g>{labels}</g></svg>\n')
        if kind == "vinyl": pv = pv.replace('class="art" d=', f'fill-rule="evenodd" style="fill:{VOID}" d=')
        tmp = save_svg(f"{D}/.{name}-preview.svg", pv); png(tmp, f"{D}/{name}-preview.png", w=1240, bg="#FFFFFF"); os.remove(tmp)
    sizes = "; ".join(f"{h} mm ×{n} ({what})" for p, h, n, what in DECALS)
    build.wr(f"{D}/README.md", f"""# FusionSpace rocket decals (A4)

| File | For |
|---|---|
| `decal-sheet-a4-print-and-cut-dark.svg/.pdf` (+ `-cmyk.pdf`) | printable vinyl or sticker paper: color art on a Void backing, magenta CutContour around each piece |
| `decal-sheet-a4-print-and-cut-light.svg/.pdf` (+ `-cmyk.pdf`) | the same on a white backing |
| `decal-sheet-a4-vinyl-cut.svg/.pdf` | plotter-cut one-color vinyl: the art's outline is the cut, with a weeding box around each piece |

Pieces: {sizes}. Horizontal lockups go along the body tube; marks go on fins (one per fin, both sides if you like) and nose cones.
Rough guide for the lockup: about a third of the airframe diameter tall reads well from the pad.

- Print-and-cut: open the SVG in your cutter's software (Silhouette Studio, Cricut Design Space) or send the PDF to a sticker printer.
  The `CutContour` layer is the cut; the 13 mm margin leaves room for registration marks.
- Vinyl: the narrowest feet are floored at {VINYL_MIN_WALL} mm so they don't tear when weeding; below about 12 mm the wordmark gets fiddly.
- Clear-coat over printed decals on flown rockets, and keep decals off the fin root fillets.
- `*-preview.png` shows the sheet with size labels (the labels are not in the print or cut files).
""")
    note(f"{D}/decal-sheet-a4-print-and-cut-{{dark,light}}.svg/.pdf", G, "rocket decal sheet: lockups for body tubes, marks for fins, with CutContour", "A4", "Model and high-power rockets; print-and-cut vinyl")
    note(f"{D}/decal-sheet-a4-vinyl-cut.svg/.pdf", G, "rocket decal sheet for one-color plotter-cut vinyl, with weeding boxes", "A4", "Model and high-power rockets")
