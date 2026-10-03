"""FusionSpace Rev C mark: four nose-cone profiles, 22.5° lean, deep notch.
Local cone frame (size s): tip at (0,-0.58H), base corners (+-W, 0.42H), H=1.30s, W=0.40s.
Everything is exact SVG geometry: lines, circular arcs, one elliptical arc, fitted cubics (Von Karman)."""
import math
import numpy as np
from scipy.optimize import minimize

TILT = 45.0
H_K, W_K, TIP_K = 1.40, 0.40, 0.58   # length / base radius = 3.50
SAG_K = 1.00                      # notch depth / half-width
FOOT_K = 0.05                     # foot width / base radius: each foot is cut off flat, parallel to the base
                                  # line, where the cone wall between flank and notch is this wide
KINDS = {"main": "vonkarman", "west": "conical", "east": "elliptical", "south": "ogive"}
NAMES = {"main": "Main cone", "west": "West cone", "east": "East cone", "south": "South cone"}
PROFILE_NAMES = {"vonkarman": "Von Kármán", "conical": "conical", "ogive": "tangent ogive", "elliptical": "elliptical"}
# Diamond spacing rule (read with the lean at 0): see layout(). Centres in units of a (main cone size), y down.
GAP_W_R = 0.19      # horizontal gap from the left Von Karman foot corner to the west wing's inner foot corner, in r
GAP_E_R = 0.23      # horizontal gap from the right Von Karman foot corner to the east wing's inner foot corner, in r
WING_R = 0.47       # wing centroid line (both wings' area centroids) relative to the Von Karman foot line, in r (+ = below)
TAIL_R = 0.21      # tail cone (ogive) tip relative to the Von Karman foot line, in r (+ = below, - = up into the notch)

def centroid_y(kind, s):
    """Height of a cone's area centroid relative to its own centre (y down), in units of a. Shoelace over the
    exact outline, sampled finely (the outline is lines, arcs and cubics; 200 points per segment)."""
    pts = sample(cone_segments(None, 1.0, (0.0, 0.0), tilt=0.0, kind=kind, size=s, pos=(0.0, 0.0)), 200)
    a2 = 0.0; cy = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]
        c = x0 * y1 - x1 * y0
        a2 += c; cy += (y0 + y1) * c
    return cy / (3.0 * a2)

def layout(gap_w_r=None, gap_e_r=None, wing_r=None, tail_r=None, tilt=None):
    """Diamond: with the lean at 0, the Von Karman cone is north, the ogive sits behind it (south) on the same
    axis, and the conical (west) and elliptical (east) cones are the wings, with their area centroids on one
    line. Laid out upright on the grid, then the whole grid is rotated by TILT. Returns cone centres in units
    of a (main cone size), y down. Each cone's foot line is its visible bottom edge (see foot())."""
    gap_w_r = GAP_W_R if gap_w_r is None else gap_w_r
    gap_e_r = GAP_E_R if gap_e_r is None else gap_e_r
    wing_r = WING_R if wing_r is None else wing_r
    tail_r = TAIL_R if tail_r is None else tail_r
    tilt = TILT if tilt is None else tilt
    r = W_K                                  # Von Karman base radius in units of a
    B = (1 - TIP_K) * H_K                    # centre-to-base, per unit size
    F = {n: foot(KINDS[n], SIZE[n]) for n in SIZE}          # (height above base, flank half-width, notch half-width)
    cf = {n: B * SIZE[n] - F[n][0] for n in SIZE}           # centre to foot line
    X = {n: F[n][1] for n in SIZE}                          # foot corner half-width
    yf = cf["main"]                                         # Von Karman foot line
    wing = yf + wing_r * r                                  # wing centroid line
    up = {"main": (0.0, 0.0)}
    up["west"] = (-X["main"] - gap_w_r * r - X["west"], wing - centroid_y(KINDS["west"], SIZE["west"]))
    up["east"] = (X["main"] + gap_e_r * r + X["east"], wing - centroid_y(KINDS["east"], SIZE["east"]))
    up["south"] = (0.0, yf + tail_r * r + TIP_K * H_K * SIZE["south"])
    return {n: rot(p, (0.0, 0.0), tilt) for n, p in up.items()}, up

SIZE = {"main": 1.0, "west": 0.40, "east": 0.30, "south": 0.50}   # base radius relative to r (Von Karman)
ORDER = ["main", "west", "east", "south"]
DRAW_ORDER = ["south", "west", "east", "main"]   # back to front: the ogive (south, the tail) sits behind the Von Karman

