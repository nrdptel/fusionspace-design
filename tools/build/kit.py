"""FusionSpace Rev C asset kit: every target × color mode × background × size, generated from the master geometry.

    python3 tools/build/build.py      # build_all() calls kit.build_kit() at the end

Writes into <OUT>/kit (and the color-mode matrix of the logos into <OUT>/kit/logo). Every file is listed in
MANIFEST, which also becomes kit/README.md and the guide's Kit sheet. Office files (slides .pptx, letterhead
.docx) come from kit_office.js and need node with the `pptxgenjs` and `docx` packages; without them they are
skipped with a warning. CMYK PDFs need Ghostscript (`gs`); without it they are skipped with a warning."""
import os, re, json, math, shutil, subprocess, textwrap, datetime
import geo, build
from build import f, VOID, PAPER, WHITE, STOPS, MODES, ION, EMBER, M_ORANGE, O_BLUE, WARM, COOL

ABYSS, GRAPHITE, SLATE, HAZE, MIST = "#141A2B", "#2A3248", "#566079", "#98A1B8", "#D6DAE4"
KIT = "kit"
# Logo color mode used on light composites (banners, avatars, covers, cards, letterhead, slides). Since October 2, 2026
# the gradient is the same on dark and light (>= 3:1 on white); "twotone-on-light" (flat cones, Void wordmark) is the alternative.
LIGHT_MODE = os.environ.get("FS_LIGHT_MODE", "color")
MANIFEST = []            # (path, group, what, size, use)
WARN = []
TAGLINE = "Tolerances tight. Ambitions loose."          # brand line on banners, covers, slides (one place to change it)
INTRO = "Everything I make, under one name."     # opening line of the guide and README
SCOPE = "software and embedded systems, games, electronics, mechanical and machined parts, and aerospace"
ROLE = "Founder · Engineer"
EMAIL = "NeerDPatel@FusionSpace.co"                   # contact details on cards, letterhead, signature, slides
SITE = "FusionSpace.co"
SITE_URL = "https://fusionspace.co"
SIGNATURE_LOGO_BASE = "https://fusionspace.co/brand"   # where the site hosts the email-signature logo
GITHUB = "github.com/nrdptel"
GITHUB_URL = "https://github.com/nrdptel"                  # title on business cards, signature and letterhead
# Optional discipline tags for designations: FS-VEGA · EMB
DISCIPLINES = [("SW", "Software"), ("EMB", "Embedded and flight software"), ("ELEC", "Electronics and PCBs"),
               ("MECH", "Mechanical design"), ("MFG", "Machining and fabrication"), ("AERO", "Aerospace"), ("GAME", "Games")]

def out(p): return os.path.join(build.OUT, p)
def note(path, group, what, size, use): MANIFEST.append((path, group, what, size, use))

# ---------------------------------------------------------------- low-level writers
def svg_open(w, h, title, units="", desc="", page=VOID):
    return build.header(w, h, title, desc, page, units)

def gradient(gid, x1, x2):
    st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in STOPS)
    return f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{f(x1)}" y1="0" x2="{f(x2)}" y2="0">{st}</linearGradient>'

def save_svg(path, s):
    build.wr(path, s)
    return out(path)

def png(svg_path, png_path, w=None, h=None, bg=None):
    args = ["rsvg-convert", svg_path, "-o", out(png_path)]
    if w: args[1:1] = ["-w", str(w)]
    if h: args[1:1] = ["-h", str(h)]
    if bg: args[1:1] = ["-b", bg]
    os.makedirs(os.path.dirname(out(png_path)), exist_ok=True)
    subprocess.run(args, check=True)
    return out(png_path)

def pdf(svg_path, pdf_path):
    os.makedirs(os.path.dirname(out(pdf_path)), exist_ok=True)
    subprocess.run(["rsvg-convert", "-f", "pdf", svg_path, "-o", out(pdf_path)], check=True)
    return out(pdf_path)

def cmyk(pdf_rel, cmyk_rel):
    if not shutil.which("gs"):
        if "gs" not in WARN: WARN.append("gs"); print("WARN kit: Ghostscript (gs) not found, CMYK PDFs skipped")
        return None
    subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pdfwrite", "-sColorConversionStrategy=CMYK",
                    "-sProcessColorModel=DeviceCMYK", "-dAutoRotatePages=/None", "-dOmitInfoDate", "-dOmitID", "-dOmitXMP", f"-sOutputFile={out(cmyk_rel)}", out(pdf_rel)], check=True)
    return out(cmyk_rel)

# ---------------------------------------------------------------- art pieces (mark, lockups, wordmark, cone)
_WM = {}
def wordmark_path():
    """The outlined wordmark, top-left at (0, 0), in stacked-file units (width WM_W)."""
    if "d" not in _WM:
        d, _ = build.get_wordmark("logo/lockup/fusion-space-stacked-color.svg")
        b = build.path_bbox(d)
        _WM["d"] = build.translate_d(d, -b[0], -b[1]); _WM["w"] = b[2] - b[0]; _WM["h"] = b[3] - b[1]
        _WM["cap_top"] = 228.0 - b[1]; _WM["base"] = 287.0 - b[1]
    return _WM

class Art:
    """A logo piece in its own units: w × h, with a list of (d, role, cone) and the bboxes for gradients."""
    def __init__(self, w, h, parts, mark_bb=None, wm_bb=None):
        self.w, self.h, self.parts, self.mark_bb, self.wm_bb = w, h, parts, mark_bb, wm_bb
    def render(self, mode, prefix):
        """(defs, body) with ids prefixed. Fills follow build.MODES."""
        mf, wf, g = build.mode_fills(mode, f"url(#{prefix}-mg)", f"url(#{prefix}-wg)")
        defs = ""
        if g:
            if self.mark_bb: defs += gradient(f"{prefix}-mg", self.mark_bb[0], self.mark_bb[2])
            if self.wm_bb: defs += gradient(f"{prefix}-wg", self.wm_bb[0], self.wm_bb[2])
        body = []
        for d, role, cone in self.parts:
            fl = (mf[cone] if isinstance(mf, dict) else mf) if role == "mark" else wf
            body.append(f'<path fill="{fl}" d="{d}"/>')
        return defs, "".join(body)
    def place(self, mode, prefix, x, y, scale):
        defs, body = self.render(mode, prefix)
        return defs, f'<g transform="translate({f(x)} {f(y)}) scale({scale:.6f})">{body}</g>'

def art_mark(h=200.0):
    cl, A, bb = geo.fit_cluster(height=h)
    return Art(bb[2], h, [(geo.seg_to_d(cl[n]), "mark", n) for n in geo.DRAW_ORDER], mark_bb=bb)

def art_stacked():
    cl, bb, d, _, H = build.stacked_geometry()
    return Art(build.WM_W, H, [(geo.seg_to_d(cl[n]), "mark", n) for n in geo.DRAW_ORDER] + [(d, "wm", None)],
               mark_bb=bb, wm_bb=build.path_bbox(d))

def art_horizontal():
    cl, bb, d, _, W, H, m = build.horizontal_geometry()
    return Art(W, H, [(geo.seg_to_d(cl[n]), "mark", n) for n in geo.DRAW_ORDER] + [(d, "wm", None)],
               mark_bb=bb, wm_bb=build.path_bbox(d))

def art_wordmark():
    w = wordmark_path()
    return Art(w["w"], w["h"], [(w["d"], "wm", None)], wm_bb=(0, 0, w["w"], w["h"]))

PIECES = {"mark": art_mark, "horizontal": art_horizontal, "stacked": art_stacked, "wordmark": art_wordmark}
LOGO_MODES = list(MODES)                               # color, twotone-on-dark, twotone-on-light, void, white
MODE_BG = {"color": VOID, "twotone-on-dark": VOID, "twotone-on-light": PAPER, "void": PAPER, "white": VOID}
MODE_USE = {
    "color": "Full color (Fusion gradient). Screen, color print. The same gradient on Void, white and Paper",
    "twotone-on-dark": "Flat two-tone on dark: M orange + O blue cones, white wordmark. Two spot colors, vinyl, embroidery, screen print",
    "twotone-on-light": "Flat two-tone on light: the same M orange + O blue cones, Void wordmark. Two spot colors, vinyl, embroidery, screen print",
    "void": "One color, Void. Light backgrounds, fax/laser print, engraving, stamps",
    "white": "One color, white. Dark backgrounds, photos, reversed print",
}

# ---------------------------------------------------------------- shared backgrounds
def grid_path(w, h, cell, x0=0.0, y0=0.0):
    d = []
    x = x0 % cell
    while x <= w + 1e-6: d.append(f"M{f(x)},0V{f(h)}"); x += cell
    y = y0 % cell
    while y <= h + 1e-6: d.append(f"M0,{f(y)}H{f(w)}"); y += cell
    return "".join(d)

def theme(dark):
    return dict(bg=VOID if dark else PAPER, grid=GRAPHITE if dark else MIST, grid_op=0.55 if dark else 0.9,
                text=PAPER if dark else VOID, muted=HAZE if dark else SLATE, label=O_BLUE if dark else ION,
                mode="color" if dark else LIGHT_MODE, flat_wm=WHITE if dark else VOID)

