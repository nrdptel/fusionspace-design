"""FusionSpace icons: product/icons/. Drawn on a 24 x 24 grid with a 1.5 stroke, square caps and mitred corners, lines at 0, 45
and 90 degrees, arcs where the object is round. The domain icons (nose cone, chutes, pyro channels, CG and CP) are drawn
from the real shapes: the nose cone is the Von Karman profile the mark uses, on its shoulder. Status icons differ in shape,
not only colour: a circle for normal, a triangle for caution, an octagon for danger.
"""
import math

def f(v): s=f"{v:.2f}".rstrip("0").rstrip("."); return "0" if s=="-0" else s
def P(*pts, close=False):
    d="M"+" L".join(f"{f(x)} {f(y)}" for x,y in pts)+(" Z" if close else "")
    return f'<path d="{d}"/>'
def D(d): return f'<path d="{d}"/>'
def C(x,y,r,fill=False): return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}"{" fill=\"currentColor\" stroke=\"none\"" if fill else ""}/>'
def DOT(x,y,r=1.25): return C(x,y,r,True)
def FILL(d): return f'<path fill="currentColor" stroke="none" d="{d}"/>'
def vk(tipx, tipy, L, R, n=16):
    """Von Karman (LD-Haack C=0) half-profile points from the tip: list of (x offset, y)."""
    pts=[]
    for i in range(n+1):
        x=L*(i/n)**1.6
        th=math.acos(1-2*x/L); y=R/math.sqrt(math.pi)*math.sqrt(th-math.sin(2*th)/2)
        pts.append((y, tipy+x))
    return pts
def smooth(pts):
    """Catmull-Rom through points -> cubic path data (no M)."""
    out=[]
    for i in range(len(pts)-1):
        p0=pts[max(i-1,0)]; p1=pts[i]; p2=pts[i+1]; p3=pts[min(i+2,len(pts)-1)]
        c1=(p1[0]+(p2[0]-p0[0])/6, p1[1]+(p2[1]-p0[1])/6); c2=(p2[0]-(p3[0]-p1[0])/6, p2[1]-(p3[1]-p1[1])/6)
        out.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}")
    return " ".join(out)
def cone_path(cx, tip, base, R, notch=True):
    pr=vk(0,tip,base-tip,R)
    right=[(cx+x,y) for x,y in pr]; left=[(cx-x,y) for x,y in pr][::-1]
    d=f"M{f(left[0][0])} {f(left[0][1])} "+smooth(left)+" "+smooth(right)
    if notch: d+=f" A{f(R)} {f(R)} 0 0 0 {f(cx-R)} {f(base)} Z"
    else: d+=" Z"
    return d

ICONS = I = {}
# ---------------- rocketry
I["nose-cone"]=D(cone_path(12,2.5,16.5,5.5,notch=False))+P((8.5,16.5),(8.5,21.5),(15.5,21.5),(15.5,16.5))   # Von Karman profile and its shoulder
pr=vk(0,2,7,3); right=[(12+x,y) for x,y in pr]; left=[(12-x,y) for x,y in pr][::-1]
I["rocket"]=(D(f"M{f(left[0][0])} {f(left[0][1])} "+smooth(left)+" "+smooth(right)+" L15 19 L9 19 Z")
             +P((9,13),(5.5,17.5),(5.5,21),(9,19.5))+P((15,13),(18.5,17.5),(18.5,21),(15,19.5)))
I["fin"]=P((6,3),(6,21))+P((6,7),(18,16),(18,20),(6,20))
I["motor"]=P((8,3),(16,3),(16,16),(8,16),close=True)+P((8,5.5),(16,5.5))+P((10,16),(8.5,21),(15.5,21),(14,16))
I["thrust-curve"]=P((3,3),(3,21),(21,21))+D("M3 21 L4.5 7 L7 10.5 L15 11.5 Q17 12 18.5 21")
I["parachute"]=(D("M3 11 A9 8 0 0 1 21 11")+D("M3 11 Q6 9.5 9 11 Q12 9.5 15 11 Q18 9.5 21 11")
               +P((3,11),(12,19))+P((21,11),(12,19))+P((9,11),(12,19))+P((15,11),(12,19))+P((12,19),(12,22)))
I["drogue"]=(D("M7 8 A5 4.5 0 0 1 17 8")+D("M7 8 Q9.5 7 12 8 Q14.5 7 17 8")+P((7,8),(12,13))+P((17,8),(12,13))+P((12,13),(12,21.5)))
I["flight-computer"]=(P((3,6),(18,6),(21,9),(21,18),(3,18),close=True)+C(6,9,1)+C(6,15,1)+P((10,9),(16,9),(16,15),(10,15),close=True)
                      +P((11.5,18),(11.5,21))+P((14.5,18),(14.5,21)))