# ---------- Von Karman (LD-Haack, C = 0) as C1-continuous cubic Beziers ----------
# Wikipedia / Haack: theta = arccos(1 - 2x/L), y = R/sqrt(pi) * sqrt(theta - sin(2 theta)/2 + C sin^3 theta)
# Normalised (r in units of R, x in units of L, x from the tip). Tangent at the tip is perpendicular to the axis.
def _haack_pt(t):
    th = math.acos(1 - 2 * t)
    return (math.sqrt(max(th - math.sin(2 * th) / 2, 0.0)) / math.sqrt(math.pi), t)

def _haack_tan(t):
    if t <= 0: return (1.0, 0.0)
    if t >= 1: return (0.0, 1.0)
    th = math.acos(1 - 2 * t)
    g = th - math.sin(2 * th) / 2
    drdx = 2 * math.sin(th) / (math.sqrt(math.pi) * math.sqrt(g))
    n = math.hypot(drdx, 1.0)
    return (drdx / n, 1.0 / n)

VK_BREAKS = [0.0, 0.004, 0.03, 0.12, 0.35, 1.0]
def _fit_segment(t0, t1):
    p0, p3 = np.array(_haack_pt(t0)), np.array(_haack_pt(t1))
    d0, d3 = np.array(_haack_tan(t0)), np.array(_haack_tan(t1))
    ts = np.linspace(t0, t1, 120)
    ref = np.array([_haack_pt(t) for t in ts])
    def curve(h):
        P = np.array([p0, p0 + h[0] * d0, p3 - h[1] * d3, p3])
        return P, _bez(P, np.linspace(0, 1, 240))
    def err(h):
        P, B = curve(h)
        d = np.min(np.linalg.norm(ref[:, None, :] - B[None, :, :], axis=2), axis=1)
        return float(np.max(d))
    L = float(np.linalg.norm(p3 - p0))
    best = min((minimize(err, [L * k, L * k], method="Nelder-Mead", options={"xatol": 1e-10, "fatol": 1e-12, "maxiter": 6000})
                for k in (0.2, 0.33, 0.45)), key=lambda r: r.fun)
    P, _ = curve(best.x)
    return P, best.fun

def _bez(P, t):
    t = t[:, None]
    return ((1 - t) ** 3) * P[0] + 3 * ((1 - t) ** 2) * t * P[1] + 3 * (1 - t) * t * t * P[2] + t ** 3 * P[3]

VK_SEGS = []
VK_ERR = 0.0
for _i in range(len(VK_BREAKS) - 1):
    _P, _e = _fit_segment(VK_BREAKS[_i], VK_BREAKS[_i + 1])
    VK_SEGS.append(_P); VK_ERR = max(VK_ERR, _e)
def vk_max_error(): return VK_ERR

# ---------- feet ----------
def _bez1(P, u):
    m = 1 - u
    return (m * m * m * P[0][0] + 3 * m * m * u * P[1][0] + 3 * m * u * u * P[2][0] + u * u * u * P[3][0],
            m * m * m * P[0][1] + 3 * m * m * u * P[1][1] + 3 * m * u * u * P[2][1] + u * u * u * P[3][1])

def _vk_at(tn):
    """Point on the fitted Von Karman curve at normalised distance tn from the tip: (segment, u, radius/R)."""
    for i, P in enumerate(VK_SEGS):
        if P[3][1] >= tn or i == len(VK_SEGS) - 1: break
    if tn >= P[3][1]: return i, 1.0, float(P[3][0])
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if _bez1(P, mid)[1] < tn: lo = mid
        else: hi = mid
    u = (lo + hi) / 2
    return i, u, float(_bez1(P, u)[0])

def flank_x(kind, W, L, h):
    """Half-width of the drawn profile at height h above the base line."""
    if kind == "conical": return W * (L - h) / L
    if kind == "ogive":
        rho = (W * W + L * L) / (2 * W); return math.sqrt(max(rho * rho - h * h, 0.0)) + W - rho
    if kind == "elliptical": return W * math.sqrt(max(1 - h * h / (L * L), 0.0))
    return W * _vk_at((L - h) / L)[2]

