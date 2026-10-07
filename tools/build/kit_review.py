"""FusionSpace review page: review.html at the build root.

Lists every file the build makes, grouped into items (one item = one piece of artwork in all its formats, e.g. a card back
as SVG + PDF + CMYK PDF + preview PNG). For each item you pick Keep / Change / Remove and write a note. Decisions are saved
in the browser and exported as a Markdown file (with a JSON block) that a later session reads to apply the changes.

Each item carries a content hash (pixels for PNGs, bytes for SVG and text; PDFs, Office files, DXF, STL and video are left
out because they embed timestamps), so after a rebuild the page marks reviewed items whose artwork changed as "re-check".

The page also runs a light audit and shows flags: empty files, leftover placeholders, PNG sizes that don't match the size
in the file name, SVG or JSON that doesn't parse.
"""
import os, re, json, hashlib, html, datetime, shutil, subprocess, tempfile, glob
import xml.etree.ElementTree as ET
from PIL import Image
import build, kit

Image.MAX_IMAGE_PIXELS = None
SKIP = {"review.html", "verify.png"}; SKIP_DIRS = ("review-previews/",)
TEXT_EXT = {".md", ".txt", ".json", ".h", ".c", ".py", ".rs", ".xbm", ".ans", ".sh", ".css", ".kicad_mod", ".toml", ".yml",
            ".yaml", ".conf", ".itermcolors", ".webmanifest", ".xml", ".html", ".svg", ".js", ".ts", ".fcmacro", ".swift", ".kt", ""}
NO_HASH = {".pdf", ".docx", ".pptx", ".dxf", ".stl", ".mp4", ".webm", ".gif", ".ico", ".zip"}
PLACEHOLDER = re.compile(r"example\.com|your-name|LOGO_URL|Lorem ipsum|TODO|FIXME|name@")
SIZE_SUFFIX = re.compile(r"(-preview(@\dx)?|@\dx|-cmyk|-lvgl|-1200dpi|-\d+w|-(16|32|48|64|96|128|150|152|167|180|192|256|310|384|400|500|512|800|1000|1024|2000|2048|4000))$")
DIMS = re.compile(r"(?<![\d.])(\d{2,5})x(\d{2,5})(?!\d|in|mm)")
ANSI = re.compile(r"\x1b\[([0-9;]*)m")
SECTION_ORDER = ["guide", "product", "logo", "graphics", "templates", "color", "kit/logo", "kit/web", "kit/apps", "kit/github", "kit/social", "kit/documents",
                 "kit/projects", "kit/embedded", "kit/pcb", "kit/software", "kit/games", "kit/video", "kit/wallpapers", "kit/merch",
                 "kit/production", "kit/3d-print", "kit", "(root)"]

NOTES_FILE = os.path.join(build.ROOT, "reviews", "session-notes.json")   # {item id: note from the last working session}
PREV_DIR = "review-previews"
PREFER_EXTRA = ("kit/production/cut/", "kit/3d-print/sketch/", "kit/software/banner/", "kit/pcb/FusionSpace.pretty/", "kit/documents/email-signature/signature")          # generated previews for files a browser can't show (Office, DXF)
DIR_DESC = [("logo/mark/", "Master mark files (gradient, one color, two-tone) and the 50 mm DXF"),
            ("logo/lockup/", "Master lockups: horizontal and stacked in every color mode"),
            ("logo/png/", "Master PNG exports of the logo"), ("logo/favicon/", "Master favicon and app icon artwork"),
            ("logo/", "Master logo files"), ("graphics/", "Construction drawing of the mark (used in the guide and on posters)"),
            ("templates/freecad/", "FreeCAD drawing title-block template"), ("templates/", "Project social card template"),
            ("product/tokens/", "Product tokens for every platform (generated from the same values as product/foundations.md)"),
            ("product/", "The product system: rules for sites, tools, CLIs, apps, devices, boards and rockets, with reference parts"),
            ("color/", "Design tokens: colors, geometry values, type"), ("guide/", "The brand guide (open in a browser)"),
            ("README.md", "Repository README"), ("verify.png", "Build check image from verify.py")]

