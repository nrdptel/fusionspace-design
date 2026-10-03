"""FusionSpace kit: solids for CAD and 3D printing (kit/3d-print/).

Outlines come in as shapely polygons (with holes) in millimetres, or, for the mark, as exact Outlines: the cones' own lines,
circular arcs, elliptical arc and cubic Béziers from geo.cone_segments(), placed by a similarity transform. In STEP the mark
is therefore exact (lines, circles, an ellipse and Bézier curves, no fitting); other outlines (the wordmark, plates built with
shapely) become smooth B-spline edges between their corners, fitted within STEP_TOL.

STEP and 3MF are written with Open CASCADE (the `cadquery-ocp` package, `pip install cadquery-ocp`). Simple prints (layers
extruded between two heights) get their STL from kit_targets.extrude without OCP; the prints that need booleans (pockets,
slots, curved backs, engraving) are built as OCP solids and meshed with BRepMesh. Without OCP those, and every STEP and 3MF,
are skipped with a warning.

FDM rules for a 0.4 mm nozzle and 0.2 mm layers are the constants under "printer rules"; check_print() tests every printed
outline against them.

nonzero_region() turns SVG path data into the area it fills under SVG's default nonzero rule. The outlined wordmark is built
from overlapping and self-crossing contours (the letters are drawn that way in the font), so its subpaths can't be used one
by one as faces or cut lines.
"""
import os, re, math, datetime
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union, polygonize

try:
    from OCP.gp import gp_Pnt, gp_Vec
    try: from OCP.TColgp import TColgp_Array1OfPnt                     # OCP 7.x
    except ImportError: from OCP.collections import Array1_gp_Pnt as TColgp_Array1OfPnt   # OCP 8: NCollection arrays live here
    from OCP.GeomAPI import GeomAPI_PointsToBSpline
    from OCP.GeomAbs import GeomAbs_C2
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
    from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCP.ShapeFix import ShapeFix_Face, ShapeFix_Wire
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.BRep import BRep_Builder, BRep_Tool
    from OCP.TopoDS import TopoDS_Compound
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCP.Interface import Interface_Static
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.gp import gp_Dir, gp_Ax1, gp_Ax2, gp_Elips, gp_Trsf, gp_Pnt as _P
    from OCP.GC import GC_MakeArcOfCircle, GC_MakeArcOfEllipse
    from OCP.Geom import Geom_BezierCurve
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeBox
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID, TopAbs_REVERSED
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.STEPControl import STEPControl_Reader
    HAVE_OCC, OCC_ERROR = True, ""
except ImportError as e:
    HAVE_OCC, OCC_ERROR = False, str(e)

STEP_TOL = 0.002        # mm: largest distance between a fitted edge and the outline it follows
_FIT = [STEP_TOL]       # the tolerance in use (fit_tolerance() changes it for a block)

def fit_tolerance(tol):
    """with fit_tolerance(0.005): ... fits B-spline edges within tol instead of STEP_TOL (smaller files for plates)."""
    import contextlib
    @contextlib.contextmanager
    def cm():
        _FIT.append(tol)
        try: yield
        finally: _FIT.pop()
    return cm()
CORNER_DEG = 28.0       # a turn sharper than this between two sample steps is a corner (edges meet there, not smoothed)

# ---------------------------------------------------------------- outlines
def _winding(ring, pts):
    """Winding number of closed ring (N x 2) around each point (M x 2)."""
    a = ring; b = np.roll(ring, -1, axis=0)
    x, y = pts[:, 0][:, None], pts[:, 1][:, None]
    up = (a[:, 1][None] <= y) & (b[:, 1][None] > y)
    dn = (a[:, 1][None] > y) & (b[:, 1][None] <= y)
    side = (b[:, 0] - a[:, 0])[None] * (y - a[:, 1][None]) - (x - a[:, 0][None]) * (b[:, 1] - a[:, 1])[None]
    return (up & (side > 0)).sum(1) - (dn & (side < 0)).sum(1)

def nonzero_region(d, n=24):
    """The area SVG path data d fills (nonzero rule), as a shapely (Multi)Polygon in the path's units."""
    from svgpathtools import parse_path
    rings = []
    for sub in parse_path(d).continuous_subpaths():
        m = max(8, n * len(sub))
        r = np.array([(p.real, p.imag) for p in (sub.point(i / m) for i in range(m))])
        rings.append(r)
    faces = list(polygonize(unary_union([LineString(np.vstack([r, r[:1]])) for r in rings])))
    if not faces: return Polygon()
    reps = np.array([f.representative_point().coords[0] for f in faces])
    w = sum(_winding(r, reps) for r in rings)
    return unary_union([f for f, k in zip(faces, w) if k != 0]).buffer(0)

def polys_of(g):
    return [p for p in getattr(g, "geoms", [g]) if isinstance(p, Polygon) and not p.is_empty]

# ---------------------------------------------------------------- STEP
def _cross2(a, b):
    """z of the cross product of 2D vectors (NumPy 2 dropped 2D input to np.cross)."""
    a, b = np.broadcast_arrays(np.asarray(a, float), np.asarray(b, float))
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]