_FOOT_CACHE = {}
FOOT_STEPS = 400
def foot(kind, s, min_wall=0.0):
    """Where the foot is cut: (h, xf, xa) in units of a. h is the height above the base line, xf the flank
    half-width and xa the notch half-width there. It is the lowest height from which the wall between flank
    and notch is at least FOOT_K x W wide all the way up (so a notch that bulges outside a straight
    conical flank is always cut away). min_wall (units of a) is a production floor: the wall is at least
    max(FOOT_K x W, min_wall) wide. It is only used for cut files (see build.build_dxf); the layout always
    uses the brand foot (min_wall = 0)."""
    key = (kind, s, H_K, W_K, SAG_K, FOOT_K, min_wall)
    if key in _FOOT_CACHE: return _FOOT_CACHE[key]
    W, L = W_K * s, H_K * s
    sag = SAG_K * W; Rn = (W * W + sag * sag) / (2 * sag); c = Rn - sag
    xa = lambda h: math.sqrt(max(Rn * Rn - (h + c) * (h + c), 0.0))
    wall = max(FOOT_K * W, min_wall)
    d = lambda h: flank_x(kind, W, L, h) - xa(h) - wall
    lo = 0.0
    for i in range(FOOT_STEPS - 1, -1, -1):                 # walk down from the top of the notch
        h = sag * i / FOOT_STEPS
        if d(h) < 0: lo = h; break
    else:
        _FOOT_CACHE[key] = (0.0, W, W); return _FOOT_CACHE[key]
    hi = lo + sag / FOOT_STEPS
    for _ in range(60):
        mid = (lo + hi) / 2
        if d(mid) < 0: lo = mid
        else: hi = mid
    h = hi
    _FOOT_CACHE[key] = (h, flank_x(kind, W, L, h), xa(h))
    return _FOOT_CACHE[key]

def _split(P, u):
    """Left part [0, u] of a cubic (de Casteljau)."""
    if u >= 1.0: return [tuple(p) for p in P]
    l = lambda a, b: (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
    a, b, c = l(P[0], P[1]), l(P[1], P[2]), l(P[2], P[3])
    d, e = l(a, b), l(b, c)
    return [tuple(P[0]), a, d, l(d, e)]

# ---------- segments ----------
def rot(p, c, deg):
    a = math.radians(deg); x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def cone_segments(name, A=1.0, origin=(0.0, 0.0), tilt=TILT, kind=None, size=None, pos=None, min_wall=0.0):
    """Segments in output coords. A = px per unit; origin = where unit (0,0) lands. min_wall: see foot()."""
    s = SIZE[name] if size is None else size
    cx, cy = POS[name] if pos is None else pos
    H, W = H_K * s, W_K * s
    ytip, yb = cy - TIP_K * H, cy + (1 - TIP_K) * H
    L = yb - ytip
    kind = kind or KINDS[name]
    c = (cx, cy)
    def T(p):
        q = rot(p, c, tilt)
        return (origin[0] + A * q[0], origin[1] + A * q[1])
    hf, xf, xa = foot(kind, s, min_wall)
    yf = yb - hf
    tip = (cx, ytip)
    fr, fl, nr, nl = (cx + xf, yf), (cx - xf, yf), (cx + xa, yf), (cx - xa, yf)   # foot corners, notch ends
    if kind == "vonkarman":
        i, u, _ = _vk_at((L - hf) / L)
        vk = [P for P in VK_SEGS[:i]] + [_split(VK_SEGS[i], u)]
    segs = [("M", T(tip))]
    def flank(p_to, side):                  # side +1 right flank (tip->foot), -1 left (foot->tip)
        if kind == "conical":
            return [("L", T(p_to))]
        if kind == "ogive":
            rho = (W * W + L * L) / (2 * W)
            return [("A", A * rho, A * rho, 0.0, 0, 1, T(p_to))]
        if kind == "elliptical":
            return [("A", A * W, A * L, tilt, 0, 1, T(p_to))]
        if kind == "vonkarman":
            out = []
            segs_n = vk if side > 0 else [P[::-1] for P in vk[::-1]]
            for P in segs_n:
                pts = [(cx + side * q[0] * W, ytip + q[1] * L) for q in P]
                out.append(("C", T(pts[1]), T(pts[2]), T(pts[3])))
            return out
    segs += flank(fr, +1)
    if hf > 0: segs += [("L", T(nr))]
    sag = SAG_K * W
    R = (W * W + sag * sag) / (2 * sag)
    segs += [("A", A * R, A * R, 0.0, 0, 0, T(nl))]
    if hf > 0: segs += [("L", T(fl))]
    segs += flank(tip, -1)
    segs += [("Z",)]
    return segs

def fnum(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

def seg_to_d(segs):
    out = []
    for sg in segs:
        k = sg[0]
        if k in "ML": out.append(f"{k}{fnum(sg[1][0])},{fnum(sg[1][1])}")
        elif k == "A": out.append(f"A{fnum(sg[1])},{fnum(sg[2])} {fnum(sg[3])} {sg[4]} {sg[5]} {fnum(sg[6][0])},{fnum(sg[6][1])}")
        elif k == "C": out.append("C" + " ".join(f"{fnum(p[0])},{fnum(p[1])}" for p in sg[1:]))
        elif k == "Z": out.append("Z")
    return " ".join(out)

# ---------- sampling (for bbox, checks, DXF) ----------
def _arc_center(p0, p1, rx, ry, phi, fa, fs):
    # SVG spec F.6.5
    ph = math.radians(phi); cp, sp = math.cos(ph), math.sin(ph)
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1 = cp * dx + sp * dy; y1 = -sp * dx + cp * dy
    lam = x1 * x1 / (rx * rx) + y1 * y1 / (ry * ry)
    if lam > 1: rx *= math.sqrt(lam); ry *= math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    co = math.sqrt(max(0, num / den)) * (-1 if fa == fs else 1)
    cx1 = co * rx * y1 / ry; cy1 = -co * ry * x1 / rx
    cx = cp * cx1 - sp * cy1 + (p0[0] + p1[0]) / 2
    cy = sp * cx1 + cp * cy1 + (p0[1] + p1[1]) / 2
    def ang(u, v):
        a = math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]); return a
    t1 = ang((1, 0), ((x1 - cx1) / rx, (y1 - cy1) / ry))
    dt = ang(((x1 - cx1) / rx, (y1 - cy1) / ry), ((-x1 - cx1) / rx, (-y1 - cy1) / ry))
    if not fs and dt > 0: dt -= 2 * math.pi
    if fs and dt < 0: dt += 2 * math.pi
    return (cx, cy), rx, ry, t1, dt

