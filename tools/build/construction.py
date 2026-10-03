"""Construction drawing for the Rev C cone cluster."""
import math
import geo
from build import grad, header, f, PAPER

INK, SLATE, ION = "#0B0F1C", "#566079", "#3350D6"
CANVAS_W, CANVAS_H = 910, 1040
FONT = "font-family:'Cascadia Mono',monospace"

def T(x, y, s, size=13, anchor="start", fill=INK, rot=None):
    if rot is not None:
        return f'<text transform="translate({f(x)},{f(y)}) rotate({rot})" text-anchor="{anchor}" fill="{fill}" style="{FONT};font-size:{size}px">{s}</text>'
    return f'<text x="{f(x)}" y="{f(y)}" text-anchor="{anchor}" fill="{fill}" style="{FONT};font-size:{size}px">{s}</text>'

def arrow(x, y, deg):
    return f'<path d="M0,0 L-9,-3.2 L-9,3.2 Z" fill="{INK}" transform="translate({f(x)},{f(y)}) rotate({f(deg)})"/>'

def hdim(x0, x1, y, label, ext_from=None, above=True):
    s = ""
    if ext_from is not None:
        s += f'<path d="M{f(x0)},{f(ext_from[0])} V{f(y + 8)} M{f(x1)},{f(ext_from[1])} V{f(y + 8)}" stroke="{SLATE}" stroke-width="0.75"/>'
    s += f'<path d="M{f(x0)},{f(y)} H{f(x1)}" stroke="{INK}" stroke-width="1"/>' + arrow(x0, y, 180) + arrow(x1, y, 0)
    s += T((x0 + x1) / 2, y - 8 if above else y + 18, label, 13, "middle")
    return s

def vdim(x, y0, y1, label, ext_from=None, text_side=1):
    s = ""
    if ext_from is not None:
        s += f'<path d="M{f(ext_from[0])},{f(y0)} H{f(x + 8 * text_side)} M{f(ext_from[1])},{f(y1)} H{f(x + 8 * text_side)}" stroke="{SLATE}" stroke-width="0.75"/>'
    s += f'<path d="M{f(x)},{f(y0)} V{f(y1)}" stroke="{INK}" stroke-width="1"/>' + arrow(x, y0, -90) + arrow(x, y1, 90)
    s += T(x + 18 * text_side, (y0 + y1) / 2, label, 13, "middle", rot=90 if text_side > 0 else -90)
    return s

def centerline(d):
    return f'<path d="{d}" stroke="{SLATE}" stroke-width="0.75" stroke-dasharray="14 3 2 3" fill="none"/>'

def pts_bbox(segs):
    p = geo.sample(segs); xs = [q[0] for q in p]; ys = [q[1] for q in p]
    return min(xs), min(ys), max(xs), max(ys)