I["ejection-charge"]=(C(12,11,3.5)+P((10.5,14.2),(10.5,21))+P((13.5,14.2),(13.5,21))+P((12,2.5),(12,5))+P((5.5,5.5),(7.5,7.5))+P((18.5,5.5),(16.5,7.5)))
I["continuity"]=P((5,12),(8,12),(9.5,9),(12,15),(14.5,9),(16,12),(19,12))+DOT(4,12)+DOT(20,12)
I["no-continuity"]=P((5,12),(9,12))+P((15,12),(19,12))+P((10.5,16.5),(13.5,7.5))+DOT(4,12)+DOT(20,12)
I["armed"]=P((5.5,15),(18,13.2))+DOT(4.5,15,1.75)+DOT(19.5,15,1.75)+P((3,19.5),(21,19.5))+P((12,4),(10,9),(14,9),(12,12))
I["safe"]=P((5.5,15),(16.5,7))+C(19.5,15,1.75)+DOT(4.5,15,1.75)+P((3,19.5),(21,19.5))
I["launch-rail"]=P((10.5,2.5),(10.5,18))+P((13.5,2.5),(13.5,18))+P((5,18),(19,18))+P((8,18),(5,22))+P((16,18),(19,22))+P((10.5,6),(13.5,6))
I["liftoff"]=P((12,15.5),(12,3))+P((7.5,7.5),(12,3),(16.5,7.5))+P((3,19.5),(21,19.5))+P((5,22),(7,19.5))+P((10,22),(12,19.5))+P((15,22),(17,19.5))
I["apogee"]=D("M3 21 Q12 -5 21 21")+P((7,8),(17,8))+DOT(12,8,1.5)
I["touchdown"]=P((12,3),(12,15.5))+P((7.5,11),(12,15.5),(16.5,11))+P((3,19.5),(21,19.5))+P((5,22),(7,19.5))+P((10,22),(12,19.5))+P((15,22),(17,19.5))
I["windsock"]=P((4,2.5),(4,21.5))+P((4,4.5),(20,7),(20,10.5),(4,13),close=True)+P((9.5,5.4),(9.5,12.1))+P((15,6.2),(15,11.3))
I["cloud"]=D("M7 18 A4 4 0 0 1 7 10 A5.5 5.5 0 0 1 17.5 9 A4.5 4.5 0 0 1 17 18 Z")
I["thermometer"]=D("M10 14.5 V5 A2 2 0 0 1 14 5 V14.5 A4 4 0 1 1 10 14.5 Z")+P((12,10),(12,17))+DOT(12,17.5,1.6)
I["gauge"]=D("M4.5 17 A8.5 8.5 0 1 1 19.5 17")+P((12,13),(16.5,8.5))+DOT(12,13,1.5)+P((4.5,17),(19.5,17))
I["gps-fix"]=C(12,12,6.5)+P((12,2),(12,7))+P((12,17),(12,22))+P((2,12),(7,12))+P((17,12),(22,12))+DOT(12,12,1.5)
I["landing-site"]=D("M12 21.5 L6.2 14 A7.25 7.25 0 1 1 17.8 14 Z")+C(12,9.5,2.5)
I["battery"]=P((3,7.5),(18,7.5),(18,16.5),(3,16.5),close=True)+P((18,10),(21,10),(21,14),(18,14))+P((6.5,10.5),(6.5,13.5))+P((9.5,10.5),(9.5,13.5))+P((12.5,10.5),(12.5,13.5))
I["telemetry"]=P((12,11),(12,21.5))+P((8,21.5),(16,21.5))+DOT(12,9.5,1.5)+D("M8.5 13 A5 5 0 0 1 8.5 6")+D("M15.5 13 A5 5 0 0 0 15.5 6")+D("M5.5 15.5 A8.5 8.5 0 0 1 5.5 3.5")+D("M18.5 15.5 A8.5 8.5 0 0 0 18.5 3.5")
I["flight-log"]=P((5,2.5),(15,2.5),(19,6.5),(19,21.5),(5,21.5),close=True)+P((8,17),(10,13),(12,15),(16,8))
I["simulate"]=D("M3 21 Q11 -3 21 15")+DOT(3,21,1.5)
I["simulate"]=I["simulate"].replace('<path d=','<path stroke-dasharray="2.5 2.5" stroke-linecap="butt" d=')
I["dimension"]=P((4,5),(4,19))+P((20,5),(20,19))+P((6.5,12),(17.5,12))+FILL("M4.75 12 L8.5 10 L8.5 14 Z")+FILL("M19.25 12 L15.5 10 L15.5 14 Z")
I["mass"]=P((6,20.5),(8,9),(16,9),(18,20.5),close=True)+C(12,5.5,2.5)
I["cg"]=C(12,12,7.5)+FILL("M12 12 L12 4.5 A7.5 7.5 0 0 1 19.5 12 Z")+FILL("M12 12 L12 19.5 A7.5 7.5 0 0 1 4.5 12 Z")
I["cp"]=C(12,12,7.5)+DOT(12,12,2.25)
# ---------------- status
I["ok"]=C(12,12,9)+P((7.5,12),(10.5,15),(16.5,9))
I["info"]=P((3,3),(21,3),(21,21),(3,21),close=True)+P((12,10.5),(12,17))+DOT(12,7,1.25)
I["caution"]=P((12,3),(21.5,20),(2.5,20),close=True)+P((12,9),(12,14))+DOT(12,16.75,1.25)
I["danger"]=P((8.3,3),(15.7,3),(21,8.3),(21,15.7),(15.7,21),(8.3,21),(3,15.7),(3,8.3),close=True)+P((12,7.5),(12,13.5))+DOT(12,16.5,1.25)
# ---------------- interface
I["check"]=P((4.5,12.5),(9.5,17.5),(19.5,7.5))
I["close"]=P((5.5,5.5),(18.5,18.5))+P((18.5,5.5),(5.5,18.5))
I["plus"]=P((12,4.5),(12,19.5))+P((4.5,12),(19.5,12))
I["minus"]=P((4.5,12),(19.5,12))
I["chevron"]=P((9,5),(16,12),(9,19))
I["arrow"]=P((4,12),(19.5,12))+P((13,5.5),(19.5,12),(13,18.5))
I["external"]=P((18.5,13),(18.5,20),(4,20),(4,5.5),(11,5.5))+P((14,3.5),(20.5,3.5),(20.5,10))+P((20.5,3.5),(11.5,12.5))
I["copy"]=P((8,8),(20,8),(20,20.5),(8,20.5),close=True)+P((4,16),(4,3.5),(16,3.5))
I["download"]=P((12,3),(12,15))+P((7,10),(12,15),(17,10))+P((4,15.5),(4,20.5),(20,20.5),(20,15.5))
I["upload"]=P((12,15),(12,3))+P((7,8),(12,3),(17,8))+P((4,15.5),(4,20.5),(20,20.5),(20,15.5))
I["search"]=C(10,10,6.25)+P((14.5,14.5),(20.5,20.5))
hexpts=[(12+8.5*math.cos(math.radians(a)),12+8.5*math.sin(math.radians(a))) for a in range(0,360,60)]
I["settings"]=P(*hexpts,close=True)+C(12,12,3.5)
I["menu"]=P((3.5,6.5),(20.5,6.5))+P((3.5,12),(20.5,12))+P((3.5,17.5),(20.5,17.5))
I["more"]=DOT(5,12,1.6)+DOT(12,12,1.6)+DOT(19,12,1.6)
I["link"]=D("M10 14 L14 10")+D("M11 7 L13 5 A3.54 3.54 0 0 1 19 11 L17 13")+D("M13 17 L11 19 A3.54 3.54 0 0 1 5 13 L7 11")
I["sun"]=C(12,12,4)+"".join(P((12+6.5*math.cos(math.radians(a)),12+6.5*math.sin(math.radians(a))),(12+9.5*math.cos(math.radians(a)),12+9.5*math.sin(math.radians(a)))) for a in range(0,360,45))
I["moon"]=D("M19.5 14.5 A8 8 0 1 1 9.5 4.5 A6.5 6.5 0 0 0 19.5 14.5 Z")
I["print"]=P((7,9),(7,3.5),(17,3.5),(17,9))+P((7,17),(3.5,17),(3.5,9),(20.5,9),(20.5,17),(17,17))+P((7,14),(17,14),(17,20.5),(7,20.5),close=True)
I["refresh"]=D("M19.5 12 A7.5 7.5 0 1 1 17.3 6.7")+P((18,2.5),(18,7.5),(13,7.5))
I["edit"]=P((4,20),(4,16),(15,5),(19,9),(8,20),close=True)+P((12.5,7.5),(16.5,11.5))
I["delete"]=P((3.5,6),(20.5,6))+P((9,6),(9,3.5),(15,3.5),(15,6))+P((5.5,6),(6.5,21),(17.5,21),(18.5,6))+P((10,10),(10,17))+P((14,10),(14,17))
I["clock"]=C(12,12,9)+P((12,6.5),(12,12),(16,14.5))
I["calendar"]=P((3.5,5.5),(20.5,5.5),(20.5,20.5),(3.5,20.5),close=True)+P((3.5,10),(20.5,10))+P((8,3),(8,7.5))+P((16,3),(16,7.5))
I["filter"]=P((3.5,4.5),(20.5,4.5),(14,12.5),(14,19.5),(10,21),(10,12.5),close=True)
I["help"]=C(12,12,9)+D("M9.25 9.5 A2.75 2.75 0 1 1 13.5 11.8 C12.6 12.4 12 13 12 14.25")+DOT(12,17,1.25)


