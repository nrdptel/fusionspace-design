"""FusionSpace product system, phones: product/mobile/ (reference screens, glanceable surfaces, SwiftUI and Compose parts).

product/mobile.md says what the platform owns and what FusionSpace owns; this draws it. Every screen exists twice, once per
platform, with the same content and each platform's own chrome: an iPhone 17 Pro on iOS 26 (Liquid Glass navigation and
tab bar, system lists, SF Pro) and a Pixel 10 on Android 16 (Material 3 app bar and navigation bar, Roboto). The content
layer is the same on both: Cascadia Mono titles, labels and readouts, the signal colors, sheets with 2 px edges, the title
block as the About screen. Screens are HTML pages using product/web/fusionspace.css, shot with Playwright at 2x.

The glanceable surfaces (Live Activity, Dynamic Island, Live Update, widgets) are drawn the same way, on one page.

The SwiftUI and Compose parts are written in source/product/mobile/ (with {{...}} values filled in from kit_product's
constants) and copied to product/mobile/swiftui/ and product/mobile/compose/.
"""
import os, re, math, shutil, html
import build, kit_product as kp, kit_icons, kit_clip
from build import VOID, PAPER, WHITE

M = "mobile"
SRC = os.path.join(kp.SRC, "mobile")
def wr(rel, s): return kp.wr(f"{M}/{rel}", s)
def out(rel): return kp.out(f"{M}/{rel}")

# ================================================================ devices
# Logical sizes (pt / dp) and the system insets the screens are drawn with. Checked October 2026: 402 x 874 pt is the
# iPhone 17 Pro (and 18 Pro, same panel); the Pixel 10 is 1080 x 2424 px at 2.625 (420 dpi), 411 x 923 dp. Neither vendor
# publishes inset values (apps read them from the system), so the insets here are drawn, not measured.
DEVICES = {
    "ios": {"name": "iPhone 17 Pro", "os": "iOS 27", "w": 402, "h": 874, "top": 62, "bottom": 34, "radius": 62, "mask": "iphone-17-pro",
            "island": (125, 37, 11)},                                   # Dynamic Island: width, height, top (pt)
    "android": {"name": "Pixel 10", "os": "Android 17", "w": 411, "h": 923, "top": 52, "bottom": 24, "radius": 48,
                "punch": (24, 16)},                                     # camera hole: diameter, top (dp)
}
SCALE = 2                                                               # screenshot device scale factor

def ico(name, cls=""): return kit_icons.inline(name, cls)

# Status-bar glyphs: drawn plainly, they only place the system's own icons.
def _sb_ios():
    sig = "".join(f'<rect x="{i * 6}" y="{12 - 3 - i * 3}" width="4" height="{3 + i * 3}" rx="1"/>' for i in range(4))
    wifi = ('<path d="M8 11.5 6 9.4a3 3 0 0 1 4 0Z"/><path d="M3.4 6.9a7.6 7.6 0 0 1 9.2 0l-1.3 1.3a5.8 5.8 0 0 0-6.6 0Z"/>'
            '<path d="M.6 4.1a11.6 11.6 0 0 1 14.8 0l-1.3 1.3a9.8 9.8 0 0 0-12.2 0Z"/>')
    bat = ('<rect x=".5" y=".5" width="24" height="12" rx="3.8" fill="none" stroke="currentColor" opacity=".4"/>'
           '<rect x="2" y="2" width="17" height="9" rx="2.4"/><path d="M26 4.5v4a2 2 0 0 0 0-4Z" opacity=".45"/>')
    return (f'<svg width="22" height="12" viewBox="0 0 22 12" fill="currentColor">{sig}</svg>'
            f'<svg width="16" height="12" viewBox="0 0 16 12" fill="currentColor">{wifi}</svg>'
            f'<svg width="28" height="13" viewBox="0 0 28 13" fill="currentColor">{bat}</svg>')
def _sb_android():
    wifi = '<path d="M8 13 0 4a12 12 0 0 1 16 0Z"/>'
    sig = '<path d="M14 1v13H1Z"/>'
    bat = '<rect x="2" y="2" width="7" height="12" rx="1.2" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="3.7" y="5" width="3.6" height="7.3"/><rect x="4" y=".6" width="3" height="1.6"/>'
    return (f'<svg width="16" height="15" viewBox="0 0 16 15" fill="currentColor">{wifi}</svg>'
            f'<svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">{sig}</svg>'
            f'<svg width="11" height="15" viewBox="0 0 11 15" fill="currentColor">{bat}</svg>')

CHEV_BACK = '<svg width="13" height="22" viewBox="0 0 13 22" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11 2 2 11l9 9"/></svg>'
CHEV_RIGHT = '<svg class="chev" width="8" height="14" viewBox="0 0 8 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m1.5 1.5 5.5 5.5-5.5 5.5"/></svg>'
ARROW_BACK = '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20Z"/></svg>'
DOTS_V = '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="12" cy="19" r="2"/></svg>'
ELLIPSIS = '<svg width="22" height="6" viewBox="0 0 22 6" fill="currentColor"><circle cx="3" cy="3" r="2.4"/><circle cx="11" cy="3" r="2.4"/><circle cx="19" cy="3" r="2.4"/></svg>'

TABS = [("pad", "Pad", "launch-rail"), ("track", "Track", "gps-fix"), ("flights", "Flights", "flight-log"), ("devices", "Devices", "flight-computer")]

def chrome(p, theme, body, title="", back="", trailing="", tab=None, extra="", large=True):
    """One phone screen: status bar, the platform's bars around the FusionSpace content layer, home indicator."""
    d = DEVICES[p]
    if p == "ios":
        sb = f'<div class="sb"><span class="time">9:41</span><span class="icons">{_sb_ios()}</span></div><div class="island"></div>'
        nav = ('<div class="nav">'
               + (f'<span class="gbtn glass" aria-label="{back}">{CHEV_BACK}</span>' if back else "<span></span>")
               + f'<span class="navt">{"" if large else html.escape(title)}</span>'
               + (f'<span class="gpill glass">{trailing}</span>' if trailing else "<span></span>") + "</div>")
        bars = ""
        if tab:
            bars = '<nav class="tabbar glass">' + "".join(
                f'<span class="tab"{" aria-current=\"page\"" if k == tab else ""}>{ico(i)}<span>{n}</span></span>' for k, n, i in TABS) + "</nav>"
        bars += '<div class="homebar"></div>'
    else:
        sb = f'<div class="sb"><span class="time">9:41</span><span class="icons">{_sb_android()}</span></div><div class="punch"></div>'
        nav = (f'<div class="appbar">' + (f'<span class="ibtn">{ARROW_BACK}</span>' if back else '<span class="ibtn-gap"></span>')
               + f'<span class="t">{html.escape(title) if not large else ""}</span>{trailing}<span class="ibtn">{DOTS_V}</span></div>')
        bars = ""
        if tab:
            bars = '<nav class="navbar">' + "".join(
                f'<span class="nitem"{" aria-current=\"page\"" if k == tab else ""}><span class="pill">{ico(i)}</span><span>{n}</span></span>' for k, n, i in TABS) + "</nav>"
        bars += '<div class="gesture"></div>'
    style = (f'--w:{d["w"]}px;--h:{d["h"]}px;--top:{d["top"]}px;--bottom:{d["bottom"]}px;'
             f'--tabh:{(62 + 21) if p == "ios" and tab else (64 + d["bottom"]) if tab else d["bottom"]}px')
    return f"""<!doctype html>
<html lang="en" class="{p}" data-theme="{theme}" style="{style}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={d['w']}, initial-scale=1">
<title>{html.escape(title)} · {d['name']} · example</title>
<link rel="stylesheet" href="../../web/fonts.css">
<link rel="stylesheet" href="../../web/fusionspace.css">
<link rel="stylesheet" href="mock.css">
</head>
<body>
<div class="dev">
{sb}
{nav}
<main class="scroll">
{body}
</main>
{extra}
{bars}
</div>
</body>
</html>
"""

# ================================================================ content-layer helpers (the same on both platforms)
status = kp.status
readout = kp.readout
num = kp.num