def background(w, h, dark, prefix, cell=None, strip="bottom", strip_h=None, grid=True):
    t = theme(dark); cell = cell or w / 16
    s = f'<g inkscape:groupmode="layer" id="layer-background" inkscape:label="Background">\n'
    s += f'<rect inkscape:label="Background" width="{f(w)}" height="{f(h)}" fill="{t["bg"]}"/>\n'
    if grid: s += f'<path inkscape:label="Grid" d="{grid_path(w, h, cell)}" stroke="{t["grid"]}" stroke-width="{f(max(w, h) / 1280)}" opacity="{t["grid_op"]}" fill="none"/>\n'
    defs = ""
    if strip:
        sh = strip_h or max(h / 53.0, 2.0)
        y = h - sh if strip == "bottom" else 0
        defs = gradient(f"{prefix}-strip", 0, w)
        s += f'<rect inkscape:label="Fusion gradient strip" x="0" y="{f(y)}" width="{f(w)}" height="{f(sh)}" fill="url(#{prefix}-strip)"/>\n'
    return defs, s + "</g>\n"

def text(x, y, s, size, fill, family="mono", weight=400, anchor="start", label="Text", spacing=0):
    fam = "'Cascadia Mono',monospace" if family == "mono" else "Archivo,sans-serif"
    ls = f";letter-spacing:{f(spacing)}px" if spacing else ""
    return (f'<text inkscape:label="{label}" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}" fill="{fill}" '
            f'style="font-family:{fam};font-weight:{weight};font-size:{f(size)}px{ls}">{s}</text>\n')

def layer(name, body, lid=None):
    lid = lid or "layer-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f'<g inkscape:groupmode="layer" id="{lid}" inkscape:label="{name}">\n{body}</g>\n'

# ---------------------------------------------------------------- 1. logo matrix (PDF + PNG for every piece × mode)
MARK_PX = [64, 128, 256, 512, 1024, 2048]
LOCKUP_W = [500, 1000, 2000, 4000]
def build_logo_matrix():
    for piece, fn in PIECES.items():
        a = fn()
        modes = ["color", "void", "white"] if piece == "wordmark" else LOGO_MODES
        for mode in modes:
            name = f"fusion-space-{piece}-{mode}"
            defs, body = a.render(mode, "a")
            s = svg_open(a.w, a.h, f"FusionSpace {piece} ({mode})", page=MODE_BG[mode])
            s += f'<defs id="defs">{defs}</defs>\n' + layer("Logo", body + "\n") + "</svg>\n"
            src = save_svg(f"{KIT}/logo/svg/{name}.svg", s)
            pdf(src, f"{KIT}/logo/pdf/{name}.pdf")
            sizes = MARK_PX if piece == "mark" else LOCKUP_W
            for z in sizes:
                if piece == "mark": png(src, f"{KIT}/logo/png/{name}-{z}.png", h=z)
                else: png(src, f"{KIT}/logo/png/{name}-{z}w.png", w=z)
            note(f"{KIT}/logo/svg/{name}.svg", "Logo", f"{piece}, {mode}", f"{f(a.w)} × {f(a.h)} units", MODE_USE[mode])
            note(f"{KIT}/logo/pdf/{name}.pdf", "Logo", f"{piece}, {mode}, vector PDF", "vector", "Print, documents, anything that takes PDF")
            sz = ", ".join(f"{z}" for z in sizes)
            note(f"{KIT}/logo/png/{name}-*.png", "Logo", f"{piece}, {mode}, transparent PNG",
                 ("height " if piece == "mark" else "width ") + sz + " px", "Screens, slides, web")

# ---------------------------------------------------------------- 2. web and app icons
def tile_svg(kind, rx, frac=None, fill_mode="color", bg=VOID, S=512, title="FusionSpace icon"):
    """The cluster on a tile. frac: bbox fraction of the tile (default: the app-icon framing, build.app_frac)."""
    a = art_mark(200); k = (frac or build.app_frac()) * S / max(a.w, a.h)
    x, y = (S - a.w * k) / 2, (S - a.h * k) / 2              # bbox centered, as build.icon_svg
    defs, g = a.place(fill_mode, "i", x, y, k)
    s = svg_open(S, S, title, page=PAPER)
    s += f'<defs id="defs">{defs}</defs>\n'
    if bg: s += layer("Tile", f'<rect width="{S}" height="{S}" rx="{rx}" fill="{bg}"/>\n')
    s += layer("Mark", g + "\n") + "</svg>\n"
    return s

