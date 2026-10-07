"""FusionSpace per-product images: one command makes a product's social preview, README banners, OG image, YouTube
thumbnail, title slide, report cover and a starter README, in dark and light.

    python3 tools/build/project.py --star Vega --tag EMB --desc "Flight software for a two-stage sounding rocket."
    python3 tools/build/project.py --star Achernar --name Perihelion --tag GAME --kind Game --desc "A small orbital-mechanics puzzle game." --out ~/code/achernar/.github/brand

Options: --star (the internal name: an IAU star name, see tools/callsign; its constellation is the project), --name (the
external name, default the star's), --code (default FS-<STAR>), --tag (discipline tag, see kit.DISCIPLINES), --kind (the
noun after the code, default Product), --number (default 001), --desc (one line), --out (default projects/<star>).
Needs the same tools as the build (rsvg-convert, fonts)."""
import argparse, os, re, json, subprocess, sys, importlib.util, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build, kit
from kit import theme, background, text, layer, svg_open, art_horizontal, art_mark, gradient, f, TAGLINE
from build import VOID, PAPER

MONO_EM = 1200 / 2048          # Cascadia Mono advance width per em
def fit_mono(s, size, max_w):
    w = len(s) * MONO_EM * size
    return size if w <= max_w else size * max_w / w

def wrap(s, n):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    return lines

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

SANS_EM = 0.485                # Archivo's average advance per em, for wrapping estimates
def fit_desc(desc, max_w, sizes, max_lines, room):
    """The largest size at which the whole description fits in max_lines lines and in `room` px of height (lines at 1.3 x
    the size). Never truncates: returns None when nothing fits, and the caller asks for a shorter description."""
    for size in sizes:
        lines = wrap(desc, max(8, int(max_w / (SANS_EM * size))))
        if len(lines) <= max_lines and len(lines) * size * 1.3 <= room: return size, lines
    return None

def too_long(where, desc, max_chars):
    raise SystemExit(f"project.py: the description doesn't fit the {where} at any allowed size ({len(desc)} characters). "
                     f"Shorten --desc to about {max_chars} characters; images never cut text off.")