def _edges(coords, z):
    """Edges for one closed ring: B-splines between corners, straight lines where the run is straight."""
    P = np.array(coords[:-1] if np.allclose(coords[0], coords[-1]) else coords, dtype=float)
    keep = [0]
    for i in range(1, len(P)):
        if np.hypot(*(P[i] - P[keep[-1]])) > 1e-6: keep.append(i)
    P = P[keep]
    if np.hypot(*(P[-1] - P[0])) < 1e-6: P = P[:-1]
    n = len(P); dv = np.roll(P, -1, 0) - P
    ang = np.degrees(np.abs(np.arctan2(_cross2(np.roll(dv, 1, 0), dv), (np.roll(dv, 1, 0) * dv).sum(1))))
    seg = np.hypot(dv[:, 0], dv[:, 1]); long_ = seg > 4 * np.median(seg)       # a long straight side: its ends are breaks too
    corners = [i for i in range(n) if ang[i] > CORNER_DEG or long_[i] or long_[i - 1]]
    if not corners: corners = [0, n // 3, 2 * n // 3]          # a smooth closed loop: three B-splines
    edges = []
    for k, c0 in enumerate(corners):
        c1 = corners[(k + 1) % len(corners)]
        idx = list(range(c0, (c1 if c1 > c0 else c1 + n) + 1))
        run = P[[i % n for i in idx]]
        a, b = run[0], run[-1]
        chord = b - a; L = np.hypot(*chord)
        dev = np.abs(_cross2(chord, run - a)) / L if L > 1e-9 else np.hypot(*(run - a).T)
        if len(run) == 2 or dev.max() < _FIT[-1]:
            edges.append(BRepBuilderAPI_MakeEdge(gp_Pnt(a[0], a[1], z), gp_Pnt(b[0], b[1], z)).Edge())
        else:
            arr = _points([gp_Pnt(p[0], p[1], z) for p in run])
            crv = GeomAPI_PointsToBSpline(arr, 3, 8, GeomAbs_C2, _FIT[-1]).Curve()
            edges.append(BRepBuilderAPI_MakeEdge(crv).Edge())
    mw = BRepBuilderAPI_MakeWire()
    for e in edges: mw.Add(e)
    sw = ShapeFix_Wire(); sw.Load(mw.Wire()); sw.ClosedWireMode = True; sw.FixConnected(1e-4); sw.FixClosed(1e-4)
    return sw.Wire()

def _points(pts):
    """A 1-based point array for GeomAPI_PointsToBSpline (TColgp_Array1OfPnt in OCP 7, collections.Array1_gp_Pnt in OCP 8)."""
    try:
        arr = TColgp_Array1OfPnt(1, len(pts))
        for j, p in enumerate(pts): arr.SetValue(j + 1, p)
        return arr
    except TypeError:
        return TColgp_Array1OfPnt(pts)                                    # bindings that build the array from a list

def _solid(poly, z0, z1):
    poly = orient(poly, 1.0)
    mf = BRepBuilderAPI_MakeFace(_edges(list(poly.exterior.coords), z0), True)
    for h in poly.interiors: mf.Add(_edges(list(h.coords), z0))
    fx = ShapeFix_Face(mf.Face()); fx.Perform()
    s = BRepPrimAPI_MakePrism(fx.Face(), gp_Vec(0, 0, z1 - z0)).Shape()
    return s

def write_step(parts, path, name):
    """parts: [(shapely polygon, z0, z1)] in mm. One solid per polygon, all in one compound."""
    if not HAVE_OCC: return False
    comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp)
    for poly, z0, z1 in parts:
        for p in polys_of(poly):
            try: s = _solid(p, z0, z1)
            except Exception as e: raise ValueError(f"{name}: no solid for the outline at {[round(v, 2) for v in p.bounds]} ({len(p.exterior.coords)} points, {len(p.interiors)} holes): {e}")
            if not BRepCheck_Analyzer(s).IsValid(): raise ValueError(f"{name}: invalid solid")
            bb.Add(comp, s)
    Interface_Static.SetCVal_s("write.step.unit", "MM")
    Interface_Static.SetCVal_s("write.step.schema", "AP214IS")
    Interface_Static.SetCVal_s("write.step.product.name", name)
    w = STEPControl_Writer(); w.Transfer(comp, STEPControl_AsIs)
    if w.Write(path) != IFSelect_RetDone: raise IOError(path)
    # reproducible: fixed date, no local path, fixed originating system
    t = open(path, encoding="utf-8", errors="replace").read()
    when = datetime.datetime.fromtimestamp(int(os.environ.get("SOURCE_DATE_EPOCH", "1790812800")), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    t = re.sub(r"FILE_NAME\('[^']*','[^']*'", f"FILE_NAME('{os.path.basename(path)}','{when}'", t, count=1)
    t = re.sub(r"FILE_DESCRIPTION\(\('[^']*'\)", f"FILE_DESCRIPTION(('FusionSpace {name}')", t, count=1)
    with open(path, "w", encoding="utf-8", newline="\n") as fh: fh.write(t)
    return True

# ---------------------------------------------------------------- sketches (DXF and SVG outlines to import, extrude or cut)
def write_sketch_dxf(geom, path, layer="OUTLINE"):
    """Closed polylines for every ring of the region (outer and holes), in mm, y up, no default blocks."""
    import ezdxf
    try: ezdxf.options.write_fixed_meta_data_for_testing = True
    except Exception: pass
    doc = ezdxf.new("R2010", setup=False); doc.units = 4    # mm
    doc.layers.add(layer); msp = doc.modelspace()
    for p in polys_of(geom):
        for r in [p.exterior] + list(p.interiors):
            msp.add_lwpolyline([(round(x, 4), round(y, 4)) for x, y in list(r.coords)[:-1]], close=True, dxfattribs={"layer": layer})
    doc.saveas(path)

def sketch_svg(geom, title, margin=2.0):
    """Hairline outline SVG in mm (y down, as drawn), with a margin of empty page."""
    x0, y0, x1, y1 = geom.bounds
    d = ""
    for p in polys_of(geom):
        for r in [p.exterior] + list(p.interiors):
            d += "M" + " L".join(f"{x:.4f},{y:.4f}" for x, y in list(r.coords)[:-1]) + "Z"
    w, h = x1 - x0 + 2 * margin, y1 - y0 + 2 * margin
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}mm" height="{h:.3f}mm" '
            f'viewBox="{x0 - margin:.3f} {y0 - margin:.3f} {w:.3f} {h:.3f}">\n<title>{title}</title>\n'
            f'<path d="{d}" fill="none" stroke="#000000" stroke-width="0.01" fill-rule="evenodd"/>\n</svg>\n')

# ================================================================ printer rules (FDM, 0.4 mm nozzle, 0.2 mm layers)
NOZZLE, LAYER = 0.4, 0.2
MIN_FEATURE = 0.6     # thinnest raised or free-standing stroke: 1.5 line widths (a 0.6 mm line, or Arachne's variable width)
MIN_GAP = 0.5         # narrowest gap between two raised features, or a slit in a plate (a slicer closes anything narrower)
MIN_WALL = 1.2        # structural walls and floors under a load: 3 lines / 6 layers
FOOT_MM = 0.6         # printed cones: each foot is cut where the wall reaches this (like the DXF's 0.5 mm floor)
CLEAR = 0.2           # clearance per side for a slip fit (a plate in a slot)
MAGNET = (10.0, 3.0)  # the magnet the pockets are sized for: 10 x 3 mm neodymium disc (N35-N52), the commonest size
MAGNET_CLEAR = 0.15   # per side on the magnet's diameter (10.3 mm pocket: snug, with a drop of glue); +0.2 on the depth

def _cast_face(s):
    return (getattr(TopoDS, "Face_s", None) or TopoDS.Face)(s)        # OCP 7.x: Face_s; OCP 8: Face

def check_print(name, region, min_feature=MIN_FEATURE, min_gap=MIN_GAP):
    """FDM check of a printed outline (shapely, mm). A stroke thinner than min_feature splits a piece when the region is
    shrunk by half of it (sharp tips just shrink, so the trimmed cone feet and tips pass); a gap narrower than min_gap
    closes when it is grown by half of it (pieces merge or a hole fills). Returns a list of problems (empty: printable)."""
    region = region.buffer(0); probs = []
    n0 = len(polys_of(region)); h0 = sum(len(p.interiors) for p in polys_of(region))
    thin = region.buffer(-min_feature / 2 + 1e-3, join_style=2)
    for p in polys_of(region):
        k = len(polys_of(p.buffer(-min_feature / 2 + 1e-3, join_style=2)))
        if k != 1: probs.append(f"{name}: a stroke under {min_feature} mm near {[round(v, 1) for v in p.bounds]} ({k} pieces after shrinking)")
    grown = region.buffer(min_gap / 2 - 1e-3, join_style=2)
    if len(polys_of(grown)) != n0 or sum(len(p.interiors) for p in polys_of(grown)) != h0:
        probs.append(f"{name}: a gap under {min_gap} mm ({n0} pieces/{h0} holes -> {len(polys_of(grown))}/{sum(len(p.interiors) for p in polys_of(grown))})")
    return probs

