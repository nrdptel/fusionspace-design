"""FusionSpace product system, watches: product/watch/ (reference screens, complications and tiles, SwiftUI and Compose parts).

product/watch.md says what a watch is for in this system: finding a landed rocket, glancing at a flight, and feeling the
events that matter, with the phone or the device doing anything that changes hardware. This draws it. Every screen exists
twice, once per platform: an Apple Watch Ultra 3 on watchOS 27 (SF type, Liquid Glass toolbar buttons) and a Pixel Watch 4
on Wear OS 6 (round, curved time text, edge-hugging button, Roboto). The content layer is the same on both: Cascadia Mono
readouts and labels, the signal colors, the state box. Watches are emissive screens, so they always use the dark roles.

Screens and the complication/tile page are HTML on product/web/fusionspace.css, shot with Playwright at 2x. The SwiftUI and
Compose parts are written in source/product/watch/ and copied with their {{...}} values filled in.
"""
import os, re, math, shutil, html
import build, kit_product as kp, kit_icons, kit_mobile as km
from build import VOID, PAPER, WHITE

W = "watch"
SRC = os.path.join(kp.SRC, "watch")
def wr(rel, s): return kp.wr(f"{W}/{rel}", s)
def out(rel): return kp.out(f"{W}/{rel}")
ico = km.ico

# ================================================================ devices
# Logical sizes (pt / dp), checked October 2026; see product/watch.md. Corner radius and round insets are drawn, not
# measured: neither vendor publishes them, apps read safe areas from the system.
# Apple: px from apple.com/watch/compare at @2x. Google publishes size classes, not per-device dp: small 192-224 dp, large
# 225 dp and up; the large watch is drawn at 228 dp, the small at the class's 192 dp floor.
DEVICES = {
    "watchos": {"name": "Apple Watch Ultra 4", "size": "49 mm", "short": "Ultra 4 49 mm", "os": "watchOS 27", "w": 211, "h": 257, "radius": 52, "round": False},
    "wearos": {"name": "Pixel Watch 5", "size": "45 mm", "short": "Pixel Watch 5 45 mm", "os": "Wear OS 7", "w": 228, "h": 228, "radius": 114, "round": True},
    "watchos-small": {"name": "Apple Watch SE 3", "size": "40 mm", "short": "SE 3 40 mm", "os": "watchOS 27", "w": 162, "h": 197, "radius": 40, "round": False},
    "wearos-small": {"name": "Wear OS small round", "size": "", "short": "small class", "os": "Wear OS 7", "w": 192, "h": 192, "radius": 96, "round": True},
}
def plat(p): return p.split("-")[0]
SCALE = 2
DESIG = "FS-VEGA-004"
# The rocket is at 062° true; the wearer faces 020°, so the arrow turns 42° clockwise.
ROCKET = {"dist": 1352, "bearing": 62, "heading": 20, "fix_s": 4}

