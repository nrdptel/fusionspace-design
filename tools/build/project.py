"""FusionSpace per-project images: one command makes a project's social preview, README banners, OG image, YouTube
thumbnail, title slide, report cover and a starter README, in dark and light.

    python3 tools/build/project.py --name Vega --tag EMB --desc "Flight software for a two-stage sounding rocket."
    python3 tools/build/project.py --name Achernar --tag GAME --kind "Game" --desc "A small orbital-mechanics puzzle game." --out ~/code/achernar/.github/brand

Options: --name (an IAU star name, see tools/christen), --code (default FS-<NAME>), --tag (discipline tag, see
kit.DISCIPLINES), --kind (free text after the code, default: the tag's description), --number (default 001),
--desc (one line), --out (default projects/<name>). Needs the same tools as the build (rsvg-convert, fonts)."""
import argparse, os, re, json, subprocess, sys
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

class Project:
    def __init__(self, name, code=None, tag=None, kind=None, number="001", desc=""):
        self.name = name; self.code = code or "FS-" + re.sub(r"[^A-Z0-9]+", "-", name.upper()).strip("-")
        self.tag = tag; self.number = number; self.desc = desc
        tags = dict(kit.DISCIPLINES)
        self.kind = kind or "Project"
        self.discipline = tags.get(tag, "") if tag else ""
        parts = [self.code] + ([tag] if tag else []) + [f"{self.kind.upper()} {number}"]
        self.designation = " · ".join(parts)
        self.slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

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
    lines = wrap(p.desc, int(maxw / (15.5 * u)))
    if len(lines) > 2: lines = lines[:2]; lines[1] = lines[1].rstrip(".,;:") + "…"
    for i, line in enumerate(lines):
        tx += text(x, y + i * 42 * u, esc(line), 32 * u, t["muted"], family="sans", label=f"Description line {i + 1}")
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
        ls = wrap(p.desc, int(w * 0.6 / (10.5 * u))); line = ls[0] + ("…" if len(ls) > 1 else "")
        tx += text(80 * u, 118 * u + 22 * u + size * 0.8 + 44 * u, esc(line), 21 * u, t["muted"], family="sans", label="Description")
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
            open(fp, "w", encoding="utf-8").write(kit.cover_svg(page, dark, designation=p.designation, title=p.name, subtitle=p.desc or p.discipline))
            subprocess.run(["rsvg-convert", "-f", "pdf", fp, "-o", fp[:-4] + ".pdf"], check=True)
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

## Project

`{p.designation}` · part of [FusionSpace]({kit.SITE_URL}) · drawings and parts number off `{p.code}-001`.
'''
    open(os.path.join(outdir, "README-starter.md"), "w", encoding="utf-8").write(readme)
    json.dump(vars(p), open(os.path.join(outdir, "project.json"), "w"), indent=2)
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
    ap.add_argument("--name", required=True); ap.add_argument("--code"); ap.add_argument("--tag")
    ap.add_argument("--kind"); ap.add_argument("--number", default="001"); ap.add_argument("--desc", default="")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    p = Project(a.name, a.code, a.tag, a.kind, a.number, a.desc)
    outdir = os.path.expanduser(a.out or os.path.join(build.ROOT, "projects", p.slug))
    make(p, outdir); print("wrote", outdir)

if __name__ == "__main__":
    main()