def sheet(n, total, name, body, aside=""):
    return (f'<section class="m-sheet"><header><h2>{name}</h2><span class="no">{aside}SHEET {n} / {total}</span></header>{body}</section>')
def rows(items):
    """Label / value / state rows: the content layer's own table, in Cascadia Mono."""
    return '<div class="m-rows">' + "".join(
        f'<div class="m-row"><span class="k">{k}</span><span class="v">{v}</span>{s}</div>' for k, v, s in items) + "</div>"
def phases(current, done_all=False):
    names = ["PAD", "BOOST", "COAST", "APOGEE", "DROGUE", "MAIN", "LANDED"]
    i = names.index(current)
    return '<ol class="m-phases" aria-label="Flight phase">' + "".join(
        f'<li data-s="{"done" if j < i else "now" if j == i else "next"}">{n}</li>' for j, n in enumerate(names)) + "</ol>"

def system_list(p, head, items, foot=""):
    """A platform list (UITableView/List inset grouped; Material list items). Each item: (title, secondary, trailing, sup)."""
    li = []
    for t, sec, trail, sup in items:
        if p == "ios":
            li.append(f'<div class="li"><span class="lt">{t}{f"<span class=sup>{sup}</span>" if sup else ""}</span>'
                      f'<span class="sec">{sec}</span>{trail}</div>')
        else:
            li.append(f'<div class="li"><span class="lt">{t}{f"<span class=sup>{sup}</span>" if sup else ""}</span>'
                      f'<span class="sec">{sec}</span>{trail}</div>')
    return (f'<div class="lgroup"><div class="lhead">{head}</div><div class="list">{"".join(li)}</div>'
            + (f'<div class="lfoot">{foot}</div>' if foot else "") + "</div>")

# ================================================================ the four screens
DESIG = "FS-VEGA-004"

def scr_pad(p):
    """At the pad, field theme: checks and channels, then the device's state next to the controls that change it: arming is
    a held second step showing the device's designation, SAFE is one action to its right (product/embedded.md)."""
    tags = f'<div class="m-tags"><span class="fs-tag">{DESIG} rev B</span>{status("ok", 'Link · 0.3 <span class="u">s</span>', "link")}</div>'
    head = f'{tags}<h1 class="m-title">Pad 3 · Flight 04</h1><p class="m-sub">K535W · dual deploy · screen stays on</p>'
    checks = rows([
        ("Switch", "ON", status("ok", "On", "ok")),
        ("Battery", '8.1 <span class="u">V</span>', status("ok", "OK", "battery")),
        ("GPS", '3D · 11 sat', status("ok", "Fix", "gps-fix")),
    ])
    chans = rows([
        ("1 · DROGUE", "Apogee + 0.4 s", status("ok", "Cont", "continuity")),
        ("2 · MAIN", "700 ft desc.", status("ok", "Cont", "continuity")),
        ("3 · —", '<span class="fs-muted">Not used</span>', status("off", "Not used")),
    ])
    body = head + sheet(1, 2, "Checks", checks) + sheet(2, 2, "Channels", chans)
    act = ('<div class="m-arm">'
           '<div class="m-state"><span class="box">SAFE</span><dl>'
           '<div><dt>Commanded</dt><dd>—</dd></div><div><dt>Confirmed</dt><dd>SAFE · 0.3 s ago</dd></div></dl></div>'
           '<div class="hold" role="button" aria-label="Arm FS-VEGA-004: press and hold for 2 seconds">'
           '<span class="fill" style="width:62%"></span>'
           f'<span class="hl">{ico("armed")}Hold to arm</span><span class="hd">{DESIG} · 2 s</span>'
           '<span class="hk">Keep holding · 0.8 s</span><span class="bar"><span style="width:62%"></span></span></div>'
           f'<div class="safe" role="button">{ico("safe")}<span>SAFE</span></div>'
           '<div class="alt">Arm with a confirmation instead</div></div>')
    return chrome(p, "field", body, title="Pad 3", back="Flights", trailing=(ELLIPSIS if p == "ios" else ""), extra=act)