def body(prefix="cons"):
    out = []; defs = []
    r = geo.W_K                       # Von Karman base radius, in units of a
    B = (1 - geo.TIP_K) * geo.H_K
    # ------------------------------------------------ 1 · CONE
    out.append(T(30, 40, "1 · CONE (VON KÁRMÁN)"))
    a = 150.0
    cx, cy = 190.0, 215.0
    H, W = geo.H_K * a, geo.W_K * a
    ytip, yb = cy - geo.TIP_K * H, cy + (1 - geo.TIP_K) * H
    sag = geo.SAG_K * W; R = (W * W + sag * sag) / (2 * sag); ncy = yb - sag + R
    segs = geo.cone_segments("main", a, (cx, cy), tilt=0, size=1, pos=(0, 0))
    defs.append(grad(f"{prefix}-grad-1", cx - W, cx + W))
    out.append(f'<rect x="{f(cx - W)}" y="{f(ytip)}" width="{f(2 * W)}" height="{f(H)}" fill="none" stroke="{ION}" stroke-width="0.75"/>')
    out.append(f'<circle cx="{f(cx)}" cy="{f(ncy)}" r="{f(R)}" fill="none" stroke="{ION}" stroke-width="1" stroke-dasharray="6 4"/>')
    out.append(f'<path d="{geo.seg_to_d(segs)}" fill="url(#{prefix}-grad-1)"/>')
    out.append(f'<circle cx="{f(cx)}" cy="{f(ncy)}" r="2.5" fill="{ION}"/>')
    out.append(centerline(f"M{f(cx)},{f(ytip - 22)} V{f(ncy + R + 14)}"))
    lx, ly = cx + R * math.cos(math.radians(40)), ncy + R * math.sin(math.radians(40))
    out.append(f'<path d="M{f(cx)},{f(ncy)} L{f(lx)},{f(ly)} L{f(lx + 26)},{f(ly + 22)} H{f(lx + 56)}" stroke="{SLATE}" stroke-width="0.75" fill="none"/>')
    out.append(T(lx + 62, ly + 27, f"R = {R / W:.2f} r"))
    Lr = geo.H_K / geo.W_K
    out.append(vdim(cx + W + 52, ytip, yb, f"L = {Lr:.2f} r", ext_from=(cx + 6, cx + W + 4)))
    out.append(hdim(cx - W, cx + W, ncy + R + 38, "2 r", ext_from=(yb + 4, yb + 4), above=False))
    out.append(vdim(cx - W - 46, yb - sag, yb, f"{geo.SAG_K:.2f} r", ext_from=(cx - 6, cx - W - 4), text_side=-1))
    out.append(T(cx - W - 14, ytip + 14, "r = base radius", 11, "end", fill=SLATE))
    # ------------------------------------------------ 4 · PROFILES
    out.append(T(30, 470, "4 · PROFILES (EQUAL L / R)"))
    pa = 72.0
    kinds = [(geo.KINDS[n], geo.PROFILE_NAMES[geo.KINDS[n]].upper(), "r" if geo.SIZE[n] == 1 else f"{geo.SIZE[n]:.1f} r") for n in ("main", "west", "south", "east")]
    for i, (k, lab, who) in enumerate(kinds):
        px = 75 + i * 100; py = 545
        sg = geo.cone_segments("main", pa, (px, py), tilt=0, kind=k, size=1, pos=(0, 0))
        defs.append(grad(f"{prefix}-grad-p{i}", px - geo.W_K * pa, px + geo.W_K * pa))
        out.append(f'<path d="{geo.seg_to_d(sg)}" fill="url(#{prefix}-grad-p{i})"/>')
        out.append(T(px, 606, lab, 10, "middle"))
        out.append(T(px, 620, who, 10, "middle", fill=SLATE))
    # ------------------------------------------------ 2 · SPACING on the leaned grid
    out.append(T(470, 40, f"2 · SPACING ON THE {geo.TILT:g}° GRID"))
    up = geo.POS_UPRIGHT
    # fit the leaned cluster into the panel (leaving room for the dimensions), then draw upright inside a rotated group
    b0 = geo.bbox(geo.cluster())
    A = min(300.0 / (b0[2] - b0[0]), 250.0 / (b0[3] - b0[1]))
    px0, py0 = 690.0 - A * (b0[0] + b0[2]) / 2, 215.0 - A * (b0[1] + b0[3]) / 2
    upc = {n: geo.cone_segments(n, A, (0, 0), tilt=0, pos=up[n]) for n in geo.ORDER}
    g_open = f'<g transform="translate({f(px0)},{f(py0)}) rotate({geo.TILT:g})">'
    inner = []
    allx = [p[0] for n in geo.ORDER for p in geo.sample(upc[n])]
    ally = [p[1] for n in geo.ORDER for p in geo.sample(upc[n])]
    defs.append(grad(f"{prefix}-grad-s", min(allx), max(allx)))
    for n in geo.DRAW_ORDER:
        inner.append(f'<path d="{geo.seg_to_d(upc[n])}" fill="url(#{prefix}-grad-s)"/>')
    def corner(n, side):                      # foot corner (the visible bottom corner of each cone)
        c = up[n]; s_ = geo.SIZE[n]; hf, xf, _ = geo.foot(geo.KINDS[n], s_)
        return (A * (c[0] + side * xf), A * (c[1] + B * s_ - hf))
    yh = corner("main", 1)[1]
    yw = A * (up["west"][1] + geo.centroid_y(geo.KINDS["west"], geo.SIZE["west"]))       # wing centroid line
    xl, xr = min(allx) - 14, max(allx) + 14
    inner.append(f'<path d="M{f(xl)},{f(yh)} H{f(xr)} M{f(xl)},{f(yw)} H{f(xr)}" stroke="{ION}" stroke-width="0.75" stroke-dasharray="6 4" fill="none"/>')
    for n in ("west", "east"):                 # centroid marks
        cx_ = A * up[n][0]
        inner.append(f'<circle cx="{f(cx_)}" cy="{f(yw)}" r="3.2" fill="{PAPER}" stroke="{INK}" stroke-width="1"/><path d="M{f(cx_ - 6)},{f(yw)} H{f(cx_ + 6)} M{f(cx_)},{f(yw - 6)} V{f(yw + 6)}" stroke="{INK}" stroke-width="0.75"/>')
    inner.append(centerline(f"M0,{f(min(ally) - 16)} V{f(max(ally) + 16)}"))
    ydim = max(corner("west", 1)[1], corner("east", -1)[1], yh) + 22
    pairs = [(corner("west", 1), corner("main", -1), "g₁"), (corner("main", 1), corner("east", -1), "g₂")]
    for p, q, lab in pairs:
        inner.append(f'<path d="M{f(p[0])},{f(p[1] + 4)} V{f(ydim + 6)} M{f(q[0])},{f(q[1] + 4)} V{f(ydim + 6)}" stroke="{SLATE}" stroke-width="0.75"/>')
        inner.append(f'<path d="M{f(p[0])},{f(ydim)} H{f(q[0])}" stroke="{INK}" stroke-width="1"/>' + arrow(p[0], ydim, 180) + arrow(q[0], ydim, 0))
        inner.append(T((p[0] + q[0]) / 2, ydim + 18, lab, 12, "middle"))
    # wing centroid line below the Von Karman foot line
    lx = xr + 10
    if abs(yw - yh) > 1:
        inner.append(f'<path d="M{f(lx)},{f(yh)} V{f(yw)}" stroke="{INK}" stroke-width="1"/>' + arrow(lx, yh, -90 if yw > yh else 90) + arrow(lx, yw, 90 if yw > yh else -90))
    inner.append(T(lx + 8, (yh + yw) / 2 + 4, "w", 12, "start"))
    # tail: ogive tip to the Von Karman foot line, on the shared axis
    st = A * (up["south"][1] - geo.TIP_K * geo.H_K * geo.SIZE["south"])
    dx = -A * geo.W_K * geo.SIZE["south"] - 16
    inner.append(f'<path d="M-4,{f(st)} H{f(dx - 8)}" stroke="{SLATE}" stroke-width="0.75"/>')
    if abs(st - yh) > 1:
        inner.append(f'<path d="M{f(dx)},{f(st)} V{f(yh)}" stroke="{INK}" stroke-width="1"/>' + arrow(dx, st, 90 if st < yh else -90) + arrow(dx, yh, -90 if st < yh else 90))
    inner.append(T(dx - 8, (st + yh) / 2 + 4, "t", 12, "end"))
    out.append(g_open + "".join(inner) + "</g>")
    side = "above" if geo.TAIL_R < 0 else "below"
    wside = "below" if geo.WING_R >= 0 else "above"
    out.append(T(470, 400, f"g₁ = {geo.GAP_W_R:.2f} r, g₂ = {geo.GAP_E_R:.2f} r from the Von Kármán foot corners to the", 11, fill=SLATE))
    out.append(T(470, 416, f"wings. Wing centroids share a line w = {abs(geo.WING_R):.2f} r {wside} the", 11, fill=SLATE))
    out.append(T(470, 432, f"Von Kármán foot line. The ogive is the tail, on the same axis,", 11, fill=SLATE))
    out.append(T(470, 448, f"tip t = {abs(geo.TAIL_R):.2f} r {side} the Von Kármán foot line.", 11, fill=SLATE))
    out.append(T(470, 464, "Lay out on the grid, then the grid leans as one piece.", 11, fill=SLATE))
    # ------------------------------------------------ 3 · CLUSTER
    top3 = 500
    out.append(T(470, top3, "3 · CLUSTER"))
    b = geo.bbox(geo.cluster())
    A = min(340.0 / (b[2] - b[0]), 230.0 / (b[3] - b[1]))
    org = (490 - A * b[0], top3 + 40 - A * b[1])
    cl = geo.cluster(A, org); bb = geo.bbox(cl)
    defs.append(grad(f"{prefix}-grad-2", bb[0], bb[2]))
    for n in geo.DRAW_ORDER:
        out.append(f'<path d="{geo.seg_to_d(cl[n])}" fill="url(#{prefix}-grad-2)"/>')
    # tilt callout at the main cone
    ang = math.radians(geo.TILT)
    mb = geo.rot((0, B), (0, 0), geo.TILT); mbp = (org[0] + A * mb[0], org[1] + A * mb[1])
    rr = 150
    out.append(f'<path d="M{f(mbp[0])},{f(mbp[1])} V{f(mbp[1] - rr - 12)}" stroke="{SLATE}" stroke-width="0.75"/>')
    out.append(centerline(f"M{f(mbp[0])},{f(mbp[1])} L{f(mbp[0] + (rr + 12) * math.sin(ang))},{f(mbp[1] - (rr + 12) * math.cos(ang))}"))
    p0 = (mbp[0], mbp[1] - rr); p1 = (mbp[0] + rr * math.sin(ang), mbp[1] - rr * math.cos(ang))
    out.append(f'<path d="M{f(p0[0])},{f(p0[1])} A{rr},{rr} 0 0 1 {f(p1[0])},{f(p1[1])}" stroke="{INK}" stroke-width="1" fill="none"/>')
    out.append(T(mbp[0] - 8, mbp[1] - rr - 2, f"{geo.TILT:g}°", 13, "end"))
    wa, ha = (b[2] - b[0]) / r, (b[3] - b[1]) / r
    allp = [p for n in geo.ORDER for p in geo.sample(cl[n])]
    pl = min(allp, key=lambda p: p[0]); pr = max(allp, key=lambda p: p[0])
    pt = min(allp, key=lambda p: p[1]); pb = max(allp, key=lambda p: p[1])
    out.append(hdim(bb[0], bb[2], bb[3] + 30, f"{wa:.2f} r", ext_from=(pl[1] + 4, pr[1] + 4), above=False))
    out.append(vdim(bb[2] + 30, bb[1], bb[3], f"{ha:.2f} r", ext_from=(pt[0] + 4, pb[0] + 4)))
    # ------------------------------------------------ 5 · FEET (detail)
    out.append(T(30, 655, "5 · FEET (DETAIL)"))
    def foot_detail(name, wx, wy, ww, wh, label):
        """Right foot of one cone, upright and magnified, inside the window (wx, wy, ww, wh)."""
        kind = geo.KINDS[name]; s_ = geo.SIZE[name]
        W, L = geo.W_K * s_, geo.H_K * s_
        sag = geo.SAG_K * W; Rn = (W * W + sag * sag) / (2 * sag); c0 = Rn - sag
        hf, xf, xa = geo.foot(kind, s_)
        xa_h = lambda h: math.sqrt(max(Rn * Rn - (h + c0) ** 2, 0.0))
        H = min(1.6 * hf, 0.85 * sag)                      # top of the detail, above the base line
        x_l, x_r = xa_h(H), W                              # content span at the top of the detail
        sc = min((wh - 26) / H, (ww - 40) / (x_r - x_l))
        ox = wx + ww / 2 + sc * (W - (x_l + x_r) / 2)       # where the base corner (W, 0) lands
        oy = wy + wh - 10
        P = lambda x, h: (ox + sc * (x - W), oy - sc * h)
        cid = f"{prefix}-clip-{name}"
        defs.append(f'<clipPath id="{cid}"><rect x="{f(wx)}" y="{f(wy)}" width="{f(ww)}" height="{f(wh)}"/></clipPath>')
        n = 60
        Ht = H * 1.3
        fl = [P(geo.flank_x(kind, W, L, Ht - (Ht - hf) * i / n), Ht - (Ht - hf) * i / n) for i in range(n + 1)]
        nt = [P(xa_h(hf + (Ht - hf) * i / n), hf + (Ht - hf) * i / n) for i in range(n + 1)]
        d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in fl + nt) + " Z"
        defs.append(grad(f"{prefix}-grad-f{name}", wx, wx + ww))
        g = [f'<path d="{d}" fill="url(#{prefix}-grad-f{name})"/>']
        # the uncut outline below the cut: flank and notch arc down to the base line, and the base line
        for fn in (lambda h: geo.flank_x(kind, W, L, h), xa_h):
            pts = [P(fn(hf * (1 - i / n)), hf * (1 - i / n)) for i in range(n + 1)]
            g.append('<path d="M' + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + f'" stroke="{ION}" stroke-width="1" stroke-dasharray="5 3" fill="none"/>')
        g.append(f'<path d="M{f(wx)},{f(oy)} H{f(wx + ww)}" stroke="{SLATE}" stroke-width="0.75" stroke-dasharray="14 3 2 3"/>')
        out.append(f'<rect x="{f(wx)}" y="{f(wy)}" width="{f(ww)}" height="{f(wh)}" fill="none" stroke="{SLATE}" stroke-width="0.5"/>')
        out.append(f'<g clip-path="url(#{cid})">' + "".join(g) + "</g>")
        # foot width dimension, under the window
        q0, q1 = P(xa, hf), P(xf, hf)
        yd = wy + wh + 16
        out.append(f'<path d="M{f(q0[0])},{f(q0[1] + 3)} V{f(yd + 6)} M{f(q1[0])},{f(q1[1] + 3)} V{f(yd + 6)}" stroke="{SLATE}" stroke-width="0.75"/>')
        out.append(f'<path d="M{f(q0[0] - 22)},{f(yd)} H{f(q1[0] + 22)}" stroke="{INK}" stroke-width="1"/>' + arrow(q0[0], yd, 0) + arrow(q1[0], yd, 180))
        out.append(T(q0[0] - 26, yd + 4, f"{geo.FOOT_K:.2f}", 11, "end"))
        out.append(T(wx + ww / 2, yd + 22, label, 10, "middle", fill=SLATE))
    foot_detail("main", 60, 668, 140, 120, "VON KÁRMÁN")
    foot_detail("west", 250, 668, 140, 120, "CONICAL")
    for i, line in enumerate(["Each foot is cut flat, parallel to the base (dash-dot),",
                              f"where the wall between flank and notch is {geo.FOOT_K:.2f} × the",
                              "cone's base radius wide. Dashed: the uncut outline. On",
                              "the conical cone the notch arc runs outside the straight",
                              "flank near the base, so the cut also removes that sliver."]):
        out.append(T(30, 862 + 16 * i, line, 11, fill=SLATE))
    # ------------------------------------------------ table (right, under the cluster)
    ty = 850
    out.append(T(470, ty, "CONE     PROFILE          RADIUS   BASE CENTRE (u, v)".replace(" ", "&#160;"), 12, fill=SLATE))
    for i, n in enumerate(geo.ORDER):
        c = up[n]; s_ = geo.SIZE[n]
        u, v = c[0] / r, (c[1] + B * s_ - B) / r
        prof = geo.PROFILE_NAMES[geo.KINDS[n]].upper()
        rad = "r" if s_ == 1 else f"{s_:.1f} r"
        out.append(T(470, ty + 20 * (i + 1), f"{n.upper():<9}{prof:<17}{rad:<9}({u:+.1f}, {v:+.1f})".replace(" ", "&#160;"), 12))
    out.append(T(470, ty + 110, "u, v in r on the leaned grid, v down.", 11, fill=SLATE))
    out.append(T(30, CANVAS_H - 44, f"Standard nose-cone profiles, L = {Lr:.2f} × base radius, notch {geo.SAG_K:.2f} deep, feet cut flat where the wall is {geo.FOOT_K:.2f} wide (all × base radius).", 11, fill=SLATE))
    out.append(T(30, CANVAS_H - 27, f"Von Kármán is the LD-Haack series (C = 0), drawn as smooth curves. The whole cluster leans {geo.TILT:g}° as one piece.", 11, fill=SLATE))
    out.append(T(30, CANVAS_H - 10, "One gradient spans the whole cluster, M orange left to O blue right.", 11, fill=SLATE))
    return "".join(defs), "\n".join(out)

def construction_svg():
    defs, b = body("cons")
    s = header(CANVAS_W, CANVAS_H, "FusionSpace mark construction", "", PAPER)
    s += '<defs id="defs"></defs>\n<g inkscape:groupmode="layer" id="layer-construction" inkscape:label="Construction">\n'
    s += f"<defs>{defs}</defs>\n{b}\n</g>\n</svg>\n"
    return s