# ---------------------------------------------------------------- exact outlines (the mark)
class Outline:
    """A closed outline of geo segments (M, L, A, C, Z) placed by p -> M p + t, M a similarity (uniform scale, maybe a
    mirror). poly() samples it for shapely and STL; curves() gives the exact pieces for STEP, DXF and SVG."""
    def __init__(self, segs, M=((1, 0), (0, 1)), t=(0, 0), name=""):
        self.segs, self.M, self.t, self.name = segs, np.array(M, float), np.array(t, float), name
    def T(self, p): return tuple(float(v) for v in self.M @ np.asarray(p, float) + self.t)
    def affine(self, M2, t2=(0, 0)):
        M2 = np.array(M2, float); return Outline(self.segs, M2 @ self.M, M2 @ self.t + np.array(t2, float), self.name)
    def moved(self, dx, dy): return self.affine(np.eye(2), (dx, dy))
    def scaled(self, k, origin=(0, 0)): o = np.array(origin, float); return self.affine(np.eye(2) * k, o - k * o)
    def mirrored_x(self, x0=0.0): return self.affine(((-1, 0), (0, 1)), (2 * x0, 0))
    @property
    def k(self): return abs(np.linalg.det(self.M)) ** 0.5
    def points(self, n=40):
        import geo
        return [self.T(p) for p in geo.sample(self.segs, n)]
    def poly(self, n=40): return Polygon(self.points(n)).buffer(0)
    def curves(self):
        """[("line", p0, p1) | ("circle", p0, pm, p1, centre, r) | ("ellipse", p0, pm, p1, centre, major_dir, a, b) |
        ("bezier", [p0, c1, c2, p1])] in placed coordinates, in path order."""
        import geo
        out_, cur = [], None
        for sg in self.segs:
            k = sg[0]
            if k == "M": cur = sg[1]; continue
            if k == "Z": continue
            p1 = sg[-1]
            if k == "L": out_.append(("line", self.T(cur), self.T(p1)))
            elif k == "C": out_.append(("bezier", [self.T(cur), self.T(sg[1]), self.T(sg[2]), self.T(p1)]))
            elif k == "A":
                c, rx, ry, t1, dt = geo._arc_center(cur, p1, sg[1], sg[2], sg[3], sg[4], sg[5])
                pm = self.T(geo.seg_param(cur, sg)(0.5))
                if abs(rx - ry) <= 1e-9 * max(rx, ry):
                    out_.append(("circle", self.T(cur), pm, self.T(p1), self.T(c), rx * self.k))
                else:
                    ph = math.radians(sg[3]); u = np.array([math.cos(ph), math.sin(ph)]); v = np.array([-math.sin(ph), math.cos(ph)])
                    a, b, ax = (rx, ry, u) if rx >= ry else (ry, rx, v)
                    d = self.M @ ax; d = d / np.hypot(*d)
                    out_.append(("ellipse", self.T(cur), pm, self.T(p1), self.T(c), (float(d[0]), float(d[1])), a * self.k, b * self.k))
            cur = p1
        return out_
    def svg_d(self):
        """Exact SVG path data (y as given): the same lines, arcs and Béziers."""
        import geo
        f = lambda p: f"{p[0]:.4f},{p[1]:.4f}"
        d = ""; flip = np.linalg.det(self.M) < 0
        for sg in self.segs:
            k = sg[0]
            if k == "M": d += "M" + f(self.T(sg[1]))
            elif k == "L": d += " L" + f(self.T(sg[1]))
            elif k == "C": d += " C" + " ".join(f(self.T(p)) for p in sg[1:])
            elif k == "A":
                ph = math.radians(sg[3]); u = self.M @ np.array([math.cos(ph), math.sin(ph)])
                d += f" A{sg[1] * self.k:.4f},{sg[2] * self.k:.4f} {math.degrees(math.atan2(u[1], u[0])):.4f} {sg[4]} {(1 - sg[5]) if flip else sg[5]} " + f(self.T(sg[6]))
            elif k == "Z": d += " Z"
        return d

_DXF_GEO = {}
def mark_outlines(height_mm, min_wall=FOOT_MM, centre=False, mirror=False):
    """The four cones as exact Outlines in mm, y up, for a mark height_mm tall (feet trimmed to min_wall, then scaled to
    exactly that height, as for the DXF). Bottom left of the bbox at (0, 0), or the bbox centre at (0, 0) with centre=True.
    Returns ([Outline] in geo.ORDER, (w, h))."""
    import geo, build
    key = (round(float(height_mm), 9), float(min_wall))
    if key not in _DXF_GEO: _DXF_GEO[key] = build.dxf_geometry(float(height_mm), min_wall)
    cl, A, bb = _DXF_GEO[key]
    ols = [Outline(cl[n], ((1, 0), (0, -1)), (0, bb[3]), n) for n in geo.ORDER]      # y down -> y up, as cone_polys()
    w, h = bb[2], bb[3]
    if centre: ols = [o.moved(-w / 2, -h / 2) for o in ols]
    if mirror: ols = [o.mirrored_x(0.0 if centre else w / 2) for o in ols]
    return ols, (w, h)

def _exact_wire(ol, z):
    P = lambda p: gp_Pnt(p[0], p[1], z)
    mw = BRepBuilderAPI_MakeWire()
    for c in ol.curves():
        if c[0] == "line": e = BRepBuilderAPI_MakeEdge(P(c[1]), P(c[2])).Edge()
        elif c[0] == "circle": e = BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(P(c[1]), P(c[2]), P(c[3])).Value()).Edge()
        elif c[0] == "bezier": e = BRepBuilderAPI_MakeEdge(Geom_BezierCurve(_points([P(q) for q in c[1]]))).Edge()
        else:
            _, p0, pm, p1, cen, d, a, b = c
            el = gp_Elips(gp_Ax2(P(cen), gp_Dir(0, 0, 1), gp_Dir(d[0], d[1], 0)), a, b)
            n_ = np.array([-d[1], d[0]])
            ang = lambda p: math.atan2((np.subtract(p, cen) @ n_) / b, (np.subtract(p, cen) @ np.array(d)) / a)
            t0, tm, t1 = ang(p0), ang(pm), ang(p1)
            ccw = (tm - t0) % (2 * math.pi) < (t1 - t0) % (2 * math.pi)
            a0, a1 = (p0, p1) if ccw else (p1, p0)                          # always counter-clockwise; MakeWire takes either direction
            e = BRepBuilderAPI_MakeEdge(GC_MakeArcOfEllipse(el, P(a0), P(a1), True).Value()).Edge()
            ad = BRepAdaptor_Curve(e); q = ad.Value((ad.FirstParameter() + ad.LastParameter()) / 2)
            if math.hypot(q.X() - pm[0], q.Y() - pm[1]) > 1e-6 * max(a, 1): raise ValueError(f"{ol.name}: elliptical arc on the wrong side")
        mw.Add(e)
        if not mw.IsDone(): raise ValueError(f"{ol.name}: edges don't connect ({c[0]})")
    w = mw.Wire()
    return w

def _signed_area(pts):
    p = np.asarray(pts); return 0.5 * float(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]))

def face_of(region, z=0.0):
    """Planar faces at height z for an Outline (exact) or a shapely region (B-spline fit), normal +z."""
    faces = []
    if isinstance(region, Outline):
        w = _exact_wire(region, z)
        if _signed_area(region.points(8)) < 0: w = (getattr(TopoDS, "Wire_s", None) or TopoDS.Wire)(w.Reversed())
        mf = BRepBuilderAPI_MakeFace(w, True); fx = ShapeFix_Face(mf.Face()); fx.Perform(); faces.append(fx.Face())
    elif isinstance(region, (list, tuple)):
        for r in region: faces += face_of(r, z)
    else:
        for p in polys_of(region):
            p = orient(p, 1.0)
            mf = BRepBuilderAPI_MakeFace(_edges(list(p.exterior.coords), z), True)
            for h in p.interiors: mf.Add(_edges(list(h.coords), z))
            fx = ShapeFix_Face(mf.Face()); fx.Perform(); faces.append(fx.Face())
    return faces

def region_poly(region, n=40):
    """shapely for any region (Outline, shapely, or a list of them)."""
    if isinstance(region, Outline): return region.poly(n)
    if isinstance(region, (list, tuple)): return unary_union([region_poly(r, n) for r in region]) if region else Polygon()
    return region