def callsign():
    """source/callsign/callsign.py, for the IAU star list and the codes."""
    spec = importlib.util.spec_from_file_location("callsign_src", os.path.join(build.SRC, "callsign", "callsign.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def stars():
    return json.load(open(os.path.join(build.SRC, "callsign", "iau-star-names.json"), encoding="utf-8"))["stars"]

def find_star(m, name):
    """The IAU star with this name (any case, with or without accents), or None."""
    return next((r for r in stars() if m.fold(r[0]) == m.fold(name.strip())), None)

class Project:
    """A product's brand files. With a star, the star is the internal name and its constellation the project; the name
    (the external one) defaults to the star's. Without one (the tools from before the naming rule) only the name is used."""
    def __init__(self, name=None, code=None, tag=None, kind=None, number="001", desc="", star=None):
        self.star = self.constellation = self.project = self.project_code = None
        if star:
            m = callsign(); r = find_star(m, star)
            if not r:
                raise SystemExit(f"{star} isn't an IAU star name; internal names are always stars (python3 tools/callsign/callsign.py list)")
            self.star, abbr = r[0], r[3]
            self.constellation = m.CONSTELLATIONS[abbr]; self.project = abbr; self.project_code = m.project_code(abbr)
            code = code or m.code(self.star)
            other = name and find_star(m, name)
            if other and other[0] != self.star:
                raise SystemExit(f"{name} is another star's name; an external name is the product's own star or a name that isn't a star")
        name = name or self.star
        assert name, "a star or a name"
        self.name = name; self.code = code or "FS-" + re.sub(r"[^A-Z0-9]+", "-", name.upper()).strip("-")
        self.tag = tag; self.number = number; self.desc = desc
        tags = dict(kit.DISCIPLINES)
        self.kind = kind or "Product"
        self.discipline = tags.get(tag, "") if tag else ""
        parts = [self.code] + ([tag] if tag else []) + [f"{self.kind.upper()} {number}"]
        self.designation = " · ".join(parts)
        self.slug = self.code[3:].lower() if self.star else re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def card(p, w, h, dark, big=None, lockup_h=None, mark_side=True):
    """Social-card layout: small lockup top left, designation, project name, description, mark on the right."""
    t = theme(dark); u = h / 640.0
    bdefs, bg = background(w, h, dark, "pb", cell=80 * u, strip="bottom", strip_h=12 * u)
    a = art_horizontal(); lh = (lockup_h or 54) * u; k = lh / a.h
    ldefs, lg = a.place(t["mode"], "pl", 80 * u, 72 * u, k)
    lockup_w = a.w * k
    defs = bdefs + ldefs; brand = lg
    x = 80 * u; maxw = w - 160 * u
    if mark_side:
        m = art_mark(200); km = 0.56 * h / m.h; mx = w - m.w * km - 70 * u
        mdefs, mg = m.place(t["mode"], "pm", mx, (h - m.h * km) / 2 + 20 * u, km)
        defs += mdefs; brand += mg; maxw = mx - x - 40 * u
    size = fit_mono(p.name, big or 140 * u, maxw)
    tx = text(x, 300 * u, esc(p.designation), min(24 * u, maxw / (len(p.designation) * (MONO_EM + 0.06))), t["label"], label="Designation", spacing=1.5 * u)
    tx += text(x - 6 * u, 300 * u + 30 * u + size * 0.82, esc(p.name), size, t["text"], weight=600, label="Project name")
    y = 300 * u + 30 * u + size * 0.82 + 62 * u
    got = fit_desc(p.desc, maxw, [z * u for z in (32, 29, 26, 24)], 4, h - 56 * u - (y - 32 * u)) if p.desc else (32 * u, [])
    if got is None: too_long("social preview", p.desc, 150)
    dsize, lines = got
    for i, line in enumerate(lines):
        tx += text(x, y + i * dsize * 1.3, esc(line), dsize, t["muted"], family="sans", label=f"Description line {i + 1}")
    s = svg_open(w, h, f"{p.name} · FusionSpace", page=t["bg"])
    s += f'<defs id="defs">{defs}</defs>\n' + bg + layer("Brand", brand + "\n") + layer("Text (edit me)", tx) + "</svg>\n"
    return s

def banner(p, w, h, dark):
    """README banner: name and designation left, mark right."""
    t = theme(dark); u = h / 320.0
    bdefs, bg = background(w, h, dark, "rb", cell=80 * u, strip="bottom", strip_h=8 * u)
    m = art_mark(200); km = 0.64 * h / m.h
    mdefs, mg = m.place(t["mode"], "rm", w - m.w * km - 80 * u, (h - m.h * km) / 2 - 4 * u, km)
    size = fit_mono(p.name, 92 * u, w * 0.6)
    tx = text(80 * u, 118 * u, esc(p.designation), 18 * u, t["label"], label="Designation", spacing=1.2 * u)
    tx += text(76 * u, 118 * u + 22 * u + size * 0.8, esc(p.name), size, t["text"], weight=600, label="Project name")
    if p.desc:
        y0 = 118 * u + 22 * u + size * 0.8 + 44 * u
        got = fit_desc(p.desc, w * 0.6, [z * u for z in (21, 19, 17)], 2, h - 30 * u - (y0 - 21 * u))
        if got is None: too_long("README banner", p.desc, 120)
        dsize, ls = got
        for i, line in enumerate(ls):
            tx += text(80 * u, y0 + i * dsize * 1.3, esc(line), dsize, t["muted"], family="sans", label=f"Description line {i + 1}")
    s = svg_open(w, h, f"{p.name} README banner", page=t["bg"])
    s += f'<defs id="defs">{bdefs}{mdefs}</defs>\n' + bg + layer("Brand", mg + "\n") + layer("Text (edit me)", tx) + "</svg>\n"
    return s

def write(outdir, rel, svg, w, h):
    fp = os.path.join(outdir, rel); os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, "w", encoding="utf-8").write(svg)
    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), fp, "-o", fp[:-4] + ".png"], check=True)