def arrow(deg, size=112, outline=False, stale=False):
    """The way to the rocket, relative to where the wrist points: a nose cone (the brand's own shape) as the arrowhead,
    on a ring with the wearer's heading at the top. Outline only when the screen is dimmed (Always On)."""
    c = size / 2; r = c - 4
    fill = "none" if outline else "var(--fs-ink)"
    o = [f'<svg class="w-arrow" viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img" aria-label="Rocket {deg} degrees to your right">',
         f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="var(--fs-rule-strong)" stroke-width="1.5"/>']
    for a in range(0, 360, 30):
        r0 = r - (7 if a == 0 else 4)
        x0, y0 = c + r0 * math.sin(math.radians(a)), c - r0 * math.cos(math.radians(a))
        x1, y1 = c + r * math.sin(math.radians(a)), c - r * math.cos(math.radians(a))
        o.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="var(--fs-ink-muted)" stroke-width="{2 if a == 0 else 1}"/>')
    # Von Karman nose cone, tip at the ring's top, length 0.62 r, base radius 0.2 r, then a short shaft
    L, R = r * 0.78, r * 0.3
    pts = []
    for i in range(0, 21):
        x = L * i / 20; th = math.acos(1 - 2 * x / L); y = R / math.sqrt(math.pi) * math.sqrt(th - math.sin(2 * th) / 2)
        pts.append((x, y))
    tip = c - r + 10
    path = "M" + " L".join(f"{c - y:.2f},{tip + x:.2f}" for x, y in reversed(pts)) + " L" + " L".join(f"{c + y:.2f},{tip + x:.2f}" for x, y in pts) + "Z"
    sw = 2 if outline else 0
    o.append(f'<g transform="rotate({deg} {c} {c})"><path d="{path}" fill="{fill}" stroke="var(--fs-ink)" stroke-width="{sw}"/>'
             f'<line x1="{c}" y1="{tip + L:.1f}" x2="{c}" y2="{c + r * 0.45:.1f}" stroke="var(--fs-ink)" stroke-width="{4 if not outline else 2}"/></g>')
    o.append(f'<circle cx="{c}" cy="{c}" r="3" fill="var(--fs-ink-muted)"/>')
    o.append("</svg>")
    return "".join(o)

def curved_time(d, text="9:41"):
    """Wear OS TimeText: the time on an arc along the top edge (the system draws it; this is a stand-in)."""
    w = d["w"]; r = w / 2 - 14
    return (f'<svg class="timetext" viewBox="0 0 {w} 40" width="{w}" height="40"><defs><path id="tt" d="M {w / 2 - r} {w / 2} A {r} {r} 0 0 1 {w / 2 + r} {w / 2}"/></defs>'
            f'<text font-family="Roboto" font-size="13" font-weight="500" fill="var(--fs-ink)" text-anchor="middle"><textPath href="#tt" startOffset="50%">{text}</textPath></text></svg>')

def chrome(p, body, title="", theme="dark", aod=False, edge="", bg=None, extra_cls=""):
    """One watch screen. watchOS: title top-left in the app's tint, time top-right, page dots on the right. Wear OS: time on
    an arc at the top, the content centered, an edge-hugging button along the bottom, the scroll indicator on the right."""
    d = DEVICES[p]
    if plat(p) == "watchos":
        top = (f'<div class="wt-top"><span class="wt-title">{html.escape(title)}</span><span class="wt-time">9:41</span></div>'
               + ('<div class="wt-dots"><i></i><i class="on"></i><i></i><i></i></div>' if not aod else ""))
        bottom = edge
    else:
        top = curved_time(d) + ('<div class="wo-pos"><i></i></div>' if not aod else "")
        bottom = edge
    style = f'--w:{d["w"]}px;--h:{d["h"]}px' + (f';--fs-canvas:{bg}' if bg else "")
    return f"""<!doctype html>
<html lang="en" class="{plat(p)}{' aod' if aod else ''}{' small' if p.endswith('small') else ''} {extra_cls}" data-theme="{theme}" style="{style}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={d['w']}, initial-scale=1">
<title>{html.escape(title)} · {d['name']} · example</title>
<link rel="stylesheet" href="../../web/fonts.css">
<link rel="stylesheet" href="../../web/fusionspace.css">
<link rel="stylesheet" href="watch.css">
</head>
<body>
<div class="face">
{top}
<main class="wbody">
{body}
</main>
{bottom}
</div>
</body>
</html>
"""

def edge_button(p, label, kind="primary"):
    if plat(p) == "wearos":
        return f'<div class="edgebtn {kind}">{label}</div>'
    return f'<div class="wt-btn {kind}">{label}</div>'

# ================================================================ the screens
def scr_find(p, aod=False):
    """Walking to a landed rocket: the way, how far, how old the fix is. The one screen a watch is best at."""
    rel = ROCKET["bearing"] - ROCKET["heading"]
    age = "fix 4 s ago" if not aod else "as of 9:41"
    size = {"watchos": 104, "wearos": 84, "watchos-small": 60, "wearos-small": 60}[p]
    body = (f'<div class="w-find">{arrow(rel, size, outline=aod)}'
            f'<div class="w-read"><span class="w-big">1,352</span><span class="u">ft</span></div>'
            f'<div class="w-sub">062° T · {age}</div></div>')
    # Always On keeps the layout and shows the control as unavailable (Apple), outlined (Google), instead of removing it
    edge = edge_button(p, "Found it", "quiet" + (" dim" if aod else ""))
    return chrome(p, body, title="Find", aod=aod, edge=edge)

def scr_flight(p):
    """A flight in progress: the phase, the one number that matters now, its rate, the link's age."""
    names = ["PAD", "BOOST", "COAST", "APOGEE", "DROGUE", "MAIN", "LANDED"]; i = names.index("MAIN")
    ticks = '<ol class="w-ticks" aria-label="Phase: main">' + "".join(
        f'<li data-s="{"done" if j < i else "now" if j == i else "next"}"></li>' for j in range(len(names))) + "</ol>"
    body = (f'<div class="w-flight"><span class="w-k">MAIN · T+1:02</span>{ticks}'
            f'<span class="w-k">ALTITUDE</span><div class="w-read"><span class="w-big">612</span><span class="u">ft AGL</span></div>'
            f'<div class="w-row"><span class="w-k">DESCENT</span><span class="w-v">18 <span class="u">ft/s</span></span></div>'
            f'<div class="w-row"><span class="w-k">LINK</span><span class="w-v">0.4 <span class="u">s</span></span></div></div>')
    return chrome(p, body, title="Flight 04")

def scr_pad(p):
    """The device's state at the pad, read only: ARMED in its inverted box, the channels. The watch sends nothing."""
    chans = "".join(f'<div class="w-ch"><span>{n}</span>{s}</div>' for n, s in (
        ("1 DROGUE", kp.status("ok", "Cont", "continuity")), ("2 MAIN", kp.status("ok", "Cont", "continuity")), ("3 —", kp.status("off", "Not used"))))
    body = (f'<div class="w-pad"><span class="w-box armed">ARMED</span><span class="w-k">{DESIG} · 0.3 <span class="u">s</span></span>{chans}'
            f'<p class="w-note">Safe it with the switch or the phone.</p></div>')
    return chrome(p, body, title="Pad 3")

def scr_unfired(p):
    """After landing, a configured charge didn't fire: first, before anything else, until it's acknowledged."""
    fill = kp.SIGNALS["danger"][2]
    body = (f'<div class="w-alert">{ico("danger")}<span class="w-alert-h">UNFIRED</span>'
            f'<span class="w-alert-c">2 · MAIN</span><p>Approach as live. Disarm before handling.</p></div>')
    return chrome(p, body, title="Vega", edge=edge_button(p, "OK", "onfill"), bg=fill, extra_cls="alert")

SCREENS = [("find", lambda p: scr_find(p), "Find: the way to the rocket, how far, how old the fix is"),
           ("find-small", lambda p: scr_find(p + "-small"), "Find, smallest: the same screen at the smallest size"),
           ("find-aod", lambda p: scr_find(p, aod=True), "Find, Always On: outlines, muted, updated once a minute"),
           ("flight", scr_flight, "Flight: phase, altitude, descent rate, link age"),
           ("pad", scr_pad, "Pad: the device's state, read only"),
           ("unfired", scr_unfired, "Unfired: a charge that didn't fire, first")]


# ================================================================ watch faces: complications, Smart Stack, tiles (product/watch/faces/)
# Sizes (pt / dp) for the 49 mm Ultra and a 45 mm round Wear OS watch; see product/watch.md for the sources.
FACE = {
    "rect": (193, 82), "circ": 50, "corner": 38,                     # watchOS accessory families at 45/49 mm (HIG)
    "stack": (191, 81.5),                                              # Smart Stack Live Activity, 49 mm
}

def comp_rect(kind="find", tint=None):
    if kind == "find":
        return ('<div class="c-rect"><div class="c-h"><span>VEGA · LANDED</span><span class="u">4 s</span></div>'
                '<div class="c-big">1,352 <span class="u">ft</span></div><div class="c-q">062° T from you</div></div>')
    return ('<div class="c-rect"><div class="c-h"><span>WIND · 4 MIN</span></div>'
            '<div class="c-big">12 <span class="u">mph</span> G19</div>'
            f'<div class="c-caution">{ico("caution")}NEAR LIMIT</div></div>')

def comp_circ(kind="find"):
    if kind == "find":
        return (f'<div class="c-circ">{arrow(ROCKET["bearing"] - ROCKET["heading"], 30)}<span class="c-cv">1352</span><span class="c-cu">ft</span></div>')
    if kind == "wind":
        return '<div class="c-circ"><span class="c-cu">MPH</span><span class="c-cv l">12</span><span class="c-cu">G19</span></div>'
    return '<div class="c-circ"><span class="c-box">SAFE</span></div>'

def apple_face(mode):
    """A Modular-style face with FusionSpace complications: inline, rectangular, three circular, one corner. mode:
    full (full color), tinted (accented: the system draws everything in one tint)."""
    return (f'<div class="wface apple {mode}"><div class="f-inline">Vega 1,352 ft 062° T</div><div class="f-time">9:41</div>'
            f'{comp_rect("find")}<div class="f-row">{comp_circ("find")}{comp_circ("wind")}{comp_circ("state")}</div></div>')

def smart_stack():
    return (f'<div class="wface apple stack"><div class="f-sttime">9:41</div>'
            '<div class="st-card la"><div class="c-h"><span>FLIGHT 04 · MAIN</span><span class="u">0.4 s</span></div>'
            '<div class="c-big">612 <span class="u">ft AGL</span></div><div class="c-q">1,352 ft from you · 062° T</div></div>'
            f'<div class="st-card">{comp_rect("wind").replace("c-rect", "c-rect flat")}</div></div>')

def wear_tile(kind):
    if kind == "find":
        body = ('<div class="t-title">VEGA · LANDED</div><div class="t-main"><div class="c-big">1,352 <span class="u">ft</span></div>'
                '<div class="c-q">062° T · fix 4 s ago</div></div><div class="t-edge">Find</div>')
    else:
        body = ('<div class="t-title">WINDOW · 2:10 PM</div><div class="t-main"><div class="c-big">12 <span class="u">mph</span></div>'
                f'<div class="c-q">Gusts 19 · from 270°</div><div class="c-caution">{ico("caution")}NEAR LIMIT</div></div><div class="t-edge q">Refresh</div>')
    return f'<div class="wface wear tile">{curved_time(DEVICES["wearos"])}{body}</div>'

def wear_face():
    """A Wear OS face with FusionSpace complications: SHORT_TEXT, RANGED_VALUE and LONG_TEXT, and the ongoing activity."""
    ring_r = 22; frac = 612 / 5104; circ = 2 * math.pi * ring_r
    ranged = (f'<div class="wc ranged"><svg width="56" height="56" viewBox="0 0 56 56"><circle cx="28" cy="28" r="{ring_r}" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="4"/>'
              f'<circle cx="28" cy="28" r="{ring_r}" fill="none" stroke="var(--fs-ink)" stroke-width="4" stroke-dasharray="{circ * frac:.1f} {circ:.1f}" transform="rotate(-90 28 28)"/></svg>'
              '<span class="c-cv">612</span><span class="c-cu">ft AGL</span></div>')
    return (f'<div class="wface wear face"><div class="wc short">{ico("rocket")}<span>1,352 ft</span></div>'
            f'<div class="f-time r">9:41</div>{ranged}<div class="wc long">Vega 1,352 ft at 062° T</div>'
            f'<div class="wc ongoing" aria-label="Tracking: tap to return">{ico("gps-fix")}</div>'
            f'<div class="wc side">{ico("windsock")}<span class="c-cv">12</span><span class="c-cu">mph</span></div></div>')

FACES_CSS = """
body { margin: 0; background: #fff; }
.fig { display: inline-block; padding: 22px; background: %(paper)s; }
.fig > h2 { font: 600 15px/20px 'Cascadia Mono', monospace; margin: 0 0 4px; color: #0B0F1C; }
.fig > p.cap { font: 400 13px/18px 'Cascadia Mono', monospace; color: #566079; margin: 0 0 16px; max-width: 760px; }
.row { display: flex; gap: 22px; align-items: flex-start; }
.col { display: grid; gap: 10px; justify-items: center; }
.lab { font: 400 12px/16px 'Cascadia Mono', monospace; color: #566079; }
.u { color: var(--fs-ink-muted); text-transform: none; letter-spacing: 0; }
.wface { position: relative; box-sizing: border-box; background: #000; color: var(--fs-ink); overflow: hidden; }
.wface.apple { width: %(aw)spx; height: %(ah)spx; border-radius: 52px; padding: 12px 10px; display: grid; align-content: start; gap: 6px; }
.wface.wear { width: %(ww)spx; height: %(wh)spx; border-radius: 50%%; }
.f-inline { font: 600 13px/16px -apple-system, system-ui; text-align: center; color: var(--fs-ink); }
.f-time { font: 600 44px/44px -apple-system, system-ui; color: #fff; padding-left: 4px; }
.f-row { display: flex; justify-content: space-between; padding: 0 2px; }
.c-rect { width: 100%%; box-sizing: border-box; padding: 6px 8px; border-radius: 14px; background: rgba(255,255,255,.10); display: grid; gap: 1px; }
.c-rect.flat { background: transparent; padding: 0; }
.c-h { display: flex; justify-content: space-between; font: 400 11px/14px 'Cascadia Mono', monospace; letter-spacing: .05em; color: var(--fs-ink-muted); }
.c-big { font: 400 24px/28px 'Cascadia Mono', monospace; font-variant-numeric: tabular-nums; }
.c-big .u { font-size: 12px; }
.c-q { font: 400 11px/14px 'Archivo', sans-serif; color: var(--fs-ink-muted); }
.c-caution { display: inline-flex; width: fit-content; align-items: center; gap: 3px; font: 600 10px/13px 'Cascadia Mono', monospace; padding: 1px 5px;
  background: var(--fs-caution-fill); color: var(--fs-on-caution-fill); }
.c-caution svg { width: 11px; height: 11px; }
.c-circ { width: %(circ)spx; height: %(circ)spx; border-radius: 50%%; background: rgba(255,255,255,.10); display: grid; place-content: center; justify-items: center; gap: 0; }
.c-circ .w-arrow { width: 24px; height: 24px; }
.c-cv { font: 400 13px/14px 'Cascadia Mono', monospace; }
.c-cv.l { font-size: 18px; line-height: 19px; }
.c-cu { font: 400 10px/11px 'Cascadia Mono', monospace; color: var(--fs-ink-muted); letter-spacing: .04em; }
.c-box { font: 600 10px/1 'Cascadia Mono', monospace; padding: 3px 4px; border: 1.5px solid var(--fs-ink); }
.c-corner { position: absolute; }
/* accented: the system draws everything in one tint; meaning stays in words and shapes */
/* accented: primary content tinted white, the accent group (the values) in the face's color */
.tinted { --fs-ink: #fff; --fs-ink-muted: rgba(255,255,255,.62); --fs-rule-strong: rgba(255,255,255,.5); }
.tinted .f-time, .tinted .c-big, .tinted .c-cv { color: #FFB25C; }
.tinted .w-arrow path { fill: #FFB25C; stroke: #FFB25C; }
.tinted .w-arrow g line { stroke: #FFB25C; }
.tinted .c-caution { background: transparent; color: #fff; border: 1.5px solid #fff; }
.tinted .c-box { border-color: #fff; }
/* Smart Stack */
.stack { gap: 8px; }
.f-sttime { font: 600 15px/18px -apple-system, system-ui; text-align: right; padding-right: 8px; color: #fff; }
.st-card { border-radius: 18px; background: #1c1d22; padding: 8px 10px; display: grid; gap: 1px; }
.st-card.la { background: %(abyss)s; }
/* Wear OS tile: title slot, main slot, edge button */
.tile { display: grid; justify-items: center; align-content: start; }
.t-title { margin-top: 34px; font: 400 11px/14px 'Cascadia Mono', monospace; letter-spacing: .06em; color: var(--fs-ink-muted); }
.t-main { margin-top: 14px; display: grid; justify-items: center; gap: 2px; text-align: center; }
.tile .c-big { font-size: 30px; line-height: 34px; }
.t-edge { position: absolute; left: 50%%; bottom: 0; width: 132px; margin-left: -66px; height: 46px; padding-top: 8px; box-sizing: border-box;
  border-radius: 23px 23px 66px 66px / 23px 23px 46px 46px; text-align: center; font: 500 15px/20px Roboto, sans-serif; background: var(--fs-action); color: var(--fs-on-action); }
.t-edge.q { background: var(--fs-surface); color: var(--fs-ink); }
.timetext { position: absolute; top: 0; left: 0; }
/* Wear OS face */
.face .f-time.r { position: absolute; top: 78px; left: 0; right: 0; text-align: center; font: 500 46px/46px Roboto, sans-serif; padding: 0; }
.wc { position: absolute; display: flex; align-items: center; gap: 4px; font: 500 12px/14px Roboto, sans-serif; }
.wc svg { width: 14px; height: 14px; }
.wc.short { top: 34px; left: 0; right: 0; justify-content: center; }
.wc.ranged { top: 128px; left: 50%%; margin-left: -28px; width: 56px; height: 56px; display: grid; place-content: center; justify-items: center; }
.wc.ranged svg { position: absolute; inset: 0; width: 56px; height: 56px; }
.wc.ranged .c-cv { font-size: 12px; }
.wc.ranged .c-cu { font-size: 7px; }
.wc.long { bottom: 22px; left: 0; right: 0; justify-content: center; font-size: 11px; color: var(--fs-ink-muted); }
.wc.ongoing { top: 143px; left: 44px; width: 26px; height: 26px; border-radius: 50%%; background: var(--fs-ok-fill); color: #fff; justify-content: center; }
.wc.side { top: 130px; right: 30px; width: 52px; height: 52px; border-radius: 50%%; background: rgba(255,255,255,.10); display: grid; place-content: center; justify-items: center; gap: 0; }
.wc.side svg { width: 13px; height: 13px; }
"""

def faces_page():
    a, w_ = DEVICES["watchos"], DEVICES["wearos"]
    css = FACES_CSS % {"paper": PAPER, "aw": a["w"], "ah": a["h"], "ww": w_["w"], "wh": w_["h"], "circ": FACE["circ"], "abyss": kp.role("surface", "dark")}
    figs = [
        ("watchos-complications", "watchOS · Complications",
         "On a Modular-style face: inline, rectangular, and three circular (the way to the rocket, the wind, the device's state). In accented "
         "rendering the system draws the content white and only the value in the face's color, so the caution is an outlined word and the state a box, never only a color.",
         '<div class="row">' + "".join(f'<div class="col"><span class="lab">{n}</span>{apple_face(m)}</div>' for m, n in (("full", "Full color"), ("tinted", "Accented (tinted)"))) + "</div>"),
        ("watchos-smart-stack", "watchOS · Smart Stack",
         "The phone's Live Activity arrives on its own at the top of the Smart Stack while a flight is on; under it, the wind widget, "
         "ranked by relevance on launch days.", f'<div class="row"><div class="col">{smart_stack()}</div></div>'),
        ("wearos-tiles", "Wear OS · Tiles",
         "Title slot, main slot, edge button: one readout with its unit and its age, and one action. A tile is a glance; anything that "
         "moves (the arrow, a live altitude) belongs in the app.",
         '<div class="row">' + "".join(f'<div class="col"><span class="lab">{n}</span>{wear_tile(k)}</div>' for k, n in (("find", "Find: opens the app"), ("wind", "Window"))) + "</div>"),
        ("wearos-face", "Wear OS · Complications and the ongoing activity",
         "SHORT_TEXT (distance with a rocket icon), RANGED_VALUE (altitude on the way down), LONG_TEXT, and the ongoing activity's icon, "
         "which brings the app back in one tap while tracking runs.", f'<div class="row"><div class="col">{wear_face()}</div></div>'),
    ]
    body = "\n".join(f'<section class="fig" id="{i}"><h2>{t}</h2><p class="cap">{c}</p>{h}</section><br>' for i, t, c, h in figs)
    page_ = f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Watch faces · FusionSpace watch · example</title>
<link rel="stylesheet" href="../../web/fonts.css">
<link rel="stylesheet" href="../../web/fusionspace.css">
<style>
@font-face {{ font-family: 'Roboto'; font-weight: 100 900; font-stretch: 75% 100%; src: url('../../mobile/fonts/Roboto.woff2') format('woff2'); }}
{css}
</style>
</head>
<body>
{body}
</body>
</html>
"""
    return page_, [f[0] for f in figs]

def build_faces():
    pg, ids = faces_page()
    wr("faces/index.html", pg)
    return shots([("faces/index.html", f"faces/{i}.png", 1200, 900, f"#{i}") for i in ids])


# ================================================================ code (product/watch/swiftui/, product/watch/compose/)
FIND_STALE_S = 60                  # a rocket's fix older than this shows as stale on the watch (it is sent every few s)
UNFIRED_GAP_S = 0.6                # between taps in a pattern: the beep language's 600 ms between groups
TILE_FRESH_MS = 60_000             # a Find tile asks for a refresh once a minute while tracking
def _ident(n): return re.sub(r"-(\w)", lambda m: m.group(1).upper(), n)
def code_values():
    cols = [f"    val {_ident(n)} = Color(0xFF{kp.role(n, 'dark')[1:]})   // {use}" for n, l, d_, f, use in kp.ROLES]
    for n, fill, on in kp.FILLS:
        cols.append(f"    val {_ident(n)} = Color(0xFF{fill[1:]})")
        cols.append(f"    val on{_ident(n)[0].upper() + _ident(n)[1:]} = Color(0xFF{on[1:]})")
    return {"COLORS": "\n".join(cols), "FIND_STALE_X": FIND_STALE_S // km.STALE_S["flight"], "FIND_STALE_S": FIND_STALE_S,
            "UNFIRED_GAP_S": UNFIRED_GAP_S, "GAP_MS": int(UNFIRED_GAP_S * 1000), "TILE_FRESH_MS": TILE_FRESH_MS}
CODE = [("swiftui/FSWatch.swift", "watchOS: FSBearingArrow, FSWatchFind (Always On aware), FSWatchState, FSWatchUnfired, FSWristEvent (the wrist language)"),
        ("swiftui/FSWatchComplications.swift", "WidgetKit: Find on every accessory family, with Smart Stack relevance"),
        ("compose/FsWear.kt", "Wear OS: FsWearColors, FusionSpaceWearTheme, FsBearingArrow, FsWearFind (ambient aware), FsWearStateBox, FsWearUnfired, FsWristEvent, the ongoing activity"),
        ("compose/FsWearTile.kt", "Wear OS: the Find tile (ProtoLayout Material 3) and its complications")]
def build_code():
    vals = code_values()
    for rel, _ in CODE:
        t = open(os.path.join(SRC, rel), encoding="utf-8").read()
        t = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: str(vals[m.group(1)]), t)
        assert "{{" not in t, rel
        wr(rel, t)


README = """# Watches

Reference parts for FusionSpace apps on Apple Watch and Wear OS. The rules are in `product/watch.md`; this folder draws them
and puts the watch's content layer into code. Generated by `tools/build/kit_watch.py` from `source/product/watch/`.

![Five screens on Apple Watch and Wear OS](preview.png)

## Screens

Each screen exists on both platforms with the same content and each platform's own chrome: the {a[name]} {a[size]}
({a[w]} × {a[h]} pt, {a[os]}) and the {w[name]} {w[size]} (drawn at {w[w]} dp, Wear OS's large round class, {w[os]}).
Find is also drawn at the smallest sizes: the {sa[name]} {sa[size]} ({sa[w]} × {sa[h]} pt) and Wear OS's small class
({sw[w]} dp). Always the dark roles.
Open the HTML in a browser, or look at the PNG (2x).

| Screen | What it shows |
|---|---|
{screens}

`screens/watch.css` draws the platform chrome for the mock-ups only (time, page dots, toolbar and edge buttons); apps use
the system's. The case outlines are drawn, not Apple's or Google's artwork.

## Complications, Smart Stack and tiles

`faces/index.html`, shot as one PNG per surface:

| File | What |
|---|---|
| `faces/watchos-complications.png` | Inline, rectangular and circular complications on a Modular-style face, full color and accented |
| `faces/watchos-smart-stack.png` | The phone's Live Activity at the top of the Smart Stack, the wind widget under it |
| `faces/wearos-tiles.png` | Find and Window tiles: title slot, main slot, edge button |
| `faces/wearos-face.png` | SHORT_TEXT, RANGED_VALUE and LONG_TEXT complications and the ongoing activity on a Wear OS face |

## Code (Apache-2.0)

| File | What |
|---|---|
{code}

**Checked** (October 2026): the Swift typechecks in Swift 6 mode against the macOS 26.2 SDK's SwiftUI, SwiftUICore,
WidgetKit and RelevanceKit interfaces with their macOS restrictions removed (there is no watchOS SDK on the build machine),
which checks every SwiftUI and WidgetKit call and type but isn't a watchOS build; `WKInterfaceDevice` haptics (WatchKit) and
`widgetLabel` aren't in that SDK and are unchecked. The Kotlin compiles with Kotlin 2.2.20 against Android API 36.1, Compose
1.12.1 for Android, Wear Compose Material 3 1.7.0, Tiles 1.6.2, ProtoLayout 1.4.2, watchface-complications 1.3.0 and
wear-ongoing 1.1.0. None of it has run on a watch yet.
"""
def build_readme():
    a, w_ = DEVICES["watchos"], DEVICES["wearos"]
    screens = "\n".join(f"| `screens/{{watchos,wearos}}-{k}` | {cap.split(': ', 1)[1]} |" for k, _, cap in SCREENS)
    code = "\n".join(f"| `{rel}` | {what} |" for rel, what in CODE)
    wr("README.md", README.format(a=a, w=w_, sa=DEVICES["watchos-small"], sw=DEVICES["wearos-small"], screens=screens, code=code))

# ================================================================ build
def shots(jobs):
    """jobs: (html rel, png rel, width, height, selector or None), under product/watch/. False without Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    with sync_playwright() as p_:
        b = p_.chromium.launch()
        for rel, dest, w, h, sel in jobs:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=SCALE)
            pg.goto("file://" + out(rel)); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
            os.makedirs(os.path.dirname(out(dest)), exist_ok=True)
            if sel: pg.locator(sel).screenshot(path=out(dest))
            else: pg.screenshot(path=out(dest), clip={"x": 0, "y": 0, "width": w, "height": h})
            pg.close()
        b.close()
    return True

def build_screens():
    css = open(os.path.join(SRC, "watch.css"), encoding="utf-8").read()
    wr("screens/watch.css", "/* Generated by tools/build/kit_watch.py from source/product/watch/watch.css; edit there. */\n" + css)
    jobs = []
    for key, fn, _ in SCREENS:
        for p in ("watchos", "wearos"):
            wr(f"screens/{p}-{key}.html", fn(p))
            d = DEVICES[p + "-small" if key.endswith("small") else p]; jobs.append((f"screens/{p}-{key}.html", f"screens/{p}-{key}.png", d["w"], d["h"], None))
    return shots(jobs)

def watch_tile(png, p, scale=1.0):
    """A shot masked to the screen's shape, with a 2 px drawn outline of the case (a line drawing, not a photo)."""
    from PIL import Image, ImageDraw
    d = DEVICES[p]; im = Image.open(png).convert("RGB")
    w, h = round(d["w"] * scale), round(d["h"] * scale)
    im = im.resize((w, h), Image.LANCZOS)
    pad = 14
    tile = Image.new("RGB", (w + 2 * pad, h + 2 * pad), tuple(kp._hex_rgb(PAPER)))
    mask = Image.new("L", (w, h), 0); md = ImageDraw.Draw(mask)
    dr = ImageDraw.Draw(tile); ink = tuple(kp._hex_rgb(VOID))
    if d["round"]:
        md.ellipse((0, 0, w - 1, h - 1), fill=255)
        dr.ellipse((pad - 10, pad - 10, w + pad + 9, h + pad + 9), outline=ink, width=2)
    else:
        r = round(d["radius"] * scale); md.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
        dr.rounded_rectangle((pad - 10, pad - 10, w + pad + 9, h + pad + 9), r + 10, outline=ink, width=2)
        cy = pad + h * 0.30; dr.rounded_rectangle((w + pad + 9, cy, w + pad + 15, cy + 34), 3, outline=ink, width=2)   # crown
    tile.paste(im, (pad, pad), mask)
    return tile

def build_preview():
    """product/watch/preview.png: every screen on both platforms, watchOS above Wear OS."""
    from PIL import Image, ImageDraw
    sc = 1.0; gap = 34; lab = 50; margin = 36
    rows_ = ("watchos", "wearos")
    tiles = {(p, k): watch_tile(out(f"screens/{p}-{k}.png"), p + "-small" if k.endswith("small") else p, sc) for k, *_ in SCREENS for p in rows_}
    tw = max(t.width for t in tiles.values()); th = {p: max(t.height for (pp, _), t in tiles.items() if pp == p) for p in rows_}
    W_ = margin * 2 + len(SCREENS) * tw + (len(SCREENS) - 1) * gap
    H_ = margin * 2 + sum(lab + th[p] for p in rows_) + gap
    im = Image.new("RGB", (W_, H_), tuple(kp._hex_rgb(PAPER))); dr = ImageDraw.Draw(im)
    f1, f2 = km._font(16, True), km._font(13)
    y = margin
    for p in rows_:
        for i, (k, _, cap) in enumerate(SCREENS):
            d = DEVICES[p + "-small" if k.endswith("small") else p]
            x = margin + i * (tw + gap)
            dr.text((x + 4, y), f'{cap.split(":")[0]} · {d["os"]}', fill=tuple(kp._hex_rgb(VOID)), font=f1)
            dr.text((x + 4, y + 22), f'{d["short"]} · {d["w"]} × {d["h"]} {"pt" if p == "watchos" else "dp"}', fill=tuple(kp._hex_rgb("#566079")), font=f2)
            t = tiles[(p, k)]; im.paste(t, (x + (tw - t.width) // 2, y + lab))
        y += lab + th[p] + gap
    im.save(out("preview.png"), optimize=True)

def build_watch():
    build_code(); build_readme()
    ok = build_screens()
    if not ok: print("WARN watch: no Playwright, watch screens not shot"); return
    build_preview(); build_faces()

if __name__ == "__main__":
    build_watch()