GROUPS = [("Rocketry", ["nose-cone", "rocket", "fin", "motor", "thrust-curve", "parachute", "drogue", "flight-computer", "ejection-charge",
                        "continuity", "no-continuity", "armed", "safe", "launch-rail", "liftoff", "apogee", "touchdown", "simulate",
                        "flight-log", "telemetry", "gps-fix", "landing-site", "battery", "dimension", "mass", "cg", "cp"]),
          ("Weather", ["windsock", "cloud", "thermometer", "gauge"]),
          ("Status", ["ok", "info", "caution", "danger"]),
          ("Interface", ["check", "close", "plus", "minus", "chevron", "arrow", "external", "copy", "download", "upload", "search",
                         "settings", "menu", "more", "link", "sun", "moon", "print", "refresh", "edit", "delete", "clock", "calendar",
                         "filter", "help"])]
ATTRS = ('fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" stroke-linejoin="miter" stroke-miterlimit="4"')
def svg(name, size=24):
    """A standalone icon: currentColor, no styles, safe to inline."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" {ATTRS} '
            f'aria-hidden="true" focusable="false">{ICONS[name]}</svg>')
def symbol(name):
    return f'<symbol id="fs-{name}" viewBox="0 0 24 24" {ATTRS}>{ICONS[name]}</symbol>'
def inline(name, cls="fs-icon"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" {ATTRS} aria-hidden="true" focusable="false">{ICONS[name]}</svg>'
assert sorted(ICONS) == sorted(n for _, ns in GROUPS for n in ns), set(ICONS) ^ {n for _, ns in GROUPS for n in ns}

def _dashed_quad(p0, c, p1, dash=2.5, gap=2.5, n=400):
    """A quadratic Bezier as separate dash subpaths (Android vector drawables have no stroke dashes)."""
    pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1])
           for t in (i / n for i in range(n + 1))]
    out, run, on, seg = [], 0.0, True, [pts[0]]
    for a, b in zip(pts, pts[1:]):
        run += math.dist(a, b)
        if on: seg.append(b)
        if run >= (dash if on else gap):
            if on: out.append("M" + " L".join(f"{f(x)} {f(y)}" for x, y in seg))
            on = not on; run = 0.0; seg = [b]
    if on and len(seg) > 1: out.append("M" + " L".join(f"{f(x)} {f(y)}" for x, y in seg))
    return " ".join(out)

def vector_drawable(name):
    """Android VectorDrawable XML for one icon: strokes and fills in white, tinted by the theme (colorControlNormal)."""
    import re
    body = ICONS[name]; paths = []
    for m in re.finditer(r"<(path|circle)([^>]*)/>", body):
        tag, attrs = m.group(1), m.group(2)
        A = dict(re.findall(r'([\w-]+)="([^"]*)"', attrs))
        if tag == "circle":
            cx, cy, r = float(A["cx"]), float(A["cy"]), float(A["r"])
            d = f"M{f(cx - r)} {f(cy)} A{f(r)} {f(r)} 0 1 0 {f(cx + r)} {f(cy)} A{f(r)} {f(r)} 0 1 0 {f(cx - r)} {f(cy)} Z"
        else: d = A["d"]
        if A.get("stroke-dasharray"):           # the dashed trajectory in "simulate": M x y Q cx cy x1 y1
            q = [float(v) for v in re.findall(r"-?[\d.]+", d)]
            d = _dashed_quad((q[0], q[1]), (q[2], q[3]), (q[4], q[5]))
        if A.get("fill") == "currentColor":
            paths.append(f'    <path android:fillColor="#FFFFFFFF" android:pathData="{d}"/>')
        else:
            cap = "butt" if A.get("stroke-dasharray") else "square"
            paths.append(f'    <path android:strokeColor="#FFFFFFFF" android:strokeWidth="1.5" android:strokeLineCap="{cap}" '
                         f'android:strokeLineJoin="miter" android:strokeMiterLimit="4" android:pathData="{d}"/>')
    return ('<?xml version="1.0" encoding="utf-8"?>\n<!-- FusionSpace icon: ' + name + '. Generated by tools/build/kit_icons.py. -->\n'
            '<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp"\n'
            '    android:viewportWidth="24" android:viewportHeight="24" android:tint="?attr/colorControlNormal">\n'
            + "\n".join(paths) + "\n</vector>\n")