def make(p, outdir):
    for dark in (True, False):
        tone = "dark" if dark else "light"
        write(outdir, f"social-preview-{tone}.svg", card(p, 1280, 640, dark), 1280, 640)
        write(outdir, f"og-image-{tone}.svg", card(p, 1200, 630, dark), 1200, 630)
        write(outdir, f"readme-banner-{tone}.svg", banner(p, 1280, 320, dark), 1280, 320)
        write(outdir, f"readme-banner-{tone}@2x.svg", banner(p, 2560, 640, dark), 2560, 640)
        write(outdir, f"title-slide-{tone}.svg", card(p, 1920, 1080, dark), 1920, 1080)
    write(outdir, "youtube-thumbnail.svg", card(p, 1280, 720, True, mark_side=True), 1280, 720)
    for page in ("letter", "a4"):
        for dark in (True, False):
            tone = "dark" if dark else "light"
            fp = os.path.join(outdir, f"report-cover-{page}-{tone}.svg")
            open(fp, "w", encoding="utf-8").write(kit.cover_svg(page, dark, designation=p.designation, title=p.name, subtitle=p.desc or p.discipline,
                                                                   when=datetime.date.today()))
            subprocess.run(["rsvg-convert", "-f", "pdf", fp, "-o", fp[:-4] + ".pdf"], check=True)
    names = ""
    if p.star:
        names = (f"\nInternal name {p.star} (`{p.code}`), one of the stars of {p.constellation}, project `{p.project_code}`. "
                 + ("External name: the same." if p.name == p.star else f"External name: {p.name}.") + "\n")
    readme = f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/brand/readme-banner-dark.png">
  <source media="(prefers-color-scheme: light)" srcset=".github/brand/readme-banner-light.png">
  <img alt="{p.name} · FusionSpace" src=".github/brand/readme-banner-dark.png" width="100%">
</picture>

# {p.name}

{p.desc}

![{p.code}](https://img.shields.io/badge/{p.code.replace("-", "--")}-{(p.tag or "project").replace("-", "--")}-0B0F1C?style=flat-square&labelColor=3350D6)
![FusionSpace](https://img.shields.io/badge/FusionSpace-{p.number}-0B0F1C?style=flat-square&labelColor=B34F0C)

## Overview

What it is, why it exists, and its current status.

## Getting started

How to build, run or use it.

## {'Names' if p.star else 'Project'}

`{p.designation}` · part of [FusionSpace]({kit.SITE_URL}) · drawings and parts number off `{p.code}-001`.
{names}'''
    open(os.path.join(outdir, "README-starter.md"), "w", encoding="utf-8").write(readme)
    STAR = ("star", "constellation", "project", "project_code")
    json.dump({k: v for k, v in vars(p).items() if p.star or k not in STAR}, open(os.path.join(outdir, "project.json"), "w"), indent=2)
    open(os.path.join(outdir, "HOW-TO-USE.md"), "w", encoding="utf-8").write(f'''# {p.name}: brand files

Made with `tools/build/project.py` from `project.json`. Re-run it to regenerate after changing the name or description.

| File | Use |
|---|---|
| `social-preview-dark.png` | GitHub → Settings → Social preview (1280 × 640) |
| `readme-banner-{{dark,light}}.png` (+ `@2x`) | Top of the README; copy them to `.github/brand/` and use `README-starter.md` |
| `og-image-{{dark,light}}.png` | Website link previews (1200 × 630) |
| `youtube-thumbnail.png` | Video thumbnail (1280 × 720) |
| `title-slide-{{dark,light}}.png` | First slide of a talk (1920 × 1080) |
| `report-cover-{{letter,a4}}-{{dark,light}}.pdf` | Cover page for reports and design reviews |
| `*.svg` | Editable sources (Inkscape); text is on the "Text (edit me)" layer |
''')

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--star", help="the internal name: an IAU star name"); ap.add_argument("--name", help="the external name (default: the star's)")
    ap.add_argument("--code"); ap.add_argument("--tag")
    ap.add_argument("--kind"); ap.add_argument("--number", default="001"); ap.add_argument("--desc", default="")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if not a.star and not a.name: ap.error("give --star (the internal name), and --name if the external name is different")
    p = Project(a.name, a.code, a.tag, a.kind, a.number, a.desc, star=a.star)
    outdir = os.path.expanduser(a.out or os.path.join(build.ROOT, "projects", p.slug))
    make(p, outdir); print("wrote", outdir)

if __name__ == "__main__":
    main()