def build_web():
    W = f"{KIT}/web"
    fav = out("logo/favicon/favicon.svg"); ico = out("logo/favicon/icon.svg"); app = out("logo/favicon/app-icon.svg")
    for src, dst in [(fav, "favicon.svg"), ("logo/favicon/favicon.ico", "favicon.ico"), ("logo/favicon/favicon-16.png", "favicon-16.png"),
                     ("logo/favicon/favicon-32.png", "favicon-32.png"), ("logo/favicon/apple-touch-icon.png", "apple-touch-icon.png")]:
        os.makedirs(out(W), exist_ok=True); shutil.copy(src if os.path.isabs(src) else out(src), out(f"{W}/{dst}"))
    png(fav, f"{W}/favicon-48.png", 48, 48)
    for z in (64, 96, 128, 192, 256, 384, 512, 1024): png(ico, f"{W}/icon-{z}.png", z, z)
    for z in (192, 512): png(app, f"{W}/icon-maskable-{z}.png", z, z)
    # monochrome (Android themed icons use the alpha only): white cluster, transparent, inside the safe zone
    save_svg(f"{W}/icon-monochrome.svg", tile_svg("cluster", 0, fill_mode="white", bg=None, title="FusionSpace monochrome icon"))
    png(out(f"{W}/icon-monochrome.svg"), f"{W}/icon-monochrome-512.png", 512, 512)
    # adaptive transparent favicon: gradient cluster on dark UI, Void cluster on light UI
    a = art_mark(200); k = 0.94 * 512 / max(a.w, a.h); x, y = (512 - a.w * k) / 2, (512 - a.h * k) / 2
    defs, body = a.place("color", "c", x, y, k)
    s = ('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">\n<title>FusionSpace favicon (adaptive)</title>\n'
         f'<style>path{{fill:{VOID}}}@media (prefers-color-scheme:dark){{path{{fill:url(#c-mg)}}}}</style>\n'
         f'<defs>{defs}</defs>\n' + re.sub(r' fill="[^"]+"', "", body) + "\n</svg>\n")
    save_svg(f"{W}/favicon-adaptive.svg", s)
    # Safari pinned tab (legacy mask-icon): one black shape
    save_svg(f"{W}/safari-pinned-tab.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
             + re.sub(r' fill="[^"]+"', ' fill="#000000"', body) + "</svg>\n")
    # Windows tile (legacy)
    save_svg(f"{W}/mstile.svg", tile_svg("cluster", 0, frac=0.62, bg=VOID, title="FusionSpace Windows tile"))
    png(out(f"{W}/mstile.svg"), f"{W}/mstile-150x150.png", 150, 150); os.remove(out(f"{W}/mstile.svg"))
    build.wr(f"{W}/browserconfig.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<browserconfig><msapplication><tile><square150x150logo src="/mstile-150x150.png"/><TileColor>{VOID}</TileColor></tile></msapplication></browserconfig>
''')
    manifest = {
        "name": "FusionSpace", "short_name": "FusionSpace", "theme_color": VOID, "background_color": VOID, "display": "standalone",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
            {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
            {"src": "/icon-monochrome-512.png", "sizes": "512x512", "type": "image/png", "purpose": "monochrome"},
        ]}
    build.wr(f"{W}/site.webmanifest", json.dumps(manifest, indent=2) + "\n")
    build.wr(f"{W}/head.html", f'''<!-- FusionSpace icons: copy kit/web/* to the site root, then paste this into <head>. -->
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="{PAPER}" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="{VOID}" media="(prefers-color-scheme: dark)">
<!-- Legacy, only if you care about old Safari pinned tabs and Windows Start tiles:
<link rel="mask-icon" href="/safari-pinned-tab.svg" color="{VOID}">
<meta name="msapplication-config" content="/browserconfig.xml"> -->
<!-- For a Next.js site (App Router), see kit/web/site/ instead: same icons under the file names Next picks up. -->
<!-- Optional: a transparent favicon that follows the browser theme (Void cluster on light, gradient cluster on dark).
     Use it instead of /favicon.svg if you prefer no tile:
<link rel="icon" href="/favicon-adaptive.svg" type="image/svg+xml"> -->
''')
    G = "Web & app icons"
    for p, what, size, use in [
        ("favicon.ico", "favicon, ICO (16 hinted, 32, 48)", "16/32/48", "Legacy browsers, Windows shortcuts"),
        ("favicon.svg", "favicon, full cluster on a Void tile", "vector", "Modern browsers"),
        ("favicon-adaptive.svg", "favicon without tile; follows light/dark theme", "vector", "Optional alternative to favicon.svg"),
        ("favicon-16.png", "favicon 16 px, pixel-hinted", "16", "Tabs, bookmarks"),
        ("favicon-32.png / favicon-48.png", "favicon PNGs", "32, 48", "Tabs on high-DPI, shortcuts"),
        ("apple-touch-icon.png", "iOS home screen, full-bleed, safe-zone framed", "180", "iOS/iPadOS"),
        ("icon-{64…1024}.png", "full cluster on rounded Void tile", "64, 96, 128, 192, 256, 384, 512, 1024", "App stores, docs, launchers, purpose any"),
        ("icon-maskable-192/512.png", "full-bleed, cluster inside the 0.40 safe circle", "192, 512", "Android/PWA purpose maskable"),
        ("icon-monochrome-512.png / .svg", "white silhouette, transparent", "512", "Android themed icons, purpose monochrome"),
        ("safari-pinned-tab.svg", "one-color cluster", "vector", "Safari pinned tabs (legacy)"),
        ("mstile-150x150.png + browserconfig.xml", "Windows tile", "150", "Windows Start tiles (legacy)"),
        ("site.webmanifest", "PWA manifest", "", "Install as an app"),
        ("head.html", "copy-paste <head> snippet", "", "Wiring it all up")]:
        note(f"{W}/{p}", G, what, size, use)

# ---------------------------------------------------------------- 3. composites (avatars, banners, cards)
def lockup_on(w, h, dark, piece, cx, cy, height=None, width=None, prefix="l", mode=None):
    a = PIECES[piece]()
    k = (height / a.h) if height else (width / a.w)
    mode = mode or theme(dark)["mode"]
    return a.place(mode, prefix, cx - a.w * k / 2, cy - a.h * k / 2, k) + (a.w * k, a.h * k)

def avatar_svg(S, dark):
    t = theme(dark); a = art_mark(200)
    k = build.app_frac() * S / max(a.w, a.h)
    defs, g = a.place(t["mode"], "m", (S - a.w * k) / 2, (S - a.h * k) / 2, k)
    s = svg_open(S, S, "FusionSpace avatar", page=t["bg"])
    s += f'<defs id="defs">{defs}</defs>\n' + layer("Background", f'<rect width="{S}" height="{S}" fill="{t["bg"]}"/>\n') + layer("Mark", g + "\n") + "</svg>\n"
    return s

def banner_svg(w, h, dark, title, lockup_h, cx=None, cy=None, tagline=True, safe=None, piece="horizontal", strip="bottom", label=None):
    """Grid background, gradient strip, lockup centered at (cx, cy); optional tagline under it; optional safe-area guide
    (hidden layer)."""
    t = theme(dark); cx = w / 2 if cx is None else cx; cy = h / 2 if cy is None else cy
    bdefs, bg = background(w, h, dark, "b", cell=h / 4 if w / h > 2.5 else w / 16, strip=strip)
    ty = 0
    if tagline:
        cy_l = cy - lockup_h * 0.32
    else:
        cy_l = cy
    ldefs, lg, lw, lh = lockup_on(w, h, dark, piece, cx, cy_l, height=lockup_h)
    s = svg_open(w, h, title, page=t["bg"])
    s += f'<defs id="defs">{bdefs}{ldefs}</defs>\n' + bg + layer("Brand", lg + "\n")
    txt = ""
    if tagline:
        txt += text(cx, cy_l + lh / 2 + lockup_h * 0.66, TAGLINE.upper(), lockup_h * 0.2, t["label"], anchor="middle", label="Tagline", spacing=lockup_h * 0.02)
    if label:
        txt += text(w * 0.035, h * 0.09, label, h * 0.035, t["muted"], label="Corner label")
    if txt: s += layer("Text (edit me)", txt)
    if safe:
        sx, sy, sw, sh = safe
        s += (f'<g inkscape:groupmode="layer" id="layer-safe-area" inkscape:label="Safe area (hidden)" style="display:none" sodipodi:insensitive="true">'
              f'<rect x="{f(sx)}" y="{f(sy)}" width="{f(sw)}" height="{f(sh)}" fill="none" stroke="#FF7A7A" stroke-width="{f(w / 640)}" stroke-dasharray="{f(w / 100)} {f(w / 200)}"/></g>\n')
    return s + "</svg>\n"

SOCIAL = [
    # (folder, name, w, h, lockup_h, cx, cy, tagline, safe, use). Checked Oct 2, 2026: GitHub social preview 1280 × 640, Open Graph
    # 1200 × 630, X/Mastodon header 1500 × 500 (Bluesky 3:1, same file), LinkedIn banner 1584 × 396 and Page cover 4200 × 700,
    # YouTube 2560 × 1440 (safe 1546 × 423), Facebook cover 851 × 315 shown (mobile crops the sides to 16:9), Discord 960 × 540.
    ("github", "readme-banner", 1280, 320, 96, None, None, True, None, "README header (use the <picture> snippet for light/dark)"),
    ("github", "readme-banner@2x", 2560, 640, 192, None, None, True, None, "README header, high-DPI"),
    ("github", "social-preview", 1280, 640, 150, None, None, True, None, "Repository social preview (Settings → Social preview)"),
    ("social", "og-image", 1200, 630, 140, None, None, True, None, "Open Graph / link previews for websites"),
    ("social", "header-1500x500", 1500, 500, 120, 750, 230, True, (0, 60, 1500, 380), "X/Twitter, Bluesky and Mastodon header (top/bottom 60 px may crop)"),
    ("social", "linkedin-banner", 1584, 396, 100, 950, 198, True, (500, 0, 1084, 396), "LinkedIn personal banner (profile photo covers the lower left)"),
    ("social", "linkedin-company-cover", 4200, 700, 260, None, None, True, (300, 0, 3600, 700), "LinkedIn company page cover"),
    ("social", "youtube-banner", 2560, 1440, 220, None, None, True, (507, 508, 1546, 423), "YouTube channel art (logo inside the 1546 × 423 safe area)"),
    ("social", "facebook-cover", 1702, 630, 130, None, None, True, (0, 0, 1702, 630), "Facebook page cover (851 × 315 at 2×)"),
    ("social", "discord-banner", 960, 540, 90, None, None, True, None, "Discord server banner"),
]
AVATARS = [400, 500, 800, 1024]

def build_social():
    for dark in (True, False):
        tone = "dark" if dark else "light"
        for z in AVATARS:
            folder = "github" if z == 500 else "social"
            src = save_svg(f"{KIT}/{folder}/avatar-{tone}-{z}.svg", avatar_svg(z, dark))
            png(src, f"{KIT}/{folder}/avatar-{tone}-{z}.png", z, z)
            os.remove(src)
        for folder, name, w, h, lh, cx, cy, tag, safe, use in SOCIAL:
            src = save_svg(f"{KIT}/{folder}/{name}-{tone}.svg", banner_svg(w, h, dark, f"FusionSpace {name}", lh, cx, cy, tag, safe))
            png(src, f"{KIT}/{folder}/{name}-{tone}.png", w, h)
    for z in AVATARS:
        folder = "github" if z == 500 else "social"
        note(f"{KIT}/{folder}/avatar-{{dark,light}}-{z}.png", "Profiles & social", "avatar, mark centered inside a circle-safe zone",
             f"{z} × {z}", "GitHub (500), LinkedIn/X/Mastodon (400), YouTube (800), Bluesky/Instagram/Discord (1024; they downscale)")
    for folder, name, w, h, *_rest in SOCIAL:
        note(f"{KIT}/{folder}/{name}-{{dark,light}}.png/.svg", "Profiles & social", name.replace("-", " "), f"{w} × {h}", _rest[-1])
    build.wr(f"{KIT}/github/README-snippet.md", '''<!-- FusionSpace README banner that follows GitHub's light/dark theme.
     Copy readme-banner-dark.png and readme-banner-light.png (or the @2x files) into your repo, e.g. .github/, and adjust the paths. -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme-banner-dark.png">
  <source media="(prefers-color-scheme: light)" srcset=".github/readme-banner-light.png">
  <img alt="FusionSpace" src=".github/readme-banner-dark.png" width="100%">
</picture>
''')
    note(f"{KIT}/github/README-snippet.md", "Profiles & social", "<picture> snippet for light/dark README banners", "", "Paste at the top of a README")

# ---------------------------------------------------------------- 4. documents
MM = 1.0
PAGES = {"letter": (215.9, 279.4), "a4": (210.0, 297.0)}

def letterhead_svg(page):
    w, h = PAGES[page]
    a = art_horizontal(); lh = 11.0; k = lh / a.h
    defs, g = a.place(theme(False)["mode"], "lh", 20, 16, k)
    sdefs = gradient("lh-strip", 0, w)
    s = svg_open(w, h, f"FusionSpace letterhead ({page})", units="mm", page=WHITE)
    s += f'<defs id="defs">{sdefs}{defs}</defs>\n'
    s += layer("Background", f'<rect width="{f(w)}" height="{f(h)}" fill="{WHITE}"/>\n<rect inkscape:label="Fusion gradient strip" x="0" y="0" width="{f(w)}" height="3" fill="url(#lh-strip)"/>\n')
    s += layer("Brand", g + "\n")
    ft = (text(20, h - 14, f"FUSIONSPACE · {TAGLINE.upper()}", 2.6, SLATE, label="Footer line 1", spacing=0.15)
          + text(20, h - 10, f"{EMAIL} · {SITE} · {GITHUB}", 2.6, SLATE, label="Footer line 2 (edit me)")
          + text(w - 20, 23.5, "FS-VEGA · LETTER · REV A", 2.6, ION, anchor="end", label="Reference (edit me)"))
    s += layer("Text (edit me)", ft)
    s += layer("Rule", f'<path d="M20,{f(h - 20)}H{f(w - 20)}" stroke="{MIST}" stroke-width="0.25"/>\n')
    return s + "</svg>\n"

def cover_svg(page, dark, designation="FS-VEGA · REPORT 001 · REV A", title="Report title", subtitle="A one-line subtitle for this document.", when=None):
    """when: the date printed under the title (a datetime.date); default the build's fixed date (SOURCE_DATE_EPOCH)."""
    E = lambda x: x.replace("&", "&amp;").replace("<", "&lt;")
    w, h = PAGES[page]; t = theme(dark)
    bdefs, bg = background(w, h, dark, "cv", cell=w / 12, strip="bottom", strip_h=4)
    a = art_horizontal(); k = 12.0 / a.h
    ldefs, lg = a.place(t["mode"], "cvl", 20, 20, k)
    m = art_mark(200); km = 0.62 * w / m.w
    mdefs, mg = m.place("white" if dark else "void", "cvm", w - m.w * km * 0.78, h * 0.30, km)
    s = svg_open(w, h, f"FusionSpace report cover ({page}, {'dark' if dark else 'light'})", units="mm", page=t["bg"])
    s += f'<defs id="defs">{bdefs}{ldefs}{mdefs}</defs>\n' + bg
    s += layer("Brand", lg + f'<g inkscape:label="Watermark" opacity="{0.05 if dark else 0.045}">{mg}</g>\n')
    tsz = min(15.0, (w - 40) / max(1, len(title) * 0.586))
    # the subtitle wraps, at a smaller size if it must; it is never cut off with "…"
    for ssz in (5.4, 4.8, 4.2):
        lines = textwrap.wrap(subtitle, max(8, int((w - 40) / (0.485 * ssz))), break_long_words=False, break_on_hyphens=False)
        if len(lines) <= 3: break
    else:
        raise SystemExit(f"report cover: the subtitle doesn't fit in three lines ({len(subtitle)} characters); shorten it")
    if when is None:
        when = datetime.datetime.fromtimestamp(int(os.environ.get("SOURCE_DATE_EPOCH", "1790812800")), datetime.timezone.utc).date()
    tx = (text(20, h * 0.52, E(designation), 4.2, t["label"], label="Designation (edit me)", spacing=0.2)
          + text(19, h * 0.52 + 18, E(title), tsz, t["text"], weight=600, label="Title (edit me)")
          + "".join(text(20, h * 0.52 + 29 + i * ssz * 1.3, E(ln), ssz, t["muted"], family="sans", label="Subtitle (edit me)") for i, ln in enumerate(lines))
          + text(20, h - 16, f"NEER PATEL · {when.strftime('%B %Y').upper()}", 3.4, t["muted"], label="Author and date (edit me)", spacing=0.15))
    s += layer("Text (edit me)", tx)
    return s + "</svg>\n"

CARDS = {"us": (88.9, 50.8), "eu": (85.0, 55.0)}
BLEED = 3.0
def card_svg(region, side):
    w, h = CARDS[region]; W, H = w + 2 * BLEED, h + 2 * BLEED; b = BLEED
    dark = side == "front"; t = theme(dark)
    s = svg_open(W, H, f"FusionSpace business card ({region}, {side}), with {BLEED:g} mm bleed", units="mm", page=t["bg"])
    if side == "front":
        bdefs, bg = background(W, H, True, "cf", cell=h / 5, strip="bottom", strip_h=b + 1.2)
        m = art_mark(200); km = 0.46 * h / m.h
        mdefs, mg = m.place("color", "cfm", (W - m.w * km) / 2, (H - m.h * km) / 2 - 1.5, km)
        s += f'<defs id="defs">{bdefs}{mdefs}</defs>\n' + bg + layer("Brand", mg + "\n")
    else:
        a = art_horizontal(); k = 6.0 / a.h
        ldefs, lg = a.place(theme(False)["mode"], "cbl", b + 6, b + 6, k)
        s += f'<defs id="defs">{ldefs}</defs>\n' + layer("Background", f'<rect width="{f(W)}" height="{f(H)}" fill="{PAPER}"/>\n')
        s += layer("Brand", lg + "\n")
        x = b + 6; y = b + h - 19
        tx = (text(x, y, "Neer Patel", 3.6, VOID, weight=600, label="Name (edit me)")
              + text(x, y + 4.4, ROLE, 2.5, SLATE, family="sans", label="Role (edit me)")
              + text(x, y + 9.2, EMAIL, 2.3, VOID, label="Email (edit me)")
              + text(x, y + 12.6, f"{SITE} · {GITHUB}", 2.3, ION, label="Links (edit me)"))
        s += layer("Text (edit me)", tx)
    s += (f'<g inkscape:groupmode="layer" id="layer-trim" inkscape:label="Trim and safe lines (hidden)" style="display:none" sodipodi:insensitive="true">'
          f'<rect x="{f(b)}" y="{f(b)}" width="{f(w)}" height="{f(h)}" fill="none" stroke="#FF7A7A" stroke-width="0.15"/>'
          f'<rect x="{f(b + 3)}" y="{f(b + 3)}" width="{f(w - 6)}" height="{f(h - 6)}" fill="none" stroke="#3350D6" stroke-width="0.15" stroke-dasharray="1 0.6"/></g>\n')
    return s + "</svg>\n"

def signature_files():
    D = f"{KIT}/documents/email-signature"
    a = art_horizontal()
    for tone, bg in (("on-white", WHITE), ("transparent", None)):
        defs, body = a.render(theme(False)["mode"], "s")
        pad = 0.25 * a.h                                   # the guide's clear space, so the white tile doesn't end at the art
        W, H = a.w + 2 * pad, a.h + 2 * pad
        s = svg_open(W, H, "FusionSpace email signature logo", page=WHITE)
        s += f'<defs id="defs">{defs}</defs>\n' + (f'<rect width="{f(W)}" height="{f(H)}" fill="{bg}"/>' if bg else "") \
             + f'<g transform="translate({f(pad)} {f(pad)})">{body}</g></svg>\n'
        src = save_svg(f"{D}/logo-{tone}.svg", s); png(src, f"{D}/logo-{tone}@2x.png", w=round(400 * W / a.w)); os.remove(src)
    m = art_mark(200); defs, body = m.render("color", "s")
    S = 200; k = 0.8 * S / max(m.w, m.h)
    s = svg_open(S, S, "FusionSpace email signature mark", page=VOID) + f'<defs id="defs">{defs}</defs>\n<rect width="{S}" height="{S}" rx="40" fill="{VOID}"/>' \
        + f'<g transform="translate({f((S - m.w * k) / 2)} {f((S - m.h * k) / 2)}) scale({k:.5f})">{body}</g></svg>\n'
    src = save_svg(f"{D}/mark-tile.svg", s); png(src, f"{D}/mark-tile@2x.png", 96, 96); os.remove(src)
    a_ = art_horizontal(); pw = 0.25 * a_.h; img_w = round(200 * (a_.w + 2 * pw) / a_.w); ind = round(img_w * pw / (a_.w + 2 * pw))
    build.wr(f"{D}/signature.html", f'''<!-- FusionSpace email signature. The logo loads from {SIGNATURE_LOGO_BASE}/logo-on-white@2x.png (the site's copy is
     kit/web/site/public/brand/logo-on-white@2x.png). Edit the text, then paste the rendered table into your mail client's signature settings.
     The logo art is 200 px wide on screen ({img_w} px with its white margin; the PNG is 400 px for sharp high-DPI display).
     It sits on a white tile with clear space all round so it reads in dark-mode mail clients too; the text is indented
     {ind} px to line up with the art. -->
<table cellpadding="0" cellspacing="0" border="0" style="font-family:Arial,Helvetica,sans-serif;color:{VOID};border-collapse:collapse">
  <tr><td style="padding:0 0 2px 0"><img src="{SIGNATURE_LOGO_BASE}/logo-on-white@2x.png" width="{img_w}" alt="FusionSpace" style="display:block;border:0;width:{img_w}px;height:auto"></td></tr>
  <tr><td style="font-family:'Cascadia Mono',Consolas,'Courier New',monospace;font-size:14px;font-weight:600;color:{VOID};padding:0 0 0 {ind}px">Neer Patel</td></tr>
  <tr><td style="font-size:13px;color:{SLATE};padding:2px 0 0 {ind}px">{ROLE}</td></tr>
  <tr><td style="font-size:13px;padding:6px 0 0 {ind}px"><a href="mailto:{EMAIL}" style="color:{ION};text-decoration:none">{EMAIL}</a>
    &nbsp;·&nbsp; <a href="{SITE_URL}" style="color:{ION};text-decoration:none">{SITE}</a>
    &nbsp;·&nbsp; <a href="{GITHUB_URL}" style="color:{ION};text-decoration:none">GitHub</a></td></tr>
</table>
''')
    # the site hosts the signature logo at SIGNATURE_LOGO_BASE; its copy goes with the other site drop-ins
    os.makedirs(os.path.join(build.OUT, f"{KIT}/web/site/public/brand"), exist_ok=True)
    shutil.copy(os.path.join(build.OUT, f"{D}/logo-on-white@2x.png"), os.path.join(build.OUT, f"{KIT}/web/site/public/brand/logo-on-white@2x.png"))
    note(f"{KIT}/web/site/public/brand/logo-on-white@2x.png", "Web", "email signature logo, for the site to host at /brand/ (copy of documents/email-signature/logo-on-white@2x.png)", "400 px wide", "fusionspace.co/brand/")
    G = "Documents & comms"
    note(f"{D}/signature.html", G, "email signature, HTML table (logo hosted on the site)", "", "Gmail, Apple Mail, Outlook")
    note(f"{D}/logo-on-white@2x.png", G, "signature logo on a white tile with clear space", "art 400 px wide (2×), shown at 200", "Signature image; safe in dark-mode mail")
    note(f"{D}/logo-transparent@2x.png", G, "signature logo, transparent, same margins", "art 400 px wide (2×)", "Light-only mail clients")
    note(f"{D}/mark-tile@2x.png", G, "mark on a Void tile", "96 px, shown at 48", "Compact signatures, chat profile")

def build_documents():
    D = f"{KIT}/documents"; G = "Documents & comms"
    for page in PAGES:
        src = save_svg(f"{D}/letterhead/letterhead-{page}.svg", letterhead_svg(page))
        pdf(src, f"{D}/letterhead/letterhead-{page}.pdf"); cmyk(f"{D}/letterhead/letterhead-{page}.pdf", f"{D}/letterhead/letterhead-{page}-cmyk.pdf")
        png(src, f"{D}/letterhead/letterhead-{page}-preview.png", w=1200)
        for dark in (True, False):
            tone = "dark" if dark else "light"
            src = save_svg(f"{D}/report-cover/report-cover-{page}-{tone}.svg", cover_svg(page, dark))
            pdf(src, f"{D}/report-cover/report-cover-{page}-{tone}.pdf"); cmyk(f"{D}/report-cover/report-cover-{page}-{tone}.pdf", f"{D}/report-cover/report-cover-{page}-{tone}-cmyk.pdf")
            png(src, f"{D}/report-cover/report-cover-{page}-{tone}-preview.png", w=1200)
    note(f"{D}/letterhead/letterhead-{{letter,a4}}.svg/.pdf", G, "letterhead: lockup, gradient strip, footer (edit text layer)", "US Letter, A4", "Letters, memos; -cmyk.pdf for a print shop")
    note(f"{D}/letterhead/letterhead-{{letter,a4}}.docx", G, "Word letterhead template (header logo, footer text)", "US Letter, A4", "Writing letters in Word, Pages or Google Docs")
    note(f"{D}/report/report-template-{{letter,a4}}.docx", G, "Word report / technical document template: title page, heading, caption, table and code styles, page numbers", "US Letter, A4", "Design reviews, test reports, write-ups")
    note(f"{D}/report-cover/report-cover-{{letter,a4}}-{{dark,light}}.svg/.pdf", G, "report / PDF cover (edit text layer)", "US Letter, A4", "Reports, design reviews, theses; -cmyk.pdf for print")
    for region in CARDS:
        for side in ("front", "back"):
            src = save_svg(f"{D}/business-card/card-{region}-{side}.svg", card_svg(region, side))
            pdf(src, f"{D}/business-card/card-{region}-{side}.pdf"); cmyk(f"{D}/business-card/card-{region}-{side}.pdf", f"{D}/business-card/card-{region}-{side}-cmyk.pdf")
            png(src, f"{D}/business-card/card-{region}-{side}-preview.png", w=1000)
    note(f"{D}/business-card/card-{{us,eu}}-{{front,back}}.svg/.pdf", G, f"business card with {BLEED:g} mm bleed (front: mark on Void; back: details)",
         "US 3.5 × 2 in, EU 85 × 55 mm", "Print shops (send the -cmyk.pdf); trim and 3 mm safe lines are on a hidden layer")
    signature_files()
    # slide backgrounds (for Keynote / Google Slides, and used by the .pptx)
    for tone, dark in (("dark", True), ("light", False)):
        bdefs, bg = background(1920, 1080, dark, "sl", cell=120, strip="bottom", strip_h=12)
        s = svg_open(1920, 1080, f"FusionSpace slide background ({tone})", page=VOID if dark else PAPER) + f'<defs id="defs">{bdefs}</defs>\n' + bg + "</svg>\n"
        src = save_svg(f"{D}/slides/slide-background-{tone}.svg", s); png(src, f"{D}/slides/slide-background-{tone}.png", 1920, 1080)
        defs, lg, lw, lh = lockup_on(1920, 1080, dark, "horizontal", 960, 470, height=150)
        s = svg_open(1920, 1080, f"FusionSpace title slide ({tone})", page=VOID if dark else PAPER) + f'<defs id="defs">{bdefs}{defs}</defs>\n' + bg + layer("Brand", lg)
        s += layer("Text (edit me)", text(960, 640, TAGLINE.upper(), 26, theme(dark)["label"], anchor="middle", label="Tagline", spacing=3)) + "</svg>\n"
        src = save_svg(f"{D}/slides/slide-title-{tone}.svg", s); png(src, f"{D}/slides/slide-title-{tone}.png", 1920, 1080)
    for piece, mode, tag in (("horizontal", "color", "color"), ("horizontal", theme(False)["mode"], "light"), ("mark", "color", "color")):
        a = PIECES[piece](); defs, body = a.render(mode, "x")
        s = svg_open(a.w, a.h, "logo for slides", page=VOID) + f'<defs id="defs">{defs}</defs>\n' + body + "</svg>\n"
        src = save_svg(f"{D}/slides/_logo-{piece}-{tag}.svg", s)
        png(src, f"{D}/slides/_logo-{piece}-{tag}.png", h=600 if piece == "mark" else 300); os.remove(src)
    for tone, fill, ink in (("light", MIST, HAZE), ("dark", GRAPHITE, SLATE)):     # stand-in picture for the image layouts
        pict = (f'<rect width="1600" height="900" fill="{fill}"/><g fill="{ink}"><circle cx="890" cy="380" r="34"/>'
                f'<path d="M650 540 L750 410 L820 490 L870 445 L950 540 Z"/></g>')
        src = save_svg(f"{D}/slides/_img-{tone}.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">{pict}</svg>')
        png(src, f"{D}/slides/_img-{tone}.png", 1600, 900); os.remove(src)
    note(f"{D}/slides/fusionspace-slides.pptx", G, "16:9 slide template, 14 layouts: title, agenda, section, content, two-column, image and caption, "
         "full-bleed image, table, chart, key numbers, timeline, code, quote, closing", "13.33 × 7.5 in", "PowerPoint, Keynote, Google Slides (import)")
    note(f"{D}/slides/slide-{{background,title}}-{{dark,light}}.png/.svg", G, "slide backgrounds and title slides", "1920 × 1080", "Any slide app")

# ---------------------------------------------------------------- 5. physical production
CUT_MM = [25, 50, 75, 100, 150, 200, 300]
MM_MARGIN = 2.0      # mm of empty page around cut and embroidery art (design review: the art touched the page edge, and a line
                     # drawn on the outline was half cut off there). The art keeps its size and its own coordinates.
def mm_svg_open(w, h, m=MM_MARGIN):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{f(w + 2 * m)}mm" height="{f(h + 2 * m)}mm" '
            f'viewBox="{f(-m)} {f(-m)} {f(w + 2 * m)} {f(h + 2 * m)}">\n')

def svg_mm_paths(cl, w, h, title, stroke=True):
    body = "".join(f'<path id="cut-{n}" d="{geo.seg_to_d(cl[n])}" fill="none" stroke="#000000" stroke-width="0.01"/>' for n in geo.ORDER)
    return mm_svg_open(w, h) + f'<title>{title}</title>\n{body}\n</svg>\n'


def polygons(d, n=40):
    from svgpathtools import parse_path
    from shapely.geometry import Polygon
    polys = []
    for sub in parse_path(d).continuous_subpaths():
        pts = []
        for seg in sub: pts += [(seg.point(t).real, seg.point(t).imag) for t in [i / n for i in range(n)]]
        if len(pts) > 2: polys.append(Polygon(pts).buffer(0))
    return polys

STICKER_CLOSE = 1.0                                               # contour sticker: closing radius (x art height) that merges the cones into one piece
STICKER_SHAPES = {"contour": "die-cut to a smooth outline around the art", "circle": "circle", "square": "rounded square", "rect": "rounded rectangle (horizontal lockup)"}
def sticker_svg(piece, size_mm, dark, shape="contour"):
    """Sticker print file in mm: Backing (with 1.5 mm bleed past the cut), Art, and a CutContour layer (magenta hairline,
    the usual name for the cut path in sticker and vinyl RIPs). size_mm: art height for contour stickers, the sticker's
    diameter/side for circle/square, its width for rect."""
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    a = PIECES[piece]()
    if shape == "contour":
        k = size_mm / a.h
        U = unary_union([p for d, role, cone in a.parts for p in polygons(d)])
        off = max(2.0, 0.045 * size_mm) / k                       # cut line clear of the art
        if piece == "mark":                                          # closing: one smooth piece, no inner bays
            R = STICKER_CLOSE * a.h; cut = U.buffer(R, resolution=48).buffer(-R, resolution=48).buffer(off, resolution=48)
        else:                                                        # lockups: rounded box (letters would make a contour wavy)
            bx0 = U.bounds; pad = off * 2.0
            cut = box(*bx0).buffer(pad, resolution=48)
        if cut.geom_type != "Polygon": cut = U.convex_hull.buffer(off, resolution=48)
        cut = cut.simplify(0.02 / k)
        ax, ay = 0.0, 0.0
    else:
        if shape == "circle":
            D = size_mm; k = 0.60 * D / max(a.w, a.h); cut = Point(D / 2, D / 2).buffer(D / 2, resolution=96)
        elif shape == "square":
            D = size_mm; k = 0.62 * D / max(a.w, a.h); rr = 0.16 * D
            cut = box(rr, rr, D - rr, D - rr).buffer(rr, resolution=48)
        else:
            Wm = size_mm; k = 0.80 * Wm / a.w; Hm = a.h * k + 0.30 * Wm * 0.5; rr = 0.18 * Hm
            cut = box(rr, rr, Wm - rr, Hm - rr).buffer(rr, resolution=48); D = Wm
        bx = cut.bounds
        ax, ay = (bx[0] + bx[2]) / 2 - a.w * k / 2, (bx[1] + bx[3]) / 2 - a.h * k / 2
        cut = __import__("shapely.affinity", fromlist=["scale"]).scale(cut, 1 / k, 1 / k, origin=(0, 0))
        ax, ay = ax / k, ay / k
        cut = __import__("shapely.affinity", fromlist=["translate"]).translate(cut, -ax, -ay)
    back = cut.buffer(1.5 / k, resolution=48)                        # 1.5 mm print bleed past the cut
    bx = back.bounds; m = 2.0
    W = (bx[2] - bx[0]) * k + 2 * m; H = (bx[3] - bx[1]) * k + 2 * m
    ox, oy = -bx[0] * k + m, -bx[1] * k + m
    def ring_d(g):
        return "".join("M" + " L".join(f"{f(x * k + ox)},{f(y * k + oy)}" for x, y in p.exterior.coords) + " Z" for p in getattr(g, "geoms", [g]))
    defs, g = a.place("color", "st", ox, oy, k)
    s = svg_open(W, H, f"FusionSpace sticker ({piece}, {STICKER_SHAPES[shape]}, {size_mm:g} mm, {'dark' if dark else 'light'})", units="mm", page=WHITE)
    s += f'<defs id="defs">{defs}</defs>\n'
    s += layer("Backing (print, includes 1.5 mm bleed)", f'<path d="{ring_d(back)}" fill="{VOID if dark else WHITE}"/>\n')
    s += layer("Art", g + "\n")
    s += layer("CutContour", f'<path id="CutContour" d="{ring_d(cut)}" fill="none" stroke="#FF00FF" stroke-width="0.25"/>\n', lid="layer-CutContour")
    return s + "</svg>\n"

def build_production():
    P = f"{KIT}/production"; G = "Physical production"
    for z in CUT_MM:
        build.build_dxf(height_mm=float(z), path=f"{P}/cut/fusion-space-mark-{z}mm.dxf")
        cl, A, bb = build.dxf_geometry(float(z))
        build.wr(f"{P}/cut/fusion-space-mark-{z}mm.svg", svg_mm_paths(cl, bb[2], bb[3], f"FusionSpace mark, cut outline, {z} mm"))
    note(f"{P}/cut/fusion-space-mark-{{{','.join(map(str, CUT_MM))}}}mm.dxf/.svg", G, f"cut outlines (lines + arcs DXF, hairline SVG with {MM_MARGIN:g} mm of empty page around it); feet trimmed to ≥ 0.5 mm",
         ", ".join(f"{z}" for z in CUT_MM) + " mm tall", "Laser, waterjet, CNC router, vinyl plotter")
    # engraving / stamps
    for piece in ("mark", "horizontal", "stacked"):
        a = PIECES[piece](); k = 40.0 / a.h if piece != "horizontal" else 20.0 / a.h
        for mirror in (False, True):
            defs, body = a.render("void", "e")
            W, H = a.w * k, a.h * k
            tr = f"translate({f(W)} 0) scale(-{k:.6f} {k:.6f})" if mirror else f"scale({k:.6f})"
            s = (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{f(W)}mm" height="{f(H)}mm" viewBox="0 0 {f(W)} {f(H)}">\n'
                 f'<title>FusionSpace {piece}, one color{", mirrored for stamps" if mirror else ""}</title>\n<g transform="{tr}">{body}</g>\n</svg>\n')
            build.wr(f"{P}/engrave/fusion-space-{piece}{'-mirrored' if mirror else ''}.svg", s)
    note(f"{P}/engrave/fusion-space-{{mark,horizontal,stacked}}.svg", G, "one-color Void art in mm (scale freely)", "mark 40 mm, lockups 40/20 mm tall", "Laser engraving, etching, pad printing")
    note(f"{P}/engrave/*-mirrored.svg", G, "mirrored one-color art", "", "Rubber/polymer stamps if the maker doesn't mirror")
    # stickers
    STK = [("mark", "contour", (50, 75, 100)), ("stacked", "contour", (50, 75)), ("mark", "circle", (50, 75)),
           ("mark", "square", (50, 75)), ("horizontal", "rect", (100,))]
    for piece, shape, sizes in STK:
        for z in sizes:
            for dark in (True, False):
                tone = "dark" if dark else "light"
                name = f"sticker-{piece}-{shape}-{z}mm-{tone}" if shape != "contour" else f"sticker-{piece}-{z}mm-{tone}"
                src = save_svg(f"{P}/stickers/{name}.svg", sticker_svg(piece, float(z), dark, shape))
                pdf(src, f"{P}/stickers/{name}.pdf"); cmyk(f"{P}/stickers/{name}.pdf", f"{P}/stickers/{name}-cmyk.pdf")
                png(src, f"{P}/stickers/{name}-preview.png", w=800, bg="#E6E8EE")
    note(f"{P}/stickers/sticker-{{mark,stacked}}-{{50,75,100}}mm-{{dark,light}}.svg/.pdf", G,
         "die-cut sticker, one smooth piece: art + backing (1.5 mm bleed) + CutContour line (magenta, own layer)", "art 50/75/100 mm tall",
         "Sticker printers (Sticker Mule, Stickerapp, local) and vinyl cutters")
    note(f"{P}/stickers/sticker-mark-{{circle,square}}-{{50,75}}mm-{{dark,light}}.svg/.pdf", G, "circle and rounded-square stickers, mark centered",
         "50, 75 mm", "Laptop stickers, packaging seals; simplest to order")
    note(f"{P}/stickers/sticker-horizontal-rect-100mm-{{dark,light}}.svg/.pdf", G, "rounded-rectangle sticker with the horizontal lockup", "100 mm wide",
         "Equipment and case labels, bumper-style stickers")
    # embroidery: flat two-tone, feet floored at 1 mm at the size
    for z in (50, 75, 100):
        for mode in ("twotone-on-dark", "twotone-on-light"):
            cl, A, bb = build.dxf_geometry(float(z), 1.0)
            mf, wf, _ = build.mode_fills(mode)
            body = "".join(f'<path fill="{mf[n]}" d="{geo.seg_to_d(cl[n])}"/>' for n in geo.DRAW_ORDER)
            s = mm_svg_open(bb[2], bb[3]) + f'<title>FusionSpace mark for embroidery, {z} mm, {mode}</title>\n{body}\n</svg>\n'
            build.wr(f"{P}/embroidery/fusion-space-mark-{z}mm-{mode}.svg", s)
    note(f"{P}/embroidery/fusion-space-mark-{{50,75,100}}mm-{{twotone-on-dark,twotone-on-light}}.svg", G,
         f"flat two-tone mark, feet ≥ 1 mm, no gradient, {MM_MARGIN:g} mm of empty page around it", "50, 75, 100 mm tall", "Embroidery digitizers, patches; two thread colors")
    build.wr(f"{P}/CAD.md", """# The mark in CAD

Which kit file to use for logos on parts and drawings. All sizes are in millimeters.

| Job | Fusion | Onshape | FreeCAD | SolidWorks |
|---|---|---|---|---|
| **Emboss or engrave** the mark into a face | Insert → Insert DXF → `kit/production/cut/fusion-space-mark-<size>mm.dxf` onto a sketch plane, then Emboss / Extrude | Sketch → Import DXF (same file), then Extrude add/remove | Import the DXF (Draft), Part → Extrude | Sketch → Insert DXF (same file), Extruded Boss/Cut |
| **Decal** (color image on a face, for renders) | Insert → Decal → `kit/logo/png/fusion-space-mark-color-1024.png` (transparent) | Insert → Decal (same PNG) | Appearance texture, or skip | Appearances → Decals (same PNG) |
| **Drawing title block** | use `templates/freecad/` as the pattern, or the one-color SVG | Drawing template logo: `kit/logo/svg/fusion-space-horizontal-void.svg` | `templates/freecad/FusionSpace_*.svg` | Sheet format: insert `kit/logo/png/fusion-space-horizontal-void-1000w.png` |

- The DXF is lines and true arcs only (no splines), so every CAD package imports it cleanly. Its feet are trimmed to at least
  0.5 mm; for a smaller logo on a part, check the tool size first (a 0.5 mm foot needs a 0.4 mm or smaller cutter).
- Pick the DXF closest to the size you need and scale in the sketch; the outlines are exact at any scale.
- For two-color prints, model the mark as a separate body (see `kit/3d-print/`).
- `kit/3d-print/` also has STEP solids with the mark as exact curves (lines, arcs, the ellipse, Béziers) in named, colored
  bodies, sketches with exact ARC/ELLIPSE/SPLINE entities (`sketch/`), and a parametric badge for FreeCAD and Fusion (`parametric/`).
""")
    note(f"{P}/CAD.md", G, "which file to use for emboss, decals and title blocks in Fusion, Onshape, FreeCAD and SolidWorks", "", "Mechanical CAD")

# ---------------------------------------------------------------- 6. office files (node)
def build_office():
    js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_office.js")
    if not shutil.which("node"):
        WARN.append("node"); print("WARN kit: node not found, .pptx/.docx skipped"); return
    meta = out(f"{KIT}/.office.json")
    with open(meta, "w") as fh: json.dump({"tagline": TAGLINE, "role": ROLE, "email": EMAIL, "site": SITE, "github": GITHUB}, fh)
    # Node's require() doesn't look in the global npm folder, so point it there (and at a local tools/build/node_modules)
    env = dict(os.environ); paths = [os.path.join(os.path.dirname(js), "node_modules")]
    try:
        paths.append(subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, check=True).stdout.strip())
    except Exception:
        pass
    env["NODE_PATH"] = os.pathsep.join(paths + ([env["NODE_PATH"]] if env.get("NODE_PATH") else []))
    r = subprocess.run(["node", js, os.path.join(build.OUT, KIT)], capture_output=True, text=True, env=env)
    os.remove(meta)
    if r.returncode != 0:
        WARN.append("office"); print("WARN kit: kit_office.js failed, .pptx/.docx skipped\n" + r.stderr[-800:])
    for fn in os.listdir(out(f"{KIT}/documents/slides")):
        if fn.startswith(("_logo-", "_img-")): os.remove(out(f"{KIT}/documents/slides/{fn}"))

# ---------------------------------------------------------------- 7. README
def build_readme():
    groups = []
    for p, g, *_ in MANIFEST:
        if g not in groups: groups.append(g)
    L = ["# FusionSpace asset kit (Rev C)", "",
         "Every file here is generated by `tools/build/build.py` (see `tools/build/kit.py`) from the master geometry, so a",
         "change to the mark regenerates the whole kit. Don't edit these files by hand; edit the build, or copy a file out and",
         "edit the copy. Files with a **Text (edit me)** layer are meant to be opened in Inkscape and filled in.", "",
         "## Color modes", "", "| Mode | Use |", "|---|---|"]
    L += [f"| `{m}` | {MODE_USE[m]} |" for m in LOGO_MODES]
    side = build.twotone_side()
    L += ["", f"Two-tone rule: each cone takes the gradient end nearest its own position in the sweep, so the "
          f"{' and '.join(n for n in geo.ORDER if side[n] == 'warm')} cones are warm and the "
          f"{' and '.join(n for n in geo.ORDER if side[n] == 'cool')} cones are cool. The cones are the same on every background, "
          f"M orange `{WARM}` and O blue `{COOL}`; only the wordmark changes: white on dark (`twotone-on-dark`), Void on light "
          f"(`twotone-on-light`). Ion `{ION}` and Ember `{EMBER}` are text and UI colors on light, not logo colors.", "",
          "The gradient is the same on dark and light backgrounds. WCAG 2 contrast of every part of it: at least 3:1 on white,",
          "6:1 on Void; 2.8:1 on Paper (accepted).", "",
          "Light and dark: composites (avatars, banners, covers, slides) come in `-dark` (Void background) and `-light` (Paper",
          "background) versions. Logos are transparent; pick the mode for the background (the `MODE_BG` pairing: color, twotone-on-dark",
          "and white on dark; color, twotone-on-light and void on light).", "",
          "## Minimum sizes", "",
          "- Screen: cluster at least 24 px tall; smaller, use the favicons (the full cluster, hinted at 16 px: the wing cones become small arrows).",
          f"- {build.SMALL_RULE}",
          "- Print: cluster at least 8 mm tall. Two-tone and one-color versions hold up best when small.",
          f"- Cutting: use `production/cut/` (feet trimmed to ≥ {build.DXF_MIN_WALL_MM:g} mm). Many vendors need features about half the material thickness; cut larger for thick stock.",
          "- Embroidery: mark at least 25 mm tall; wordmark only when its cap height is at least 6 mm (horizontal lockup ≥ 10 mm tall).",
          "- PCB silkscreen: mark at least 6 mm tall (8 mm safest); features trimmed to ≥ 0.15 mm.",
          "- 3D printing (0.4 mm nozzle): features ≥ 0.6 mm, cone feet trimmed to 0.6 mm; the name at least 104 mm wide (horizontal lockup 130 mm). Print settings in `3d-print/README.md`.", "",
          f"Brand line: **{TAGLINE}**. Title on cards and signatures: **{ROLE}**. Change them in `tools/build/kit.py` (`TAGLINE`, `ROLE`) and rebuild.", "",
          "Browse every image in `index.html`. New product? `python3 tools/build/project.py --star <Star> [--name <external name>] --tag <TAG> --desc \"...\"` (see `projects/example-vega/`).", ""]
    for g in groups:
        L += [f"## {g}", "", "| File | What | Size | Use |", "|---|---|---|---|"]
        for p, gg, what, size, use in MANIFEST:
            if gg == g: L.append(f"| `{p[len(KIT) + 1:]}` | {what} | {size} | {use} |")
        L.append("")
    L += ["## Notes", "",
          "- Platform sizes were checked in October 2026; platforms change them, so check before a big launch.",
          "- CMYK PDFs (`-cmyk.pdf`) are converted with Ghostscript's default CMYK profile. Most print shops accept the RGB PDF too; ask yours which they prefer and for a proof.",
          "- Brand fonts: Cascadia Mono and Archivo (`type/fonts`). Install them before editing text layers or the Office templates.",
          "- The per-project social card is `templates/project-social-card.svg`; FreeCAD title blocks are in `templates/freecad/`."]
    if WARN: L += ["", "**Skipped in this build:** " + ", ".join(WARN)]
    build.wr(f"{KIT}/README.md", "\n".join(L) + "\n")

def build_kit():
    MANIFEST.clear(); WARN.clear()
    if os.path.exists(out(KIT)): shutil.rmtree(out(KIT))
    import kit_github, kit_targets
    import kit_site, kit_apps
    build_logo_matrix(); build_web(); kit_apps.build_apps(); build_social(); kit_site.build_site(); kit_github.build_github_extras(); build_documents(); build_production()
    kit_targets.build_targets(); __import__('kit_docs').build_docs(); __import__('kit_decals').build_decals(); kit_github.build_example_project(); kit_github.build_naming_option(); build_office(); build_readme(); build_gallery()
    with open(os.path.join(os.path.dirname(build.OUT), ".kit-manifest.json"), "w") as fh: json.dump(MANIFEST, fh)   # lets kit_review.py run on its own
    return len(MANIFEST), list(WARN)

# ---------------------------------------------------------------- 8. guide sheet
GROUP_DIRS = [
    ("kit/logo/", "Every logo piece (mark, horizontal, stacked, wordmark) in every color mode, as SVG, vector PDF and transparent PNG (mark 64–2048 px tall, lockups 500–4000 px wide)."),
    ("kit/web/", "Drop-in site icons: favicon .ico/.svg/PNGs, Apple touch, Android/PWA any, maskable and monochrome icons, Safari and Windows icons, <code>site.webmanifest</code> and a <code>&lt;head&gt;</code> snippet; <code>site/</code> holds drop-in Rev C files for fusionspace.co."),
    ("kit/apps/", "Native app icons and store art: iOS (1024, Icon Composer layers), macOS, Android adaptive icon layers, Google Play icon and feature graphic."),
    ("kit/github/", "Avatar (500 px), README banners for light and dark with the <code>&lt;picture&gt;</code> snippet, and the repository social preview."),
    ("kit/social/", "Avatars (400–1024 px), Open Graph image, X/Bluesky/Mastodon header, LinkedIn banner and company cover, YouTube banner, Facebook cover, Discord banner. Dark and light."),
    ("kit/documents/", "Letterhead (Letter, A4; SVG, PDF, Word), report covers, business cards with bleed (US, EU), email signature, 16:9 slide template (.pptx) and slide backgrounds. Print PDFs also come as <code>-cmyk.pdf</code>."),
    ("kit/production/", "Cut files (DXF, SVG) from 25 to 300 mm; stickers (die-cut, circle, square, rectangle) with a CutContour layer; engraving and mirrored stamp art; two-tone embroidery art; A4 rocket decal sheets (print-and-cut and vinyl); a remove-before-flight tag to have woven or embroidered; a CAD how-to."),
    ("kit/projects/", "Per-project images from <code>tools/build/project.py</code> (example: Vega): social preview, README banners, OG image, YouTube thumbnail, title slides, report covers, starter README."),
    ("kit/embedded/", "Boot logos for OLED, e-paper and TFT displays as C headers (Adafruit GFX, U8g2/XBM, SSD1306 pages, RGB565) and LVGL v9 images, including a round GC9A01 display."),
    ("kit/pcb/", "KiCad footprint library (front and back silkscreen, copper) of the mark from 4 to 20 mm, plus SVG and 1200 dpi PNG for other EDA tools."),
    ("kit/3d-print/", "Print-ready STL, STEP (exact mark) and two-color 3MF for a 0.4 mm nozzle: extruded mark, lockups and name, badges, keychain, sign, coaster, fridge magnet, rocket fin-can and nose-cone badges, desk stand, cable tags, stencils, lithophane, cookie cutter, remove-before-flight tag; sketches (DXF/SVG) and a FreeCAD/Fusion parametric badge."),
    ("kit/software/", "Terminal color schemes (Windows Terminal, iTerm2, Alacritty, kitty, Ghostty, VS Code) and CLI banners (braille text art, 24-bit color, Python/C/Rust); MkDocs Material and Docusaurus themes."),
    ("kit/games/", "Studio splash screens; Steam store and library templates; itch.io cover."),
    ("kit/video/", "Logo animation (MP4, WebM, transparent WebM, GIF) and the YouTube watermark."),
    ("kit/wallpapers/", "Desktop, laptop, phone and tablet wallpapers, and video-call backgrounds, dark and light."),
    ("kit/merch/", "T-shirt, hoodie, cap and mug print files at 300 dpi in every color mode; posters (A3, A2, 18 × 24 in)."),
]
def guide_sheet(n_sheets):
    tiles = []
    for mode in LOGO_MODES:
        a = art_mark(100); defs, body = a.render(mode, f"km-{mode}")
        bg = MODE_BG[mode]; light = bg == PAPER
        svg = (f'<svg viewBox="0 0 {f(a.w)} {f(a.h)}" xmlns="http://www.w3.org/2000/svg" style="width:58%;height:auto" aria-hidden="true">'
               f'<defs>{defs}</defs>{body}</svg>')
        tiles.append(f'<figure class="panel {"light" if light else "dark"}" style="margin:0"><div class="specimen" style="min-height:120px;padding:24px 12px">{svg}</div>'
                     f'<div class="cap"><span>{mode}</span></div></figure>')
    side = build.twotone_side()
    warm = " and ".join(geo.NAMES[n].split()[0].lower() for n in geo.ORDER if side[n] == "warm")
    cool = " and ".join(geo.NAMES[n].split()[0].lower() for n in geo.ORDER if side[n] == "cool")
    rows = "".join(f"<tr><td>{d}</td><td>{t}</td></tr>" for d, t in GROUP_DIRS)
    return f'''
  <section class="sheet" id="kit">
    <div class="sheet-head"><span class="sheet-no">SHEET {n_sheets} / {n_sheets}</span><h2>Kit</h2><p class="muted" style="font-size:14px">Ready-made files for every place the brand shows up. All of them are generated from the mark, so they never drift.</p></div>
    <div class="sheet-body">
      <p>Five color modes cover every background and process. Use the gradient wherever color reproduces well. Use flat two-tone where only spot colors work (screen print, vinyl, embroidery): each cone takes the nearer end of the gradient, so the {warm} cones are warm and the {cool} cones are cool. Use one color for engraving, stamps and single-ink print.</p>
      <div class="kitmodes">{"".join(tiles)}</div>
      <div class="rules">
        <div><h3>Light and dark</h3><p>Every banner, avatar, cover and slide comes in a dark (Void) and a light (Paper) version. On GitHub, the README snippet swaps them with the reader's theme.</p></div>
        <div><h3>Two-tone colors</h3><p>The same cones on every background: M orange {WARM} and O blue {COOL}. Only the wordmark changes, white on dark and Void on light. Ion and Ember stay text and UI colors.</p></div>
        <div><h3>Production</h3><p>Cut files trim each foot to at least {build.DXF_MIN_WALL_MM:g} mm. Embroidery art trims to 1 mm; keep the mark at least 25 mm tall there.</p></div>
      </div>
      <table class="files"><tbody>{rows}</tbody></table>
      <p class="muted" style="font-size:14px">Open <code>kit/index.html</code> to browse every image. <code>kit/README.md</code> lists every file with its size and where to use it.</p>
    </div>
  </section>
'''
GUIDE_CSS = ".kitmodes{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}@media (max-width:760px){.kitmodes{grid-template-columns:repeat(2,minmax(0,1fr))}}\n"

# ---------------------------------------------------------------- 9. browsable gallery (kit/index.html)
GALLERY_SKIP = re.compile(r"logo/png/.*-(64|128|256|1024|2048)\.png$|logo/png/.*-(500|2000|4000)w\.png$|/@|@2x|-1200dpi|embedded/.*(?<!preview@4x)(?<!preview@2x)\.png$|projects/.*-light|wallpapers/(?!desktop-2560|phone-1320|call)|web/site/(app|public)/|apps/macos/AppIcon-(16|32|64|128|256|512)\.png")
def build_gallery():
    root = out(KIT); groups = {}
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for n in sorted(fn):
            rel = os.path.relpath(os.path.join(dp, n), root).replace(os.sep, "/")
            if not n.endswith(".png") or GALLERY_SKIP.search(rel): continue
            groups.setdefault(rel.split("/")[0], []).append(rel)
    order = ["logo", "web", "apps", "github", "social", "documents", "projects", "embedded", "pcb", "software", "games", "video", "wallpapers", "merch", "production", "3d-print"]
    secs = []
    for g in [g for g in order if g in groups] + [g for g in groups if g not in order]:
        dk = lambda p: " dk" if re.search(r"-white|twotone-on-dark|monochrome|watermark|tshirt-.*-(white|twotone-on-dark)", p) else ""
        cards = "".join(f'<a class="c" href="{p}"><span class="t{dk(p)}"><img loading="lazy" src="{p}" alt=""></span><span class="n">{p[len(g) + 1:]}</span></a>' for p in groups[g])
        secs.append(f'<section id="{g}"><h2>{g}</h2><div class="g">{cards}</div></section>')
    nav = "".join(f'<a href="#{g}">{g}</a>' for g in [g for g in order if g in groups] + [g for g in groups if g not in order])
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FusionSpace kit</title><link rel="icon" href="web/favicon.svg">
<style>
:root{{--bg:#F3F4F7;--fg:#0B0F1C;--mut:#566079;--rule:#D6DAE4;--card:#fff;--chk:#E6E8EE}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0B0F1C;--fg:#F3F4F7;--mut:#98A1B8;--rule:#2A3248;--card:#141A2B;--chk:#1B2236}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 Archivo,system-ui,sans-serif;padding:0 16px 48px}}
.strip{{height:6px;margin:0 -16px;background:{build.css_gradient()}}}
header{{max-width:1400px;margin:0 auto;padding:24px 0 8px}}h1{{font:600 28px 'Cascadia Mono',monospace;margin:0}}
p{{color:var(--mut);max-width:75ch}}nav{{display:flex;flex-wrap:wrap;gap:6px 14px;font:13px 'Cascadia Mono',monospace;margin:12px 0}}nav a{{color:var(--fg)}}
section{{max-width:1400px;margin:0 auto;padding-top:28px;border-top:1px solid var(--rule)}}h2{{font:600 15px 'Cascadia Mono',monospace;text-transform:uppercase;letter-spacing:.06em}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
.c{{display:grid;gap:6px;text-decoration:none;color:var(--fg);background:var(--card);border:1px solid var(--rule);padding:8px;min-width:0}}
.t{{display:grid;place-items:center;height:160px;background:repeating-conic-gradient(var(--chk) 0 25%,transparent 0 50%) 0 0/16px 16px}}
.t.dk{{background:repeating-conic-gradient(#141A2B 0 25%,#0B0F1C 0 50%) 0 0/16px 16px}}.t img{{max-width:100%;max-height:160px;image-rendering:auto}}.n{{font:11px 'Cascadia Mono',monospace;color:var(--mut);overflow-wrap:anywhere}}
</style></head><body><div class="strip"></div><header><h1>FusionSpace kit</h1>
<p>Every image in the kit, grouped by folder. Click one to open it. Vector sources (SVG, PDF), Office files, STL, DXF and code sit next to these; <a href="README.md">README.md</a> lists every file and where to use it.</p>
<nav>{nav}</nav></header>{"".join(secs)}</body></html>
"""
    build.wr(f"{KIT}/index.html", html)