def prism(region, z0, z1):
    """One shape (compound if several pieces) for region extruded from z0 to z1."""
    sh = [BRepPrimAPI_MakePrism(f, gp_Vec(0, 0, z1 - z0)).Shape() for f in face_of(region, z0)]
    return compound(sh)

def compound(shapes):
    shapes = [s for s in shapes if s is not None]
    if len(shapes) == 1: return shapes[0]
    comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp)
    for s in shapes: bb.Add(comp, s)
    return comp

def fuse(*shapes):
    shapes = [s for s in shapes if s is not None]; r = shapes[0]
    for s in shapes[1:]: r = BRepAlgoAPI_Fuse(r, s).Shape()
    return r
def cut(a, *tools):
    for t in tools: a = BRepAlgoAPI_Cut(a, t).Shape()
    return a
def common(a, b): return BRepAlgoAPI_Common(a, b).Shape()

def cylinder(r, z0, z1, x=0.0, y=0.0):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y, z0), gp_Dir(0, 0, 1)), r, z1 - z0).Shape()

def box(x0, y0, z0, x1, y1, z1):
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), gp_Pnt(x1, y1, z1)).Shape()

def transformed(shape, rot=None, move=(0, 0, 0)):
    """rot: (axis point, axis direction, degrees), applied before the move."""
    t = gp_Trsf()
    if rot:
        p, d, deg = rot; t.SetRotation(gp_Ax1(gp_Pnt(*p), gp_Dir(*d)), math.radians(deg))
    if any(move):
        t2 = gp_Trsf(); t2.SetTranslation(gp_Vec(*move)); t = t2.Multiplied(t)
    return BRepBuilderAPI_Transform(shape, t, True).Shape()

def prism_along(region, axis, d0, d1):
    """region drawn in a plane, extruded along a world axis: axis "y": region (x, z) from y=d0 to y=d1; "x": region (y, z)."""
    s = prism(region, d0, d1)                                               # in (u, v, w) = (x, y, z) first
    if axis == "y":   # (u, v, w) -> (u, w, v): rotate +90 deg about x maps y -> z, z -> -y; then mirror... do it exactly
        t = gp_Trsf(); t.SetValues(1, 0, 0, 0,  0, 0, 1, 0,  0, 1, 0, 0)     # (x, y, z) -> (x, z, y): a reflection
        return BRepBuilderAPI_Transform(s, t, True).Shape()
    if axis == "x":
        t = gp_Trsf(); t.SetValues(0, 0, 1, 0,  1, 0, 0, 0,  0, 1, 0, 0)     # (x, y, z) -> (z, x, y): a rotation
        return BRepBuilderAPI_Transform(s, t, True).Shape()
    return s

def volume(shape):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(shape, g); return g.Mass()

def is_valid(shape): return BRepCheck_Analyzer(shape).IsValid()

# ---------------------------------------------------------------- meshes (STL, 3MF, previews)
def mesh_of(shape, lin=0.02, ang=0.1):
    """(V, F) for a shape: BRepMesh, faces joined on their shared edge nodes (watertight for a closed solid)."""
    BRepMesh_IncrementalMesh(shape, lin, False, ang, True)
    V, F = [], []
    ex = TopExp_Explorer(shape, TopAbs_FACE)
    while ex.More():
        f = _cast_face(ex.Current()); loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f, loc)
        if tri is None: raise ValueError("face without a triangulation")
        tr = loc.Transformation(); b = len(V)
        for i in range(1, tri.NbNodes() + 1):
            p = tri.Node(i).Transformed(tr); V.append((p.X(), p.Y(), p.Z()))
        rev = f.Orientation() == TopAbs_REVERSED
        for i in range(1, tri.NbTriangles() + 1):
            a, b_, c = tri.Triangle(i).Get()
            F.append((b + a - 1, b + c - 1, b + b_ - 1) if rev else (b + a - 1, b + b_ - 1, b + c - 1))
        ex.Next()
    return weld(np.array(V, float).reshape(-1, 3), np.array(F, int).reshape(-1, 3))

def weld(V, F, tol=1e-6):
    """Merge vertices closer than tol and drop triangles that collapse."""
    key = np.round(V / tol).astype(np.int64)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    Vn = np.zeros((len(uniq), 3)); Vn[inv] = V
    Fn = inv[F]
    ok = (Fn[:, 0] != Fn[:, 1]) & (Fn[:, 1] != Fn[:, 2]) & (Fn[:, 0] != Fn[:, 2])
    return Vn, Fn[ok]

def mesh_from_tris(tris):
    """(V, F) from a triangle list [(a, b, c)] (kit_targets.extrude), welded."""
    T = np.array(tris, float).reshape(-1, 3, 3)
    return weld(T.reshape(-1, 3), np.arange(len(T) * 3).reshape(-1, 3))

def mesh_check(V, F, cavity_ok=False):
    """Watertight and consistently wound: every edge is used once in each direction, and the volume is positive (or, with
    cavity_ok, negative: the inside-out shell of a closed void, like the hidden magnet's pocket). Returns (ok, message)."""
    if len(F) == 0: return False, "no triangles"
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    d = {}
    for a, b in map(tuple, e): d[(a, b)] = d.get((a, b), 0) + 1
    bad = [k for k, n in d.items() if n != 1 or d.get((k[1], k[0]), 0) != 1]
    vol = float(np.sum(np.einsum("ij,ij->i", V[F[:, 0]], np.cross(V[F[:, 1]], V[F[:, 2]])))) / 6
    if bad: return False, f"{len(bad)} open or doubled edges"
    if vol < 0 and cavity_ok: return True, f"{len(F)} triangles, closed void of {-vol:.1f} mm3"
    if vol <= 0: return False, f"inside out (volume {vol:.1f})"
    return True, f"{len(F)} triangles, closed, {vol / 1000:.2f} cm3"

def check_stl(path):
    """Every shell of an STL closed and consistently wound; a shell inside out only as a void inside another one. (ok, msg)"""
    V, F = read_stl(path); sh = shells(V, F)
    res = [mesh_check(v, f, cavity_ok=True) for v, f in sh]
    vol = sum(float(np.sum(np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])))) / 6 for v, f in sh)
    bad = [m for ok, m in res if not ok]
    if bad: return False, f"{len(bad)} of {len(sh)} shells open: {bad[0]}"
    if vol <= 0: return False, "inside out"
    voids = sum(1 for _, m in res if "void" in m)
    return True, f"{len(sh)} closed shells" + (f" ({voids} of them a sealed void)" if voids else "") + f", {len(F)} triangles"

def stl_bytes(meshes):
    import struct, io
    tris = np.concatenate([V[F] for V, F in meshes]) if meshes else np.zeros((0, 3, 3))
    buf = io.BytesIO(); buf.write(b"FusionSpace kit".ljust(80, b" ")); buf.write(struct.pack("<I", len(tris)))
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]); l = np.linalg.norm(n, axis=1); l[l == 0] = 1; n = n / l[:, None]
    rec = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"] = n; rec["v"] = tris
    buf.write(rec.tobytes()); return buf.getvalue()