def track_map(theme, w=370, h=200):
    """Offline recovery map (product/data.md#maps): muted base, north up, scale bar, pad square, measured track, rocket
    diamond with its age, the predicted landing as a dashed Nebula ellipse, the phone as the platform's location dot."""
    c = lambda r: kp.role(r, theme)
    o = [f'<svg class="m-map" viewBox="0 0 {w} {h}" width="{w}" height="{h}" overflow="hidden" role="img" aria-label="Recovery map: rocket 1,352 feet from you, bearing 62 degrees true">',
         f'<rect width="{w}" height="{h}" fill="{c("surface")}"/>']
    # muted base: section lines and a dirt road (playa grid), drawn in rule color
    for x in range(-40, w + 60, 64): o.append(f'<line x1="{x}" y1="0" x2="{x + 40}" y2="{h}" stroke="{c("rule")}" stroke-width="1"/>')
    for y in range(18, h, 64): o.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y - 25}" stroke="{c("rule")}" stroke-width="1"/>')
    o.append(f'<path d="M0 {h - 40} C {w * .3} {h - 70}, {w * .6} {h - 20}, {w} {h - 60}" fill="none" stroke="{c("rule")}" stroke-width="5" stroke-linecap="round"/>')
    # positions were laid out on a 236-high map; scale them to this height so nothing lands on the edge
    k = h / 236
    pad = (110, round(176 * k)); you = (64, round(206 * k) - 12); rk = (258, round(92 * k)); pl = (300, round(62 * k))
    o.append(f'<ellipse cx="{pl[0]}" cy="{pl[1]}" rx="48" ry="25" transform="rotate(-24 {pl[0]} {pl[1]})" fill="{c("predicted")}" fill-opacity=".08" stroke="{c("predicted")}" stroke-width="2" stroke-dasharray="8 4"/>')
    o.append(f'<text x="{pl[0] - 36}" y="{pl[1] - 36}" font-family="Cascadia Mono" font-size="11" fill="{c("predicted")}" text-anchor="middle">PREDICTED LANDING</text>')
    tr = [(110, 176), (124, 150), (146, 126), (174, 112), (202, 104), (226, 98), (244, 95), (258, 92)]
    tr = [(x, round(y * k)) for x, y in tr]
    o.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in tr) + f'" fill="none" stroke="{c("ink")}" stroke-width="2" stroke-linejoin="round"/>')
    for x, y in tr[1:-1]: o.append(f'<circle cx="{x}" cy="{y}" r="2" fill="{c("ink")}"/>')
    o.append(f'<line x1="{you[0]}" y1="{you[1]}" x2="{rk[0]}" y2="{rk[1]}" stroke="{c("ink-muted")}" stroke-width="1" stroke-dasharray="24 3 1 3"/>')
    o.append(f'<rect x="{pad[0] - 6}" y="{pad[1] - 6}" width="12" height="12" fill="{c("ink")}"/>')
    o.append(f'<text x="{pad[0] + 12}" y="{pad[1] + 4}" font-family="Cascadia Mono" font-size="11" fill="{c("ink-muted")}">PAD 3</text>')
    o.append(f'<rect x="{rk[0] - 7}" y="{rk[1] - 7}" width="14" height="14" transform="rotate(45 {rk[0]} {rk[1]})" fill="{c("ink")}" stroke="{c("surface")}" stroke-width="2"/>')
    o.append(f'<text x="{rk[0]}" y="{rk[1] + 26}" font-family="Cascadia Mono" font-size="11" fill="{c("ink")}" text-anchor="middle">VEGA · 0.4 s</text>')
    o.append(f'<circle cx="{you[0]}" cy="{you[1]}" r="11" fill="{c("action")}" fill-opacity=".18"/><circle cx="{you[0]}" cy="{you[1]}" r="6" fill="{c("action")}" stroke="{c("surface")}" stroke-width="2"/>')
    # north arrow and scale bar
    o.append(f'<g transform="translate({w - 24},24)"><path d="M0 -12 6 6 0 2 -6 6Z" fill="{c("ink")}"/><text y="20" font-family="Cascadia Mono" font-size="11" fill="{c("ink")}" text-anchor="middle">N</text></g>')
    o.append(f'<g transform="translate(12,{h - 14})" font-family="Cascadia Mono" font-size="11" fill="{c("ink-muted")}"><path d="M0 -6V0H80V-6" fill="none" stroke="{c("ink")}" stroke-width="1.5"/><text x="88" y="0">500 ft</text></g>')
    o.append(f'<text x="{w - 12}" y="{h - 10}" font-family="Cascadia Mono" font-size="11" fill="{c("ink-muted")}" text-anchor="end">TILES 2026-10-03</text>')
    o.append(f'<text x="12" y="20" font-family="Cascadia Mono" font-size="11" fill="{c("ink-muted")}">GPS 11 sat · HDOP 0.9</text>')
    o.append(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" fill="none" stroke="{c("rule-strong")}"/></svg>')
    return "".join(o)

def scr_track(p):
    """Recovery, dark theme: the phase, the readouts that matter now, the map, distance and bearing."""
    head = (f'<div class="m-tags"><span class="fs-tag">FLIGHT 04 · {DESIG}</span>{status("ok", 'Link · 0.4 <span class="u">s</span>', "telemetry")}</div>'
            f'<h1 class="m-title">Track</h1>{phases("MAIN")}')
    now = ('<div class="fs-readouts">' + readout("Altitude", "612", "ft AGL", "Barometer · 0.4 s ago")
           + readout("Descent", "18", "ft/s", "Under the main") + "</div>")
    find = ('<div class="fs-readouts">' + readout("Distance", "1,352", "ft", "From you", size="m")
            + readout("Bearing", "062° T", "", "Declination 13° E", size="m") + "</div>"
            + '<div class="m-coord"><span class="fs-mono">40.86512, −119.06274</span>'
            + f'<span class="m-copy">{ico("copy")}Copy</span></div>')
    body = head + sheet(1, 2, "Now", now) + track_map("dark") + sheet(2, 2, "Find it", find)
    return chrome(p, "dark", body, title="Track", tab="track")

def mini_chart(theme, w=370, h=196):
    """Altitude only, for a phone: measured solid, predicted dashed Nebula with its band, events as numbered balloons."""
    import numpy as np
    pred, meas = kp.example_flight(); ev = meas["events"]
    c = lambda r: kp.role(r, theme)
    left, right, top, bot = 44, 8, 52, 26
    tmax = max(meas["t"][-1], pred["t"][-1]) * 1.02; hi = 6000
    X = lambda t: left + (w - left - right) * t / tmax
    Y = lambda v: top + (h - top - bot) * (1 - v / hi)
    o = [f'<svg class="m-chart" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Altitude against time, measured and predicted">']
    o.append(f'<g font-family="Cascadia Mono" font-size="11" fill="{c("ink-muted")}">')
    for v in range(0, hi + 1, 2000):
        o.append(f'<line x1="{left}" x2="{w - right}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{c("rule")}"/>'
                 f'<text x="{left - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:,}</text>')
    for t in range(0, int(tmax) + 1, 20):
        o.append(f'<text x="{X(t):.1f}" y="{h - 8}" text-anchor="middle">{t}</text>')
    o.append(f'<text x="{w - right}" y="{h - 8 - 14}" text-anchor="end">s</text>')
    o.append(f'<text x="{left}" y="12" fill="{c("ink")}">ALTITUDE · ft AGL</text></g>')
    t = pred["t"]; pa = pred["alt"]; band = 0.04 * pa + 8
    up = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(t[::20], (pa + band)[::20]))
    dn = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(t[::20][::-1], (pa - band)[::20][::-1]))
    o.append(f'<polygon points="{up} {dn}" fill="{c("predicted")}" fill-opacity=".10"/>')
    o.append('<polyline points="' + " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(t[::10], pa[::10])) + f'" fill="none" stroke="{c("predicted")}" stroke-width="2" stroke-dasharray="8 4"/>')
    o.append('<polyline points="' + " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(meas["t"][::10], meas["alt"][::10])) + f'" fill="none" stroke="{c("ink")}" stroke-width="2" stroke-linejoin="round"/>')
    o.append(f'<line x1="{left}" x2="{left}" y1="{top}" y2="{h - bot}" stroke="{c("rule-strong")}"/><line x1="{left}" x2="{w - right}" y1="{h - bot}" y2="{h - bot}" stroke="{c("rule-strong")}"/>')
    placed = []
    for i, k in enumerate(("liftoff", "burnout", "apogee", "drogue", "main", "landing")):
        x = X(ev[k]); bx = x
        while any(abs(bx - q) < 20 for q in placed): bx += 20
        placed.append(bx)
        o.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{h - bot}" stroke="{c("ink-muted")}" stroke-dasharray="1 3"/>')
        if bx != x: o.append(f'<line x1="{x:.1f}" y1="{top}" x2="{bx:.1f}" y2="{top - 6}" stroke="{c("ink-muted")}" stroke-dasharray="1 3"/>')
        o.append(f'<circle cx="{bx:.1f}" cy="{top - 13}" r="8" fill="{c("canvas")}" stroke="{c("ink")}"/>'
                 f'<text x="{bx:.1f}" y="{top - 9.5:.1f}" font-family="Cascadia Mono" font-size="10" fill="{c("ink")}" text-anchor="middle">{i + 1}</text>')
    o.append("</svg>")
    return "".join(o)

def scr_report(p):
    """A flight report, light theme: the same numbers as product/web/examples/flight-report.html, on a phone."""
    pred, meas = kp.example_flight(); ev = meas["events"]
    ap, pap = float(meas["alt"].max()), float(pred["alt"].max())
    spread = 0.04 * pap + 8
    head = (f'<div class="m-tags"><span class="fs-tag">FS-VEGA · REPORT 003</span>{status("ok", "Released", "check")}</div>'
            f'<h1 class="m-title">Flight 03</h1><p class="m-sub">J350W-L · 2026-10-04 · dual deploy</p>'
            f'<p class="m-lead">Apogee {num(pap - ap)} ft ({(1 - ap / pap) * 100:.1f}%) under the prediction.</p>')
    reads = ('<div class="fs-readouts">' + readout("Apogee", num(ap), "ft AGL", "Barometer, 20 Hz", size="m")
             + readout("Predicted", num(pap), "ft AGL", f"±{num(spread)} ft · hpr-sim 0.9", "predicted", size="m")
             + "</div>")
    chart = mini_chart("light") + '<p class="m-note">Solid measured, dashed predicted. 1 liftoff · 3 apogee · 5 main · 6 landing.</p>'
    ch = rows([("1 · DROGUE", f'{ev["drogue"]:.2f} <span class="u">s</span>', status("ok", "Fired", "check")),
               ("2 · MAIN", f'{ev["main"]:.2f} <span class="u">s</span>', status("ok", "Fired", "check"))])
    body = head + sheet(1, 2, "Flight", reads + chart) + sheet(2, 2, "Channels", ch)
    share = f'{ico("upload")}' if p == "ios" else f'<span class="ibtn">{ico("upload")}</span>'
    return chrome(p, "light", body, title="Flight 03", back="Flights", trailing=share, tab="flights")

def scr_device(p):
    """A connected flight computer, light theme: system lists for settings (the platform's), the title block as About."""
    head = (f'<div class="m-tags"><span class="fs-tag">{DESIG} rev B</span>{status("ok", "Connected", "link")}</div>'
            f'<h1 class="m-title">Vega</h1><p class="m-sub">Flight computer · −64 dBm · 0.2 s</p>')
    tr = CHEV_RIGHT if p == "ios" else ""
    chans = system_list(p, "Channels", [("1 · Drogue", "Apogee + 0.4 s", tr, ""), ("2 · Main", "700 ft, descending", tr, ""),
                                        ("3", "Not used", tr, "")],
                        "Changes need SAFE. Nothing here can fire a channel.")
    fw = system_list(p, "Firmware", [("Installed", "1.2.0", "", ""), ("Available", "1.3.0", f'<span class="lbtn">Update…</span>', "")])
    tb = ('<div class="m-tb">'
          f'<div><span class="k">Owner</span><span class="v">{_mark()}FusionSpace</span></div>'
          + "".join(f'<div{" class=wide" if wide else ""}><span class="k">{k}</span><span class="v">{v}</span></div>' for k, v, wide in (
              ("Title", "Vega", False), ("Designation", "FS-VEGA-004", False), ("Rev", "B", False),
              ("Firmware", "1.2.0 (412)", False), ("App", "2.0.1 (88)", False), ("Data", "Motors 2026-09 · tiles 2026-10-03", True))) + "</div>")
    body = head + chans + fw + sheet(1, 1, "About", tb)
    return chrome(p, "light", body, title="Vega", tab="devices")

def _mark():
    return build.inline(open(os.path.join(build.OUT, "logo/mark/fusion-space-mark.svg"), encoding="utf-8").read(), "tbm", "height:18px;width:auto")

SCREENS = [("pad", scr_pad, "Pad · field theme: checks, channels, state, hold to arm"),
           ("track", scr_track, "Track · dark: phase, readouts, offline map, distance and bearing"),
           ("report", scr_report, "Flight report · light: readouts, altitude chart, channels"),
           ("device", scr_device, "Device · light: system lists for settings, the title block as About")]


# ================================================================ glanceable surfaces (product/mobile/glance/)
# Sizes from Apple's HIG (Live Activities, Widgets) and Android's Live Update and widget docs, checked October 2026. Apple
# lists widget sizes per screen class and has no row for the 402 pt iPhone 17 Pro, so widgets use the 393 pt class.
GLANCE = {
    "la_w": 374, "la_h": (84, 160),        # Lock Screen Live Activity: screen width less 14 pt margins; 84-160 pt tall
    "di_w": 371, "di_compact": 230, "di_h": 36.67, "di_min": 45,   # Dynamic Island on 17 / 17 Pro: expanded, compact, minimal
    "small": 158, "medium": (338, 158), "rect": (160, 72), "circ": 72, "inline": (234, 26),
    "chip_dp": 96, "chip_chars": 7,        # Android status-bar chip: 96 dp wide at most, 7 characters of critical text
    "watch": (184, 80.5),                  # Smart Stack Live Activity on a 45 mm watch (46 mm isn't listed)
    "aw": (4 * 73 - 16, 2 * 118 - 16),      # Android widget, 4 x 2 cells in portrait: (73n - 16) x (118m - 16) dp
}

def theme_vars():
    """.t-light / .t-dark / .t-field: the role variables on any element, so one page can show every theme."""
    L = []
    for t in kp.THEMES:
        v = [f"--fs-{n}:{kp.role(n, t)}" for n, *_ in kp.ROLES] + [f"--fs-{n}:{f};--fs-on-{n}:{o}" for n, f, o in kp.FILLS]
        L.append(f".t-{t}{{{';'.join(v)};color:var(--fs-ink)}}")
    # Dynamic Island: always black, dark roles on it (Apple: the island's background is fixed)
    L.append(".t-island{" + ";".join(f"--fs-{n}:{kp.role(n, 'dark')}" for n, *_ in kp.ROLES) + ";--fs-canvas:#000;--fs-surface:#000;color:var(--fs-ink)}")
    return "\n".join(L)

def _phases_row(cur, cls="g-ph"):
    names = ["PAD", "BOOST", "COAST", "APOGEE", "DROGUE", "MAIN", "LANDED"]; i = names.index(cur)
    return f'<ol class="{cls}">' + "".join(f'<li data-s="{"done" if j < i else "now" if j == i else "next"}">{n}</li>' for j, n in enumerate(names)) + "</ol>"

def la_card(state):
    """The Lock Screen Live Activity in its three states. Dark roles on Abyss (activityBackgroundTint), 14 pt margins."""
    if state == "pad":
        inner = ('<div class="la-top"><span class="g-k">PAD 3 · FLIGHT 04</span><span class="g-k">LINK 0.3 <span class="u">s</span></span></div>'
                 '<div class="la-mid"><div><div class="g-big">T−00:04:45</div><div class="g-q">to your pad time, 2:30 PM MDT</div></div>'
                 '<span class="g-box">SAFE</span></div>'
                 f'<div class="la-bot"><span class="g-q">{DESIG} · K535W</span>{status("ok", "Cont 1 · 2", "continuity")}</div>')
    elif state == "flight":
        inner = (f'<div class="la-top"><span class="g-k">FLIGHT 04 · T+00:01:02</span><span class="g-k">LINK 0.4 <span class="u">s</span></span></div>'
                 + _phases_row("MAIN")
                 + '<div class="la-mid"><div><span class="g-k">ALTITUDE</span><div class="g-big">612 <span class="u">ft AGL</span></div></div>'
                 '<div><span class="g-k">DESCENT</span><div class="g-mid">18 <span class="u">ft/s</span></div></div>'
                 '<div><span class="g-k">FROM YOU</span><div class="g-mid">1,352 <span class="u">ft</span></div><div class="g-q">062° T</div></div></div>')
    else:
        inner = ('<div class="la-top"><span class="g-k">FLIGHT 04 · LANDED 0:42 AGO</span><span class="g-k">FIX 4 <span class="u">s</span></span></div>'
                 '<div class="la-mid"><div><span class="g-k">FROM YOU</span><div class="g-big">1,352 <span class="u">ft</span></div></div>'
                 '<div><span class="g-k">BEARING</span><div class="g-big">062° T</div></div></div>'
                 f'<div class="la-bot"><span class="g-q">Apogee 5,104 ft AGL</span>{status("ok", "Both fired", "check")}</div>')
    return f'<div class="la t-dark">{inner}</div>'

def island(kind):
    if kind == "compact-pad":
        return ('<div class="di compact t-island"><span class="di-l g-mono">T−4:45</span><span class="di-cam"></span>'
                '<span class="di-r"><span class="g-boxs">SAFE</span></span></div>')
    if kind == "compact-flight":
        return ('<div class="di compact t-island"><span class="di-l g-mono">MAIN</span><span class="di-cam"></span>'
                '<span class="di-r g-mono">612<span class="u"> ft</span></span></div>')
    if kind == "minimal":
        return '<div class="di minimal t-island"><span class="g-mono">612<span class="u">ft</span></span></div>'
    return ('<div class="di expanded t-island"><div class="di-row"><div><span class="g-k">ALTITUDE</span><div class="g-big">612 <span class="u">ft AGL</span></div></div>'
            '<div class="di-cam2"></div><div style="text-align:right"><span class="g-k">FROM YOU</span><div class="g-mid">1,352 <span class="u">ft</span></div><div class="g-q">062° T</div></div></div>'
            + _phases_row("MAIN") + f'<div class="di-foot"><span class="g-q">{DESIG} · T+00:01:02 · link 0.4 s</span></div></div>')

def widget(size, mode):
    """Window's widget: surface wind with its age, and how close the gusts are to the limit, as words and a shape.
    mode: light / dark (full color), tinted and clear (accented: one tint, so meaning can't be in color)."""
    th = {"light": "t-light", "dark": "t-dark", "tinted": "t-dark acc tinted", "clear": "t-dark acc clear"}[mode]
    caution = (f'<span class="w-caution">{ico("caution")}NEAR LIMIT</span>')
    if size == "small":
        body = ('<span class="g-k">SURFACE WIND</span><div class="w-big">12 <span class="u">mph</span></div>'
                '<div class="g-q">Gusts 19 · from 270°</div>' + caution + '<div class="g-q w-age">2:10 PM · 4 min ago</div>')
    else:
        body = ('<div class="w-cols"><div class="w-main"><span class="g-k">SURFACE WIND</span><div class="w-big">12 <span class="u">mph</span></div>'
                '<div class="g-q">Gusts 19 · from 270°</div>' + caution + '<div class="g-q">2:10 PM · 4 min ago</div></div>'
                '<div class="w-side"><div><span class="g-k">CEILING</span><div class="g-mid">6,500 <span class="u">ft AGL</span></div></div>'
                '<div class="w-stale"><span class="g-k">UPPER WIND</span><div class="g-mid">31 <span class="u">mph</span></div><div class="g-q">at 6,000 ft · 4 h old</div></div></div></div>')
    return f'<div class="wg {size} {th}">{body}</div>'

def accessories():
    return ('<div class="acc-row">'
            '<div class="acc rect"><span class="g-k">WIND · 4 MIN</span><div class="g-mid">12 <span class="u">mph</span> G19</div>'
            f'<div class="g-q">{ico("caution")} near the 20 mph limit</div></div>'
            '<div class="acc circ"><span class="g-k">MPH</span><div class="g-mid">12</div><span class="g-k">G19</span></div>'
            '<div class="acc inline">Wind 12 mph G19 · 4 min</div></div>')

def android_shade():
    """Live Update (Android 16, ProgressStyle) and the Android 17 MetricStyle version, in the system's shade. The system
    draws the card; the app gives text, a progress model and, on Android 17, a semantic color (safe here: normal)."""
    pred, meas = kp.example_flight(); ev = meas["events"]
    land = ev["landing"]; segs = [("Boost", ev["burnout"]), ("Coast", ev["apogee"] - ev["burnout"]), ("Drogue", ev["main"] - ev["apogee"]), ("Main", land - ev["main"])]
    now = 62.0
    bar = '<div class="lu-bar">' + "".join(f'<span class="seg" style="flex:{d:.2f}"></span>' for _, d in segs) + \
          f'<span class="trk" style="left:{now / land * 100:.1f}%">{ico("rocket")}</span>' + \
          "".join(f'<span class="pt" style="left:{t / land * 100:.1f}%"></span>' for t in (ev["apogee"], ev["main"])) + "</div>"
    card16 = (f'<div class="lu"><div class="lu-h">{ico("rocket")}<span>FusionSpace Track · now</span></div>'
              '<div class="lu-t">Flight 04 · under the main</div><div class="lu-x">612 ft AGL · −18 ft/s · 1,352 ft at 062° T</div>'
              f'{bar}<div class="lu-a"><span>Open map</span><span>Stop tracking</span></div></div>')
    card17 = (f'<div class="lu"><div class="lu-h">{ico("rocket")}<span>FusionSpace Track · now</span><span class="lu-sem">SAFE</span></div>'
              '<div class="lu-t">Flight 04 · under the main</div>'
              '<div class="lu-m"><div><span>Altitude</span><b>612 ft</b></div><div><span>From you</span><b>1,352 ft</b></div><div><span>Since liftoff</span><b>1:02</b></div></div>'
              '<div class="lu-a"><span>Open map</span><span>Stop tracking</span></div></div>')
    chip = '<span class="chip">' + ico("rocket") + '612 ft</span>'
    return chip, card16, card17

def watch_la():
    w, h = GLANCE["watch"]
    return (f'<div class="watch t-island" style="width:{w}px;height:{h}px"><div class="la-top"><span class="g-k">FLIGHT 04 · MAIN</span><span class="g-k">0.4 <span class="u">s</span></span></div>'
            '<div class="g-mid">612 <span class="u">ft AGL</span></div><div class="g-q">1,352 ft from you · 062° T</div></div>')

GLANCE_CSS = """
body { margin: 0; background: #fff; }
.fig { display: inline-block; padding: 24px; background: var(--paper); }
.fig > h2 { font: 600 15px/20px 'Cascadia Mono', monospace; margin: 0 0 4px; color: #0B0F1C; }
.fig > p.cap { font: 400 13px/18px 'Cascadia Mono', monospace; color: #566079; margin: 0 0 16px; max-width: 780px; }
.row { display: flex; gap: 20px; align-items: flex-start; flex-wrap: nowrap; }
.col { display: grid; gap: 14px; justify-items: start; }
.lab { font: 400 12px/16px 'Cascadia Mono', monospace; color: #566079; }
.wall { background: #0B0F1C url('../../../kit/wallpapers/phone-1206x2622-dark.png') center 38%% / cover; padding: 14px; border-radius: 28px; }
.u { color: var(--fs-ink-muted); text-transform: none; letter-spacing: 0; }
.g-k { font: 400 11px/14px 'Cascadia Mono', monospace; letter-spacing: .06em; color: var(--fs-ink-muted); text-transform: uppercase; }
.g-q { font: 400 12px/16px 'Archivo', sans-serif; color: var(--fs-ink-muted); }
.g-big { font: 400 30px/34px 'Cascadia Mono', monospace; font-variant-numeric: tabular-nums slashed-zero; }
.g-big .u, .g-mid .u { font-size: 13px; }
.g-mid { font: 400 20px/24px 'Cascadia Mono', monospace; font-variant-numeric: tabular-nums slashed-zero; }
.g-mono { font: 600 15px/18px 'Cascadia Mono', monospace; font-variant-numeric: tabular-nums; }
.g-box { font: 600 20px/1 'Cascadia Mono', monospace; padding: 8px 10px; border: 2px solid var(--fs-ink); }
.g-boxs { font: 600 11px/1 'Cascadia Mono', monospace; padding: 3px 5px; border: 1.5px solid var(--fs-ink); }
.g-ph { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(7, 1fr); border: 1px solid var(--fs-rule-strong); }
.g-ph li { font: 400 8.5px/12px 'Cascadia Mono', monospace; text-align: center; padding: 4px 0; border-right: 1px solid var(--fs-rule); }
.g-ph li:last-child { border-right: 0; }
.g-ph li[data-s="done"] { color: var(--fs-ink); }
.g-ph li[data-s="now"] { background: var(--fs-ink); color: var(--fs-canvas); font-weight: 600; }
.g-ph li[data-s="next"] { color: var(--fs-ink-muted); }
.fs-status { min-height: 22px; font-size: 11px; }

/* Lock Screen Live Activity */
.la { width: %(la_w)spx; box-sizing: border-box; min-height: %(la_min)spx; max-height: %(la_max)spx; padding: 14px; border-radius: 24px;
  background: var(--fs-surface); display: grid; gap: 10px; align-content: start; }
.la-top, .la-bot { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.la-mid { display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; }
.lock-time { font: 600 84px/1 -apple-system, system-ui; color: #fff; text-align: center; letter-spacing: -1px; margin: 18px 0 6px; }
.lock-date { font: 600 19px/24px -apple-system, system-ui; color: rgba(255,255,255,.85); text-align: center; }

/* Dynamic Island: fixed black, dark roles */
.strip { width: 402px; padding: 11px 0 14px; background: #D6DAE4; border-radius: 0 0 24px 24px; display: grid; justify-items: center; }
.di { background: #000; color: var(--fs-ink); }
.di.compact { width: %(di_c)spx; height: %(di_h)spx; border-radius: 19px; display: flex; align-items: center; justify-content: space-between; padding: 0 12px; box-sizing: border-box; }
.di-cam { width: 10px; height: 10px; border-radius: 50%%; background: #15161c; margin-left: 66px; }
.di.minimal { width: %(di_m)spx; height: %(di_h)spx; border-radius: 19px; display: grid; place-items: center; }
.di.minimal .g-mono { font-size: 12px; line-height: 12px; display: grid; justify-items: center; }
.di.minimal .u { font-size: 9px; line-height: 10px; font-weight: 400; }
.di.expanded { width: %(di_w)spx; box-sizing: border-box; padding: 16px 18px 14px; border-radius: 44px; display: grid; gap: 10px; }
.di-row { display: flex; justify-content: space-between; align-items: flex-start; }
.di-cam2 { width: 120px; }
.di .fs-status { background: transparent; }

/* widgets */
.wg { box-sizing: border-box; padding: 16px; border-radius: 22px; background: var(--fs-surface); display: grid; align-content: start; gap: 4px; position: relative; overflow: hidden; }
.wg.small { width: %(small)spx; height: %(small)spx; }
.wg.medium { width: %(med_w)spx; height: %(med_h)spx; }
.w-big { font: 400 34px/38px 'Cascadia Mono', monospace; }
.w-big .u { font-size: 14px; }
.w-caution { display: inline-flex; width: fit-content; align-items: center; gap: 4px; margin-top: 4px; padding: 2px 6px;
  font: 600 11px/14px 'Cascadia Mono', monospace; background: var(--fs-caution-fill); color: var(--fs-on-caution-fill); }
.w-caution svg { width: 13px; height: 13px; }
.w-age { position: absolute; left: 16px; bottom: 12px; font-size: 11px; }
.w-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.w-main { display: grid; gap: 4px; align-content: start; }
.aw.medium { width: %(aw_w)spx; height: %(aw_h)spx; padding: 14px; }
.aw .w-cols { gap: 8px; }
.aw .w-big { font-size: 30px; line-height: 34px; }
.aw .g-mid { font-size: 18px; }
.aw-foot { position: absolute; left: 14px; right: 8px; bottom: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; border-top: 1px solid var(--fs-rule); padding-top: 4px; }
.aw-btn { width: 48px; height: 48px; display: grid; place-items: center; color: var(--fs-action); }
.aw-btn svg { width: 22px; height: 22px; }
.w-side { display: grid; gap: 8px; }
.w-stale { padding-left: 8px; border-left: 6px solid transparent; border-image: repeating-linear-gradient(-45deg, var(--fs-ink-faint) 0 1px, transparent 1px 5px) 6; }
.w-stale .g-mid { color: var(--fs-ink-muted); }
/* accented (tinted, clear): the system removes the background and draws everything in one tint; meaning stays in words and shapes */
.wg.acc { --fs-ink: #fff; --fs-ink-muted: rgba(255,255,255,.72); --fs-ink-faint: rgba(255,255,255,.45); --fs-rule-strong: rgba(255,255,255,.6); }
.wg.acc .w-caution { background: transparent; color: #fff; border: 1.5px solid #fff; }
.wg.tinted { background: rgba(70, 92, 170, .55); -webkit-backdrop-filter: blur(20px) saturate(1.4); backdrop-filter: blur(20px) saturate(1.4); }
.wg.clear { background: rgba(255,255,255,.10); -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px); border: 1px solid rgba(255,255,255,.35); }
/* Lock Screen accessories: vibrant (desaturated, the system picks the shade) */
.acc-row { display: flex; gap: 14px; align-items: center; color: #fff; }
.acc { --fs-ink: #fff; --fs-ink-muted: rgba(255,255,255,.75); color: #fff; box-sizing: border-box; }
.acc.rect { width: %(rect_w)spx; height: %(rect_h)spx; padding: 6px 8px; border-radius: 14px; background: rgba(255,255,255,.14); display: grid; align-content: center; }
.acc.rect svg { width: 11px; height: 11px; vertical-align: -1px; }
.acc.circ { width: %(circ)spx; height: %(circ)spx; border-radius: 50%%; background: rgba(255,255,255,.14); display: grid; place-content: center; justify-items: center; }
.acc.inline { font: 600 15px/20px -apple-system, system-ui; }

/* Android: the system shade and its notification cards (system colors; the app supplies content) */
.shade { width: 411px; box-sizing: border-box; padding: 0 0 16px; background: #1b1c22; border-radius: 0 0 28px 28px; display: grid; gap: 10px; color: #e6e6ee; }
.shade .sbar { height: 52px; display: flex; align-items: center; justify-content: space-between; padding: 0 22px; font: 500 15px Roboto, sans-serif; }
.chip { display: inline-flex; align-items: center; gap: 4px; height: 28px; max-width: %(chip)spx; padding: 0 10px; border-radius: 14px;
  background: #0A6355; color: #fff; font: 500 14px Roboto, sans-serif; white-space: nowrap; overflow: hidden; }
.chip svg { width: 16px; height: 16px; }
.lu { margin: 0 12px; padding: 14px 16px; border-radius: 24px; background: #2a2b33; display: grid; gap: 4px; font-family: Roboto, sans-serif; }
.lu svg { width: 16px; height: 16px; }
.lu-h { display: flex; align-items: center; gap: 8px; font: 400 12px/16px Roboto, sans-serif; color: #b9bac6; }
.lu-sem { margin-left: auto; font: 600 11px/14px 'Cascadia Mono', monospace; padding: 2px 6px; background: #0A6355; color: #fff; }
.lu-t { font: 500 16px/22px Roboto, sans-serif; color: #f2f2f8; }
.lu-x { font: 400 14px/20px Roboto, sans-serif; color: #c9cad4; }
.lu-bar { position: relative; display: flex; gap: 4px; height: 8px; margin: 14px 0 10px; }
.lu-bar .seg { height: 8px; border-radius: 4px; background: #c9cad4; }
.lu-bar .pt { position: absolute; top: -2px; width: 12px; height: 12px; margin-left: -6px; border-radius: 50%%; background: #1b1c22; border: 2px solid #c9cad4; box-sizing: border-box; }
.lu-bar .trk { position: absolute; top: -10px; margin-left: -14px; width: 28px; height: 28px; border-radius: 50%%; background: #f2f2f8; color: #1b1c22; display: grid; place-items: center; z-index: 2; }
.lu-m { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 8px 0 4px; }
.lu-m span { display: block; font: 400 12px/16px Roboto, sans-serif; color: #b9bac6; }
.lu-m b { font: 500 20px/26px Roboto, sans-serif; color: #f2f2f8; }
.lu-a { display: flex; gap: 20px; margin-top: 8px; font: 500 14px/20px Roboto, sans-serif; color: #c4cbff; }
/* Android widget (Glance): the launcher's corner radius, the static FusionSpace scheme inside */
.aw { box-sizing: border-box; padding: 16px; border-radius: 24px; background: var(--fs-surface); position: relative; display: grid; gap: 4px; align-content: start; }
/* watch Smart Stack */
.watch { box-sizing: border-box; padding: 8px 10px; border-radius: 16px; background: #1c1d22; display: grid; gap: 4px; }
.watch .g-mid { font-size: 18px; }
"""

AW_FOOT = ('<div class="aw-foot"><span class="g-q">Example field · no verdict: your RSO decides</span>'
           '<span class="aw-btn" role="button" aria-label="Refresh">' + kit_icons.inline("refresh", "") + '</span></div>')

def glance_page():
    g = GLANCE
    css = GLANCE_CSS % {"la_w": g["la_w"], "la_min": g["la_h"][0], "la_max": g["la_h"][1], "di_c": g["di_compact"], "di_h": g["di_h"],
                        "di_m": g["di_min"], "di_w": g["di_w"], "small": g["small"], "med_w": g["medium"][0], "med_h": g["medium"][1],
                        "rect_w": g["rect"][0], "rect_h": g["rect"][1], "circ": g["circ"], "chip": g["chip_dp"], "aw_w": g["aw"][0], "aw_h": g["aw"][1]}
    chip, c16, c17 = android_shade()
    figs = []
    figs.append(('ios-live-activity', 'iOS · Live Activity on the Lock Screen',
                 f'Three states of one activity: at the pad, in flight, landed. {g["la_w"]} pt wide (14 pt margins), 84 to 160 pt tall; dark roles on Abyss; up to 8 h, then 4 h on the Lock Screen. Each value says how old it is.',
                 '<div class="row"><div class="wall" style="width:402px;box-sizing:border-box"><div class="lock-date">Saturday, October 10</div><div class="lock-time">9:41</div>'
                 + la_card("flight") + '</div><div class="col"><span class="lab">At the pad · counting to your pad time</span>' + la_card("pad")
                 + '<span class="lab">In flight · phase, then the numbers that matter now</span>' + la_card("flight")
                 + '<span class="lab">Landed · where it is, and whether every charge fired</span>' + la_card("landed") + '</div></div>'))
    figs.append(('ios-dynamic-island', 'iOS · Dynamic Island',
                 f'Always black, so always the dark roles. Compact {g["di_compact"]} pt across on iPhone 17 Pro: the state on the left, one number on the right. Minimal shows live data, not a logo. Expanded {g["di_w"]} pt.',
                 '<div class="row"><div class="col"><span class="lab">Compact · at the pad</span><div class="strip">' + island("compact-pad") + '</div>'
                 '<span class="lab">Compact · in flight</span><div class="strip">' + island("compact-flight") + '</div>'
                 '<span class="lab">Minimal · another activity is running too</span><div class="strip" style="justify-items:end;padding-right:24px;box-sizing:border-box">' + island("minimal") + '</div></div>'
                 '<div class="col"><span class="lab">Expanded · touch and hold</span><div class="strip" style="padding-bottom:20px">' + island("expanded") + '</div>'
                 f'<span class="lab">Apple Watch · Smart Stack (shown automatically; {g["watch"][0]} × {g["watch"][1]} pt at 45 mm)</span>' + watch_la() + '</div></div>'))
    figs.append(('ios-widgets', 'iOS · Widgets in every appearance',
                 'Window\'s widget: one readout, its age, and how close it is to a limit. In tinted and clear the system draws everything in one tint, so the caution is a word and a triangle, never just amber. Sizes are Apple\'s 393 pt class (Apple lists none for 402 pt).',
                 '<div class="col">' + "".join(f'<span class="lab">{n}</span><div class="row{" wall" if m in ("tinted", "clear") else ""}" style="{"padding:14px;border-radius:24px" if m in ("tinted", "clear") else ""}">{widget("small", m)}{widget("medium", m)}</div>'
                    for m, n in (("light", "Light · full color"), ("dark", "Dark · full color"), ("tinted", "Tinted · accented rendering"), ("clear", "Clear · accented, on Liquid Glass")))
                 + '<span class="lab">Lock Screen · vibrant: rectangular, circular, inline</span><div class="wall" style="padding:16px 18px;border-radius:24px">' + accessories() + '</div></div>'))
    figs.append(('android-live-update', 'Android · Live Update',
                 f'A promoted ongoing notification: the status-bar chip ({g["chip_chars"]} characters at most, {g["chip_dp"]} dp wide), then the card. Android 16: ProgressStyle, with the flight\'s phases as segments, apogee and main as points, the rocket as the tracker. Android 17: MetricStyle with up to three values, and a semantic color that matches the signal colors.',
                 f'<div class="row"><div class="col"><span class="lab">Android 16 · ProgressStyle</span><div class="shade"><div class="sbar"><span>9:41 {chip}</span><span></span></div>{c16}</div></div>'
                 f'<div class="col"><span class="lab">Android 17 · MetricStyle, semantic color safe</span><div class="shade"><div class="sbar"><span>9:41 {chip}</span><span></span></div>{c17}</div></div></div>'))
    figs.append(('android-widget', 'Android · Widget (Glance)',
                 f'The launcher draws the container and its radius; inside, the static FusionSpace scheme, never wallpaper color, because the caution means something. 4 × 2 cells, {g["aw"][0]} × {g["aw"][1]} dp in portrait.',
                 '<div class="row">' + "".join(f'<div class="col"><span class="lab">{n}</span>{widget("medium", m).replace("class=\"wg medium", "class=\"wg medium aw").replace("</div></div></div></div>", "</div></div></div></div>" + AW_FOOT, 1)}</div>' for m, n in (("light", "Light"), ("dark", "Dark"))) + '</div>'))
    body = "\n".join(f'<section class="fig" id="{i}"><h2>{t}</h2><p class="cap">{c}</p>{h}</section><br>' for i, t, c, h in figs)
    page_ = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Glanceable surfaces · FusionSpace mobile · example</title>
<link rel="stylesheet" href="../../web/fonts.css">
<link rel="stylesheet" href="../../web/fusionspace.css">
<style>
@font-face {{ font-family: 'Roboto'; font-weight: 100 900; font-stretch: 75% 100%; src: url('../fonts/Roboto.woff2') format('woff2'); }}
:root {{ --paper: {PAPER}; }}
{theme_vars()}
{css}
</style>
</head>
<body>
{body}
</body>
</html>
"""
    return page_, [f[0] for f in figs]

def build_glance():
    pg, ids = glance_page()
    wr("glance/index.html", pg)
    frames = [{"selector": ".la"}, {"selector": ".di"}, {"selector": ".wg"}, {"selector": ".acc.rect"},
              {"selector": ".acc.circ", "circle": True}, {"selector": ".lu"}, {"selector": ".watch"}, {"selector": ".chip"}]
    return shots([("glance/index.html", f"glance/{i}.png", 1400, 1000, f"#{i}", {"frames": frames}) for i in ids])


# ================================================================ code (product/mobile/swiftui/, product/mobile/compose/)
HOLD_S = 2                                  # arming from an app: a press held this long (product/embedded.md)
STALE_S = {"flight": 2, "weather": 30 * 60}  # past this a value shows as stale (product/data.md#live-telemetry)
def code_values():
    readout = next(size for name, size, *_ in kp.TYPE if name == "readout")
    return {"READOUT": readout, "HOLD_S": HOLD_S, "HOLD_MS": HOLD_S * 1000, "STALE_FLIGHT_S": STALE_S["flight"],
            "STALE_WEATHER_S": STALE_S["weather"], "STALE_FLIGHT_MS": STALE_S["flight"] * 1000,
            "STALE_WEATHER_MS": STALE_S["weather"] * 1000, "FIELD": kp.TARGET["field"], "CHIP_CHARS": GLANCE["chip_chars"]}
CODE = [("swiftui/FSComponents.swift", "SwiftUI parts: FSStatus, FSReadout, FSSheetHeader, FSTitleBlock, FSStateBox, FSCommandedConfirmed, FSHoldToConfirm, FSFreshness, fsKeepsScreenOn()"),
        ("swiftui/FSWindWidget.swift", "WidgetKit: Window's surface-wind widget, in full color, tinted, clear and vibrant"),
        ("swiftui/FSFlightActivity.swift", "ActivityKit: a flight's Live Activity, Lock Screen and Dynamic Island"),
        ("compose/FsComponents.kt", "Compose parts: FusionSpaceTheme, FsStatus, FsReadout, FsSheetHeader, FsTitleBlock, FsStateBox, FsCommandedConfirmed, FsHoldToConfirm, FsFreshness"),
        ("compose/FsLiveUpdate.kt", "A flight's Live Update: ProgressStyle on Android 16, MetricStyle with semantic colors on Android 17")]
def build_code():
    vals = code_values()
    for rel, _ in CODE:
        t = open(os.path.join(SRC, rel), encoding="utf-8").read()
        t = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: str(vals[m.group(1)]), t)
        assert "{{" not in t, rel
        wr(rel, t)

README = """# Phones

Reference parts for FusionSpace iOS and Android apps. The rules are in `product/mobile.md`; this folder draws them and puts
the content layer into code. Generated by `tools/build/kit_mobile.py` from `source/product/mobile/`.

![Four screens on iOS and Android](preview.png)

## Screens

Each screen exists on both platforms with the same content and each platform's own chrome: the {ios[name]} ({ios[w]} × {ios[h]} pt) on
{ios[os]} with Liquid Glass bars and system lists, and the {android[name]} ({android[w]} × {android[h]} dp) on {android[os]} with Material 3
bars and Roboto. Open the HTML in a browser, or look at the PNG (2x).

| Screen | Theme | What it shows |
|---|---|---|
{screens}

`devices/` has the same screens running for real (simulator and emulator captures).

`screens/mock.css` draws the platform chrome for the mock-ups only; apps use the system's bars. The status-bar and Dynamic
Island glyphs are drawn stand-ins, not Apple's or Google's artwork.

## Glanceable surfaces

`glance/index.html`, shot as one PNG per surface:

| File | What |
|---|---|
| `glance/ios-live-activity.png` | Lock Screen Live Activity: at the pad, in flight, landed |
| `glance/ios-dynamic-island.png` | Dynamic Island compact, minimal and expanded, and the Apple Watch Smart Stack |
| `glance/ios-widgets.png` | Window's widget in light, dark, tinted and clear, and the Lock Screen accessories |
| `glance/android-live-update.png` | Live Update: the status-bar chip, ProgressStyle (Android 16) and MetricStyle (Android 17) |
| `glance/android-widget.png` | The Glance widget, 4 × 2 cells, light and dark |

## Code (Apache-2.0)

Copy these into an app with `product/tokens/FusionSpaceColors.swift` or `FusionSpaceColors.kt`.

| File | What |
|---|---|
{code}

**Proven on real screens** (October 6, 2026): every file here runs in the sample apps (`source/product/samples/apple`,
`source/product/samples/android`) on the iOS 27 simulator (iPhone 17 Pro) and the Android 17 emulator (Pixel 10); their
captures are in `devices/`, next to the drawn screens they prove. Running them found what compiling didn't: the hold
control filling the screen (both platforms), `fsKeepsScreenOn()` breaking widget extensions, status chips upper-casing
units, Material's default purple in Compose dialogs, the Dynamic Island cutting the SAFE box. The drawn screens are
checked by `tools/build/kit_clip.py`: nothing may be cut by the screen's real outline or sit under a bar.

`fonts/Roboto.woff2` is a Latin subset of Roboto (SIL OFL, `fonts/OFL-Roboto.txt`) so the Android mock-ups show Android's
type; apps get Roboto from the system.
"""
def build_readme():
    d = DEVICES
    screens = "\n".join(f"| `screens/{{ios,android}}-{k}` | {cap.split(' · ')[1].split(':')[0]} | {cap.split(': ', 1)[1]} |" for k, _, cap in SCREENS)
    code = "\n".join(f"| `{rel}` | {what} |" for rel, what in CODE)
    wr("README.md", README.format(ios=d["ios"], android=d["android"], screens=screens, code=code))

# ================================================================ build
def build_fonts():
    """product/mobile/fonts/Roboto.woff2: a Latin subset of Roboto (variable, SIL OFL), so the Android mock-ups show
    Android's own type. Only the mock-ups use it; apps get Roboto from the system."""
    from fontTools import subset
    os.makedirs(out("fonts"), exist_ok=True)
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]; opts.name_IDs = ["*"]; opts.notdef_outline = True
    f_ = subset.load_font(os.path.join(SRC, "fonts", "Roboto[wdth,wght].ttf"), opts); s_ = subset.Subsetter(opts)
    s_.populate(unicodes=subset.parse_unicodes(kp.SUBSET)); s_.subset(f_)
    if "head" in f_: f_["head"].modified = f_["head"].created
    subset.save_font(f_, out("fonts/Roboto.woff2"), opts)
    shutil.copy(os.path.join(SRC, "fonts", "OFL-Roboto.txt"), out("fonts/OFL-Roboto.txt"))

def shots(jobs):
    """jobs: (html rel path, png rel path, width, height, selector or None). Playwright, at SCALE. False if missing."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    with sync_playwright() as p_:
        b = p_.chromium.launch()
        problems = []
        for job in jobs:
            rel, dest, w, h, sel = job[:5]; clip = job[5] if len(job) > 5 else None
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=SCALE)
            pg.goto("file://" + out(rel)); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
            os.makedirs(os.path.dirname(out(dest)), exist_ok=True)
            if sel: pg.locator(sel).screenshot(path=out(dest), animations="disabled")
            else: pg.screenshot(path=out(dest), clip={"x": 0, "y": 0, "width": w, "height": h}, animations="disabled")
            if clip: problems += [f"{dest}: {x}" for x in kit_clip.check(pg, **clip)]
            pg.close()
        b.close()
    kit_clip.assert_clean(problems, os.path.dirname(jobs[0][1]) if jobs else "")
    return True

def build_screens():
    css = open(os.path.join(SRC, "mock.css"), encoding="utf-8").read()
    wr("screens/mock.css", "/* Generated by tools/build/kit_mobile.py from source/product/mobile/mock.css; edit there. */\n" + css)
    jobs = []
    for key, fn, _ in SCREENS:
        for p in ("ios", "android"):
            wr(f"screens/{p}-{key}.html", fn(p))
            d = DEVICES[p]
            clip = {"frames": [{"selector": ".dev", "radius": d["radius"], "mask": d.get("mask")}],
                    "content": {"selector": ".scroll", "above": [".sb", ".nav", ".appbar"],
                                "below": [".tabbar", ".navbar", ".m-arm", ".homebar", ".gesture"]},
                    "overlays": [".tabbar", ".navbar", ".m-arm", ".nav .gbtn", ".nav .gpill", ".appbar"]}
            jobs.append((f"screens/{p}-{key}.html", f"screens/{p}-{key}.png", d["w"], d["h"], None, clip))
    return shots(jobs)

def _font(size, semibold=False):
    from PIL import ImageFont
    try: return ImageFont.truetype(os.path.join(build.ROOT, "type", "fonts", "CascadiaMono-SemiBold.ttf" if semibold else "CascadiaMono-Regular.ttf"), size)
    except OSError: return ImageFont.load_default()

def screen_tile(png, w, h, mask=None, radius=0, circle=False, pad=8, gap=4, line=2):
    """A screen cut to its real outline (the simulator's mask, a circle, or a rounded rectangle), with a 2 px drawn case
    line `gap` px outside it: a line drawing of the device, not a photo of one."""
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    im = Image.open(png).convert("RGB").resize((w, h), Image.LANCZOS)
    big = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    if mask:
        m = Image.open(os.path.join(kit_clip.MASKS, mask + ".png")).convert("L").resize((w, h), Image.LANCZOS)
    else:
        m = Image.new("L", (w, h), 0); dr = ImageDraw.Draw(m)
        if circle: dr.ellipse((0, 0, w - 1, h - 1), fill=255)
        else: dr.rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=255)
    big.paste(m, (pad, pad))
    grow = lambda img, n: img.filter(ImageFilter.MaxFilter(2 * n + 1)) if n else img
    ring = ImageChops.subtract(grow(big, gap + line), grow(big, gap))
    tile = Image.new("RGB", big.size, tuple(kp._hex_rgb(PAPER)))
    tile.paste(Image.new("RGB", big.size, tuple(kp._hex_rgb(VOID))), (0, 0), ring)
    tile.paste(im, (pad, pad), m)
    return tile

def phone_tile(png, p, scale=1.0):
    d = DEVICES[p]
    return screen_tile(png, round(d["w"] * scale), round(d["h"] * scale), d.get("mask"), round(d["radius"] * scale))

def build_preview():
    """product/mobile/preview.png: the four screens on both platforms, iOS above Android."""
    from PIL import Image, ImageDraw
    sc = 0.75; gap = 36; lab = 52; margin = 40
    tiles = {(p, k): phone_tile(out(f"screens/{p}-{k}.png"), p, sc) for k, *_ in SCREENS for p in ("ios", "android")}
    tw = max(t.width for t in tiles.values()); th = {p: max(t.height for (pp, _), t in tiles.items() if pp == p) for p in ("ios", "android")}
    W = margin * 2 + len(SCREENS) * tw + (len(SCREENS) - 1) * gap
    H = margin * 2 + (lab + th["ios"]) + gap + (lab + th["android"])
    im = Image.new("RGB", (W, H), tuple(kp._hex_rgb(PAPER))); dr = ImageDraw.Draw(im)
    f1, f2 = _font(18, True), _font(14)
    y = margin
    for p in ("ios", "android"):
        d = DEVICES[p]
        for i, (k, _, cap) in enumerate(SCREENS):
            x = margin + i * (tw + gap)
            dr.text((x + 6, y), f'{cap.split(" · ")[0]} · {d["os"]}', fill=tuple(kp._hex_rgb(VOID)), font=f1)
            dr.text((x + 6, y + 24), f'{d["name"]} · {d["w"]} × {d["h"]} {"pt" if p == "ios" else "dp"} · {cap.split(" · ")[1].split(":")[0]}', fill=tuple(kp._hex_rgb("#566079")), font=f2)
            im.paste(tiles[(p, k)], (x, y + lab))
        y += lab + th[p] + gap
    im.save(out("preview.png"), optimize=True)

def build_mobile():
    build_fonts(); build_code(); build_readme()
    ok = build_screens()
    if not ok: print("WARN mobile: no Playwright, phone screens not shot"); return
    build_preview(); build_glance()

if __name__ == "__main__":
    build_mobile()