def contact_sheet(pngs, dest, cols=4, width=1600):
    ims = [Image.open(p).convert("RGB") for p in pngs]
    if not ims: return False
    cols = min(cols, len(ims)); cw = width // cols; pad = 12
    th = [int(im.height * (cw - pad) / im.width) for im in ims]
    rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
    H = sum(max(th[i * cols:(i + 1) * cols]) + pad for i in range(len(rows))) + pad
    sheet = Image.new("RGB", (width, H), (214, 218, 228)); y = pad
    for ri, row in enumerate(rows):
        rh = 0
        for ci, im in enumerate(row):
            t = im.resize((cw - pad, th[ri * cols + ci])); sheet.paste(t, (ci * cw + pad // 2, y)); rh = max(rh, t.height)
        y += rh + pad
    os.makedirs(os.path.dirname(dest), exist_ok=True); sheet.save(dest, optimize=True); return True

def _svg_png(svg_text, dest, w=1000):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run(["rsvg-convert", "-w", str(w), "-o", dest], input=svg_text.encode(), check=True, capture_output=True)

def kicad_preview(path, dest):
    """Draw a .kicad_mod's polygons: silkscreen white on PCB green, copper gold, so the review shows what the board gets."""
    t = open(path, encoding="utf-8").read()
    polys = [(m.group(2), [(float(x), float(y)) for x, y in re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", m.group(1))])
             for m in re.finditer(r"\(fp_poly \(pts (.*?)\) \(stroke.*?\(layer \"([^\"]+)\"\)\)", t)]
    pts = [p for _, ps in polys for p in ps]
    x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts); x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
    pad = 0.15 * max(x1 - x0, y1 - y0); W, H = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    col = {"F.SilkS": "#F3F4F7", "B.SilkS": "#F3F4F7", "F.Cu": "#D9A441", "B.Cu": "#D9A441", "F.Mask": None, "B.Mask": None}
    body = "".join(f'<path d="M{" L".join(f"{x - x0 + pad:.4f},{y - y0 + pad:.4f}" for x, y in ps)} Z" fill="{col.get(ly) or "#D9A441"}"/>'
                   for ly, ps in polys if col.get(ly, "x") is not None)
    mm = re.search(r'\(descr "([^"]+)"', t)
    _svg_png(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.4f} {H:.4f}"><rect width="{W:.4f}" height="{H:.4f}" fill="#1E5631"/>{body}</svg>', dest, 600)

def make_previews(fams):
    """Contact sheets for .pptx/.docx (needs LibreOffice + pdftoppm), drawings for DXF-only items, KiCad footprints, cut
    outlines drawn with a visible line (the real files use hairlines) and the email signature with its logo. Skipped quietly
    if tools are missing."""
    root = build.OUT; extra = {}
    office = shutil.which("soffice") or shutil.which("libreoffice"); ppm = shutil.which("pdftoppm")
    for key, fl in fams.items():
        dest_rel = f"{PREV_DIR}/{key.replace('/', '__')}.png"; dest = os.path.join(root, dest_rel)
        try:
            if key.startswith(("kit/production/cut/", "kit/3d-print/sketch/")) and any(r.endswith(".svg") for r in fl):
                t = open(os.path.join(root, next(r for r in fl if r.endswith(".svg"))), encoding="utf-8").read()
                vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', t).group(1).split()]
                t = re.sub(r'stroke-width="[\d.]+"', f'stroke-width="{max(vb[2], vb[3]) / 300:.4f}"', t).replace('fill="none"', 'fill="#E6E8EE"')
                t = t.replace("<title>", f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="#FFFFFF"/><title>', 1)
                _svg_png(t, dest, 800); extra[key] = dest_rel; continue
            if any(r.endswith(".ans") for r in fl):                          # terminal art: draw it as a terminal would
                import kit_targets
                with open(os.path.join(root, next(r for r in fl if r.endswith(".ans"))), encoding="utf-8") as fh: lines = fh.read().splitlines()
                os.makedirs(os.path.dirname(dest), exist_ok=True); kit_targets.term_preview(lines, dest); extra[key] = dest_rel; continue
            if any(r.endswith(".kicad_mod") for r in fl):
                kicad_preview(os.path.join(root, fl[0]), dest); extra[key] = dest_rel; continue
            if key.endswith("email-signature/signature.html"):
                import kit_shot
                if kit_shot.html_png(os.path.join(root, fl[0]), dest, 640, 220, subst={"https://fusionspace.co/brand/": "", "font-family:Arial,Helvetica,sans-serif": "font-family:Archivo,Arial,Helvetica,sans-serif"}): extra[key] = dest_rel
                continue
            if any(r.endswith((".png", ".svg", ".jpg", ".gif")) for r in fl): continue
            if any(r.endswith(".ico") for r in fl):                       # icon file on its own: show its largest image
                with Image.open(os.path.join(root, next(r for r in fl if r.endswith(".ico")))) as im:
                    im.size = max(im.info.get("sizes") or [im.size])             # ICO: setting size picks that frame
                    os.makedirs(os.path.dirname(dest), exist_ok=True); im.convert("RGBA").resize((192, 192), Image.NEAREST).save(dest)
                extra[key] = dest_rel; continue
            src = next((r for r in fl if r.endswith((".pptx", ".docx"))), None)
            if src and office and ppm:
                with tempfile.TemporaryDirectory() as td:
                    subprocess.run([office, "--headless", "--convert-to", "pdf", "--outdir", td, os.path.join(root, src)],
                                   check=True, capture_output=True, timeout=180)
                    pdf = glob.glob(os.path.join(td, "*.pdf"))[0]
                    subprocess.run([ppm, "-png", "-r", "72" if src.endswith(".pptx") else "50", pdf, os.path.join(td, "p")], check=True, capture_output=True, timeout=120)
                    pages = sorted(glob.glob(os.path.join(td, "p*.png")))
                    if contact_sheet(pages, dest, cols=3 if src.endswith(".pptx") else 2): extra[key] = dest_rel
            elif any(r.endswith(".dxf") for r in fl):
                import ezdxf, matplotlib; matplotlib.use("Agg")
                from ezdxf.addons.drawing import matplotlib as dm
                doc = ezdxf.readfile(os.path.join(root, next(r for r in fl if r.endswith(".dxf"))))
                os.makedirs(os.path.dirname(dest), exist_ok=True); dm.qsave(doc.modelspace(), dest, bg="#FFFFFF", dpi=150)
                extra[key] = dest_rel
        except Exception as e:
            print("review preview skipped:", key, e)
    return extra

def pattern_rx(p):
    """Manifest paths use shell-ish patterns: {a,b}, *, 'x.png/.svg' and 'a / b'. Turn one into a regex over file paths.
    A pattern also matches the same artwork's companions (-cmyk.pdf, -preview.png)."""
    parts = [x.strip() for x in p.split(" / ")]
    base_dir = parts[0].rsplit("/", 1)[0] + "/" if "/" in parts[0] else ""
    alts = []
    for i, part in enumerate(parts):
        if i and "/" not in part: part = base_dir + part
        m = re.match(r"(.*?)((?:\.\w+)(?:/\.\w+)*)$", part) if not part.endswith("/") else None
        stem, exts = (m.group(1), [e.lstrip("/.") for e in re.findall(r"\.\w+", m.group(2))]) if m and "/" not in m.group(2).replace("/.", "") else (part, [])
        rx = re.escape(stem).replace(r"\*", "[^/]*")
        rx = re.sub(r"\\\{([^}]*)\\\}", lambda g: "(?:" + "|".join(re.escape(x) for x in g.group(1).replace("\\", "").split(",")) + ")", rx)
        if part.endswith("/"): rx += ".*"
        else: rx += r"(?:-cmyk|-preview(?:@\dx)?)?\.(?:" + ("|".join(exts + ["png"]) if exts else r"[\w.]+") + ")"
        alts.append(rx)
    return re.compile("|".join(f"(?:{a})" for a in alts))

def section_of(rel):
    parts = rel.split("/")
    if len(parts) == 1: return "(root)"
    if parts[0] == "kit": return "kit" if len(parts) == 2 else f"kit/{parts[1]}"
    return parts[0]

def family(rel):
    d, n = os.path.split(rel)
    stem, ext = os.path.splitext(n)
    if n.endswith(".kicad_mod"): stem, ext = n[:-10], ".kicad_mod"
    d = re.sub(r"/(svg|pdf|png)(?=/|$)", "", "/" + d).lstrip("/") if d else d
    prev = None
    while prev != stem: prev, stem = stem, SIZE_SUFFIX.sub("", stem)
    if ext in {".md", ".json", ".sh", ".h", ".xbm", ".ans", ".txt", ".kicad_mod", ".py", ".rs", ".c", ".html", ".ts", ".FCMacro", ""} and not rel.startswith("kit/embedded"):
        stem = n                                  # text/code files are their own items (except boot logos, grouped by display)
    return f"{d}/{stem}" if d else stem

def ansi_html(s):
    out, fg, bg, bold, pos = [], None, None, False, 0
    def span(t):
        if not t: return
        st = (f"color:rgb({fg});" if fg else "") + (f"background:rgb({bg});" if bg else "") + ("font-weight:700;" if bold else "")
        out.append(f'<span style="{st}">{html.escape(t)}</span>' if st else html.escape(t))
    for m in ANSI.finditer(s):
        span(s[pos:m.start()]); pos = m.end()
        codes = [c for c in m.group(1).split(";") if c != ""] or ["0"]; i = 0
        while i < len(codes):
            c = codes[i]
            if c == "0": fg = bg = None; bold = False
            elif c == "1": bold = True
            elif c == "39": fg = None
            elif c == "49": bg = None
            elif c in ("38", "48") and i + 4 < len(codes) + 0 and codes[i + 1] == "2":
                rgb = ",".join(codes[i + 2:i + 5]); i += 4
                if c == "38": fg = rgb
                else: bg = rgb
            i += 1
    span(s[pos:])
    return "".join(out)

SIG_TOL = 15          # max gray-level difference (0-255) between 32 x 32 signatures that still counts as "the same picture"
                      # (used only when the pictures were rendered by a different rsvg/machine than when you decided)
def renderer_id():
    """Which rasterizer made the pictures (rsvg-convert version + platform). Decisions remember it; a different one means a
    rebuild on another machine, where pixel hashes change without the art changing."""
    import platform
    try: v = subprocess.run(["rsvg-convert", "--version"], capture_output=True, text=True, timeout=10).stdout.strip().split()[-1]
    except Exception: v = "?"
    return f"rsvg {v} · {platform.system()} {platform.machine()}"

def png_sig(p):
    """Coarse picture signature: 32 x 32 gray levels over mid gray, as hex. Measured October 2026: two renders of the same art
    on different machines (rsvg 2.52 vs 2.6x) differ by at most 11 levels in any cell; changing one word of small text
    (a tagline, a job title, an email) moves some cell by 19-31. SIG_TOL sits between the two."""
    with Image.open(p) as im:
        im.draft("RGBA", (512, 512)); im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
        return bg.convert("L").resize((32, 32), Image.BOX).tobytes().hex()

def phash_png(p):
    with Image.open(p) as im:
        im.draft("RGBA", (128, 128))
        return hashlib.sha1(im.convert("RGBA").resize((48, 48)).tobytes()).hexdigest()

def collect():
    root = build.OUT; files = []
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for n in sorted(fn):
            rel = os.path.relpath(os.path.join(dp, n), root).replace(os.sep, "/")
            if rel in SKIP or rel.startswith(SKIP_DIRS) or n == ".DS_Store" or n.startswith(".office"): continue
            files.append(rel)
    fams = {}
    for rel in files: fams.setdefault(family(rel), []).append(rel)
    man = kit.MANIFEST
    if not man:                                   # run on its own (python3 kit_review.py): use the last build's manifest
        try:
            with open(os.path.join(os.path.dirname(build.OUT), ".kit-manifest.json")) as fh: man = json.load(fh)
        except (OSError, ValueError): man = []
    manifest = [(pattern_rx(p), what, use) for p, g, what, size, use in sorted(man, key=lambda e: -len(e[0]))]
    extra = make_previews(fams)
    items = []
    for key, fl in fams.items():
        absf = {r: os.path.join(root, r) for r in fl}
        info, flags, h = {}, [], hashlib.sha1()
        for r in fl:
            p = absf[r]; ext = os.path.splitext(r)[1].lower(); sz = os.path.getsize(p); info[r] = {"bytes": sz}
            if sz == 0: flags.append(f"{os.path.basename(r)} is empty")
            if ext == ".png":
                with Image.open(p) as im: w, hh = im.size
                info[r]["px"] = [w, hh]
                m = DIMS.search(os.path.basename(r))
                if m and "preview" not in r and "/msix/" not in r:     # MSIX names are Windows' (Square44x44Logo.scale-200 is 88 px)
                    W, H = int(m.group(1)), int(m.group(2)); sc = 2 if "@2x" in r else 4 if "@4x" in r else 1
                    if (w, hh) != (W * sc, H * sc): flags.append(f"{os.path.basename(r)} is {w}×{hh}, name says {W}×{H}" + (f" @{sc}x" if sc > 1 else ""))
                h.update(phash_png(p).encode())
            elif ext not in NO_HASH and sz < 4_000_000:
                with open(p, "rb") as fh: b = fh.read()
                h.update(b)
                if ext in TEXT_EXT:
                    t = b.decode("utf-8", "replace")
                    for mm in sorted(set(PLACEHOLDER.findall(t))): flags.append(f"{os.path.basename(r)} contains “{mm}”")
                    if ext == ".svg":
                        try: ET.fromstring(b)
                        except ET.ParseError as e: flags.append(f"{os.path.basename(r)} SVG doesn't parse: {e}")
                    if ext in (".json", ".webmanifest"):
                        try: json.loads(t)
                        except ValueError as e: flags.append(f"{os.path.basename(r)} JSON doesn't parse: {e}")
        # preview
        pngs = [r for r in fl if r.endswith(".png")]
        prev = ([r for r in pngs if "-preview" in r] + [r for r in fl if r.endswith(".svg")]
                + sorted([r for r in pngs if info[r]["bytes"] < 3_000_000], key=lambda r: -info[r]["px"][0] * info[r]["px"][1])
                + sorted(pngs, key=lambda r: info[r]["bytes"]) + [r for r in fl if r.endswith((".gif", ".jpg"))])
        if key in extra and (not prev or key.startswith(PREFER_EXTRA)): prev = [extra[key]]
        kind, body = "none", ""
        if prev: kind, body = "img", prev[0]
        elif any(r.endswith(".mp4") for r in fl): kind, body = "video", next(r for r in fl if r.endswith(".mp4"))
        elif any(r.endswith(".webm") for r in fl): kind, body = "video", next(r for r in fl if r.endswith(".webm"))
        elif len(fl) == 1 and fl[0].endswith(".html") and re.search(r"<body|<html", open(absf[fl[0]], encoding="utf-8", errors="replace").read(4000), re.I):
            kind, body = "frame", fl[0]
        else:
            txt = [r for r in fl if os.path.splitext(r)[1].lower() in TEXT_EXT and info[r]["bytes"] < 400_000]
            if txt:
                with open(absf[txt[0]], encoding="utf-8", errors="replace") as fh: lines = fh.read().splitlines()
                more = f"\n… {len(lines) - 70} more lines" if len(lines) > 70 else ""
                kind = "ansi" if txt[0].endswith(".ans") else "text"
                snippet = "\n".join(l if kind == "ansi" else l[:160] for l in lines[:70])
                body = (ansi_html(snippet) if kind == "ansi" else html.escape(snippet)) + html.escape(more)
        desc = ""
        for rx, what, use in manifest:
            if any(rx.fullmatch(r) or rx.fullmatch(r.rstrip("/").rsplit("/", 1)[0] + "/") for r in fl):
                desc = what + (f" · Use: {use}" if use else ""); break
        if not desc:
            desc = next((v for k, v in DIR_DESC if fl[0].startswith(k)), "") or next(
                (re.sub(r"<[^>]+>", "", html.unescape(v)) for k, v in kit.GROUP_DIRS if fl[0].startswith(k)), "")
        dark = bool(re.search(r"-white|twotone-on-dark|monochrome|watermark|-dark(?!-)|-dark\b|tshirt-.*-(white|twotone-on-dark)|-colou?r\b|^logo/fusion-space-mark$|^logo/mark/fusion-space-mark$|wordmark-color", key))
        sig = ""                                  # picture signature: the preview PNG, else the item's largest PNG, else its SVG rendered
        try:
            pick = body if kind == "img" and body.endswith(".png") and body in absf else \
                   next(iter(sorted(pngs, key=lambda r: -info[r]["px"][0] * info[r]["px"][1])), None)
            if pick: sig = png_sig(absf[pick])
            elif kind == "img" and body.endswith(".svg") and body in absf and shutil.which("rsvg-convert"):
                r_ = subprocess.run(["rsvg-convert", "-w", "512", absf[body]], capture_output=True, timeout=60)
                if r_.returncode == 0: import io as _io; sig = png_sig(_io.BytesIO(r_.stdout))
        except Exception:
            sig = ""
        items.append({"id": key, "section": section_of(fl[0]), "files": fl, "info": info, "flags": flags, "hash": h.hexdigest()[:12], "sig": sig,
                      "kind": kind, "preview": body, "desc": desc, "dark": dark})
    rank = {s: i for i, s in enumerate(SECTION_ORDER)}
    items.sort(key=lambda it: (rank.get(it["section"], 99), it["id"]))
    return items

# ---------------------------------------------------------------- review scope
# Most of the 400-odd items are the same artwork in another color mode, size, theme or format, settled decisions (the mark,
# the colors, the lockups), or text and settings the build checks by itself. The page opens on the FOCUS set: one
# representative per real design, each showing the items it stands for as thumbnails. A decision on a representative
# applies to the items it covers. Everything else is "covered" (hidden by default, with the reason; still decidable).
# Rules are matched against item ids. An item no rule matches is in focus (so a new output is never skipped silently),
# unless it is text or settings.
DECIDED = ("Settled artwork: the Rev C mark, the gradient and two-tone colors (Oct 2), the horizontal lockup (Oct 3) and the "
           "stacked lockup (kept as is, Oct 3). These are the same artwork in each color mode and file format.")
TEXTY = "Text, code or settings. The build checks it parses and has no placeholders; open it only if you're curious."
COVER = [
    (r"^(logo/(lockup|wordmark|mark)/|logo/fusion-space-|kit/logo/)", DECIDED),
    (r"^kit/web/(safari-pinned-tab|icon-monochrome)$", "One-color mark for a browser slot (settled artwork)."),
    (r"^kit/web/site/public/brand/fusion-space-wordmark$", "A copy of the horizontal lockup for the website (settled artwork)."),
    (r"^color/", "Color data (tokens, CSS, GIMP palette), written from the same values as the guide's color sheet."),
    (r"^kit/index\.html$", "The kit's own browsing page (a tool, not brand output)."),
    (r"^product/tokens/", "Token files for each platform, written from the same values as product/foundations.md; the build measures every color pair and stops if one falls short."),
]
REPS = [   # (representative, [items it covers], why it stands for them)
    ("guide/index.html", [r"^graphics/(mark-construction|fusion-gradient-strip)$"], "shown in the guide"),
    ("logo/favicon/favicon", [r"^kit/web/favicon(-adaptive)?$", r"^kit/web/site/app/(favicon|icon)$"], "the same favicon, copied for the web kit and site"),
    ("logo/favicon/icon", [r"^kit/web/icon$", r"^kit/web/site/public/icon$", r"^kit/web/mstile-150x150$"], "the same rounded icon at web sizes"),
    ("logo/favicon/app-icon", [r"^kit/web/(site/public/)?icon-maskable$"], "the same full-bleed icon"),
    ("logo/favicon/apple-touch-icon", [r"^kit/web/apple-touch-icon$", r"^kit/web/site/app/apple-icon$"], "the same icon, copied"),
    ("templates/freecad/FusionSpace_ANSI-A_Landscape-dark", [r"^templates/freecad/.*-dark$"], "the same dark-page title block at other sheet sizes"),
    ("templates/freecad/FusionSpace_ANSI-A_Landscape", [r"^templates/freecad/"], "the same title block at other sheet sizes"),
    ("kit/apps/ios/AppIcon", [r"^kit/apps/ios/icon-composer/", r"^kit/apps/google-play/play-icon$"], "its layers and the same art for Google Play"),
    ("kit/apps/android/adaptive-masks", [r"^kit/apps/android/ic_launcher_(background|foreground|monochrome)$"], "the layers under the masks shown"),
    ("kit/github/avatar-dark", [r"^kit/github/avatar-light$", r"^kit/social/avatar-(dark|light)$"], "the same avatar, light theme and social copies"),
    ("kit/github/readme-banner-dark", [r"^kit/github/readme-banner(@2x)?-(dark|light)$"], "light theme and 2x"),
    ("kit/github/social-preview-dark", [r"^kit/github/social-preview-light$"], "light theme"),
    ("kit/social/og-image-dark", [r"^kit/social/og-image-light$", r"^kit/web/site/public/og$"], "light theme, and the copy that is the website's link preview"),
    ("kit/social/header-1500x500-dark", [r"^kit/social/(header-1500x500|linkedin-banner|linkedin-company-cover|discord-banner|facebook-cover|youtube-banner)-(dark|light)$"],
     "the same banner layout at each platform's size, dark and light"),
    ("kit/documents/business-card/card-us-front", [r"^kit/documents/business-card/card-eu-front$"], "EU size"),
    ("kit/documents/business-card/card-us-back", [r"^kit/documents/business-card/card-eu-back$"], "EU size"),
    ("kit/documents/email-signature/signature.html", [r"^kit/documents/email-signature/"], "its logo images"),
    ("kit/documents/letterhead/letterhead-letter", [r"^kit/documents/letterhead/"], "A4"),
    ("kit/documents/report-cover/report-cover-letter-dark", [r"^kit/documents/report-cover/"], "light theme and A4"),
    ("kit/documents/report/report-template-letter", [r"^kit/documents/report/"], "A4"),
    ("kit/documents/slides/fusionspace-slides", [r"^kit/documents/slides/"], "its slide images"),
    ("kit/projects/example-vega/social-preview-dark", [r"^kit/projects/example-vega/(?!.*\.(md|json)$)"], "the rest of the example project's images"),
    ("kit/web/site/metadata.ts", [r"^kit/web/site/public/manifest$"], "the web app manifest, with the same name"),
    ("kit/projects/hpr-motor-finder/social-preview-dark", [r"^kit/projects/hpr-motor-finder/(?!.*\.(md|json)$)"], "the rest of this tool's project images"),
    ("kit/projects/charge/social-preview-dark", [r"^kit/projects/charge/(?!.*\.(md|json)$)"], "the rest of this tool's project images"),
    ("kit/projects/window/social-preview-dark", [r"^kit/projects/window/(?!.*\.(md|json)$)"], "the rest of this tool's project images"),
    ("kit/projects/muster/social-preview-dark", [r"^kit/projects/muster/(?!.*\.(md|json)$)"], "the rest of this tool's project images"),
    ("kit/production/stickers/sticker-mark-50mm-dark", [r"^kit/production/stickers/sticker-mark-(50mm-light|75mm-|100mm-)"], "the other mark stickers (same outline)"),
    ("kit/embedded/tft-240x240", [r"^kit/embedded/tft-"], "the other color screens"),
    ("kit/embedded/oled-128x64", [r"^kit/embedded/(oled|epaper)-"], "the other one-color screens"),
    ("kit/pcb/FusionSpace.pretty/FusionSpace_Mark_12mm_F.kicad_mod", [r"^kit/pcb/(?!README)"], "every PCB footprint and image (sizes, sides, copper)"),
    ("kit/software/terminal/preview", [r"^kit/software/terminal/"], "the terminal settings files it previews"),
    ("kit/software/banner/horizontal-72.ans", [r"^kit/software/banner/"], "the other banners and code versions"),
    ("kit/software/docs-theme/docs-preview-dark", [r"^kit/software/docs-theme/(?!README)"], "light theme and the theme files"),
    ("kit/games/splash/splash-1920x1080-dark", [r"^kit/games/splash/"], "light theme and other sizes"),
    ("kit/games/steam/main-capsule-1232x706", [r"^kit/games/steam/"], "the other Steam images (same rules)"),
    ("kit/video/logo-intro-1080p", [r"^kit/video/"], "the other video formats and the watermark"),
    ("kit/wallpapers/desktop-2560x1440-dark", [r"^kit/wallpapers/(desktop|macbook|ultrawide)-"], "the other screen sizes, dark and light"),
    ("kit/wallpapers/phone-1320x2868-dark", [r"^kit/wallpapers/(phone|tablet)-"], "the other phone and tablet sizes"),
    ("kit/wallpapers/call-background-1920x1080-dark", [r"^kit/wallpapers/call-background-"], "light theme"),
    ("kit/merch/tshirt-front-center-color-10in-300dpi", [r"^kit/merch/(tshirt-front-center|tshirt-back|hoodie-front)-"], "the other color modes, the back and the hoodie"),
    ("kit/merch/tshirt-front-chest-color-4in-300dpi", [r"^kit/merch/(tshirt-front-chest|cap-front)-"], "the other color modes and the cap"),
    ("kit/merch/mug-11oz-wrap-dark-300dpi", [r"^kit/merch/mug-"], "white mug"),
    ("kit/merch/poster-mark-18x24in", [r"^kit/merch/poster-mark-"], "A2 and A3"),
    ("kit/merch/poster-construction-18x24in", [r"^kit/merch/poster-construction-"], "A2 and A3"),
    ("kit/production/cut/fusion-space-mark-50mm", [r"^kit/production/cut/"], "the other sizes"),
    ("kit/production/embroidery/fusion-space-mark-75mm-twotone-on-dark", [r"^kit/production/embroidery/"], "the other sizes and backgrounds"),
    ("kit/production/engrave/fusion-space-horizontal", [r"^kit/production/engrave/"], "the mark, stacked and mirrored versions"),
    ("kit/production/rocket-decals/decal-sheet-a4-print-and-cut-dark", [r"^kit/production/rocket-decals/decal-sheet-"], "light and vinyl-cut sheets"),
    ("kit/production/stickers/sticker-mark-circle-50mm-dark", [r"^kit/production/stickers/sticker-mark-(circle|square)-"], "the other circle and square stickers"),
    ("kit/production/stickers/sticker-horizontal-rect-100mm-dark", [r"^kit/production/stickers/sticker-horizontal-rect-"], "light theme"),
    ("kit/production/stickers/sticker-stacked-75mm-dark", [r"^kit/production/stickers/sticker-stacked-"], "the other sizes and theme"),
    # 3D print and CAD: one focus item per design
    ("kit/production/remove-before-flight/remove-before-flight-140x32mm-front", [r"^kit/production/remove-before-flight/"], "the back, the preview and what to order"),
    ("kit/3d-print/fusion-space-remove-before-flight-160mm-2part", [r"^kit/3d-print/fusion-space-remove-before-flight-160mm-2part-"], "the front and back half STLs"),
    ("kit/3d-print/fusion-space-badge-50mm", [r"^kit/3d-print/fusion-space-(keychain|coaster|mark-\d+mm-extruded)"], "the keychain, coaster and extruded marks (same layered build)"),
    ("kit/3d-print/fusion-space-horizontal-130mm-extruded-2mm", [r"^kit/3d-print/fusion-space-(stacked|wordmark)-\d+mm-extruded", r"^kit/3d-print/fusion-space-sign-"], "the stacked lockup, the name and the sign"),
    ("kit/3d-print/fusion-space-fincan-badge-54mm", [r"^kit/3d-print/fusion-space-fincan-badge-"], "the other tube sizes"),
    ("kit/3d-print/fusion-space-nosecone-badge-20mm", [r"^kit/3d-print/fusion-space-nosecone-badge-"], "30 mm"),
    ("kit/3d-print/fusion-space-desk-stand-120mm", [r"^kit/3d-print/fusion-space-desk-stand-120mm-"], "the plaque and foot STLs"),
    ("kit/3d-print/fusion-space-cable-clip-6mm", [r"^kit/3d-print/fusion-space-cable-clip-"], "the 4 and 8 mm clips"),
    ("kit/3d-print/fusion-space-stencil-mark-100mm", [r"^kit/3d-print/fusion-space-stencil-"], "50 mm"),
    ("kit/3d-print/fusion-space-cookie-80mm", [r"^kit/3d-print/fusion-space-cookie-80mm-"], "the cutter and stamp STLs"),
    ("kit/3d-print/sketch/fusion-space-mark-50mm", [r"^kit/3d-print/sketch/"], "the other sketches (mark, lockups and name at every size)"),
    ("kit/3d-print/parametric/FusionSpace_Badge.FCMacro", [r"^kit/3d-print/parametric/"], "the Fusion script"),
    # product system (October 4, 2026): one focus item per reference part; the rule documents are focus text
    ("product/web/previews/specimen-light", [r"^product/web/(index\.html|previews/specimen-dark|fusionspace\.css|tailwind-theme\.css|fonts|mdbook/|README)"],
     "the specimen page itself (dark theme too), the stylesheet, fonts, Tailwind and mdBook themes"),
    ("product/web/previews/home-light", [r"^product/web/(examples/home\.html|previews/home-dark)"], "the page itself and its dark theme"),
    ("product/web/previews/charge-light", [r"^product/web/(examples/charge\.html|previews/charge-phone)"], "the page itself and its phone layout"),
    ("product/web/previews/flight-report-dark", [r"^product/web/(examples/flight-report\.html|previews/(flight-report-light|chart-))"], "the page itself, its light theme and the chart previews"),
    ("product/web/previews/window-field", [r"^product/web/(examples/window\.html|previews/window-phone)"], "the page itself and its phone layout"),
    ("product/icons/preview", [r"^product/icons/"], "every icon as its own SVG and the sprite"),
    ("product/embedded/preview", [r"^product/embedded/"], "each screen at 1:1 and 4x, the TFT screen and the LVGL styles"),
    ("product/hardware/preview", [r"^product/hardware/"], "the KiCad footprints (front and back) and their README"),
    ("product/rockets/preview", [r"^product/rockets/"], "the wraps for every airframe size (SVG, PDF) and their README"),
    ("product/cli/preview", [r"^product/cli/"], "the Rust and Python styles and the sample output"),
    ("product/desktop/linux/hicolor/256x256/apps/co.fusionspace.HprSim", [r"^product/desktop/"], "the Windows ICO and MSIX tiles, the Linux icons and the templates"),
    # phones (October 6, 2026): the screens, the glanceable surfaces, and the code
    ("product/mobile/preview", [r"^product/mobile/(screens/|fonts/|README)"], "every screen as HTML and a 2x PNG on both platforms, the mock-up stylesheet, the Roboto subset and the folder README"),
    ("product/mobile/glance/ios-live-activity", [r"^product/mobile/glance/(index|ios-dynamic-island)"], "the Dynamic Island and Apple Watch Smart Stack, and the page they're drawn on"),
    ("product/mobile/glance/ios-widgets", [r"^product/mobile/glance/android-widget"], "the Android (Glance) widget"),
    ("product/mobile/swiftui/FSComponents", [r"^product/mobile/(swiftui|compose)/"], "the widget and Live Activity in SwiftUI, and the Compose parts and Live Update"),
    # watches (October 6, 2026)
    ("product/watch/preview", [r"^product/watch/(screens/|README)"], "every screen as HTML and a 2x PNG on both platforms, and the mock-up stylesheet"),
    ("product/watch/faces/watchos-complications", [r"^product/watch/faces/"], "the Smart Stack, the Wear OS tiles and face, and the page they're drawn on"),
    ("product/watch/swiftui/FSWatch", [r"^product/watch/(swiftui|compose)/"], "the complications in SwiftUI, and the Wear OS screens, tile and complications in Compose"),
    # real screens (October 6, 2026): simulator and emulator captures of the reference code running
    ("product/mobile/devices/preview", [r"^product/mobile/devices/"], "each capture on its own and the README saying which device and OS"),
    ("product/watch/devices/preview", [r"^product/watch/devices/"], "each capture on its own and the README saying which device and OS"),
]
CORE = (r"^(guide/|product/|logo/|kit/web/|kit/apps/|kit/github/|kit/social/|kit/documents/|README\.md$|kit/projects/(hpr-motor-finder|charge|window|muster)/|kit/production/stickers/sticker-mark-50mm-dark$)")
           # focus items people will see from you first (identity, web, GitHub, social, documents) and the open options;
           # the rest of focus is the discipline kits (screens, PCB, software, games, video, wallpapers, merch, production)
FOCUS_TEXT = {"README.md", "kit/github/profile-README.md", "kit/documents/email-signature/signature.html", "kit/web/site/metadata.ts",
              "kit/3d-print/README.md", "kit/3d-print/parametric/FusionSpace_Badge.FCMacro",
              *(f"product/{d}.md" for d in ("README", "principles", "foundations", "data", "writing", "web", "cli", "mobile", "watch", "desktop", "embedded",
                                             "hardware", "rockets", "review"))}   # text people read: always in focus
KNOWN_FLAGS = ()                    # expected audit flags; others pull an item into focus

def review_scope(items):
    """{id: {"scope": "focus"} | {"scope": "covered", "why": ..., "rep": id-or-""}}; reps get "covers": [ids]."""
    ids = [it["id"] for it in items]; byid = {it["id"]: it for it in items}; sc = {}
    for i in ids:                                  # taken out of the build: covered by the change that removed them
        if byid[i]["section"] == "removed" and ROUND and split_note(NOTES.get(i, ""))[0]:
            sc[i] = {"scope": "focus", "tier": "core" if re.search(CORE, i) else "kit"}; continue      # taken out this round: confirm it
        if byid[i]["section"] == "removed":
            sc[i] = {"scope": "covered", "rep": "", "why": "Renamed or dropped by changes you approved (two-tone file names, current phone and tablet sizes)."}
    for rep, pats, why in REPS:
        if rep not in byid: print(f"WARN review scope: representative {rep!r} is not in the build"); continue
        if rep not in sc: sc[rep] = {"scope": "focus", "covers": [], "covers_why": why}
    for rep, pats, why in REPS:
        if rep not in sc: continue
        for i in ids:
            if i != rep and i not in sc and any(re.search(p, i) for p in pats):
                sc[i] = {"scope": "covered", "rep": rep, "why": f"Covered by {rep}: {why}."}; sc[rep]["covers"].append(i)
    for i in ids:
        if i in sc: continue
        it = byid[i]
        rule = next((why for p, why in COVER if re.search(p, i)), None)
        if rule: sc[i] = {"scope": "covered", "rep": "", "why": rule}
        elif i not in FOCUS_TEXT and it["kind"] in ("text", "ansi", "frame", "none") and not any(f.endswith((".png", ".svg", ".jpg", ".gif", ".mp4", ".pptx", ".docx", ".dxf", ".stl")) for f in it["files"]):
            sc[i] = {"scope": "covered", "rep": "", "why": TEXTY}
        else: sc[i] = {"scope": "focus"}
    for i in ids:
        if sc[i]["scope"] == "focus": sc[i]["tier"] = "core" if re.search(CORE, i) else "kit"
    for i in ids:                                  # an unexpected audit flag always needs eyes
        fl = [f for f in byid[i]["flags"] if not any(k in f for k in KNOWN_FLAGS)]
        if fl and sc[i]["scope"] == "covered": sc[i] = {"scope": "focus", "tier": "core", "why": "Pulled into focus by an audit flag."}
    return sc

def session_notes():
    """Notes from the last working session, keyed by item id. A note starting with "OPTION" marks a choice waiting for
    Neer; "REMOVED" (or any id that no longer exists in the build) marks an item that was taken out."""
    try:
        with open(NOTES_FILE, encoding="utf-8") as fh: d = json.load(fh)
    except (OSError, ValueError): return {}, ""
    label = d.pop("_session", "") if isinstance(d.get("_session"), str) else ""
    global NOTES_BASE, ROUND
    NOTES_BASE = d.get("_base", "") if isinstance(d.get("_base"), str) else ""
    ROUND = d.get("_round", "") if isinstance(d.get("_round"), str) else ""
    return {k: v for k, v in d.items() if isinstance(v, str) and not k.startswith("_")}, label

NOTES = {}           # this build's session notes (review_scope reads them)
ROUND = ""           # "_round" in session-notes.json, e.g. "review round 2": this round's notes are tagged "CHANGED (review round 2): …";
                     # everything older was in front of Neer in an earlier review and folds away
NOTES_BASE = ""      # git commit the session started from ("_base" in session-notes.json): "before" previews come from it
_OLD_META = {}
def before_preview(id_, cur):
    """Copy the item's preview as it was at NOTES_BASE into review-previews/before/ and return its path, or ''.
    Needs git; quietly returns '' without it or when the item is new."""
    if not NOTES_BASE or not shutil.which("git"): return ""
    def show(rel):
        r = subprocess.run(["git", "-C", build.ROOT, "show", f"{NOTES_BASE}:{rel}"], capture_output=True)
        return r.stdout if r.returncode == 0 and r.stdout else None
    if "m" not in _OLD_META:
        raw = show("review.html"); _OLD_META["m"] = {}
        if raw:
            m = re.search(rb'<script id="meta" type="application/json">(.*?)</script>', raw, re.S)
            if m: _OLD_META["m"] = json.loads(m.group(1).decode().replace("<\\/", "</"))
    old_files = _OLD_META["m"].get(id_, {}).get("files", [])
    cands = ([cur] if cur else []) + [r for r in old_files if "-preview" in r and r.endswith(".png")] \
            + [r for r in old_files if r.endswith(".svg")] + [r for r in old_files if r.endswith(".png")]
    if not old_files and not cur: return ""
    for rel in cands:
        if not rel.endswith((".png", ".svg", ".jpg", ".gif")): continue
        if rel.startswith(PREV_DIR + "/") and not _OLD_META["m"].get(id_): continue
        data = show(rel)
        if data:
            dest = f"{PREV_DIR}/before/{id_.replace('/', '__')}{os.path.splitext(rel)[1]}"
            os.makedirs(os.path.join(build.OUT, PREV_DIR, "before"), exist_ok=True)
            with open(os.path.join(build.OUT, dest), "wb") as fh: fh.write(data)
            return dest
    return ""

APPROVED_NOTE = re.compile(r"^(CHANGED|REMOVED) \((color change|lockup proportions|review round 1)|your new wording|your pick")
SHOW_BEFORE = re.compile(r"^CHANGED \(review round 1")       # changes you asked for: show Before/Now so you can check them
def split_note(n):
    """With a round set (ROUND): (this round's notes, earlier notes). Otherwise:
    A session note is several notes joined with "Earlier:" / "Earlier today:". Returns (still to look at, already approved):
    changes you decided or asked for (the color change, the wording, the lockup proportions, review round 1) are approved;
    the rest (changes made without you, additions, fixes, options) still need your eyes."""
    segs = [x.strip() for x in re.split(r"\s*(?:Earlier today: |Earlier: )", n) if x.strip()]
    if ROUND:
        cur = [x for x in segs if any(f"({r}" in x[:60] for r in ROUND.split("|"))]   # several rounds: "a|b"
        return cur, [x for x in segs if x not in cur]
    return [x for x in segs if not APPROVED_NOTE.search(x)], [x for x in segs if APPROVED_NOTE.search(x)]

def is_opt(n):
    """An option still waiting for Neer: this round's note starts with OPTION (older options were answered in a review)."""
    if ROUND: return any(x.startswith("OPTION") for x in split_note(n)[0])
    return n.startswith("OPTION")

def note_html(t):
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return re.sub(r"^(OPTION|REMOVED|ADDED|CHANGED|FIXED|NEW)( \([^)]*\))?:", r"<b>\1\2:</b>", t)

def human(n):
    for u in ("B", "KB", "MB"):
        if n < 1024 or u == "MB": return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024

TODAY_BTN = ('<button data-f="today" title="Focus items with changes made since your last review; changes you already approved don\'t count (c jumps to the next one)">Changed without you<span class="n">%NTF%</span></button>',
             '<button data-f="today" title="Focus items changed this round from your review notes, including changes on the items they cover and items taken out (c jumps to the next one)">Changed this round<span class="n">%NTF%</span></button>')
NOTES_INTRO = ('<p class="intro"><b>Session notes:</b> a blue box is a change made since your last review, worth a look; %NTF% focus items have one, and <b>Changed without you</b> shows just those. Changes you already decided or asked for (the colors, the wording, both lockups, review round 1) are folded away under “changes you already approved”. Orange is <b>an option for you to pick</b> (%NO%), and <b>Options</b> shows just those. Your note on an option can be as short as “A”. Changed items show <b>Before</b> and <b>Now</b> side by side. <b>Grid view</b> (<kbd>g</kbd>) shrinks everything to tiles for quick passes.</p>',
               '<p class="intro"><b>This round (%ROUND%):</b> a blue box says what changed and which of your notes it answers; %NTF% focus items have one, '
               'and <b>Changed this round</b> shows just those (it also counts changes on the items a focus item covers, and items taken out). '
               'Where the artwork changed since your decision, the item also comes back under <b>To review</b> with a dashed edge. Notes from earlier '
               'rounds, which you have already reviewed, are folded away. Changed items show <b>Before</b> and <b>Now</b> side by side. '
               '<b>Grid view</b> (<kbd>g</kbd>) shrinks everything to tiles for quick passes.</p>')

def build_review():
    items = collect()
    notes, session = session_notes()
    NOTES.clear(); NOTES.update(notes)
    ids = {it["id"] for it in items}
    removed = sorted(k for k in notes if k not in ids)
    for r in removed:
        if not notes[r].startswith("REMOVED"): print(f"WARN review: note for {r!r} matches no item (shown under Removed)")
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rem_items = [{"id": r, "section": "removed", "files": [], "info": {}, "flags": [], "hash": "removed", "kind": "removed", "preview": "",
                  "desc": "Keep = agree it's gone. Change = bring it back (say how in the note).", "dark": False} for r in removed]
    SC = review_scope(items + rem_items); BYID = {it["id"]: it for it in items + rem_items}
    def thumbs(id_):
        out = []
        for c in SC[id_].get("covers", []):
            ci = BYID[c]
            if ci["kind"] == "img": out.append(f'<a href="{ci["preview"]}" target="_blank" title="{html.escape(c)}"><img loading="lazy" src="{ci["preview"]}" alt=""></a>')
            else: out.append(f'<a href="{ci["files"][0] if ci["files"] else "#"}" target="_blank" class="tn">{html.escape(c.split("/")[-1])}</a>')
        if not out: return ""
        sib = {}                                   # changes made without you on the covered items, so they aren't missed
        for c in SC[id_].get("covers", []):
            for x in split_note(notes.get(c, ""))[0]: sib.setdefault(x, []).append(c.split("/")[-1])
        sn = "".join(f'<p>{note_html(x)} <span class="on">({", ".join(html.escape(v) for v in vs[:4])}{" …" if len(vs) > 4 else ""})</span></p>' for x, vs in sib.items())
        return (f'<div class="cov"><span class="who">This decision also covers {len(out)} item{"s" if len(out) != 1 else ""}: '
                f'{html.escape(SC[id_]["covers_why"])}</span><div class="thumbs">{"".join(out)}</div>'
                + (f'<div class="sibn"><span class="who">{"Changed this round on those items:" if ROUND else "Changed without you on those items:"}</span>{sn}</div>' if sn else "") + '</div>')
    def today(id_):
        return bool(split_note(notes.get(id_, ""))[0]) or any(split_note(notes.get(c, ""))[0] for c in SC[id_].get("covers", []))
    secs, cur = [], None
    def note_box(id_):
        n = notes.get(id_)
        if not n: return ""
        kind = "opt" if is_opt(n) else "rem" if n.startswith("REMOVED") or id_ in removed else "chg"
        todo, done = split_note(n)
        out = ""
        who = f"Changed this round ({ROUND}), from your notes" if ROUND else "Changed without you, worth a look"
        if todo: out += f'<div class="cn {kind}"><span class="who">{who}</span>{"<br>".join(note_html(x) for x in todo)}</div>'
        dsum = (f'{len(done)} earlier note{"s" if len(done) != 1 else ""}, already reviewed' if ROUND
                else f'{len(done)} change{"s" if len(done) != 1 else ""} you already approved')
        if done: out += (f'<details class="cn done"><summary>{dsum}</summary>'
                         + "".join(f"<p>{note_html(x)}</p>" for x in done) + "</details>")
        return out
    def card(it):
        files = "".join(f'<li><a href="{f}" target="_blank">{html.escape(f.split("/")[-1])}</a> <span>{human(it["info"][f]["bytes"])}'
                        + (f' · {it["info"][f]["px"][0]}×{it["info"][f]["px"][1]}' if "px" in it["info"][f] else "") + "</span></li>" for f in it["files"])
        td_, dn_ = split_note(notes.get(it["id"], ""))
        want_before = it["id"] in notes and (bool(td_) or any(SHOW_BEFORE.search(x) for x in dn_) or it["kind"] == "removed")
        bf = before_preview(it["id"], it["preview"] if it["kind"] == "img" else "") if want_before else ""
        if it["kind"] == "img": pv = f'<a href="{it["preview"]}" target="_blank"><img loading="lazy" src="{it["preview"]}" alt=""></a>'
        elif it["kind"] == "video": pv = f'<video src="{it["preview"]}" controls muted loop preload="none"></video>'
        elif it["kind"] == "frame": pv = f'<iframe loading="lazy" src="{it["preview"]}" title="{it["id"]}"></iframe>'
        elif it["kind"] in ("text", "ansi"): pv = f'<pre class="{it["kind"]}">{it["preview"]}</pre>'
        elif it["kind"] == "removed": pv = '<p class="nopv">Taken out of the build this session.</p>'
        else: pv = '<p class="nopv">No preview. Open the file.</p>'
        if bf and it["kind"] == "removed":
            pv = f'<figure class="ba"><a href="{bf}" target="_blank"><img loading="lazy" src="{bf}" alt=""></a><figcaption>As it was (removed)</figcaption></figure>'
        elif bf:
            pv = (f'<div class="ba2"><figure class="ba"><a href="{bf}" target="_blank"><img loading="lazy" src="{bf}" alt=""></a><figcaption>Before</figcaption></figure>'
                  f'<figure class="ba">{pv}<figcaption>Now</figcaption></figure></div>')
        flags = "".join(f'<li>{html.escape(x)}</li>' for x in it["flags"])
        nb = note_box(it["id"]); scp = SC[it["id"]]
        cv = (f'<div class="cn cvd"><span class="who">Covered, no separate review</span>{html.escape(scp["why"])}'
              + (f' <a href="#i-{html.escape(scp["rep"])}">Go to it</a>' if scp.get("rep") else "") + '</div>') if scp["scope"] == "covered" else ""
        return f'''<article class="it" id="i-{html.escape(it["id"])}" data-scope="{scp["scope"]}" data-tier="{scp.get("tier", "")}" data-id="{html.escape(it["id"])}" data-hash="{it["hash"]}" data-flag="{1 if it["flags"] else 0}" data-today="{1 if today(it["id"]) else 0}" data-opt="{1 if is_opt(notes.get(it["id"], "")) else 0}" tabindex="-1">
<div class="pv bg-{"dark" if it["dark"] else "chk"}">{pv}<button class="mini bgb" title="Change background (b)">bg</button></div>
<div class="meta"><h3>{html.escape(it["id"])}</h3>{cv}{nb}{thumbs(it["id"])}{f'<p class="desc">{html.escape(it["desc"])}</p>' if it["desc"] else ""}
{f'<ul class="flags">{flags}</ul>' if flags else ""}<ul class="files">{files}</ul>
<div class="dec"><button data-d="keep">Keep <kbd>1</kbd></button><button data-d="change">Change <kbd>2</kbd></button><button data-d="remove">Remove <kbd>3</kbd></button><span class="st"></span></div>
<textarea placeholder="What should change? (saved automatically)" rows="2"></textarea></div></article>'''
    for it in items:
        if it["section"] != cur:
            if cur is not None: secs.append("</section>")
            cur = it["section"]; n = sum(1 for x in items if x["section"] == cur and SC[x["id"]]["scope"] == "focus")
            secs.append(f'<section data-sec="{cur}" id="s-{cur.replace("/", "-")}"><div class="sh"><h2>{cur}</h2><span class="cnt" data-cnt="{cur}">{n} items</span>'
                        f'<button class="mini" data-keepall="{cur}" title="Mark every undecided item in this section as Keep">Keep the rest of this section</button></div>')
        secs.append(card(it))
    secs.append("</section>")
    if rem_items:
        secs.append(f'<section data-sec="removed" id="s-removed"><div class="sh"><h2>removed this session</h2><span class="cnt" data-cnt="removed">{len(rem_items)} items</span></div>')
        secs += [card(it) for it in rem_items]; secs.append("</section>")
    all_items = items + rem_items
    opts = "".join(f'<option value="s-{s.replace("/", "-")}">{s}</option>' for s in dict.fromkeys(it["section"] for it in all_items))
    meta = json.dumps({it["id"]: {"files": it["files"], "hash": it["hash"], "section": it["section"], "flags": it["flags"],
                                  **({"sig": it["sig"]} if it.get("sig") else {}),
                                  "scope": SC[it["id"]]["scope"], **({"why": SC[it["id"]]["why"]} if SC[it["id"]].get("why") else {}),
                                  **({"rep": SC[it["id"]]["rep"]} if SC[it["id"]].get("rep") else {}),
                                  **({"covers": SC[it["id"]]["covers"]} if SC[it["id"]].get("covers") else {}),
                                  **({"note": notes[it["id"]]} if it["id"] in notes else {})} for it in all_items})
    nfocus = sum(1 for v in SC.values() if v["scope"] == "focus"); ncov = len(SC) - nfocus; ncore = sum(1 for v in SC.values() if v.get("tier") == "core")
    nt_focus = sum(1 for k, v in SC.items() if v["scope"] == "focus" and (split_note(notes.get(k, ""))[0] or any(split_note(notes.get(c, ""))[0] for c in v.get("covers", []))))
    page = PAGE.replace("%TODAYBTN%", TODAY_BTN[bool(ROUND)]).replace("%NOTESINTRO%", NOTES_INTRO[bool(ROUND)].replace("%ROUND%", html.escape(ROUND.replace(" ·", "").replace("|", "; ")))) \
               .replace("%NCORE%", str(ncore)).replace("%NKIT%", str(nfocus - ncore)).replace("%NFOCUS%", str(nfocus)).replace("%NCOV%", str(ncov)).replace("%NTF%", str(nt_focus)).replace("%STAMP%", stamp).replace("%N%", str(len(items))).replace("%NF%", str(sum(len(it["files"]) for it in items))) \
               .replace("%SIGTOL%", str(SIG_TOL)).replace("%RV%", renderer_id()).replace("%NT%", str(len(notes))) \
               .replace("%NO%", str(sum(1 for k, v in notes.items() if is_opt(v) and SC.get(k, {}).get("scope") == "focus"))) \
               .replace("%SESSION%", html.escape(session or "the last session")) \
               .replace("%OPTS%", opts).replace("%BODY%", "\n".join(secs)).replace("%META%", meta.replace("</", "<\\/"))
    build.wr("review.html", page)
    nflag = sum(1 for it in items if it["flags"])
    return {"core": ncore, "focus": nfocus, "covered": ncov, "items": len(items), "files": sum(len(it["files"]) for it in items), "flagged": nflag, "notes": len(notes), "removed": len(removed),
            "notes_without_item": [r for r in removed if not notes[r].startswith("REMOVED")]}

PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FusionSpace review</title><link rel="icon" href="kit/web/favicon.svg">
<style>
:root{--bg:#F3F4F7;--fg:#0B0F1C;--mut:#566079;--rule:#D6DAE4;--card:#fff;--chk:#E6E8EE;--keep:#1F7A4D;--change:#B34F0C;--remove:#B3261E;--ion:#3350D6}
@media (prefers-color-scheme:dark){:root{--bg:#0B0F1C;--fg:#F3F4F7;--mut:#98A1B8;--rule:#2A3248;--card:#141A2B;--chk:#1B2236;--keep:#5BC48A;--change:#DA7C30;--remove:#FF8A80;--ion:#768DF5}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 Archivo,system-ui,sans-serif}
.strip{height:6px;background:linear-gradient(90deg,#DA7C30,#D07D7A 35%,#A188CB 65%,#768DF5)}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--rule);padding:10px 16px}
.hrow{max-width:1400px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center}
h1{font:600 18px 'Cascadia Mono',ui-monospace,monospace;margin:0}
.bar{flex:1 1 200px;height:8px;background:var(--rule);border-radius:4px;overflow:hidden;min-width:120px}.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#DA7C30,#768DF5)}
.stats{font:12px 'Cascadia Mono',ui-monospace,monospace;color:var(--mut)}
button,select{font:13px Archivo,system-ui,sans-serif;color:var(--fg);background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:5px 10px;cursor:pointer}
button:hover{border-color:var(--mut)}.mini{font-size:12px;padding:3px 8px}
.filters button.on{background:var(--fg);color:var(--bg)}
main{max-width:1400px;margin:0 auto;padding:0 16px 80px}
.intro{color:var(--mut);max-width:80ch}.intro b{color:var(--fg)}
.warn{display:none;background:#B34F0C;color:#fff;padding:8px 16px}
.sh{scroll-margin-top:100px;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;border-top:1px solid var(--rule);padding-top:24px;margin-top:24px}
h2{font:600 15px 'Cascadia Mono',ui-monospace,monospace;text-transform:uppercase;letter-spacing:.06em;margin:0}.cnt{color:var(--mut);font-size:13px}
.it{scroll-margin-top:110px;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:16px;background:var(--card);border:1px solid var(--rule);border-left:4px solid var(--rule);padding:12px;margin:12px 0;outline:none}
.it:focus,.it.cur{box-shadow:0 0 0 2px var(--ion)}
.it[data-d=keep]{border-left-color:var(--keep)}.it[data-d=change]{border-left-color:var(--change)}.it[data-d=remove]{border-left-color:var(--remove)}
.it.recheck{border-left-style:dashed}
.pv{position:relative;display:grid;place-items:center;min-height:220px;max-height:420px;overflow:auto;border-radius:4px}
.pv img{max-width:100%;max-height:400px;display:block}.pv video{max-width:100%;max-height:400px}.pv iframe{width:100%;height:400px;border:0;background:#fff}
.bg-chk{background:repeating-conic-gradient(var(--chk) 0 25%,transparent 0 50%) 0 0/16px 16px}
.bg-dark{background:repeating-conic-gradient(#141A2B 0 25%,#0B0F1C 0 50%) 0 0/16px 16px}
.bg-white{background:#fff}.bg-black{background:#000}
.bgb{position:absolute;right:6px;bottom:6px;opacity:.8}
pre{margin:0;width:100%;align-self:stretch;font:11px/1.35 'Cascadia Mono',ui-monospace,monospace;white-space:pre;overflow:auto;padding:10px;background:var(--bg);color:var(--fg);max-height:400px}
pre.ansi{background:#0B0F1C;color:#F3F4F7;line-height:1.08}
.nopv{color:var(--mut)}
h3{font:600 14px 'Cascadia Mono',ui-monospace,monospace;margin:0 0 4px;overflow-wrap:anywhere}
.desc{margin:0 0 6px;color:var(--mut);font-size:14px}
.flags{margin:0 0 6px;padding:6px 10px 6px 26px;background:rgba(179,79,12,.12);border-radius:4px;font-size:13px}
.files{list-style:none;margin:0 0 8px;padding:0;font:12px 'Cascadia Mono',ui-monospace,monospace;max-height:132px;overflow:auto}.files span{color:var(--mut)}.files a{color:var(--fg)}
.dec{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.dec button[data-d=keep].on{background:var(--keep);color:#fff;border-color:var(--keep)}
.dec button[data-d=change].on{background:var(--change);color:#fff;border-color:var(--change)}
.dec button[data-d=remove].on{background:var(--remove);color:#fff;border-color:var(--remove)}
kbd{font:10px 'Cascadia Mono',monospace;opacity:.6}.st{font-size:12px;color:var(--mut)}.st.rc{color:var(--change);font-weight:600}
textarea{width:100%;margin-top:8px;font:14px Archivo,system-ui,sans-serif;color:var(--fg);background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:6px 8px;resize:vertical}
.hidden{display:none!important}
dialog{background:var(--card);color:var(--fg);border:1px solid var(--rule);border-radius:8px;max-width:640px}
#overall{min-height:80px}
.cn{margin:2px 0 8px;padding:8px 10px 8px 12px;border-radius:6px;font-size:14px;line-height:1.45;background:rgba(51,80,214,.10);border-left:4px solid var(--ion)}
.cn.opt{background:rgba(179,79,12,.12);border-left-color:var(--change)}.cn.rem{background:rgba(179,38,30,.10);border-left-color:var(--remove)}
.cn .who{display:block;font:600 11px 'Cascadia Mono',ui-monospace,monospace;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin-bottom:2px}
.cn code,.desc code{font:12px 'Cascadia Mono',ui-monospace,monospace;background:var(--bg);padding:0 3px;border-radius:3px}
.it[data-today="1"] h3::after{content:" ●";color:var(--ion)}.it[data-opt="1"] h3::after{color:var(--change)}
.filters .n{opacity:.7;font-size:11px;margin-left:3px}
.cov{margin:2px 0 8px;padding:6px 8px;border:1px dashed var(--rule);border-radius:6px}.cov .who{display:block;font-size:12px;color:var(--mut);margin-bottom:4px}
.thumbs{display:flex;flex-wrap:wrap;gap:4px}.thumbs a{display:block;background:repeating-conic-gradient(var(--chk) 0 25%,transparent 0 50%) 0 0/10px 10px;border:1px solid var(--rule);border-radius:3px}
.thumbs img{display:block;height:46px;max-width:110px;object-fit:contain}.thumbs a.tn{font:11px 'Cascadia Mono',ui-monospace,monospace;padding:3px 5px;color:var(--fg);text-decoration:none;height:auto}
.sibn{margin-top:6px;font-size:13px}.sibn p{margin:3px 0}.sibn .on{color:var(--mut);font-size:12px}
details.cn.done{background:transparent;border-left-color:var(--rule);font-size:13px;color:var(--mut)}details.cn.done summary{cursor:pointer}details.cn.done p{margin:4px 0}
.cn.cvd{background:rgba(152,161,184,.14);border-left-color:var(--mut)}.it[data-scope=covered]{opacity:.85}
.ba2{display:grid;grid-template-columns:1fr 1fr;gap:8px;width:100%;align-self:stretch}.ba{margin:0;display:grid;place-items:center;align-content:center;gap:4px;min-width:0}
.ba img{max-width:100%;max-height:360px}.ba figcaption{font:600 11px 'Cascadia Mono',ui-monospace,monospace;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);background:var(--card);padding:1px 6px;border-radius:3px}
.ba2 pre{max-height:360px}
/* grid view: many small tiles, for quick passes over sections you're happy with */
body.grid section[data-sec]{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px;align-items:start}
body.grid .sh{grid-column:1/-1}
body.grid .it{grid-template-columns:1fr;gap:6px;margin:0;padding:8px}
body.grid .pv{min-height:120px;max-height:170px}
body.grid .pv img,body.grid .ba img{max-height:150px}body.grid .pv pre{max-height:160px;font-size:9px}
body.grid .desc,body.grid .files,body.grid .flags,body.grid .it textarea,body.grid .cn .who,body.grid .ba figcaption{display:none}
body.grid .cn{font-size:12px;padding:4px 6px;margin:0 0 4px;max-height:3.2em;overflow:hidden}
body.grid h3{font-size:11px}body.grid .dec button{padding:3px 6px;font-size:11px}body.grid kbd{display:none}
body.grid .it.cur textarea{display:block}
@media (max-width:820px){.it{grid-template-columns:1fr}}
</style></head><body>
<div class="strip"></div><div class="warn" id="warn">This browser isn't saving your progress. Use <b>Export</b> before you close the page, and <b>Import</b> to pick up again.</div>
<header><div class="hrow"><h1>FusionSpace review</h1><div class="bar"><i id="bar"></i></div><span class="stats" id="stats"></span></div>
<div class="hrow" style="margin-top:8px"><span class="filters" id="filters"><button data-f="core" title="What people will see from you first: identity, website, GitHub, social, documents, and the open options">Core<span class="n">%NCORE%</span></button> <button data-f="focus" class="on" title="One item per real design; each shows the items it covers">Focus<span class="n">%NFOCUS%</span></button> <button data-f="todo">To review</button> <button data-f="opt" title="Choices waiting for you: pick one">Options<span class="n">%NO%</span></button> %TODAYBTN% <button data-f="change">Change</button> <button data-f="remove">Remove</button> <button data-f="flag">Flagged</button> <button data-f="covered" title="Items that don't need their own review, with the reason">Covered<span class="n">%NCOV%</span></button> <button data-f="all">All</button></span>
<select id="jump"><option value="">Jump to section…</option>%OPTS%</select>
<button id="next" title="Next item to review (n)">Next to review</button> <button id="gridv" title="Toggle small tiles (g)">Grid view</button>
<span style="flex:1"></span><button id="export">Export review</button><button id="copy">Copy</button><button id="import">Import</button><button id="help">Keys</button><input type="file" id="file" accept=".md,.json,.txt" class="hidden"></div></header>
<main>
<p class="intro"><b>Focus: %NFOCUS% items to look at.</b> The build makes %N% items (%NF% files), but most are the same artwork in another color mode, size, theme or format, settled decisions (the mark, the colors, both lockups), or text and settings the build checks by itself. Each focus item is one real design and shows, under its note, the items it stands for: <b>a decision on it applies to those too</b>. The other %NCOV% are under <b>Covered</b>, each with the reason; you can still open and decide any of them.</p>
<p class="intro"><b>Core</b> (%NCORE%) is the part to do first: the brand identity, website and app icons, GitHub, social images, documents, and the open options. The other %NKIT% focus items are the discipline kits (screens, PCB, software, games, video, wallpapers, merch, production, 3D print), worth a pass before you use them.</p>
<p class="intro">Built %STAMP%. Each item is one piece of artwork in all its formats. Pick <b>Keep</b>, <b>Change</b> or <b>Remove</b>, and write what you want in the box (a note on its own counts as Change). Progress saves in this browser as you go. When you're done, click <b>Export review</b> and keep the downloaded file with your notes. Items with a dashed edge changed since you reviewed them. Click a preview to open it full size.</p>
%NOTESINTRO%
<h2 style="margin-top:16px">Overall notes</h2><textarea id="overall" placeholder="Anything that applies to the whole kit (tone, colors, naming, things that are missing)…"></textarea>
%BODY%
</main>
<dialog id="keys"><h3>Keyboard</h3><p><kbd>j</kbd>/<kbd>k</kbd> next/previous item · <kbd>n</kbd> next item to review · <kbd>1</kbd> Keep · <kbd>2</kbd> Change (jumps to the note) · <kbd>3</kbd> Remove · <kbd>0</kbd> clear · <kbd>b</kbd> change preview background · <kbd>o</kbd> open preview · <kbd>c</kbd> next changed item · <kbd>g</kbd> grid view · <kbd>Esc</kbd> leave the note box</p><button onclick="this.closest('dialog').close()">Close</button></dialog>
<script id="meta" type="application/json">%META%</script>
<script>
const META = JSON.parse(document.getElementById('meta').textContent), KEY = 'fusionspace-review-v1', BUILT = '%STAMP%';
let S = {items: {}, overall: ''}, canSave = true;
try { const raw = localStorage.getItem(KEY); if (raw) S = JSON.parse(raw); localStorage.setItem(KEY + '-t', '1'); } catch (e) { canSave = false; }
if (!canSave) document.getElementById('warn').style.display = 'block';
S.items = S.items || {};
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { document.getElementById('warn').style.display = 'block'; } }
const arts = [...document.querySelectorAll('.it')], byId = {}; arts.forEach(a => byId[a.dataset.id] = a);
const BGS = ['chk', 'dark', 'white', 'black'];
// Changed since the decision? Pictures compare by a coarse signature (so a rebuild on another machine, with slightly different
// anti-aliasing, doesn't ask for a re-check); everything else by its content hash.
function sigDist(a, b) { let m = 0; for (let i = 0; i < a.length; i += 2) m = Math.max(m, Math.abs(parseInt(a.substr(i, 2), 16) - parseInt(b.substr(i, 2), 16))); return m; }
// Same renderer as when you decided: exact hashes (catches even a one-word change in small print). Different renderer (a
// build on another machine): pictures fall back to the tolerant signature, so anti-aliasing noise isn't a "change".
const RENDERER = '%RV%';
function changed(id) { const r = S.items[id], m = META[id]; if (!r || !r.h) return false; if (r.h === m.hash) return false;
  if ((r.rv || '') !== RENDERER && r.s && m.sig && r.s.length === m.sig.length) return sigDist(r.s, m.sig) > %SIGTOL%; return true; }
function stamp(r, id) { r.h = META[id].hash; if (META[id].sig) r.s = META[id].sig; else delete r.s; r.rv = RENDERER; r.t = new Date().toISOString(); }
function status(id) { const r = S.items[id]; if (!r || !r.d) return META[id].scope === 'covered' ? 'covered' : 'todo'; return changed(id) ? 'recheck' : r.d; }
const focusArts = () => arts.filter(a => META[a.dataset.id].scope !== 'covered');
function paint(a) {
  const id = a.dataset.id, r = S.items[id] || {}, st = status(id);
  a.dataset.d = r.d || ''; a.classList.toggle('recheck', st === 'recheck');
  a.querySelectorAll('.dec button').forEach(b => b.classList.toggle('on', b.dataset.d === r.d));
  const s = a.querySelector('.st'); s.textContent = st === 'recheck' ? 'changed since you reviewed it: re-check' : ''; s.classList.toggle('rc', st === 'recheck');
  const ta = a.querySelector('textarea'); if (document.activeElement !== ta) ta.value = r.note || '';
}
function decide(a, d) {
  const id = a.dataset.id, r = S.items[id] || (S.items[id] = {});
  if (d === null || r.d === d && !changed(id)) { delete r.d; } else { r.d = d; stamp(r, id); }
  if (!r.d && !r.note) delete S.items[id];
  save(); paint(a); stats(); applyFilter();
}
function stats() {
  const fa = focusArts(), n = fa.length; let c = {keep: 0, change: 0, remove: 0, todo: 0, recheck: 0, covered: 0};
  fa.forEach(a => c[status(a.dataset.id)]++);
  const done = n - c.todo - c.recheck;
  document.getElementById('bar').style.width = (100 * done / n) + '%';
  document.getElementById('stats').textContent = `${done}/${n} focus items reviewed · ${c.keep} keep · ${c.change} change · ${c.remove} remove` + (c.recheck ? ` · ${c.recheck} re-check` : '');
  document.querySelectorAll('[data-cnt]').forEach(el => { const sec = el.dataset.cnt, list = focusArts().filter(a => META[a.dataset.id].section === sec);
    const left = list.filter(a => ['todo', 'recheck'].includes(status(a.dataset.id))).length; el.textContent = `${list.length} items` + (left ? ` · ${left} to review` : ' · done'); });
}
let filter = 'focus';
function applyFilter() {
  arts.forEach(a => { const st = status(a.dataset.id), foc = a.dataset.scope !== 'covered'; let show = filter === 'all' || filter === 'focus' && foc || filter === 'core' && a.dataset.tier === 'core' || filter === 'covered' && !foc || filter === 'flag' && a.dataset.flag === '1' || filter === 'todo' && foc && (st === 'todo' || st === 'recheck') || filter === 'today' && foc && a.dataset.today === '1' || filter === 'opt' && foc && a.dataset.opt === '1' || filter === st;
    a.classList.toggle('hidden', !show); });
  document.querySelectorAll('section[data-sec]').forEach(s => s.classList.toggle('hidden', !s.querySelector('.it:not(.hidden)')));
}
arts.forEach(a => {
  paint(a);
  a.querySelectorAll('.dec button').forEach(b => b.onclick = () => { decide(a, b.dataset.d); if (b.dataset.d === 'change') a.querySelector('textarea').focus(); });
  const ta = a.querySelector('textarea');
  ta.oninput = () => { const id = a.dataset.id, r = S.items[id] || (S.items[id] = {}); r.note = ta.value;
    if (ta.value.trim() && !r.d) { r.d = 'change'; stamp(r, id); paint(a); stats(); }
    if (!r.d && !r.note) delete S.items[id]; save(); };
  ta.onfocus = () => setCur(a);
  a.querySelector('.bgb').onclick = () => cycleBg(a);
  a.onclick = e => { if (!e.target.closest('button,textarea,a,video')) setCur(a); };
});
function cycleBg(a) { const pv = a.querySelector('.pv'); const i = BGS.findIndex(b => pv.classList.contains('bg-' + b)); pv.classList.remove('bg-' + BGS[i]); pv.classList.add('bg-' + BGS[(i + 1) % BGS.length]); }
const ov = document.getElementById('overall'); ov.value = S.overall || ''; ov.oninput = () => { S.overall = ov.value; save(); };
document.querySelectorAll('#filters button').forEach(b => b.onclick = () => { filter = b.dataset.f; document.querySelectorAll('#filters button').forEach(x => x.classList.toggle('on', x === b)); applyFilter(); });
document.getElementById('jump').onchange = e => { if (e.target.value) document.getElementById(e.target.value).scrollIntoView(); e.target.value = ''; };
document.querySelectorAll('[data-keepall]').forEach(b => b.onclick = () => { const sec = b.dataset.keepall;
  arts.filter(a => META[a.dataset.id].section === sec && !a.classList.contains('hidden') && ['todo', 'recheck'].includes(status(a.dataset.id))).forEach(a => {
    const id = a.dataset.id, r = S.items[id] || (S.items[id] = {}); if (status(id) === 'recheck' && r.d !== 'keep') return; r.d = 'keep'; stamp(r, id); paint(a); });
  save(); stats(); applyFilter(); });
let cur = null;
function setCur(a) { if (cur) cur.classList.remove('cur'); cur = a; if (a) a.classList.add('cur'); }
function visible() { return arts.filter(a => !a.classList.contains('hidden')); }
function move(step) { const v = visible(); if (!v.length) return; let i = cur ? v.indexOf(cur) : -1; i = Math.max(0, Math.min(v.length - 1, i + step)); setCur(v[i]); v[i].scrollIntoView({block: 'center'}); }
function nextTodo() { const v = visible(), start = cur ? v.indexOf(cur) + 1 : 0; const order = v.slice(start).concat(v.slice(0, start));
  const a = order.find(a => ['todo', 'recheck'].includes(status(a.dataset.id))); if (a) { setCur(a); a.scrollIntoView({block: 'center'}); } }
document.getElementById('next').onclick = nextTodo;
function toggleGrid() { const on = document.body.classList.toggle('grid'); try { localStorage.setItem(KEY + '-grid', on ? '1' : ''); } catch (e) {} if (cur) cur.scrollIntoView({block: 'center'}); }
document.getElementById('gridv').onclick = toggleGrid;
try { if (localStorage.getItem(KEY + '-grid')) document.body.classList.add('grid'); } catch (e) {}
function nextToday() { const v = arts.filter(a => a.dataset.today === '1' && a.dataset.scope !== 'covered' && !a.classList.contains('hidden')), start = cur ? v.indexOf(cur) + 1 : 0; const a = v[start] || v[0]; if (a) { setCur(a); a.scrollIntoView({block: 'center'}); } }
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'TEXTAREA') { if (e.key === 'Escape') e.target.blur(); return; }
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key;
  if (k === 'j') move(1); else if (k === 'k') move(-1); else if (k === 'n') nextTodo();
  else if (cur && k === '1') decide(cur, 'keep'); else if (cur && k === '2') { decide(cur, 'change'); cur.querySelector('textarea').focus(); e.preventDefault(); }
  else if (cur && k === '3') decide(cur, 'remove'); else if (cur && k === '0') decide(cur, null);
  else if (cur && k === 'b') cycleBg(cur); else if (cur && k === 'o') { const l = cur.querySelector('.pv a, .files a'); if (l) window.open(l.href, '_blank'); }
  else if (k === 'c') nextToday(); else if (k === 'g') toggleGrid();
  else if (k === '?') document.getElementById('keys').showModal();
});
document.getElementById('help').onclick = () => document.getElementById('keys').showModal();
function report() {
  const d = new Date(), lines = [`# FusionSpace review — ${d.toISOString().slice(0, 10)}`, '', `Build reviewed: ${BUILT}. Exported ${d.toLocaleString()}.`, ''];
  const groups = {change: [], remove: [], keep: [], recheck: [], todo: [], covered: []};
  Object.keys(META).forEach(id => groups[status(id)].push(id));
  const nf = Object.keys(META).filter(id => META[id].scope !== 'covered').length;
  lines.push(`**${nf - groups.todo.length - groups.recheck.length} of ${nf} focus items reviewed** · ${groups.keep.length} keep · ${groups.change.length} change · ${groups.remove.length} remove · ${groups.recheck.length} need a re-check · ${groups.todo.length} not reviewed · ${groups.covered.length} covered (no separate review)`, '',
    'A decision on a focus item applies to the items it covers (listed under it).', '');
  if ((S.overall || '').trim()) lines.push('## Overall notes', '', S.overall.trim(), '');
  const item = id => { const r = S.items[id] || {}; const out = [`### ${id}`, '', `Files: ${META[id].files.map(f => '`' + f + '`').join(', ')}`];
    if (META[id].covers) out.push('', 'Covers: ' + META[id].covers.map(c => '`' + c + '`').join(', '));
    if (META[id].note) out.push('', 'Session note: ' + META[id].note);
    if (r.note && r.note.trim()) out.push('', '> ' + r.note.trim().replace(/\n/g, '\n> ')); out.push(''); return out.join('\n'); };
  if (groups.change.length) lines.push(`## Change (${groups.change.length})`, '', ...groups.change.map(item));
  if (groups.remove.length) lines.push(`## Remove (${groups.remove.length})`, '', ...groups.remove.map(item));
  if (groups.recheck.length) lines.push(`## Changed since reviewed, not re-checked (${groups.recheck.length})`, '', ...groups.recheck.map(id => `- \`${id}\` (was: ${S.items[id].d})`), '');
  const notedKeep = groups.keep.filter(id => (S.items[id].note || '').trim());
  if (notedKeep.length) lines.push(`## Keep, with a note (${notedKeep.length})`, '', ...notedKeep.map(item));
  if (groups.keep.length) lines.push(`## Keep (${groups.keep.length})`, '', groups.keep.map(id => '`' + id + '`').join(' · '), '');
  if (groups.todo.length) lines.push(`## Not reviewed yet (${groups.todo.length})`, '', groups.todo.map(id => '`' + id + '`').join(' · '), '');
  if (groups.covered.length) { const by = {}; groups.covered.forEach(id => { const k = META[id].rep ? 'Covered by `' + META[id].rep + '`' : META[id].why; (by[k] = by[k] || []).push(id); });
    lines.push(`## Covered, no separate review (${groups.covered.length})`, '', ...Object.entries(by).map(([k, v]) => `- ${k}: ${v.map(id => '`' + id + '`').join(' · ')}`), ''); }
  lines.push('## Data', '', 'Machine-readable copy of the review (Import this file into review.html to continue).', '', '```json', JSON.stringify({built: BUILT, overall: S.overall || '', items: S.items}, null, 1), '```', '');
  return lines.join('\n');
}
document.getElementById('export').onclick = () => { const b = new Blob([report()], {type: 'text/markdown'}); const a = document.createElement('a');
  a.href = URL.createObjectURL(b); a.download = `fusionspace-review-${new Date().toISOString().slice(0, 10)}.md`; document.body.appendChild(a); a.click(); a.remove(); };
document.getElementById('copy').onclick = async e => { try { await navigator.clipboard.writeText(report()); e.target.textContent = 'Copied'; } catch (err) { e.target.textContent = 'Copy failed: use Export'; } setTimeout(() => e.target.textContent = 'Copy', 2000); };
document.getElementById('import').onclick = () => document.getElementById('file').click();
document.getElementById('file').onchange = async e => { const f = e.target.files[0]; if (!f) return; const t = await f.text(); const m = t.match(/```json\n([\s\S]*?)\n```/);
  try { const j = JSON.parse(m ? m[1] : t); S = {items: j.items || {}, overall: j.overall || ''}; save(); ov.value = S.overall; arts.forEach(paint); stats(); applyFilter(); alert('Review imported.'); }
  catch (err) { alert('That file has no review data in it.'); } e.target.value = ''; };
stats(); applyFilter();
</script></body></html>
"""

if __name__ == "__main__":
    print(build_review())