def seg_param(p0, sg):
    """return f(t)->point for t in [0,1]"""
    k = sg[0]
    if k == "L":
        p1 = sg[1]; return lambda t: (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
    if k == "A":
        c, rx, ry, t1, dt = _arc_center(p0, sg[6], sg[1], sg[2], sg[3], sg[4], sg[5])
        ph = math.radians(sg[3]); cp, sp = math.cos(ph), math.sin(ph)
        def f(t):
            a = t1 + dt * t; x, y = rx * math.cos(a), ry * math.sin(a)
            return (c[0] + cp * x - sp * y, c[1] + sp * x + cp * y)
        return f
    if k == "C":
        c1, c2, p1 = sg[1], sg[2], sg[3]
        def f(t):
            m = 1 - t
            return (m**3 * p0[0] + 3 * m * m * t * c1[0] + 3 * m * t * t * c2[0] + t**3 * p1[0],
                    m**3 * p0[1] + 3 * m * m * t * c1[1] + 3 * m * t * t * c2[1] + t**3 * p1[1])
        return f

def seg_end(sg):
    return {"M": sg[1] if sg[0] == "M" else None}.get("M") if sg[0] == "M" else (sg[-1] if sg[0] != "Z" else None)

def sample(segs, n=120):
    pts = []; cur = None; start = None
    for sg in segs:
        if sg[0] == "M": cur = start = sg[1]; pts.append(cur); continue
        if sg[0] == "Z": continue
        f = seg_param(cur, sg)
        pts += [f(i / n) for i in range(1, n + 1)]
        cur = sg[-1]
    return pts

def cluster(A=1.0, origin=(0, 0)):
    return {n: cone_segments(n, A, origin) for n in ORDER}

def bbox(cl):
    xs, ys = [], []
    for segs in cl.values():
        for p in sample(segs): xs.append(p[0]); ys.append(p[1])
    return min(xs), min(ys), max(xs), max(ys)

def fit_cluster(height=None, width=None, x0=0.0, y0=0.0):
    """scale so cluster bbox has given height (or width), placed with bbox top-left at (x0,y0)"""
    b = bbox(cluster())
    w, h = b[2] - b[0], b[3] - b[1]
    A = height / h if height else width / w
    org = (x0 - A * b[0], y0 - A * b[1])
    cl = cluster(A, org)
    return cl, A, bbox(cl)

POS, POS_UPRIGHT = layout()   # after cone_segments()/sample(), which centroid_y() uses