def read_stl(path):
    import struct
    b = open(path, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    rec = np.frombuffer(b[84:84 + 50 * n], dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return weld(rec["v"].reshape(-1, 3).astype(float), np.arange(n * 3).reshape(-1, 3), tol=1e-4)

def shells(V, F):
    """Split a mesh into its connected shells (to check each one)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]]])
    g = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(V), len(V)))
    n, lab = connected_components(g, directed=False)
    return [(V, F[lab[F[:, 0]] == k]) for k in range(n) if (lab[F[:, 0]] == k).any()]

# ---------------------------------------------------------------- STEP with names and colours, 3MF with parts
def _hex(c): return tuple(int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))

_STYLE_TYPES = ("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION", "STYLED_ITEM", "PRESENTATION_STYLE_ASSIGNMENT",
                "SURFACE_STYLE_USAGE", "SURFACE_SIDE_STYLE", "SURFACE_STYLE_FILL_AREA", "FILL_AREA_STYLE", "FILL_AREA_STYLE_COLOUR",
                "COLOUR_RGB", "DRAUGHTING_PRE_DEFINED_COLOUR", "OVER_RIDING_STYLED_ITEM")

def _canonical_colours(t):
    """OCCT writes the colour entities (at the end of the file) in hash order, so the same model gives different bytes on
    each run. Renumber that block in a fixed order (by the solids it colours) so builds are reproducible."""
    ents = [(int(m.group(1)), m.group(2), m.start(), m.end()) for m in re.finditer(r"(?ms)^#(\d+) = (.*?);$", t)]
    if not ents: return t
    kind = lambda body: re.match(r"\s*([A-Z_]+)", body).group(1) if re.match(r"\s*([A-Z_]+)", body) else ""
    blk = [e for e in ents if kind(e[1]) in _STYLE_TYPES]
    if not blk: return t
    lo = min(e[0] for e in blk)
    tail = [e for e in ents if e[0] >= lo]
    if len(tail) != len(blk): return t                                   # not one block at the end: leave it alone
    body = {e[0]: e[1] for e in tail}
    refs = lambda b: [int(x) for x in re.findall(r"#(\d+)", b)]
    def target(i):                                                       # what a presentation colours: its styled items' targets
        out_ = []
        for r in refs(body[i]):
            if r in body and kind(body[r]) == "STYLED_ITEM": out_ += [x for x in refs(body[r]) if x not in body]
        return out_
    tops = sorted([i for i in body if kind(body[i]) == "MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION"], key=target)
    order = []
    def visit(i):
        if i not in body or i in order: return
        order.append(i)
        for r in refs(body[i]): visit(r)
    for i in tops: visit(i)
    for i in sorted(body): visit(i)                                      # anything not reached, in the old order
    new_id = {old: lo + k for k, old in enumerate(order)}
    remap = lambda b: re.sub(r"#(\d+)", lambda m: f"#{new_id.get(int(m.group(1)), int(m.group(1)))}", b)
    out_ = "".join(f"#{new_id[i]} = {remap(body[i])};\n" for i in order)
    return t[:tail[0][2]] + out_ + t[tail[-1][3]:].lstrip("\n")

def _fix_step_header(path, name):
    t = open(path, encoding="utf-8", errors="replace").read()
    t = _canonical_colours(t)
    when = datetime.datetime.fromtimestamp(int(os.environ.get("SOURCE_DATE_EPOCH", "1790812800")), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    t = re.sub(r"FILE_NAME\('[^']*','[^']*'", f"FILE_NAME('{os.path.basename(path)}','{when}'", t, count=1)
    t = re.sub(r"FILE_DESCRIPTION\(\('[^']*'\)", f"FILE_DESCRIPTION(('FusionSpace {name}')", t, count=1)
    with open(path, "w", encoding="utf-8", newline="\n") as fh: fh.write(t)

def write_step_bodies(bodies, path, name):
    """bodies: [(label, shape, "#RRGGBB" or None)]. One named, coloured shape per body (Fusion, FreeCAD and Onshape show
    the names and colours), millimetres, AP214."""
    from OCP.TDocStd import TDocStd_Document
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
    from OCP.STEPCAFControl import STEPCAFControl_Writer
    from OCP.Quantity import Quantity_Color, Quantity_TypeOfColor
    from OCP.TDataStd import TDataStd_Name
    doc = TDocStd_Document(TCollection_ExtendedString("MDTV-XCAF"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    for label, shape, col in bodies:
        if not is_valid(shape): raise ValueError(f"{name}: {label} is not a valid solid")
        lab = st.AddShape(shape, False)
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(label))
        if col: ct.SetColor(lab, Quantity_Color(*_hex(col), Quantity_TypeOfColor.Quantity_TOC_sRGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    Interface_Static.SetCVal_s("write.step.unit", "MM")
    Interface_Static.SetCVal_s("write.step.schema", "AP214IS")
    Interface_Static.SetCVal_s("write.step.product.name", name)
    w = STEPCAFControl_Writer(); w.SetColorMode(True); w.SetNameMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    if w.Write(path) != IFSelect_RetDone: raise IOError(path)
    _fix_step_header(path, name)
    return True

def read_step(path):
    """(number of solids, total volume mm3, all valid) after reading a STEP back with Open CASCADE."""
    r = STEPControl_Reader()
    if r.ReadFile(path) != IFSelect_RetDone: return 0, 0.0, False
    r.TransferRoots(); s = r.OneShape()
    n = 0; ex = TopExp_Explorer(s, TopAbs_SOLID)
    while ex.More(): n += 1; ex.Next()
    return n, volume(s), is_valid(s)

def write_3mf(parts, path, name, objects=None):
    """A 3MF for multi-material printers. parts: [(label, (V, F), "#RRGGBB", extruder)] make one object whose parts are
    the bodies (PrusaSlicer, OrcaSlicer and Bambu Studio load it as one object with named parts and set each part's
    filament from the extruder number; other programs see one coloured mesh). objects: optional list of such part lists,
    one object each, laid out one above the other (for prints that come as several pieces)."""
    import zipfile
    from xml.sax.saxutils import escape
    objs = objects if objects else [parts]
    cols = []; 
    for ps in objs:
        for _, _, c, _ in ps:
            if c not in cols: cols.append(c)
    X = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
         'xmlns:slic3rpe="http://schemas.slic3r.org/3mf/2017/06">',
         f'<metadata name="Title">{escape(name)}</metadata><metadata name="Designer">FusionSpace</metadata>'
         '<metadata name="slic3rpe:Version3mf">1</metadata>',
         '<resources>', '<basematerials id="1">' + "".join(f'<base name="{escape(c)}" displaycolor="{c}FF"/>' for c in cols) + '</basematerials>']
    cfg = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>']
    build_items = []; y_off = 0.0; boxes = []
    for ps in objs:                                   # objects in a column, the group centred on (110, 110): fits a 220 mm bed
        V = np.concatenate([m[0] for _, m, _, _ in ps]); boxes.append((V.min(0), V.max(0)))
    tot_h = sum(hi[1] - lo[1] for lo, hi in boxes) + 10.0 * (len(boxes) - 1)
    y_off = 110.0 - tot_h / 2
    for oi, ps in enumerate(objs, start=2):
        Vs, Fs, ranges = [], [], []; nv = 0; nt = 0
        for label, (V, F), c, ext in ps:
            Vs.append(V); Fs.append(F + nv); ranges.append((label, nt, nt + len(F) - 1, cols.index(c), ext)); nv += len(V); nt += len(F)
        V = np.concatenate(Vs); F = np.concatenate(Fs)
        lo = V.min(0); hi = V.max(0)
        dx = 110.0 - (lo[0] + hi[0]) / 2; dy = y_off - lo[1]; dz = -lo[2]; y_off += (hi[1] - lo[1]) + 10.0
        vx = "".join(f'<vertex x="{a:.5f}" y="{b:.5f}" z="{c:.5f}"/>' for a, b, c in V)
        tx = []
        for label, t0, t1, ci, ext in ranges:
            tx += [f'<triangle v1="{a}" v2="{b}" v3="{c}" pid="1" p1="{ci}"/>' for a, b, c in F[t0:t1 + 1]]
        oname = escape(ps[0][0].split(":")[0] if len(objs) > 1 else name)
        X.append(f'<object id="{oi}" name="{oname}" type="model" pid="1" pindex="{ranges[0][3]}"><mesh><vertices>{vx}</vertices><triangles>{"".join(tx)}</triangles></mesh></object>')
        build_items.append(f'<item objectid="{oi}" transform="1 0 0 0 1 0 0 0 1 {dx:.4f} {dy:.4f} {dz:.4f}" printable="1"/>')
        cfg.append(f'<object id="{oi}" instances_count="1">')
        cfg.append(f'<metadata type="object" key="name" value="{oname}"/>')
        for label, t0, t1, ci, ext in ranges:
            cfg.append(f'<volume firstid="{t0}" lastid="{t1}"><metadata type="volume" key="name" value="{escape(label)}"/>'
                       f'<metadata type="volume" key="extruder" value="{ext}"/><metadata type="volume" key="volume_type" value="ModelPart"/></volume>')
        cfg.append('</object>')
    X += ['</resources>', '<build>' + "".join(build_items) + '</build>', '</model>']
    cfg.append('</config>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    ctypes = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
              '<Default Extension="config" ContentType="text/xml"/></Types>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for fn, data in (("[Content_Types].xml", ctypes), ("_rels/.rels", rels), ("3D/3dmodel.model", "\n".join(X)),
                         ("Metadata/Slic3r_PE_model.config", "\n".join(cfg))):
            zi = zipfile.ZipInfo(fn, date_time=(2026, 10, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, data)

def read_3mf(path):
    """[(object name, V, F)] from a 3MF (core spec), for checking it opens and is watertight."""
    import zipfile
    import xml.etree.ElementTree as ET
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("3D/3dmodel.model"))
    out_ = []
    for o in root.iter(f"{{{ns['m']}}}object"):
        V = np.array([[float(v.get(k)) for k in "xyz"] for v in o.iter(f"{{{ns['m']}}}vertex")])
        F = np.array([[int(t.get(k)) for k in ("v1", "v2", "v3")] for t in o.iter(f"{{{ns['m']}}}triangle")])
        out_.append((o.get("name"), V, F))
    return out_

# ---------------------------------------------------------------- previews: a small z-buffer renderer
def render_preview(meshes, dest, S=900, elev=50.0, azim=0.0, bg="#F3F4F7", ss=2):
    """meshes: [((V, F), "#RRGGBB")]. Orthographic 3/4 view like kit_targets.stl_preview (looking from the front, elev
    degrees above), flat shading with a light from the upper left, a thin dark outline where faces meet at a crease."""
    from PIL import Image
    se, ce = math.sin(math.radians(elev)), math.cos(math.radians(elev))
    sa, ca = math.sin(math.radians(azim)), math.cos(math.radians(azim))
    allV = np.concatenate([V for (V, F), _ in meshes])
    def proj(V):
        x = V[:, 0] * ca - V[:, 1] * sa; y = V[:, 0] * sa + V[:, 1] * ca; z = V[:, 2]
        return np.stack([x, y * se + z * ce, z * se - y * ce], 1)      # screen x, screen up, depth (bigger is nearer)
    P = proj(allV); lo, hi = P[:, :2].min(0), P[:, :2].max(0)
    span = max(hi - lo) * 1.24; N = S * ss; k = N / span
    off = (lo + hi) / 2
    img = np.zeros((N, N, 3)); img[:] = _hex(bg); zb = np.full((N, N), -1e18); nid = np.full((N, N), -1, np.int64)
    L = np.array([-0.35, 0.55, 0.76]); L = L / np.linalg.norm(L)       # view space: from the upper left, toward the viewer
    tid = 0
    for (V, F), col in meshes:
        Q = proj(V); sx = (Q[:, 0] - off[0]) * k + N / 2; sy = N / 2 - (Q[:, 1] - off[1]) * k; d = Q[:, 2]
        T = V[F]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1; n /= ln[:, None]
        nr = np.stack([n[:, 0] * ca - n[:, 1] * sa, n[:, 0] * sa + n[:, 1] * ca, n[:, 2]], 1)
        nv = np.stack([nr[:, 0], nr[:, 1] * se + nr[:, 2] * ce, nr[:, 2] * se - nr[:, 1] * ce], 1)   # in view space
        shade = np.minimum(1.0, 0.5 + 0.5 * np.clip(nv @ L, 0, 1) / 0.9)
        base = np.array(_hex(col))
        # back faces can't be seen on a closed mesh: skip them (about half the work)
        front = (n[:, 2] * se - (n[:, 0] * sa + n[:, 1] * ca) * ce) > -1e-9
        X0 = np.floor(np.minimum(np.minimum(sx[F[:, 0]], sx[F[:, 1]]), sx[F[:, 2]])).astype(int).clip(0, N - 1)
        X1 = np.ceil(np.maximum(np.maximum(sx[F[:, 0]], sx[F[:, 1]]), sx[F[:, 2]])).astype(int).clip(0, N - 1)
        Y0 = np.floor(np.minimum(np.minimum(sy[F[:, 0]], sy[F[:, 1]]), sy[F[:, 2]])).astype(int).clip(0, N - 1)
        Y1 = np.ceil(np.maximum(np.maximum(sy[F[:, 0]], sy[F[:, 1]]), sy[F[:, 2]])).astype(int).clip(0, N - 1)
        DEN = (sy[F[:, 1]] - sy[F[:, 2]]) * (sx[F[:, 0]] - sx[F[:, 2]]) + (sx[F[:, 2]] - sx[F[:, 1]]) * (sy[F[:, 0]] - sy[F[:, 2]])
        for i in np.nonzero(front & (np.abs(DEN) > 1e-12))[0]:
            a, b, c = F[i]; x0, x1, y0, y1, den = X0[i], X1[i], Y0[i], Y1[i], DEN[i]
            X = np.arange(x0, x1 + 1)[None, :] + 0.5; Y = np.arange(y0, y1 + 1)[:, None] + 0.5
            w0 = ((sy[b] - sy[c]) * (X - sx[c]) + (sx[c] - sx[b]) * (Y - sy[c])) / den
            w1 = ((sy[c] - sy[a]) * (X - sx[c]) + (sx[a] - sx[c]) * (Y - sy[c])) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
            if not m.any(): continue
            z = w0 * d[a] + w1 * d[b] + w2 * d[c]
            sub = zb[y0:y1 + 1, x0:x1 + 1]; upd = m & (z > sub)
            sub[upd] = z[upd]
            img[y0:y1 + 1, x0:x1 + 1][upd] = base * shade[i]
            nid[y0:y1 + 1, x0:x1 + 1][upd] = tid + i
        tid += len(F)
    # crease lines: where neighbouring pixels belong to faces with different normals, darken a little
    allN = []
    for (V, F), _ in meshes:
        T = V[F]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1; allN.append(n / ln[:, None])
    allN = np.concatenate(allN + [np.zeros((1, 3))])
    nn = allN[nid]                                      # -1 -> the zero row (background)
    edge = np.zeros((N, N), bool)
    for dy_, dx_ in ((0, 1), (1, 0)):
        a = nn[:N - dy_, :N - dx_]; b = nn[dy_:, dx_:]
        ia = nid[:N - dy_, :N - dx_]; ib = nid[dy_:, dx_:]
        diff = (np.einsum("ijk,ijk->ij", a, b) < 0.94) & ((ia >= 0) | (ib >= 0))
        edge[:N - dy_, :N - dx_] |= diff
    img[edge] *= 0.7
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS)
    im.save(dest)

# ---------------------------------------------------------------- parametric templates (FreeCAD macro, Fusion script)
REF_MM = 50.0     # the templates carry the mark at this height, centred on the origin, y up; they scale it from there

def _mark_curves_ref():
    ols, _ = mark_outlines(REF_MM, FOOT_MM, centre=True)
    r = lambda p: [round(float(v), 10) for v in p]       # 10 places: endpoints meet within FreeCAD's 1e-7 mm
    cones = []
    for o in ols:
        cs = []
        for c in o.curves():
            if c[0] == "line": cs.append(["line", r(c[1]), r(c[2])])
            elif c[0] == "circle": cs.append(["arc", r(c[1]), r(c[2]), r(c[3])])
            elif c[0] == "ellipse": cs.append(["ellipse", r(c[1]), r(c[2]), r(c[3]), r(c[4]), r(c[5]), round(c[6], 10), round(c[7], 10)])
            else: cs.append(["bezier"] + [r(p) for p in c[1]])
        cones.append([o.name, cs])
    return cones

def _pocket_xy():
    """Where the magnet pocket goes, as a fraction of the mark height from the mark's centre (the badge base's thickest
    point, as for the magnet print)."""
    from shapely.ops import polylabel
    ols, _ = mark_outlines(REF_MM, FOOT_MM, centre=True)
    U = unary_union([o.poly(40) for o in ols]); R = 1.0 * REF_MM
    c = polylabel(U.buffer(R, resolution=32).buffer(-R, resolution=32), 0.01)
    return round(c.x / REF_MM, 5), round(c.y / REF_MM, 5)

def _reach():
    """Farthest point of the mark from its bbox centre, as a fraction of the mark height (the main cone's tip): a round plate
    needs a radius of at least this × the mark height, plus a margin."""
    ols, _ = mark_outlines(REF_MM, FOOT_MM, centre=True)
    return round(max(math.hypot(x, y) for o in ols for x, y in o.points(80)) / REF_MM, 5)

def freecad_macro():
    import json
    px, py = _pocket_xy()
    return f'''# FusionSpace badge: a parametric template for FreeCAD (0.21 and 1.x).
# Macro > Macros... > select this file > Execute. It makes a new document with a spreadsheet "Params"; change a value
# there and recompute (Ctrl+R): the badge follows. Export "Badge" (no pocket) or "BadgeMagnet" with File > Export.
# Generated by tools/build/kit_cad.py from the master geometry: the mark is exact (lines, circular arcs, the elliptical
# wing's ellipse and the Von Karman's Bezier curves), {REF_MM:g} mm tall here, feet cut at {FOOT_MM} mm, and scaled from Params.
import FreeCAD as App
import Part

MARK = {json.dumps(_mark_curves_ref())}
REF = {REF_MM!r}          # mm: the height MARK is drawn at
POCKET = ({px}, {py})     # magnet pocket centre, x and y as a fraction of the mark height (the base's thickest point)
REACH = {_reach()}          # the mark's farthest point from its centre, as a fraction of its height
PARAMS = [  # alias, value (mm), note
    ("MarkHeight", 40, "mark height, mm (the name is not in this template)"),
    ("Margin", 3, "clear plate around the mark's farthest point (the main cone's tip), mm"),
    ("PlateDiameter", "=2 * MarkHeight * REACH + 2 * Margin", "round plate diameter, mm: follows the mark and the margin (type a number to fix it)"),
    ("PlateThickness", 4.0, "plate thickness, mm (keep it in 0.2 mm layers)"),
    ("Relief", 1.2, "cones raised by, mm"),
    ("MagnetDiameter", 10.3, "pocket diameter, mm: magnet + 0.3"),
    ("MagnetDepth", 3.2, "pocket depth from the back, mm: magnet + 0.2; leave 0.8 mm above it"),
]

def V(p): return App.Vector(p[0], p[1], 0)

def edge(c):
    k = c[0]
    if k == "line": return Part.LineSegment(V(c[1]), V(c[2])).toShape()
    if k == "arc": return Part.Arc(V(c[1]), V(c[2]), V(c[3])).toShape()
    if k == "bezier":
        b = Part.BezierCurve(); b.setPoles([V(p) for p in c[1:]]); return b.toShape()
    _, p0, pm, p1, cen, d, a, b = c          # ellipse arc: centre, major-axis direction, semi-axes
    import math
    el = Part.Ellipse(V((cen[0] + d[0] * a, cen[1] + d[1] * a)), V((cen[0] - d[1] * b, cen[1] + d[0] * b)), V(cen))
    def par(p):
        return el.parameter(V(p))
    u0, um, u1 = par(p0), par(pm), par(p1)
    two = 2 * math.pi
    if (um - u0) % two < (u1 - u0) % two: s, e = u0, u0 + (u1 - u0) % two
    else: s, e = u1, u1 + (u0 - u1) % two
    return Part.ArcOfEllipse(el, s, e).toShape()

def mark_shape():
    faces = []
    for name, curves in MARK:
        w = Part.Wire(Part.__sortEdges__([edge(c) for c in curves]))
        f = Part.Face(w)
        if not f.isValid(): f.fix(1e-6, 1e-6, 1e-6)
        faces.append(f)
    return Part.makeCompound(faces)

doc = App.newDocument("FusionSpaceBadge")
sheet = doc.addObject("Spreadsheet::Sheet", "Params")
for i, (alias, val, note) in enumerate(PARAMS, start=1):
    sheet.set(f"A{{i}}", alias); sheet.set(f"C{{i}}", note); sheet.setAlias(f"B{{i}}", alias)
for i, (alias, val, note) in enumerate(PARAMS, start=1):
    sheet.set(f"B{{i}}", str(val).replace("REACH", str(REACH)))
doc.recompute()

ref = doc.addObject("Part::Feature", "MarkReference"); ref.Shape = mark_shape(); ref.Label = "Mark (reference, %g mm)" % REF
try:
    import Draft
    mark = Draft.make_clone(ref) if hasattr(Draft, "make_clone") else Draft.clone(ref)
except Exception:
    mark = doc.addObject("Part::FeaturePython", "Mark")
mark.Label = "Mark"
for ax in ("x", "y"): mark.setExpression(f"Scale.{{ax}}", f"Params.MarkHeight / {{REF}}")
mark.setExpression(".Placement.Base.z", "Params.PlateThickness")
relief = doc.addObject("Part::Extrusion", "Relief")
relief.Base = mark; relief.DirMode = "Custom"; relief.Dir = App.Vector(0, 0, 1); relief.Solid = True
relief.setExpression("LengthFwd", "Params.Relief")
plate = doc.addObject("Part::Cylinder", "Plate")
plate.setExpression("Radius", "Params.PlateDiameter / 2"); plate.setExpression("Height", "Params.PlateThickness")
badge = doc.addObject("Part::MultiFuse", "Badge"); badge.Shapes = [plate, relief]
pocket = doc.addObject("Part::Cylinder", "Pocket")
pocket.setExpression("Radius", "Params.MagnetDiameter / 2"); pocket.setExpression("Height", "Params.MagnetDepth")
pocket.setExpression(".Placement.Base.x", f"Params.MarkHeight * {{POCKET[0]}}")
pocket.setExpression(".Placement.Base.y", f"Params.MarkHeight * {{POCKET[1]}}")
withmag = doc.addObject("Part::Cut", "BadgeMagnet"); withmag.Base = badge; withmag.Tool = pocket
for o in (ref, mark, relief, plate, pocket, badge):
    try: o.Visibility = False
    except Exception: pass
doc.recompute()
try:
    import FreeCADGui as Gui
    Gui.SendMsgToActiveView("ViewFit"); Gui.activeDocument().activeView().viewIsometric()
except Exception:
    pass
'''

def fusion_script():
    import json
    px, py = _pocket_xy()
    return f'''"""FusionSpace badge: a parametric template for Autodesk Fusion.

Utilities > Add-Ins > Scripts and Add-Ins > + > Script or add-in from device > pick the folder this file is in
(FusionSpace_Badge_Fusion, with its .manifest), then Run. It makes a new design driven by user
parameters (Modify > Change Parameters): MarkHeight, PlateDiameter, PlateThickness, Relief, MagnetDiameter, MagnetDepth.
Generated by tools/build/kit_cad.py from the master geometry: lines and arcs are exact; the elliptical wing and the Von
Karman's Bezier flanks are control-point splines (exact Beziers) where Fusion offers them, else splines fitted through the
curve. The mark is drawn {REF_MM:g} mm tall and scaled from MarkHeight. (Not tested inside Fusion: there is no Fusion where
this is built. The FreeCAD macro next to it was run.)
"""
import adsk.core, adsk.fusion, traceback, math

MARK = {json.dumps(_mark_curves_ref())}
REF = {REF_MM!r}
POCKET = ({px}, {py})
REACH = {_reach()}     # the mark's farthest point from its centre, as a fraction of its height
PARAMS = [("MarkHeight", "40 mm"), ("Margin", "3 mm"), ("PlateDiameter", "2 * MarkHeight * %g + 2 * Margin" % REACH), ("PlateThickness", "4 mm"), ("Relief", "1.2 mm"),
          ("MagnetDiameter", "10.3 mm"), ("MagnetDepth", "3.2 mm")]

def P(p): return adsk.core.Point3D.create(p[0] / 10, p[1] / 10, 0)     # the API works in cm

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get(); ui = app.userInterface
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        for n, v in PARAMS: design.userParameters.add(n, adsk.core.ValueInput.createByString(v), "mm", "FusionSpace badge")
        root = design.rootComponent; ext = root.features.extrudeFeatures
        # plate
        sk = root.sketches.add(root.xYConstructionPlane); sk.name = "Plate"
        c = sk.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 2.8)
        sk.sketchDimensions.addDiameterDimension(c, adsk.core.Point3D.create(3, 3, 0)).parameter.expression = "PlateDiameter"
        plate = ext.addSimple(sk.profiles.item(0), adsk.core.ValueInput.createByString("PlateThickness"),
                              adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0)
        plate.name = "Badge"
        # mark, on a plane PlateThickness up, drawn at REF mm
        pi = root.constructionPlanes.createInput(); pi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByString("PlateThickness"))
        plane = root.constructionPlanes.add(pi)
        sk2 = root.sketches.add(plane); sk2.name = "Mark (%g mm reference)" % REF
        sk2.isComputeDeferred = True
        pts = []
        def snap(sp):
            for q in pts:
                if q.isValid and q != sp and q.geometry.distanceTo(sp.geometry) < 1e-7:
                    try: q.merge(sp); return q
                    except Exception: return sp
            pts.append(sp); return sp
        curves = sk2.sketchCurves
        for name, cs in MARK:
            for cv in cs:
                k = cv[0]
                if k == "line": e = curves.sketchLines.addByTwoPoints(P(cv[1]), P(cv[2]))
                elif k == "arc": e = curves.sketchArcs.addByThreePoints(P(cv[1]), P(cv[2]), P(cv[3]))
                elif k == "bezier":
                    col = adsk.core.ObjectCollection.create()
                    for p in cv[1:]: col.add(P(p))
                    try: e = curves.sketchControlPointSplines.add(col, adsk.fusion.SplineDegrees.SplineDegreeThree)
                    except Exception:
                        fit = adsk.core.ObjectCollection.create()
                        b = cv[1:]
                        for i in range(13):
                            t = i / 12; m = 1 - t
                            fit.add(P([m**3 * b[0][j] + 3 * m * m * t * b[1][j] + 3 * m * t * t * b[2][j] + t**3 * b[3][j] for j in (0, 1)]))
                        e = curves.sketchFittedSplines.add(fit)
                else:
                    _, p0, pm, p1, cen, d, a, bb = cv
                    nrm = (-d[1], d[0])
                    def ang(p): return math.atan2(((p[0] - cen[0]) * nrm[0] + (p[1] - cen[1]) * nrm[1]) / bb, ((p[0] - cen[0]) * d[0] + (p[1] - cen[1]) * d[1]) / a)
                    t0, tm, t1 = ang(p0), ang(pm), ang(p1); two = 2 * math.pi
                    sw = (t1 - t0) % two if (tm - t0) % two < (t1 - t0) % two else -((t0 - t1) % two)
                    fit = adsk.core.ObjectCollection.create()
                    for i in range(25):
                        t = t0 + sw * i / 24
                        fit.add(P([cen[0] + a * math.cos(t) * d[0] + bb * math.sin(t) * nrm[0], cen[1] + a * math.cos(t) * d[1] + bb * math.sin(t) * nrm[1]]))
                    e = curves.sketchFittedSplines.add(fit)
                snap(e.startSketchPoint); snap(e.endSketchPoint)
        sk2.isComputeDeferred = False
        profs = adsk.core.ObjectCollection.create()
        for i in range(sk2.profiles.count): profs.add(sk2.profiles.item(i))
        relief = ext.addSimple(profs, adsk.core.ValueInput.createByString("Relief"), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        bodies = adsk.core.ObjectCollection.create()
        for i in range(relief.bodies.count): bodies.add(relief.bodies.item(i))
        si = root.features.scaleFeatures.createInput(bodies, root.originConstructionPoint, adsk.core.ValueInput.createByReal(1))
        f = "MarkHeight / %g mm" % REF
        si.setToNonUniform(adsk.core.ValueInput.createByString(f), adsk.core.ValueInput.createByString(f), adsk.core.ValueInput.createByReal(1))
        root.features.scaleFeatures.add(si)
        tools = adsk.core.ObjectCollection.create()
        for i in range(relief.bodies.count): tools.add(relief.bodies.item(i))
        ci = root.features.combineFeatures.createInput(plate, tools); ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        root.features.combineFeatures.add(ci)
        # magnet pocket from the back, at the base's thickest point (it moves with MarkHeight)
        sk3 = root.sketches.add(root.xYConstructionPlane); sk3.name = "Magnet pocket"
        cc = sk3.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(POCKET[0] * 4, POCKET[1] * 4, 0), 0.515)
        sk3.sketchDimensions.addDiameterDimension(cc, adsk.core.Point3D.create(1, 1, 0)).parameter.expression = "MagnetDiameter"
        dx = sk3.sketchDimensions.addDistanceDimension(sk3.originPoint, cc.centerSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(0, -1, 0))
        dx.parameter.expression = "abs(MarkHeight * %g)" % POCKET[0]
        dy = sk3.sketchDimensions.addDistanceDimension(sk3.originPoint, cc.centerSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-1, 0, 0))
        dy.parameter.expression = "abs(MarkHeight * %g)" % POCKET[1]
        pocket = ext.createInput(sk3.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        pocket.setDistanceExtent(False, adsk.core.ValueInput.createByString("MagnetDepth"))
        pocket.participantBodies = [plate]
        ext.add(pocket).name = "Magnet pocket (suppress for none)"
        app.activeViewport.fit()
    except Exception:
        if ui: ui.messageBox("FusionSpace badge failed:\\n" + traceback.format_exc())
'''
