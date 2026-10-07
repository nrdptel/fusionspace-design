"""Build FusionSpace Rev C brand files (four nose-cone cluster) into ./out, mirroring the repo layout."""
import math, os, re, io, json, subprocess, shutil, tempfile
from PIL import Image
import geo

# Paths: this file lives in <repo>/tools/build/. Inputs are the archived Rev B files (untouched originals of
# the wordmark outlines, templates, guide and README); output goes to <repo>/_build/rev-c, never over the repo.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.environ.get("FS_SRC", os.path.join(ROOT, "source"))
OUT = os.environ.get("FS_OUT", os.path.join(ROOT, "_build", "rev-c"))
REV = "C"
DATE = "September 2026"
# Reproducible output: rsvg-convert and Ghostscript stamp PDFs with this date instead of "now" (and kit.cmyk() drops the
# random IDs), and DXFs are written with fixed metadata, so a rebuild only changes files whose content changed.
os.environ.setdefault("SOURCE_DATE_EPOCH", "1790812800")   # October 1, 2026, 00:00 UTC
TMP = tempfile.mkdtemp(prefix="fs-build-")               # scratch renders (a shared /tmp can hold other users' files)

VOID, PAPER, WHITE = "#0B0F1C", "#F3F4F7", "#FFFFFF"
# The Fusion gradient: one gradient for every background (decided October 2, 2026).
# Every stop is >= 3:1 on white and >= 6:1 on Void; 2.76:1 on Paper is accepted. Same stops and direction as before.
GRADIENT = [("0.0", "#DA7C30", "M orange"), ("0.35", "#D07D7A", "Rose"), ("0.65", "#A188CB", "Lavender"), ("1.0", "#768DF5", "O blue")]
STOPS = [(o, c) for o, c, _ in GRADIENT]
# The Rev B inputs (and Rev C until October 2, 2026) used the pastel gradient. rd() maps those colors to the current ones,
# so the Rev B templates, guide and README come out in today's palette. Spectral O and M are the gradient ends.
OLD_COLORS = {"#FFB56C": "#DA7C30", "#F2B3A0": "#D07D7A", "#C3B3E0": "#A188CB", "#9BB0FF": "#768DF5"}
def css_gradient():
    return "linear-gradient(90deg," + ",".join(f"{c} {round(float(o) * 100):g}%" for o, c in STOPS) + ")"
def recolor(s):
    return re.sub("|".join(OLD_COLORS), lambda m: OLD_COLORS[m.group(0).upper()], s, flags=re.I)
def contrast(a, b):
    """WCAG 2 contrast ratio of two hex colors."""
    def L(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    la, lb = sorted((L(a), L(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
f = geo.fnum

def rd(p): return recolor(open(os.path.join(SRC, p), encoding="utf-8").read())
def wr(p, s, mode="w"):
    fp = os.path.join(OUT, p); os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, mode, encoding=None if "b" in mode else "utf-8") as fh: fh.write(s)
    return fp

def grad(gid, x1, x2, label="Fusion gradient"):
    st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in STOPS)
    return (f'<linearGradient id="{gid}" inkscape:label="{label}" gradientUnits="userSpaceOnUse" '
            f'x1="{f(x1)}" y1="0" x2="{f(x2)}" y2="0">{st}</linearGradient>')

def header(w, h, title, desc="", page=VOID, units=""):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
     xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     width="{f(w)}{units}" height="{f(h)}{units}" viewBox="0 0 {f(w)} {f(h)}" version="1.1">
<title>{title}</title>
<sodipodi:namedview id="namedview" pagecolor="{page}" bordercolor="#98A1B8" borderopacity="1"
     inkscape:pageopacity="0" inkscape:pagecheckerboard="false" inkscape:deskcolor="#d6dae4"
     inkscape:document-units="{units or 'px'}" showgrid="false"/>
<metadata><rdf:RDF><cc:Work rdf:about=""><dc:title>{title}</dc:title><dc:description>{desc}</dc:description>
<dc:creator><cc:Agent><dc:title>Neer Patel · FusionSpace</dc:title></cc:Agent></dc:creator></cc:Work></rdf:RDF></metadata>
'''

# Color modes. fill: None = the Fusion gradient; a hex = one color; ("twotone", warm, cool, wordmark) = flat
# two-tone, where each cone takes the gradient end nearest its own position in the sweep (see twotone_side()).
# M orange and O blue are the gradient ends; they are also the accent colors on dark and Spectral O and M. Ion and Ember are
# text and UI colors on light (links, warnings); since October 2, 2026 they are no longer logo colors.
ION, EMBER, M_ORANGE, O_BLUE = "#3350D6", "#B34F0C", GRADIENT[0][1], GRADIENT[-1][1]
WARM, COOL = M_ORANGE, O_BLUE              # two-tone cones: one pair on every background; only the wordmark flips
MODES = {
    "color": (None, "Full color. The same gradient on Void, white and Paper", VOID),
    "twotone-on-dark": (("twotone", WARM, COOL, WHITE), "Flat two-tone on dark backgrounds: M orange and O blue cones, white wordmark. Two spot colors; screen print, vinyl, embroidery", VOID),
    "twotone-on-light": (("twotone", WARM, COOL, VOID), "Flat two-tone on light backgrounds: the same M orange and O blue cones, Void wordmark. Two spot colors; screen print, vinyl, embroidery", PAPER),
    "void": (VOID, "One color, Void. Light backgrounds, engraving, stamps, laser cutting", PAPER),
    "white": (WHITE, "One color, white. Dark backgrounds and photos", VOID),
}

_SIDE = {}
def twotone_side():
    """'warm' or 'cool' per cone: the gradient end nearest the cone's center of area along the sweep (left to right
    across the leaned cluster). With the current geometry: west and south warm, main and east cool."""
    key = (geo.TILT, tuple(sorted(geo.POS.items())))
    if key not in _SIDE:
        cl = geo.cluster(); b = geo.bbox(cl)
        out = {}
        for n in geo.ORDER:
            pts = geo.sample(cl[n], 200); a = cx = 0.0
            for i in range(len(pts)):
                x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]; c = x0 * y1 - x1 * y0; a += c; cx += (x0 + x1) * c
            t = (cx / (3 * a) - b[0]) / (b[2] - b[0])
            out[n] = "warm" if t < 0.5 else "cool"
        _SIDE[key] = out
    return _SIDE[key]

def mode_fills(mode, mark_ref="url(#fusion-gradient)", wm_ref="url(#wordmark-gradient)"):
    """(mark fill: str or {cone: hex}, wordmark fill, uses gradients?) for a color mode."""
    fill = MODES[mode][0]
    if fill is None: return mark_ref, wm_ref, True
    if isinstance(fill, tuple):
        _, warm, cool, wm = fill
        side = twotone_side()
        return {n: (warm if side[n] == "warm" else cool) for n in geo.ORDER}, wm, False
    return fill, fill, False

def cluster_group(cl, prefix, fill, indent="  "):
    out = [f'<g id="{prefix}" inkscape:label="Four-cone cluster">']
    for n in geo.DRAW_ORDER:
        label = f'{geo.NAMES[n]} ({geo.PROFILE_NAMES[geo.KINDS[n]]})'
        fl = fill[n] if isinstance(fill, dict) else fill
        out.append(f'{indent}<path id="{prefix}-{n}" inkscape:label="{label}" fill="{fl}" d="{geo.seg_to_d(cl[n])}"/>')
    out.append("</g>")
    return "\n".join(out)

# ---------------------------------------------------------------- wordmark path utilities
def translate_d(d, dx, dy, k=1.0):
    """Scale by k then translate an all-absolute path (M L H V Q C Z)."""
    assert not re.search(r"[a-y]", d.replace("e", "")), "relative commands not supported"
    toks = re.findall(r"[MLHVQCZ]|-?\d*\.?\d+(?:e-?\d+)?", d)
    out, cmd, i, coord = [], None, 0, 0
    res = []
    for t in toks:
        if t.isalpha():
            cmd = t; res.append(t); coord = 0; continue
        v = float(t)
        if cmd == "H": v = v * k + dx
        elif cmd == "V": v = v * k + dy
        else:
            v = v * k + (dx if coord % 2 == 0 else dy); coord += 1
        res.append(f(v))
    s = ""
    for t in res:
        if t.isalpha(): s += t
        else: s += ("" if s and s[-1].isalpha() else " ") + t
    return s.strip()

def get_wordmark(path):
    s = rd(path)
    d = re.search(r'id="wordmark"[^>]*d="([^"]+)"', s).group(1)
    t = re.search(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*font-size:([\d.]+)px', s)
    return d, (float(t.group(1)), float(t.group(2)), float(t.group(3)))

from svgpathtools import parse_path
def path_bbox(d):
    b = parse_path(d).bbox(); return b[0], b[2], b[1], b[3]   # x0,y0,x1,y1

# wordmark metrics in stacked-file units (width 535.737): dot top 223.056, cap top 228, baseline 287, bottom 306.113
WM_W = 535.737
def wm_metrics(bb):
    k = (bb[2] - bb[0]) / WM_W
    top = bb[1]
    return dict(k=k, cap_top=top + 4.944 * k, baseline=top + 63.944 * k, cap=59 * k, bottom=bb[3])

# ---------------------------------------------------------------- 1. mark files
MARK_H = 200.0
def build_marks():
    cl, A, bb = geo.fit_cluster(height=MARK_H)
    W = bb[2]
    for mode, (fill, desc, page) in MODES.items():
        name = "fusion-space-mark" + ("" if mode == "color" else f"-{mode}")
        fl, _, g = mode_fills(mode)
        defs = grad("fusion-gradient", 0, W) if g else ""
        s = header(W, MARK_H, "FusionSpace mark", desc, page)
        s += f'<defs id="defs">{defs}</defs>\n<g inkscape:groupmode="layer" id="layer-mark" inkscape:label="Mark">\n'
        s += cluster_group(cl, "mark", fl) + "\n</g>\n</svg>\n"
        wr(f"logo/mark/{name}.svg", s)
    return W

# ---------------------------------------------------------------- 2. lockups
STACK_H = 125.0            # stacked cluster height
STACK_GAP = 0.10 * STACK_H # stacked gap: cluster bottom to cap top (mark above), or descender bottom to cluster top (mark below)
STACK_POS = "above"        # stacked lockup: mark "above" or "below" the wordmark
H_MARK = 115.0             # horizontal mark height (cap height is 60): 1.92 x cap. Was 100 (1.67 x cap) until October 3, 2026;
                           # raised because the open, four-cone mark read light next to the semibold wordmark
                           # (measured against 13 other horizontal lockups)
H_GAP_CAP = 0.35           # horizontal gap, mark's bounding box to the F, in cap heights (21 units). Was 0.625 (37.5 units)
H_GAP_K = H_GAP_CAP * 60.0 / H_MARK   # the same gap as a fraction of the mark height (0.183), used by the geometry and the tuner
H_POS = "before"           # horizontal lockup: mark "before" (left of) or "after" (right of) the wordmark
SMALL_H_PX = 32            # small-size rule (decided October 2, 2026): on light, a horizontal lockup under this height goes one-color
                           # (28 px until October 3, 2026; 32 keeps the same wordmark size with the larger mark)
SMALL_RULE = (f"On light backgrounds, a horizontal lockup under {SMALL_H_PX} px tall uses the one-color Void lockup "
              "(`fusion-space-horizontal-void`): at that size the thin gradient details are too faint on light.")
def live_text(x, y, size, fill):
    return (f'<g inkscape:groupmode="layer" id="layer-wordmark-live-text-needs-cascadia-mono-semibold" '
            f'inkscape:label="Wordmark live text (needs Cascadia Mono SemiBold)" style="display:none" sodipodi:insensitive="true">\n'
            f'<text x="{f(x)}" y="{f(y)}" fill="{fill}" style="font-family:\'Cascadia Mono\';font-weight:600;font-size:{f(size)}px">FusionSpace</text>\n</g>\n')

def stacked_geometry():
    d, (tx, ty, ts) = get_wordmark("logo/lockup/fusion-space-stacked-color.svg")
    b = geo.bbox(geo.cluster())
    A = STACK_H / (b[3] - b[1]); w = A * (b[2] - b[0])
    cx = WM_W / 2
    if STACK_POS == "below":                # wordmark on top (its top at 0), mark under the descenders
        dy = -223.056
        y0 = 306.113 + dy + STACK_GAP
        cl, A, bb = geo.fit_cluster(height=STACK_H, x0=cx - w / 2, y0=y0)
        H = y0 + STACK_H
    else:                                   # mark on top, gap to the cap line
        cl, A, bb = geo.fit_cluster(height=STACK_H, x0=cx - w / 2, y0=0)
        dy = STACK_H + STACK_GAP - 228.0
        H = 306.113 + dy
    d2 = translate_d(d, 0, dy)
    return cl, bb, d2, (tx, ty + dy, ts), H

def horizontal_geometry(mark_h=None):
    mark_h = H_MARK if mark_h is None else mark_h
    d, (tx, ty, ts) = get_wordmark("logo/lockup/fusion-space-horizontal-color.svg")
    wb = path_bbox(d)                       # 262.699, 64.972, 807.516, 149.437 ; cap 70..130
    cap_top, base = 70.0, 130.0
    capc = (cap_top + base) / 2
    b = geo.bbox(geo.cluster()); A = mark_h / (b[3] - b[1]); w = A * (b[2] - b[0])
    top = min(capc - mark_h / 2, wb[1])
    bottom = max(capc + mark_h / 2, wb[3])
    if H_POS == "after":                    # wordmark first, then the mark
        x_wm = 0.0
        x_mk = (wb[2] - wb[0]) + H_GAP_K * mark_h
        cl, A, bb = geo.fit_cluster(height=mark_h, x0=x_mk, y0=capc - mark_h / 2 - top)
        W = x_mk + w
    else:                                   # mark first, then the wordmark
        cl, A, bb = geo.fit_cluster(height=mark_h, x0=0, y0=capc - mark_h / 2 - top)
        x_wm = w + H_GAP_K * mark_h
        W = wb[2] - wb[0] + x_wm
    dx, dy = x_wm - wb[0], -top
    d2 = translate_d(d, dx, dy)
    return cl, bb, d2, (tx + dx, ty + dy, ts), W, bottom - top, dict(cap_top=cap_top + dy, baseline=base + dy, x_wm=x_wm)

def build_lockups():
    info = {}
    cl, bb, d, (tx, ty, ts), H = stacked_geometry()
    for mode, (fill, desc, page) in MODES.items():
        fm, fw, g = mode_fills(mode)
        defs = (grad("fusion-gradient", bb[0], bb[2]) + grad("wordmark-gradient", 0, WM_W)) if g else ""
        s = header(WM_W, H, "FusionSpace stacked lockup", desc, page)
        s += f'<defs id="defs">{defs}</defs>\n<g inkscape:groupmode="layer" id="layer-mark" inkscape:label="Mark">\n'
        s += cluster_group(cl, "mark", fm) + "\n</g>\n"
        s += f'<g inkscape:groupmode="layer" id="layer-wordmark" inkscape:label="Wordmark">\n<path id="wordmark" inkscape:label="FusionSpace (outlined)" fill="{fw}" d="{d}"/>\n</g>\n'
        s += live_text(tx, ty, ts, fw) + "</svg>\n"
        wr(f"logo/lockup/fusion-space-stacked-{mode}.svg", s)
    info["stacked"] = dict(W=WM_W, H=H, bb=bb)
    cl, bb, d, (tx, ty, ts), W, H, m = horizontal_geometry()
    wb = path_bbox(d)
    for mode, (fill, desc, page) in MODES.items():
        fm, fw, g = mode_fills(mode)
        defs = (grad("fusion-gradient", bb[0], bb[2]) + grad("wordmark-gradient", wb[0], wb[2])) if g else ""
        s = header(W, H, "FusionSpace horizontal lockup", desc, page)
        s += f'<defs id="defs">{defs}</defs>\n<g inkscape:groupmode="layer" id="layer-mark" inkscape:label="Mark">\n'
        s += cluster_group(cl, "mark", fm) + "\n</g>\n"
        s += f'<g inkscape:groupmode="layer" id="layer-wordmark" inkscape:label="Wordmark">\n<path id="wordmark" inkscape:label="FusionSpace (outlined)" fill="{fw}" d="{d}"/>\n</g>\n'
        s += live_text(tx, ty, ts, fw) + "</svg>\n"
        wr(f"logo/lockup/fusion-space-horizontal-{mode}.svg", s)
    info["horizontal"] = dict(W=W, H=H, bb=bb, **m)
    return info

# ---------------------------------------------------------------- 3. favicons
FAV_FILL = 0.87           # favicon: the cluster's bounding box as a fraction of the tile. Was 0.92, which put the main
                          # cone's tip 9.5 (of 512) outside the rounded corner; 0.87 keeps every point FAV_INSET inside
FAV_RX = 96               # favicon tile corner radius (of 512)
FAV_INSET = 8             # favicon: least distance (of 512) from any point of the cluster to the rounded tile's edge
FAV_SHIFT = (-10.72, 10.07)   # favicon: cluster offset (of 512) from bbox-centered. Moves it down and left so the main cone's
                          # tip (to the rounded top-right corner), the west cone (to the left edge) and the east cone (to the
                          # bottom edge) are all the same distance from the tile's edge (FAV_GAP). Found by fav_balance().
FAV_GAP_TOL = 0.05        # the build stops if those three gaps differ by more than this (of 512)
APP_SAFE_R = 0.40         # app icon: farthest point of the cluster from the center, as a fraction of the tile
                          # (the W3C maskable-icon safe zone is a circle of radius 0.40)

def app_frac(S=512):
    """Cluster bbox fraction of the tile that puts its farthest point exactly on the APP_SAFE_R circle."""
    b = geo.bbox(geo.cluster()); w, h = b[2] - b[0], b[3] - b[1]
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    pts = [p for n in geo.ORDER for p in geo.sample(geo.cone_segments(n), 400)]
    rmax = max(math.hypot(p[0] - cx, p[1] - cy) for p in pts)        # in units of a
    return APP_SAFE_R * max(w, h) / rmax

def tile_inset(frac, rx, S=512):
    """Least distance (in px of an S tile) from any point of the cluster (bbox centered, frac of the tile) to the edge of a
    rounded tile with corner radius rx; negative when the cluster pokes outside the tile."""
    b = geo.bbox(geo.cluster()); w, h = b[2] - b[0], b[3] - b[1]
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2; A = frac * S / max(w, h); worst = float("inf")
    for n in geo.ORDER:
        for x, y in geo.sample(geo.cone_segments(n), 600):
            qx = abs(A * (x - cx)) - (S / 2 - rx); qy = abs(A * (y - cy)) - (S / 2 - rx)
            worst = min(worst, rx - math.hypot(max(qx, 0), max(qy, 0)) - min(max(qx, qy), 0))
    return worst

def cone_gaps(frac, rx, shift=(0, 0), S=512):
    """Per cone, the least distance (in px of an S tile) from its outline to the edge of a rounded tile with corner radius
    rx, for a cluster that fills frac of the tile (bbox centered, then moved by shift)."""
    b = geo.bbox(geo.cluster()); w, h = b[2] - b[0], b[3] - b[1]
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2; A = frac * S / max(w, h); out = {}
    for n in geo.ORDER:
        worst = float("inf")
        for x, y in geo.sample(geo.cone_segments(n), 1500):
            X, Y = A * (x - cx) + shift[0], A * (y - cy) + shift[1]
            qx = abs(X) - (S / 2 - rx); qy = abs(Y) - (S / 2 - rx)
            worst = min(worst, rx - math.hypot(max(qx, 0), max(qy, 0)) - min(max(qx, qy), 0))
        out[n] = worst
    return out

def fav_balance(frac=None, rx=None):
    """The shift that makes the favicon's gap even: the cluster's least distance to the tile edge as large as it can be,
    which leaves the cones nearest the edge (main tip at the corner, west at the left, east at the bottom) equally far
    from it. Run it after changing the geometry, FAV_FILL or FAV_RX and copy the result into FAV_SHIFT."""
    from scipy.optimize import minimize
    frac = FAV_FILL if frac is None else frac; rx = FAV_RX if rx is None else rx
    r = minimize(lambda v: -min(cone_gaps(frac, rx, v).values()), [0, 0], method="Nelder-Mead",
                 options=dict(xatol=1e-4, fatol=1e-5, maxiter=4000))
    return tuple(round(float(x), 2) for x in r.x), -r.fun

def favicon_geometry(S=512):
    """The favicon's cluster: FAV_FILL of the tile, bbox centered and moved by FAV_SHIFT. Returns (cluster, bbox)."""
    b = geo.bbox(geo.cluster()); A = FAV_FILL * S / max(b[2] - b[0], b[3] - b[1])
    k = S / 512
    cl = geo.cluster(A, (S / 2 - A * (b[0] + b[2]) / 2 + FAV_SHIFT[0] * k, S / 2 - A * (b[1] + b[3]) / 2 + FAV_SHIFT[1] * k))
    return cl, geo.bbox(cl)

def icon_svg(kind):
    """kind: favicon (cluster, FAV_FILL of a FAV_RX rounded tile, for 16-48 px), icon (cluster, rounded), app (cluster, square full-bleed)"""
    S = 512
    frac, rx, prefix = {"favicon": (FAV_FILL, FAV_RX, "fav"), "icon": (0.765, 112, "icon")}.get(kind, (None, 0, "app"))
    if frac is None: frac = app_frac(S)
    b = geo.bbox(geo.cluster()); w, h = b[2] - b[0], b[3] - b[1]
    A = frac * S / max(w, h)
    sh = FAV_SHIFT if kind == "favicon" else (0, 0)
    org = (S / 2 - A * (b[0] + b[2]) / 2 + sh[0], S / 2 - A * (b[1] + b[3]) / 2 + sh[1])   # bbox centered (favicon: then shifted)
    cl = geo.cluster(A, org); bb = geo.bbox(cl)
    if kind == "favicon":
        s = header(S, S, "FusionSpace favicon", "Full cluster on a Void tile, for 16-48 px (the 16 px PNG is pixel-hinted by the build)", PAPER)
    else:
        s = header(S, S, "FusionSpace icon", "Full cluster on a Void tile" + ("" if rx else ", full-bleed, inside the 0.40 maskable safe zone for iOS/Android masks"), PAPER)
    s += f'<defs id="defs">{grad("fusion-gradient", bb[0], bb[2])}</defs>\n'
    s += f'<g inkscape:groupmode="layer" id="layer-tile" inkscape:label="Tile">\n<rect inkscape:label="Tile" width="512" height="512" rx="{rx}" fill="#0B0F1C"/>\n</g>\n'
    s += '<g inkscape:groupmode="layer" id="layer-mark" inkscape:label="Mark">\n' + cluster_group(cl, prefix, "url(#fusion-gradient)") + "\n</g>\n</svg>\n"
    return s

def rast(svg_path, out_path, w=None, h=None):
    args = ["rsvg-convert", svg_path, "-o", out_path]
    if w: args[1:1] = ["-w", str(w)]
    if h: args[1:1] = ["-h", str(h)]
    subprocess.run(args, check=True)

FAV_ARROWS = ("west", "east")   # 16 px favicon: each wing cone is drawn as a 2 x 2 arrow pointing up and right (top left, top
                                # right and bottom right pixels) in the 2 x 2 box where plain hinting puts it, in its own color; the main
                                # and south cones are hinted from their outlines

def hinted_favicon(n=16, ss=32, thr=0.5, arrows=FAV_ARROWS):
    """Pixel-hinted 16 px favicon. The tile and each cone are rendered apart at n x ss; a pixel is a cone's (its mean
    gradient color, opaque) when that cone covers at least thr of it, otherwise plain tile. Only the tile's rounded corners
    keep their anti-aliasing. Cones in `arrows` are too small to hint from their outline (they come out as sideways wedges),
    so each is drawn as a 45-degree arrow (the box's top left, top right and bottom right pixels) in the 2 x 2 box with the
    most outline-hinted pixels (where the plain hinting put the cone), in the cone's mean color."""
    import numpy as np
    S = 512; cl, bb = favicon_geometry(S)
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in STOPS)
    gdef = f'<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{f(bb[0])}" y1="0" x2="{f(bb[2])}" y2="0">{stops}</linearGradient>'
    def r(body):
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}"><defs>{gdef}</defs>{body}</svg>'
        out = subprocess.run(["rsvg-convert", "-w", str(n * ss), "-h", str(n * ss)], input=svg.encode(), capture_output=True, check=True).stdout
        return np.asarray(Image.open(io.BytesIO(out)).convert("RGBA"), dtype=float).reshape(n, ss, n, ss, 4) / 255
    tl = r(f'<rect width="{S}" height="{S}" rx="{FAV_RX}" fill="#000"/>')
    void = np.array([int(VOID[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    o = np.zeros((n, n, 4)); o[..., :3] = void; o[..., 3] = tl[..., 3].mean((1, 3))
    for name in geo.DRAW_ORDER:
        cn = r(f'<path fill="url(#g)" d="{geo.seg_to_d(cl[name])}"/>')
        cov = cn[..., 3].mean((1, 3)); wsum = cn[..., 3].sum((1, 3))
        col = (cn[..., :3] * cn[..., 3:4]).sum((1, 3)) / np.maximum(wsum[..., None], 1e-9)
        if name in arrows:
            c = (col * wsum[..., None]).sum((0, 1)) / wsum.sum()
            k = (cov >= thr) * 10.0 + cov       # the box holding most of the outline-hinted pixels; coverage breaks ties
            box = k[:-1, :-1] + k[1:, :-1] + k[:-1, 1:] + k[1:, 1:]
            y0, x0 = np.unravel_index(int(np.argmax(box)), box.shape)
            for dx, dy in ((0, 0), (1, 0), (1, 1)):
                o[y0 + dy, x0 + dx, :3] = c; o[y0 + dy, x0 + dx, 3] = 1.0
        else:
            m = cov >= thr; o[m, :3] = col[m]; o[m, 3] = 1.0
    return Image.fromarray((o * 255).round().astype(np.uint8))

def build_favicons():
    if tile_inset(0.765, 112) < FAV_INSET: raise SystemExit("icon: the cluster is closer than FAV_INSET to the tile edge")
    g = cone_gaps(FAV_FILL, FAV_RX, FAV_SHIFT); near = sorted(g.values())[:3]
    if near[0] < FAV_INSET: raise SystemExit(f"favicon: the cluster is {near[0]:.1f} px (of 512) from the tile edge, under FAV_INSET = {FAV_INSET}")
    if near[2] - near[0] > FAV_GAP_TOL:
        raise SystemExit(f"favicon: uneven gap ({', '.join(f'{n} {v:.2f}' for n, v in g.items())}); set FAV_SHIFT = {fav_balance()[0]}")
    for kind, name in [("favicon", "favicon.svg"), ("icon", "icon.svg"), ("app", "app-icon.svg")]:
        wr(f"logo/favicon/{name}", icon_svg(kind))
    fav = os.path.join(OUT, "logo/favicon/favicon.svg")
    ico = os.path.join(OUT, "logo/favicon/icon.svg")
    app = os.path.join(OUT, "logo/favicon/app-icon.svg")
    fav16 = hinted_favicon(); fav16.save(os.path.join(OUT, "logo/favicon/favicon-16.png"))
    rast(fav, os.path.join(OUT, "logo/favicon/favicon-32.png"), 32, 32)
    rast(ico, os.path.join(OUT, "logo/favicon/icon-192.png"), 192, 192)
    rast(ico, os.path.join(OUT, "logo/favicon/icon-512.png"), 512, 512)
    rast(app, os.path.join(OUT, "logo/favicon/apple-touch-icon.png"), 180, 180)
    imgs = [fav16]
    for n in (32, 48):
        p = os.path.join(TMP, f"fav{n}.png"); rast(fav, p, n, n); imgs.append(Image.open(p).convert("RGBA"))
    imgs[2].save(os.path.join(OUT, "logo/favicon/favicon.ico"), format="ICO", sizes=[(16, 16), (32, 32), (48, 48)], append_images=imgs[:2])

def build_pngs():
    d = os.path.join(OUT, "logo"); os.makedirs(d + "/png", exist_ok=True)
    for m in ("", "-void", "-white"):
        rast(f"{d}/mark/fusion-space-mark{m}.svg", f"{d}/png/fusion-space-mark{m}-1024.png", w=1024)
    for lay in ("horizontal", "stacked"):
        for m in ("color", "void", "white"):
            rast(f"{d}/lockup/fusion-space-{lay}-{m}.svg", f"{d}/png/fusion-space-{lay}-{m}-2000.png", w=2000)

# ---------------------------------------------------------------- 4. DXF (50 mm tall, arcs only)
DXF_H_MM = 50.0           # DXF mark height
DXF_MIN_WALL_MM = 0.5     # production floor for the feet in the DXF only: each foot is cut where the wall is at
                          # least this wide (or FOOT_K x base radius, whichever is wider). The cone positions and scale
                          # match the master mark; only the foot spurs are trimmed. 0 = exact master outline.

def thinnest_foot_mm(height_mm=DXF_H_MM):
    """Narrowest master foot (no production floor) at the DXF size, in mm."""
    _, A, _ = geo.fit_cluster(height=height_mm)
    return min((geo.foot(geo.KINDS[n], geo.SIZE[n])[1] - geo.foot(geo.KINDS[n], geo.SIZE[n])[2]) * A for n in geo.ORDER)

def dxf_geometry(height_mm=DXF_H_MM, min_wall_mm=DXF_MIN_WALL_MM):
    """Cut-file outline in mm (y down): feet trimmed to min_wall_mm, scaled so the trimmed outline is height_mm
    tall (the feet can be its outermost points), top-left at (0, 0). Returns (cl, A, bb); A is mm per unit a."""
    _, A, _ = geo.fit_cluster(height=height_mm)
    for _ in range(4):
        b0 = geo.bbox({n: geo.cone_segments(n, min_wall=min_wall_mm / A) for n in geo.ORDER})
        A = height_mm / (b0[3] - b0[1])
    org = (-A * b0[0], -A * b0[1])
    cl = {n: geo.cone_segments(n, A, org, min_wall=min_wall_mm / A) for n in geo.ORDER}
    return cl, A, geo.bbox(cl)

def build_dxf(height_mm=DXF_H_MM, tol=0.0005, min_wall_mm=DXF_MIN_WALL_MM, path="logo/mark/fusion-space-mark-50mm.dxf"):
    import ezdxf
    cl, A, bb = dxf_geometry(height_mm, min_wall_mm)
    try: ezdxf.options.write_fixed_meta_data_for_testing = True   # fixed timestamps and GUIDs: same geometry, same bytes
    except AttributeError: pass
    doc = ezdxf.new("R2010", setup=False)    # no default arrow/linetype blocks (FreeCAD imports them as stray objects)
    doc.header["$INSUNITS"] = 4; doc.header["$MEASUREMENT"] = 1
    doc.layers.add("FS_MARK", color=7)
    msp = doc.modelspace()
    Y = lambda p: (p[0], height_mm - p[1])
    def circ3(a, b, c):
        ax, ay = a; bx, by = b; cx, cy = c
        dd = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(dd) < 1e-12: return None
        ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/dd
        uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/dd
        return (ux, uy), math.hypot(ax-ux, ay-uy)
    def bulge3(ps, pm, pe):
        r = circ3(ps, pm, pe)
        if r is None: return 0.0
        (ux, uy), R = r
        a0 = math.atan2(ps[1]-uy, ps[0]-ux); am = math.atan2(pm[1]-uy, pm[0]-ux); a1 = math.atan2(pe[1]-uy, pe[0]-ux)
        ccw = ((pe[0]-ps[0])*(pm[1]-ps[1]) - (pe[1]-ps[1])*(pm[0]-ps[0])) < 0
        sweep = (a1 - a0) % (2*math.pi) if ccw else (a0 - a1) % (2*math.pi)
        b = math.tan(sweep / 4)
        return b if ccw else -b
    def fit(fn, t0, t1, out, depth=0):
        ps, pe, pm = fn(t0), fn(t1), fn((t0+t1)/2)
        r = circ3(ps, pm, pe)
        ok = True
        if r is not None:
            (ux, uy), R = r
            for k in (0.125, 0.25, 0.375, 0.625, 0.75, 0.875):
                q = fn(t0 + (t1-t0)*k)
                if abs(math.hypot(q[0]-ux, q[1]-uy) - R) > tol: ok = False; break
        if (not ok) and depth < 14:
            fit(fn, t0, (t0+t1)/2, out, depth+1); fit(fn, (t0+t1)/2, t1, out, depth+1)
        else:
            out.append((ps, bulge3(ps, pm, pe)))
    total_arcs = 0
    for n in geo.ORDER:
        segs = cl[n]; verts = []; cur = None
        for sg in segs:
            if sg[0] == "M": cur = sg[1]; continue
            if sg[0] == "Z": continue
            fn0 = geo.seg_param(cur, sg)
            fn = lambda t, fn0=fn0: Y(fn0(t))
            if sg[0] == "L": verts.append((Y(cur), 0.0))
            elif sg[0] == "A" and abs(sg[1] - sg[2]) < 1e-9:
                verts.append((Y(cur), bulge3(fn(0), fn(0.5), fn(1))))
            else:
                part = []; fit(fn, 0, 1, part); verts += part
            cur = sg[-1]
        total_arcs += len(verts)
        msp.add_lwpolyline([(p[0], p[1], b) for p, b in verts], format="xyb", close=True, dxfattribs={"layer": "FS_MARK"})
    fp = os.path.join(OUT, path); os.makedirs(os.path.dirname(fp), exist_ok=True)
    doc.saveas(fp)
    feet = {n: round(float((lambda h: (h[1] - h[2]) * A)(geo.foot(geo.KINDS[n], geo.SIZE[n], min_wall_mm / A))), 3) for n in geo.ORDER}
    return bb, total_arcs, feet

if False:
    import sys
    if os.path.exists(OUT): shutil.rmtree(OUT)
    W = build_marks(); info = build_lockups(); build_favicons(); build_pngs(); dx = build_dxf()
    print("mark width", W, info, dx)

# ---------------------------------------------------------------- 5. graphics, tokens
def build_construction():
    import construction
    s = construction.construction_svg()
    wr("graphics/mark-construction.svg", s)
    rast(os.path.join(OUT, "graphics/mark-construction.svg"), os.path.join(TMP, "mc.png"), w=1600)
    im = Image.open(os.path.join(TMP, "mc.png")).convert("RGBA")
    bg = Image.new("RGBA", im.size, PAPER); bg.paste(im, (0, 0), im)
    bg.save(os.path.join(OUT, "graphics/mark-construction.png"))

SPECTRAL_NOTE = ("O and M are the Fusion gradient ends: the O- and M-class star colors, deepened on October 2, 2026 so the whole "
                 "gradient holds at least 3:1 on white. B to K are the star colors sampled from the Harvard classification.")
def color_tokens(tok):
    """Color sections of the tokens (the Rev B values, recolored by rd(), plus today's notes)."""
    tok["gradient"] = [{"offset": float(o), "hex": c, "name": n} for o, c, n in GRADIENT]
    tok["gradient_note"] = ("One gradient for every background, always left to right. WCAG 2 contrast of every stop: about 3.0:1 on "
                            "white, 6.3:1 on Void, 2.8:1 on Paper (accepted; the target was white).")
    tok["signal"]["Ion"]["use"] = "O-class accent for links, UI and text on light (5.9:1 on Paper). Not a logo color"
    tok["signal"]["Ember"]["use"] = "M-class accent for warnings and highlights on light (4.7:1 on Paper). Not a logo color"
    tok["accent_on_dark"] = {"M orange": {"hex": M_ORANGE, "use": "Warm accent on dark: labels, warnings (6.3:1 on Void)"},
                             "O blue": {"hex": O_BLUE, "use": "Cool accent on dark: labels, links, taglines (6.3:1 on Void)"}}
    tok["spectral_note"] = SPECTRAL_NOTE
    return tok

def build_color_files(tok):
    """color/fusion-space-tokens.css and color/fusion-space.gpl, written from the token dict."""
    g = ", ".join(f"{c['hex']} {round(c['offset'] * 100):g}%" for c in tok["gradient"])
    L = ["/* FusionSpace design tokens */", ":root {",
         f"  --fs-gradient: linear-gradient(90deg, {g});  /* the Fusion gradient, M to O, always left to right; the same on dark and light */", ""]
    L += [f"  --fs-{k.lower()}: {v['hex']};  /* {v['use']} */" for k, v in tok["core"].items()]
    L += [f"  --fs-{k.lower()}: {v['hex']};  /* {v['use']} */" for k, v in tok["signal"].items()]
    L += [f"  --fs-m-orange: {M_ORANGE};  /* gradient start; warm two-tone cones; warm accent on dark (6.3:1 on Void) */",
          f"  --fs-o-blue: {O_BLUE};  /* gradient end; cool two-tone cones; cool accent on dark (6.3:1 on Void) */"]
    L += [f"  --fs-spectral-{k.lower()}: {v['hex']};  /* class {k}, {v['temperature']}, {v['name']} */" for k, v in tok["spectral"].items()]
    L += ["", "  --fs-font-display: 'Cascadia Mono', ui-monospace, Menlo, monospace;  /* weight 600 */",
          "  --fs-font-text: 'Archivo', system-ui, sans-serif;",
          "  --fs-font-mono: 'Cascadia Mono', ui-monospace, 'SF Mono', Menlo, monospace;", "}", "",
          "/* gradient text: .fs-gradient-text { background: var(--fs-gradient); -webkit-background-clip: text; background-clip: text; color: transparent; } */",
          f"/* Spectral: {SPECTRAL_NOTE} */"]
    wr("color/fusion-space-tokens.css", "\n".join(L) + "\n")
    rgb = lambda h: " ".join(f"{int(h[i:i + 2], 16):3d}" for i in (1, 3, 5))
    P = ["GIMP Palette", "Name: FusionSpace", "Columns: 8", "#", "# FusionSpace palette: Fusion gradient stops, Core, Signal, Spectral (O-M)."]
    P += [f"{rgb(c['hex'])}\tGradient {round(c['offset'] * 100):g}% {c['name']} {c['hex']}" for c in tok["gradient"]]
    P += [f"{rgb(v['hex'])}\t{k} {v['hex']}" for k, v in tok["core"].items()]
    P += [f"{rgb(v['hex'])}\t{k} {v['hex']}" for k, v in tok["signal"].items()]
    P += [f"{rgb(v['hex'])}\tSpectral {k} {v['hex']}" for k, v in tok["spectral"].items()]
    wr("color/fusion-space.gpl", "\n".join(P) + "\n")

def build_graphics():
    """graphics/fusion-gradient-strip.svg and graphics/spectral-bar.svg."""
    s = header(1400, 16, "Fusion gradient strip", page=PAPER)
    s += (f'<defs id="defs">{grad("strip", 0, 1400)}</defs>\n<g inkscape:groupmode="layer" id="layer-strip" inkscape:label="Strip">\n'
          '<rect inkscape:label="Fusion gradient strip" x="0" y="0" width="1400" height="16" fill="url(#strip)"/>\n</g>\n</svg>\n')
    wr("graphics/fusion-gradient-strip.svg", s)
    sp = json.loads(rd("color/fusion-space-tokens.json"))["spectral"]
    s = header(1400, 150, "Spectral classes", "Seven stellar classes O B A F G K M, hottest to coolest. " + SPECTRAL_NOTE, page=PAPER)
    s += '<defs id="defs"></defs>\n<g inkscape:groupmode="layer" id="layer-spectral-bar" inkscape:label="Spectral bar">\n'
    for i, (k, v) in enumerate(sp.items()):
        x = 200 * i; w = "200" if i == len(sp) - 1 else "200.4"
        s += (f'<rect inkscape:label="Class {k}" x="{x}" y="0" width="{w}" height="80" fill="{v["hex"]}"/>\n'
              f'<text x="{x}" y="112.4" fill="#0B0F1C" style="font-family:\'Cascadia Mono\',monospace;font-size:25.2px;font-weight:600">{k}</text>\n'
              f'<text x="{x}" y="141.2" fill="#566079" style="font-family:\'Cascadia Mono\',monospace;font-size:14.4px">{v["temperature"]}</text>\n')
    wr("graphics/spectral-bar.svg", s + "</g>\n</svg>\n")

WORDMARK_K = 40.0 / 59     # the standalone wordmark: cap height 40 (stacked-file units have cap height 59)
def build_wordmarks():
    """logo/wordmark/fusion-space-wordmark-{color,void,white}.svg and their 2000 px PNGs."""
    d0, (tx, ty, ts) = get_wordmark("logo/lockup/fusion-space-stacked-color.svg")
    b = path_bbox(d0); k = WORDMARK_K
    d = translate_d(d0, -b[0] * k, -b[1] * k, k)
    w, h = (b[2] - b[0]) * k, (b[3] - b[1]) * k
    for m, fill, page in (("color", "url(#wordmark-gradient)", VOID), ("void", VOID, PAPER), ("white", WHITE, VOID)):
        s = header(w, h, "FusionSpace wordmark", page=page)
        s += f'<defs id="defs">{grad("wordmark-gradient", 0, w) if m == "color" else ""}</defs>\n'
        s += f'<g inkscape:groupmode="layer" id="layer-wordmark" inkscape:label="Wordmark">\n<path id="wordmark" inkscape:label="FusionSpace (outlined)" fill="{fill}" d="{d}"/>\n</g>\n'
        s += live_text((tx - b[0]) * k, (ty - b[1]) * k, ts * k, fill) + "</svg>\n"
        p = wr(f"logo/wordmark/fusion-space-wordmark-{m}.svg", s)
        rast(p, os.path.join(OUT, f"logo/png/fusion-space-wordmark-{m}-2000.png"), w=2000, h=round(2000 * h / w))

def build_tokens():
    tok = color_tokens(json.loads(rd("color/fusion-space-tokens.json")))
    b = geo.bbox(geo.cluster())
    tok["mark"] = {
        "cones": [{"name": n.capitalize(), "profile": geo.PROFILE_NAMES[geo.KINDS[n]],
                   "base_radius_r": geo.SIZE[n],
                   "base_center_uv_r": [round(geo.POS_UPRIGHT[n][0] / geo.W_K, 4), round((geo.POS_UPRIGHT[n][1] + (1 - geo.TIP_K) * geo.H_K * (geo.SIZE[n] - 1)) / geo.W_K, 4)]}
                  for n in geo.ORDER],
        "cone": {"length_over_base_radius": round(geo.H_K / geo.W_K, 3), "notch_depth_over_base_radius": geo.SAG_K,
                 "notch_radius_over_base_radius": round((1 + geo.SAG_K ** 2) / (2 * geo.SAG_K), 4),
                 "foot_width_over_base_radius": geo.FOOT_K,
                 "profiles": "Standard nose-cone equations (conical, tangent ogive, elliptical, LD-Haack/Von Karman C = 0)"},
        "tilt_deg": geo.TILT,
        "spacing_rule": f"Diamond, measured on a grid leaned {geo.TILT:g} deg (lay out upright, then rotate the whole cluster). r = Von Karman base radius. Each foot is cut flat, parallel to the base, where the wall between flank and notch is FOOT_K x its base radius wide. With the lean at 0 the Von Karman is north and the ogive is the tail, south on the same axis, with its tip {geo.TAIL_R:+.2f} r from the Von Karman foot line (+ = below). The area centroids of the conical (west) and elliptical (east) wings share a line {geo.WING_R:+.2f} r from the Von Karman foot line. The west wing's inner foot corner is {geo.GAP_W_R:.2f} r from the left Von Karman foot corner and the east wing's is {geo.GAP_E_R:.2f} r from the right one (horizontal gaps)",
        "cluster_size": {"width": round(b[2] - b[0], 3), "height": round(b[3] - b[1], 3)},
        "lockups": {"horizontal": f"mark {H_POS} the wordmark, mark height {H_MARK / 60:.3f} x cap height, gap {H_GAP_CAP:.2f} x cap height ({H_GAP_K:.3f} x mark height)",
                    "stacked": f"mark {STACK_POS} the wordmark, cluster height H, gap {STACK_GAP / STACK_H:.3f} H " + ("to the cap line" if STACK_POS == "above" else "below the descenders") + f", wordmark width {WM_W / STACK_H:.2f} H"},
        "two_tone": {"rule": "Each cone takes the gradient end nearest its own position in the sweep",
                     "warm_cones": [n for n in geo.ORDER if twotone_side()[n] == "warm"], "cool_cones": [n for n in geo.ORDER if twotone_side()[n] == "cool"],
                     "warm": WARM, "cool": COOL, "note": "One cone pair on every background; only the wordmark flips",
                     "on_dark": {"warm": WARM, "cool": COOL, "wordmark": WHITE}, "on_light": {"warm": WARM, "cool": COOL, "wordmark": VOID}},
        "small_size": SMALL_RULE,
        "production": {"dxf_height_mm": DXF_H_MM, "dxf_min_foot_wall_mm": DXF_MIN_WALL_MM,
                       "note": "The DXF trims each foot so the wall is at least dxf_min_foot_wall_mm wide and scales the trimmed outline to dxf_height_mm tall; otherwise it matches the master outline. Tips are true points."},
        "units": "r = Von Karman base radius. u, v are on the leaned grid, from the Von Karman base center, v down (toward the bases).",
    }
    wr("color/fusion-space-tokens.json", json.dumps(tok, indent=2, ensure_ascii=False) + "\n")
    build_color_files(tok)

# ---------------------------------------------------------------- 6. templates
def lockup_parts(wm_bb, mark_x, mark_h=None, fill="url(#g)", prefix="m"):
    """Return (mark group, dx for wordmark, mark bbox) for an inline horizontal lockup."""
    m = wm_metrics(wm_bb)
    mh = mark_h or (H_MARK / 60.0) * m["cap"]
    capc = (m["cap_top"] + m["baseline"]) / 2
    cl, A, bb = geo.fit_cluster(height=mh, x0=mark_x, y0=capc - mh / 2)
    x_wm_new = bb[2] + H_GAP_K * mh
    # wordmark path starts slightly right of the F's stem? use bbox left
    dx = x_wm_new - wm_bb[0]
    return cl, bb, dx

def replace_cluster(s, gid_prefix, cl, fill):
    """Replace <g id="{gid_prefix}" ...>...</g> (old four-star group) with the new cluster group."""
    pat = re.compile(rf'<g id="{gid_prefix}" inkscape:label="Four-star cluster">.*?</g>', re.S)
    assert pat.search(s), gid_prefix
    return pat.sub(lambda _: cluster_group(cl, gid_prefix, fill), s)

def strip_c2pa(s):
    s = re.sub(r"<c2pa:manifest>.*?</c2pa:manifest>", "", s, flags=re.S)
    return s.replace(' xmlns:c2pa="http://c2pa.org/manifest"', "")

def build_social():
    s = strip_c2pa(rd("templates/project-social-card.svg"))
    m = re.search(r'(<path inkscape:label="Wordmark" fill="url\(#card-wm\)" d=")([^"]+)(")', s)
    d = m.group(2); wb = path_bbox(d)
    old_x = 80.0
    cl, bb, dx = lockup_parts(wb, old_x)
    d2 = translate_d(d, dx, 0)
    s = s.replace(m.group(0), m.group(1) + d2 + m.group(3))
    s = replace_cluster(s, "card-mark", cl, "url(#card-grad)")
    s = re.sub(r'<linearGradient id="card-grad"[^>]*x1="[^"]*" y1="0" x2="[^"]*"',
               lambda _: f'<linearGradient id="card-grad" inkscape:label="Fusion gradient" gradientUnits="userSpaceOnUse" x1="{f(bb[0])}" y1="0" x2="{f(bb[2])}"', s)
    g = re.search(r'<linearGradient id="card-wm"[^>]*x1="([^"]*)" y1="0" x2="([^"]*)"', s)
    s = s.replace(g.group(0), g.group(0).replace(f'x1="{g.group(1)}"', f'x1="{f(float(g.group(1)) + dx)}"').replace(f'x2="{g.group(2)}"', f'x2="{f(float(g.group(2)) + dx)}"'))
    wr("templates/project-social-card.svg", s)
    rast(os.path.join(OUT, "templates/project-social-card.svg"), os.path.join(OUT, "templates/project-social-card.png"), w=1600)
    return s

def build_freecad():
    out = {}
    for fn, gid in [("FusionSpace_A4_Landscape.svg", "tb-a4"), ("FusionSpace_ANSI-A_Landscape.svg", "tb-ansia"), ("FusionSpace_ANSI-B_Landscape.svg", "tb-ansib")]:
        s = strip_c2pa(rd(f"templates/freecad/{fn}"))
        grp = re.search(rf'<g id="{gid}" inkscape:label="Four-star cluster">.*?</g>\s*<path fill="#0B0F1C" d="([^"]+)"/>', s, re.S)
        d = grp.group(1); wb = path_bbox(d)
        # old mark left edge = min x of old star paths
        old = re.search(rf'<g id="{gid}" inkscape:label="Four-star cluster">(.*?)</g>', s, re.S).group(1)
        mark_x = min(path_bbox(dd)[0] for dd in re.findall(r' d="([^"]+)"', old))
        cl, bb, dx = lockup_parts(wb, mark_x)
        s = s.replace(d, translate_d(d, dx, 0))
        s = replace_cluster(s, gid, cl, "#0B0F1C")
        # transparent: the title-block boxes were filled white, which showed as white boxes on a dark or tinted page
        # (design review, October 2026). Nothing in the template fills an area now, so FreeCAD's page color shows through.
        s = s.replace('fill="#FFFFFF" stroke="#0B0F1C"', 'fill="none" stroke="#0B0F1C"')
        assert 'fill="#FFFFFF"' not in s, fn
        wr(f"templates/freecad/{fn}", s)
        # dark-mode copy: the same template with light lines and text, for TechDraw with a dark page color
        # (Preferences → TechDraw → Colors → Page). Print or export PDFs from the light one.
        dk = s.replace("#0B0F1C", WHITE).replace("#566079", FREECAD_DARK_LABEL)
        dk = dk.replace("TechDraw template,", "TechDraw template (dark page),").replace("landscape. Editable", "landscape, for a dark page color. Editable")
        wr(f"templates/freecad/{fn.replace('.svg', '-dark.svg')}", dk)
        out[fn] = (mark_x, bb, dx)
    for suf, page in (("", WHITE), ("-dark", FREECAD_DARK_PAGE)):
        rast(os.path.join(OUT, f"templates/freecad/FusionSpace_ANSI-A_Landscape{suf}.svg"), os.path.join(TMP, "ansia.png"), w=1600)
        im = Image.open(os.path.join(TMP, "ansia.png")).convert("RGBA"); bg = Image.new("RGBA", im.size, page); bg.paste(im, (0, 0), im)
        bg.save(os.path.join(OUT, f"templates/freecad/FusionSpace_ANSI-A_Landscape{suf}.png"))
    return out

FREECAD_DARK_LABEL = "#98A1B8"   # Haze: field labels and zone letters on the dark template (Slate is too dim on dark)
FREECAD_DARK_PAGE = "#0B0F1C"    # the dark template's preview is drawn on Void; any dark page color works

# ---------------------------------------------------------------- 7. guide
def inline(svg_text, prefix, style="", extra=' aria-hidden="true"', viewbox=None):
    s = svg_text
    s = re.sub(r"<\?xml.*?\?>\s*", "", s)
    s = re.sub(r"<title>.*?</title>\s*", "", s, flags=re.S)
    s = re.sub(r"<sodipodi:namedview.*?/>\s*", "", s, flags=re.S)
    s = re.sub(r"<metadata>.*?</metadata>\s*", "", s, flags=re.S)
    s = re.sub(r'<g inkscape:groupmode="layer" id="layer-wordmark-live-text[^>]*>.*?</g>\s*', "", s, flags=re.S)
    s = re.sub(r'\s(inkscape|sodipodi|freecad):[\w-]+="[^"]*"', "", s)
    s = re.sub(r'\sid="(?!defs)[^"]*"', lambda m: m.group(0), s)
    ids = re.findall(r'\bid="([^"]+)"', s)
    for i in sorted(set(ids), key=len, reverse=True):
        s = s.replace(f'id="{i}"', f'id="{prefix}-{i}"').replace(f"url(#{i})", f"url(#{prefix}-{i})")
    m = re.search(r"<svg[^>]*>", s, re.S)
    vb = viewbox or re.search(r'viewBox="([^"]+)"', m.group(0)).group(1)
    open_tag = f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" style="{style}"{extra}>'
    body = s[m.end():]
    body = re.sub(r"\s*\n\s*", "", body)
    return open_tag + body.replace("</svg>", "").strip() + "</svg>"

def dont_svgs():
    b = geo.bbox(geo.cluster()); A = 100 / (b[3] - b[1])
    cl, A, bb = geo.fit_cluster(height=100)
    W = bb[2]
    vb = f"0 0 {f(W)} 100"
    def g(gid, stops=None):
        st = stops or STOPS
        return (f'<defs><linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{f(W)}" y2="0">'
                + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in st) + "</linearGradient></defs>")
    paths = lambda c, fill, extra="": "".join(f'<path fill="{fill}"{extra} d="{geo.seg_to_d(c[n])}"/>' for n in geo.DRAW_ORDER)
    out = []
    cx0, cy0 = W / 2, 50.0
    out.append(f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" style="width:52%;height:auto" aria-hidden="true" overflow="visible">{g("c2-g")}<g transform="translate({f(cx0)} {f(cy0)}) scale(1.4 0.6) translate({f(-cx0)} {f(-cy0)})">{paths(cl, "url(#c2-g)")}</g></svg>')
    # moved / added / dropped, on the real leaned grid: tail (ogive) dropped, west wing pulled out and up,
    # east wing dropped below its line, and a fifth cone added
    up = geo.POS_UPRIGHT; r = geo.W_K
    alt = [("main", None, None, up["main"]),
           ("west", None, None, (up["west"][0] - 0.5 * r, up["west"][1] - 1.1 * r)),
           ("east", None, None, (up["east"][0] + 0.1 * r, up["east"][1] + 0.9 * r)),
           ("south", "ogive", 0.35, (up["east"][0] + 1.0 * r, up["east"][1] - 1.0 * r))]
    raw = [geo.cone_segments(n, 1.0, (0, 0), kind=k, size=sz, pos=geo.rot(p, (0, 0), geo.TILT)) for n, k, sz, p in alt]
    rb = geo.bbox(dict(enumerate(raw)))
    A2 = min(100 / (rb[3] - rb[1]), W / (rb[2] - rb[0]))
    o2 = (W / 2 - A2 * (rb[0] + rb[2]) / 2, 50 - A2 * (rb[1] + rb[3]) / 2)
    segs = [geo.cone_segments(n, A2, o2, kind=k, size=sz, pos=geo.rot(p, (0, 0), geo.TILT)) for n, k, sz, p in alt]
    out.append(f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" style="width:52%;height:auto" aria-hidden="true" overflow="visible">{g("c3-g")}' + "".join(f'<path fill="url(#c3-g)" d="{geo.seg_to_d(sg)}"/>' for sg in segs) + "</svg>")
    rainbow = [("0", "#FF4D6D"), ("0.33", "#FFD60A"), ("0.66", "#3DDC97"), ("1", "#4361EE")]
    out.append(f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" style="width:52%;height:auto" aria-hidden="true" overflow="visible">{g("c4-g", rainbow)}{paths(cl, "url(#c4-g)")}</svg>')
    fills = {"main": O_BLUE, "west": M_ORANGE, "east": M_ORANGE, "south": M_ORANGE}
    out.append(f'<svg viewBox="-4 -4 {f(W + 8)} 108" xmlns="http://www.w3.org/2000/svg" style="width:52%;height:auto" aria-hidden="true">'
               + "".join(f'<path fill="{fills[n]}" stroke="#000" stroke-width="2.5" stroke-linejoin="round" d="{geo.seg_to_d(cl[n])}"/>' for n in geo.DRAW_ORDER) + "</svg>")
    return out

def build_guide(info):
    s = rd("guide/index.html")
    L = lambda p: open(os.path.join(OUT, p), encoding="utf-8").read()
    hc, hv, hw = (L(f"logo/lockup/fusion-space-horizontal-{m}.svg") for m in ("color", "void", "white"))
    sc = L("logo/lockup/fusion-space-stacked-color.svg")
    mk = L("logo/mark/fusion-space-mark.svg")
    import construction
    cdefs, cbody = construction.body("gc")
    cb = re.sub(r"\s*\n\s*", "", cbody)
    cons = f'<svg viewBox="0 0 {construction.CANVAS_W} {construction.CANVAS_H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Construction drawing of the FusionSpace mark"><defs>{cdefs}</defs>{cb}</svg>'
    card = L("templates/project-social-card.svg")
    tb = L("templates/freecad/FusionSpace_ANSI-A_Landscape.svg")
    donts = dont_svgs()
    spans = []
    i = 0
    for m in re.finditer(r"<svg\b", s):
        e = s.find("</svg>", m.start()) + 6
        spans.append((m.start(), e))
    assert len(spans) == 15, len(spans)
    old = [s[a:b] for a, b in spans]
    style = lambda k: re.search(r'style="([^"]*)"', old[k].split(">", 1)[0]).group(1)
    new = [
        inline(hc, "c0", "height:20px;width:auto"),
        inline(mk, "c8", "") .replace('aria-hidden="true">', 'aria-hidden="true" overflow="visible">', 1),
        cons,
        inline(hc, "c9", style(3)), inline(hc, "c10", style(4)),
        inline(sc, "c11", style(5)), inline(sc, "c12", style(6)),
        inline(hv, "c13", style(7)), inline(hw, "c14", style(8)),
        *donts,
        inline(card, "c15", style(13)),
        inline(tb, "c16", style(14)),
    ]
    for (a, b), n in sorted(zip(spans, new), key=lambda t: -t[0][0]):
        s = s[:a] + n + s[b:]
    H = info["horizontal"]; St = info["stacked"]
    cap_h = 60.0 / H_MARK
    reps = [
        ("Brand guide · Rev B · September 2026", f"Brand guide · Rev {REV} · {DATE}"),
        ("An identity for aerospace engineering projects, drawn from how stars are classified. Four stars sit in one cluster, and a soft gradient runs across them from cool M-class orange to hot O-class blue.",
         __import__("kit").INTRO + " It is drawn from how rockets are shaped and how stars are classified. Four nose cones, each a real aerodynamic profile, lean together in one cluster, and a soft gradient runs across them from cool M-class orange to hot O-class blue."),
        ('<span class="label">Stars</span>', '<span class="label">Cones</span>'),
        ("4 STARS · M → O", "4 CONES · M → O"),
        ("This is the original 2023 cluster, redrawn with exact geometry. Each star is the space left between four touching circles, so the tips come to true points. The three companions are 0.45, 0.40 and 0.32 the size of the main star, placed where the first sketch had them. One gradient sweeps across the whole cluster, so the west star comes out warm and the east star cool.",
         f"The 2023 logo was a cluster of four stars. Rev C keeps the cluster and turns each star into a nose cone: Von Kármán for the main cone, conical and elliptical for the two wings (0.4 and 0.3 of the main cone's base radius) and a tangent ogive (0.5) for the tail. The four sit in a diamond: the ogive trails behind the main cone on the same axis, which keeps the cluster close to square. Every cone has a deep notch at its base, and the cluster is laid out on a grid that leans {geo.TILT:g}° toward the blue end, so it reads as a launch. One gradient sweeps across the whole cluster, so the west cone comes out warm and the east cone cool."),
        ("Same cluster, cleaner", "Real profiles"),
        ("The layout and sharp tips match the first sketch. Every edge is a true circular arc, and <code>logo/mark/fusion-space-mark-50mm.dxf</code> carries the exact arcs for FreeCAD, laser and CNC work.",
         "The four shapes are the standard nose-cone profiles from rocketry software, drawn from their standard equations with the same length-to-radius ratio. Edges are true lines, arcs and ellipses (Von Kármán is traced with smooth curves), and <code>logo/mark/fusion-space-mark-50mm.dxf</code> is drawn only with lines and arcs for FreeCAD, laser and CNC work."),
        ("where H is the height of the star cluster.", "where H is the height of the cone cluster."),
        ("use the main star on its own.", "use the main cone on its own."),
        ("Horizontal: cap height 0.30 H, gap 0.22 H. Stacked: cap height 0.295 H, gap 0.14 H.",
         f"Horizontal: cap height {cap_h:.3f} H (the mark is {H_MARK / 60:.2f}× the caps), gap {H_GAP_CAP:.2f} × the cap height ({H_GAP_K:.3f} H). Stacked: cap height {59 / STACK_H:.3f} H, gap {STACK_GAP / STACK_H:.2f} H. Only these two arrangements are approved: mark {H_POS} the wordmark, and mark {STACK_POS} it."),
        ("Move, add or drop stars.", "Move, add or drop cones."),
        ("Each star is its own named path. There's also a 50 mm DXF of the mark with exact arcs, for cutting.",
         "Each cone is its own named path, labeled with its profile. There's also a 50 mm DXF of the mark, drawn only with lines and arcs, for cutting."),
        ("The original Illustrator and SolidWorks files, plus the Rev A single-star set.",
         "The original Illustrator and SolidWorks files, the Rev A single-star set and the Rev B star cluster."),
        ("passing through rose and lavender so the middle stays soft instead of turning gray.",
         "passing through rose and lavender so the middle doesn't turn gray. It is the same gradient on dark and light backgrounds: every part of it holds at least 3:1 against white and 6:1 against Void."),
        ("The source palette, sampled from the Harvard classification's Vega-relative chromaticity.",
         "The source palette, sampled from the Harvard classification's Vega-relative chromaticity. O and M are the gradient ends; B to K are the sampled star colors."),
        ("It's still strongest on Void, so prefer dark backgrounds where you can.",
         f"As a graphic it meets the 3:1 non-text contrast on white ({min(contrast(c, WHITE) for c in (WARM, COOL)):.1f} : 1 and up) and on Void; on Paper it is {min(contrast(c, PAPER) for _, c in STOPS):.2f} : 1, which is accepted. On light, a horizontal lockup under {SMALL_H_PX} px tall uses the one-color Void lockup."),
        ("a soft gradient runs across them", "a gradient runs across them"),
        ("On dark backgrounds, use the gradient ends instead.",
         "On dark backgrounds, use the gradient ends instead. They are text and UI colors, not logo colors: the logo uses the gradient, or the flat two-tone cones, on every background."),
        ("<span>stacked-color</span><span>the original arrangement</span>", "<span>stacked-color</span><span>on Paper</span>"),
        ("The title-block fields show up under the page's Editable Texts.",
         "The title-block fields show up under the page's Editable Texts. The sheets are transparent, so the page color shows through; if "
         "your TechDraw page color is dark, use the <code>-dark</code> sheets (light lines), and print or export PDFs from the light ones."),
        ("Rev B · supersedes the 2023 Illustrator/SolidWorks set", f"Rev {REV} · replaces the Rev B star cluster"),
        ("Cluster: 24 px or 8 mm tall. Below 48 px, as in favicons, use the main cone on its own.",
         f"Cluster: 24 px or 8 mm tall. Below 24 px, as in favicons, use the favicon files: they are the full cluster, hinted for 16 px (the two wing cones become small arrows). For cutting, use the DXF: its feet are at least {DXF_MIN_WALL_MM:g} mm wide at {DXF_H_MM:g} mm. For stock thicker than about 1 mm, cut the mark larger or ask the vendor. On light backgrounds, a horizontal lockup under {SMALL_H_PX} px tall uses the one-color Void lockup."),
    ]
    for a, b in reps:
        if a not in s:
            # tolerate markup differences in the DXF sentence
            print("WARN not found:", a[:70]); continue
        s = s.replace(a, b)
    # contrast table: gradient rows measured from today's colors
    chip = lambda c: f'<span style="display:inline-block;width:10px;height:10px;background:{c};border:1px solid var(--rule);margin-right:8px"></span>'
    def row(name, c, bgname, bg):
        r = contrast(c, bg)
        pill = '<span class="pill ok">AA</span>' if r >= 4.5 else '<span class="pill lg">Graphics, large text</span>' if r >= 3 else '<span class="pill lg">Not for text</span>'
        return f'<tr><td>{chip(c)}{name}</td><td>{bgname}</td><td class="num">{r:.1f} : 1</td><td>{pill}</td></tr>'
    rows = (row("Gradient M end", M_ORANGE, "Void", VOID) + row("Gradient O end", O_BLUE, "Void", VOID)
            + row("Gradient M end", M_ORANGE, "White", WHITE) + row("Gradient O end", O_BLUE, "White", WHITE)
            + row("Gradient O end", O_BLUE, "Paper", PAPER))
    s, n = re.subn(r'<tr><td><span[^>]*></span>Gradient M end</td>.*?(?=</tbody>)', lambda _: rows, s, count=1, flags=re.S)
    assert n == 1, "contrast table"
    # Sheet 8: the asset kit (kit.py)
    import kit, kit_product
    n = 9                                                   # sheet 8: Kit, sheet 9: Products (kit_product.py)
    for i in range(1, 8): s = s.replace(f"SHEET {i} / 7", f"SHEET {i} / {n}")
    s = s.replace('<a href="#files">Files</a>', '<a href="#files">Files</a><a href="#kit">Kit</a><a href="#products">Products</a>', 1)
    s = s.replace("</style>", kit.GUIDE_CSS + kit_product.GUIDE_CSS + "</style>", 1)
    s = s.replace("  <footer>", kit.guide_sheet(8).replace("SHEET 8 / 8", f"SHEET 8 / {n}") + kit_product.guide_sheet(9, n) + "\n  <footer>", 1)
    tags = "".join(f'<div><span class="label">Tag</span><b>{t}</b><p>{d}.<br><code style="white-space:nowrap">FS-VEGA · {t}</code></p></div>' for t, d in kit.DISCIPLINES)
    s = s.replace('      <div><a class="cta" href="../tools/callsign/callsign.html">',
                  '      <p>Products of any kind use the same scheme. An optional discipline tag after the code says what kind of work it is:</p>\n'
                  f'      <div class="codes" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">{tags}</div>\n'
                  '      <div><a class="cta" href="../tools/callsign/callsign.html">', 1)
    for a_, b_ in (("<tr><td>tools/callsign/</td><td>Callsign, the star name tool: <code>callsign.html</code> for any browser, phones included, and <code>callsign.py</code> for a terminal, with the IAU star list as JSON and CSV.</td></tr>",
                    "<tr><td>tools/callsign/</td><td>Callsign, the star name tool: <code>callsign.html</code> for any browser, phones included, and <code>callsign.py</code> for a terminal, with the IAU star list as JSON and CSV.</td></tr>\n"
                    "        <tr><td>tools/</td><td>The build scripts that make every file here, and the mark tuner. Apache-2.0 (<code>tools/LICENSE</code>).</td></tr>"),
                   ("<tr><td>_archive/</td><td>The original Illustrator and SolidWorks files, the Rev A single-star set and the Rev B star cluster.</td></tr>",
                    "<tr><td>source/</td><td>The Rev B files the build starts from: the outlined wordmark, the templates, the guide and the README text.</td></tr>")):
        assert a_ in s, a_[:40]
        s = s.replace(a_, b_)
    s = s.replace("<tr><td>templates/</td>", "<tr><td>kit/</td><td>The asset kit: logos in every color mode and size, web and app icons, social and GitHub images, documents, slides and production files. See the Kit sheet and <code>kit/README.md</code>.</td></tr>\n        <tr><td>templates/</td>", 1)
    s = s.replace("<tr><td>templates/</td>", "<tr><td>product/</td><td>The product system: rules for sites, tools, CLIs, apps, devices, boards and rockets, with tokens and reference parts. See the Products sheet and <code>product/README.md</code>.</td></tr>\n        <tr><td>templates/</td>", 1)
    s = guide_review_fixes(s)
    wr("guide/index.html", s)
    return s

def guide_review_fixes(s):
    """Guide fixes from Neer's review of October 3, 2026."""
    # Sheet 1: the inline construction drawing keeps its print colors (Void and Slate ink, Ion construction lines, Paper
    # markers), which vanish on the dark panel. Map them to the theme's colors; in the light theme they map to the same values.
    css = ".panel.draw svg [fill=\"#0B0F1C\"]{fill:var(--ink)}.panel.draw svg [stroke=\"#0B0F1C\"]{stroke:var(--ink)}" \
          ".panel.draw svg [fill=\"#566079\"]{fill:var(--muted)}.panel.draw svg [stroke=\"#566079\"]{stroke:var(--muted)}" \
          ".panel.draw svg [fill=\"#3350D6\"]{fill:var(--accent)}.panel.draw svg [stroke=\"#3350D6\"]{stroke:var(--accent)}" \
          ".panel.draw svg [fill=\"#F3F4F7\"]{fill:var(--surface)}"
    # Sheet 3, Spectral: each temperature range stays on one line (B wrapped to three lines and A's "K" dropped to a line of
    # its own), and the row switches to four columns before the seven get too narrow for the ranges.
    css += ".spectrum .rng{white-space:nowrap}#color .sheet-body>div:has(>.spectrum){container-type:inline-size}" \
           "@container (max-width:800px){.spectrum{grid-template-columns:repeat(4,minmax(0,1fr))}}"
    assert s.count("</style>") >= 1
    s = s.replace("</style>", css + "</style>", 1)
    s, n = re.subn(r'<span class="t">([^<]*?) K<br>', r'<span class="t"><span class="rng">\1&#160;K</span><br>', s)
    assert n == 7, n
    # Sheet 3: Ion and Ember are presented as text-on-light colors, not as deeper versions of O and M.
    old = re.search(r'<h3 style="margin-bottom:6px">Signal</h3>\s*<p class="muted" style="font-size:14px;margin-bottom:14px">.*?</p>', s, re.S)
    assert old, "Signal section"
    s = s.replace(old.group(0), '<h3 style="margin-bottom:6px">Text on light</h3>\n        <p class="muted" style="font-size:14px;margin-bottom:14px">'
        f"For links, labels and warnings on Paper or white. The gradient ends hold {min(contrast(c, WHITE) for c in (M_ORANGE, O_BLUE)):.1f} : 1 on white: "
        "enough for graphics and large text, not for body text, so colored text on light uses Ion and Ember, which pass WCAG AA. "
        "On dark backgrounds, use the gradient ends. They are not logo colors: the logo uses the gradient, or the flat two-tone cones, "
        "on every background. In the tokens they are the Signal group.</p>")
    for a, b in (('<span class="r">O-class accent for links, UI and text on light', '<span class="r">Links, UI and text on light'),
                 ('<span class="r">M-class accent for warnings and highlights on light', '<span class="r">Warnings and highlights on light')):
        assert a in s, a
        s = s.replace(a, b)
    return s

# ---------------------------------------------------------------- 8. README
def build_readme():
    s = rd("README.md")
    s = ('<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="kit/github/readme-banner-dark.png">\n'
         '  <source media="(prefers-color-scheme: light)" srcset="kit/github/readme-banner-light.png">\n'
         '  <img alt="FusionSpace" src="kit/github/readme-banner-dark.png" width="100%">\n</picture>\n\n') + s
    reps = [
        ("# FusionSpace: brand system, Rev B", f"# FusionSpace: brand system, Rev {REV}"),
        ("The identity for my aerospace engineering projects, rebuilt in 2026", __import__("kit").INTRO + " The identity for my own projects (software and embedded systems, games, electronics, mechanical and machined parts, aerospace), rebuilt in 2026"),
        ("It keeps the original 2023 idea, with the four-star cluster, the soft orange-to-blue gradient and Cascadia Mono, but redraws everything with exact geometry.",
         "It keeps the original 2023 idea, a loose cluster of four shapes with the soft orange-to-blue gradient and Cascadia Mono, but Rev C turns the four stars into four nose cones and redraws everything with exact geometry."),
        ("- **Mark.** Four stars in the original arrangement. Each star is the space left between four touching circles of radius *a*, so the tips are true points. The companion stars are 0.45, 0.40 and 0.32 the size of the main star (exact positions are in `color/fusion-space-tokens.json`).",
         f"- **Mark.** Four nose cones in a diamond, each a real rocketry profile: Von Kármán (main, north), conical (west), elliptical (east) and a tangent ogive tail (south). Profiles follow the standard nose-cone equations, each {geo.H_K / geo.W_K:.2f}× as long as its base radius, with a notch {geo.SAG_K:.2f} of the base radius deep and feet cut flat where the wall is {geo.FOOT_K:.2f} of the base radius wide. With *r* as the Von Kármán base radius, the others are {geo.SIZE['west']:.1f} *r* (conical), {geo.SIZE['east']:.1f} *r* (elliptical) and {geo.SIZE['south']:.1f} *r* (ogive). Spacing is measured on a grid leaned {geo.TILT:g}°: the ogive sits on the Von Kármán axis with its tip {abs(geo.TAIL_R):.1f} *r* {'above' if geo.TAIL_R < 0 else 'below'} the Von Kármán foot line, and the wings' centroids share a line {abs(geo.WING_R):.2f} *r* {'below' if geo.WING_R >= 0 else 'above'} it, with the conical {geo.GAP_W_R:.2f} *r* and the elliptical {geo.GAP_E_R:.2f} *r* out from the Von Kármán feet (exact values are in `color/fusion-space-tokens.json`)."),
        ("| `logo/mark` | The four-star mark: `fusion-space-mark` (gradient), `-void` and `-white` (one color), plus `fusion-space-mark-50mm.dxf` with exact arcs for laser/CNC | Inkscape, FreeCAD, CAM |",
         "| `logo/mark` | The four-cone mark: `fusion-space-mark` (gradient), `-void` and `-white` (one color), `-twotone-on-dark` and `-twotone-on-light` (flat two-tone), plus `fusion-space-mark-50mm.dxf` (lines and arcs only) for laser/CNC | Inkscape, FreeCAD, CAM |"),
        ("`favicon.svg` (main star, for small sizes)", "`favicon.svg` (full cluster, framed for 16–48 px)"),
        ("| `guide` | Brand guide | browser |", "| `guide` | Brand guide | browser |\n| `kit` | Asset kit, ready for any project: every logo in every color mode and size; web/app icons; GitHub and social images (dark and light); letterhead, covers, business cards, email signature, slides; boot logos for OLED/TFT displays; KiCad PCB logos; 3D-print files (STL, STEP, two-color 3MF, sketches, a parametric badge); terminal themes and CLI banners; game splash and store art; logo animation; wallpapers; merch and posters; cut files, stickers, engraving and embroidery. Open `kit/index.html` to browse, `kit/README.md` for the list | everything |\n| `tools/build/project.py` | Per-project images: `python3 tools/build/project.py --name Vega --tag EMB --desc \"...\"` makes a project's social preview, README banners, OG image, YouTube thumbnail, title slides, report covers and starter README | terminal |"),
        ("- Keep 0.25 H clear space around the logo, where H is the cluster height. The minimum cluster height is 24 px (8 mm). Below 48 px, use the main star on its own.",
         f"- Keep 0.25 H clear space around the logo, where H is the cluster height. The minimum cluster height is 24 px (8 mm). Below 24 px, as in favicons, use the favicon files: they are the full cluster, hinted for 16 px (the two wing cones become small arrows).\n- In the horizontal lockup the mark is {H_MARK / 60:.2f}× the cap height of the wordmark, {H_POS} it, with a gap of {H_GAP_CAP:.2f} × the cap height ({H_GAP_K:.3f} × the mark height). In the stacked lockup the mark sits {STACK_POS} the wordmark with a gap of {STACK_GAP / STACK_H:.2f} H ({'to the cap line' if STACK_POS == 'above' else 'below the descenders'}). These are the only approved arrangements; don't put the mark {'after' if H_POS == 'before' else 'before'} or {'below' if STACK_POS == 'above' else 'above'} the wordmark."),
        ("- The gradient always runs left to right, M orange to O blue. Don't reverse it, recolor it, or add outlines, shadows or glows.",
         "- The gradient always runs left to right, M orange to O blue. It is the same on dark and light backgrounds. Don't reverse it, recolor it, or add outlines, shadows or glows.\n"
         f"- Where gradients can't be reproduced (spot-color print, vinyl, embroidery), use the flat two-tone versions. The cones are the same on every background, M orange `{WARM}` (warm) and O blue `{COOL}` (cool); only the wordmark changes, white on dark and Void on light (`twotone-on-dark`, `twotone-on-light`). Each cone takes the nearer end of the gradient.\n"
         f"- {SMALL_RULE}\n- Ion `{ION}` and Ember `{EMBER}` are text and UI colors on light (links, warnings), not logo colors."),
        ("- Don't stretch the cluster or move, add or drop stars.", f"- Don't stretch the cluster, change the {geo.TILT:g}° lean, or move, add or drop cones."),
        ("- The star tips are true points. Most cutters handle that, but if a vendor needs a minimum feature size, ask them to apply their usual tip radius at production size.",
         f"- **Minimum feature size.** In the master artwork the feet are cut where the wall is {geo.FOOT_K:.2f} of each cone's base radius wide, which is only {thinnest_foot_mm():.2f} mm on the elliptical cone at {DXF_H_MM:g} mm. The DXF trims the feet so every foot is at least {DXF_MIN_WALL_MM:g} mm wide, then scales the trimmed outline to exactly {DXF_H_MM:g} mm tall; nothing else changes. Laser vendors typically need features of about half the material thickness, so for stock thicker than about 1 mm, scale the DXF up or ask the vendor. The cone tips are true points: ask the vendor to apply their usual tip radius."),
    ]
    reps += [
        ("One soft gradient sweeps", "One gradient sweeps"),
        ("The end colors come from the Harvard stellar classification.",
         "The end colors start from the M- and O-class star colors of the Harvard stellar classification, deepened so the whole gradient holds at least 3:1 on white and 6:1 on Void. It is the same gradient on dark and light backgrounds."),
        ("| `logo/lockup` | Horizontal and stacked lockups, each as `color`, `void` and `white` | Inkscape |",
         "| `logo/lockup` | Horizontal and stacked lockups, each as `color`, `twotone-on-dark`, `twotone-on-light`, `void` and `white` | Inkscape |"),
        ("- The gradient logo is strongest on Void.", "- The gradient logo works on Void, white and Paper."),
        ("some fill themselves in (author, date, scale, sheet).",
         "some fill themselves in (author, date, scale, sheet). The sheets are transparent; with a dark TechDraw page color use the `-dark` ones, and print from the light ones."),
    ]
    reps += [(" The old Illustrator and SolidWorks files are kept in `_archive/`.", ""),
             ("| `tools/callsign` | Callsign, the star name tool: `callsign.html` (any browser, phones included) and `callsign.py` (terminal, Python 3.8+), with the IAU star list as JSON and CSV | browser, terminal |",
              "| `tools/callsign` | Callsign, the star name tool: `callsign.html` (any browser, phones included) and `callsign.py` (terminal, Python 3.8+), with the IAU star list as JSON and CSV | browser, terminal |\n"
              "| `tools/mark-tuner` | `index.html`: tune the mark and both lockups in the browser and export SVGs | browser |\n"
              "| `product` | The product system: how FusionSpace sites, tools, PWAs, CLIs, iOS, Android, macOS, Windows and Linux apps, flight computers, boards and rockets are designed. Rules (start with `product/README.md`), tokens for every platform, a web stylesheet with a specimen and example screens, icons, device-screen mock-ups, a KiCad board title block, livery sheets, desktop packaging | anything |\n"
              "| `tools/build` | The scripts that build every file here (`python3 tools/build/build.py`); see `tools/build/README.md` | terminal |")]
    for a, b in reps:
        if a not in s: print("README WARN:", a[:60]); continue
        s = s.replace(a, b)
    s = s.rstrip("\n") + "\n\n" + README_LICENSE
    wr("README.md", s)

README_LICENSE = """## License and trademarks

- **Code.** The build scripts and the mark tuner in `tools/` are licensed under the Apache License 2.0 (`tools/LICENSE`). The
  license covers the code, not the FusionSpace name or logo, including the artwork the code draws.
- **Product code.** The code-like files in `product/` are Apache-2.0 too, so any project can copy them in: the tokens
  (`product/tokens/`), `fusionspace.css`, the Tailwind and mdBook themes, the CLI styles, the LVGL styles and the Linux
  desktop templates. Each file says so in an SPDX line.
- **Brand.** The FusionSpace name, the four-cone mark, both lockups and every brand file here (`logo/`, `kit/`, `guide/`,
  `graphics/`, `color/`, `templates/`, `source/`, and the rest of `product/`) are © 2026 Neer Patel, all rights reserved. They're published to show the work.
  `TRADEMARKS.md` says what's fine, such as linking to my projects and showing the logo unchanged when you mention them.
- **Fonts.** Archivo and Cascadia Mono in `type/fonts/` are under the SIL Open Font License, with the license files next to them.

See `LICENSE` for the full terms.
"""

def build_all():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    build_marks(); info = build_lockups(); build_favicons(); build_pngs(); dxf = build_dxf()
    build_wordmarks(); build_construction(); build_tokens(); build_graphics(); build_social(); build_freecad()
    import kit; kit_info = kit.build_kit()
    import kit_product; kit_product.build_product()   # product/: the product system (needs the logos above)
    build_guide(info); build_readme()
    import kit_callsign; kit_callsign.build_callsign()   # tools/callsign/
    import kit_review; review = kit_review.build_review()   # review.html: every output, for sign-off
    return info, dxf, kit_info, review

if __name__ == "__main__":
    if os.environ.get("PYTHONHASHSEED") != "0":            # fixed set/dict-of-set ordering (ezdxf writes DXF objects in set order)
        import sys; os.environ["PYTHONHASHSEED"] = "0"; os.execv(sys.executable, [sys.executable] + sys.argv)
    print(build_all())
