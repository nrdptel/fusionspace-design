"""FusionSpace product system: product/ (how FusionSpace apps, sites, tools and hardware are designed).

The brand files elsewhere in the repo say what FusionSpace looks like. product/ says how a FusionSpace *thing* behaves and is
laid out: the rules (Markdown, written in source/product/ and copied here with every value filled in from this file), the
semantic tokens in every format a project needs (CSS, DTCG JSON, Swift, Kotlin, C, ANSI), and reference parts (a web
stylesheet with a specimen page and example screens, the icon set, small-screen mock-ups, a KiCad board title block, rocket
livery sheets, CLI styles).

Every color pair the rules rely on is measured here and the build stops if one falls below its target, so the documents
can't drift from the tokens.
"""
import os, re, json, math, shutil, subprocess, html
import build, kit
from build import VOID, PAPER, WHITE, ION, EMBER, M_ORANGE, O_BLUE, contrast

P = "product"
SPDX = "SPDX-License-Identifier: Apache-2.0"
COPY = "Copyright 2026 Neer Patel"
DATE = "October 4, 2026"
SRC = os.path.join(build.SRC, "product")

def out(p): return os.path.join(build.OUT, P, p)
def wr(rel, s):
    path = out(rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh: fh.write(s)
    return path

# ================================================================ 1. color
# Brand primitives (decided; see color/fusion-space-tokens.json). The core neutrals, Ion and Ember are reused as they are.
CORE = {"Void": VOID, "Abyss": "#141A2B", "Graphite": "#2A3248", "Slate": "#566079", "Haze": "#98A1B8", "Mist": "#D6DAE4",
        "Paper": PAPER, "White": WHITE}
# New for products (proposed October 4, 2026, approved in Neer's review of October 5). Named after emission lines and things that glow, like
# the spectral classes: a flare (red, danger), sodium light (amber, caution), the aurora's oxygen green (normal), a hydrogen
# nebula (magenta, predicted). Each was chosen in OKLCH for contrast on Paper/white and Void/Abyss and for distance from its
# neighbours under simulated protan, deutan and tritan vision; the measurements are in product/foundations.md.
STEEL = "#6D7790"     # control borders on dark: 3:1 on Abyss, which Slate (2.76:1) misses. Same hue as the core neutrals.
SIGNALS = {
    # key: (name, role, fill, text on fill, ink on light, ink on dark)
    "danger":    ("Flare",  "Danger: live energetics (ARMED), unfired charges, hazards that can injure", "#AC001E", WHITE, "#AC001E", "#FB8083"),
    "caution":   ("Sodium", "Caution: off-nominal, a fault to fix before flight, near a limit",    "#F5AF20", VOID,  EMBER,     "#F5AF20"),
    "ok":        ("Aurora", "Normal, safe, within limits",               "#0A6355", WHITE, "#0A6355", "#6AD5B6"),
    "predicted": ("Nebula", "Predicted, simulated, forecast, target",    None,      None,  "#A22488", "#ED89D2"),
}
SIGNAL_NAMES = {k: v[0] for k, v in SIGNALS.items()}

# Semantic roles: (role, light, dark, field, what it is for). Field is the outdoor theme: white canvas, darker secondary
# text and stronger rules, for a phone in full sun at the pad.
S = SIGNALS
ROLES = [
    ("canvas",       PAPER,           VOID,            WHITE,           "Page and screen background"),
    ("surface",      WHITE,           "#141A2B",       WHITE,           "Raised panels, inputs, tables, dialogs (separated by rules, never shadows)"),
    ("rule",         "#D6DAE4",       "#2A3248",       "#98A1B8",       "Hairlines between rows, sections and cells (decoration: no contrast minimum)"),
    ("rule-strong",  "#566079",       STEEL,           VOID,            "Control borders and chart axes (3:1 against canvas and surface)"),
    ("ink",          VOID,            PAPER,           VOID,            "Text, primary lines, measured data"),
    ("ink-muted",    "#566079",       "#98A1B8",       "#2A3248",       "Secondary text: labels, units, captions, sources"),
    ("ink-faint",    "#98A1B8",       "#566079",       "#566079",       "Disabled text and hatching (not for anything that must be read, placeholders included)"),
    ("action",       ION,             O_BLUE,          ION,             "Links, selection, focus, the one interactive accent"),
    ("on-action",    WHITE,           VOID,            WHITE,           "Text on an action fill"),
    ("focus",        ION,             O_BLUE,          ION,             "Focus ring (2 px outline, 2 px offset)"),
    ("danger",       S["danger"][4],  S["danger"][5],  S["danger"][4],  "Danger ink: text, icons and lines"),
    ("caution",      S["caution"][4], S["caution"][5], S["caution"][4], "Caution ink: text, icons and lines"),
    ("ok",           S["ok"][4],      S["ok"][5],      S["ok"][4],      "Normal ink: text, icons and lines"),
    ("predicted",    S["predicted"][4], S["predicted"][5], S["predicted"][4], "Predicted, simulated or forecast data (always dashed or hatched too)"),
]
# Fills are the same on every background, like safety signs: a status chip reads the same on Paper, Void and white.
FILLS = [("danger-fill", S["danger"][2], S["danger"][3]), ("caution-fill", S["caution"][2], S["caution"][3]),
         ("ok-fill", S["ok"][2], S["ok"][3]), ("info-fill", ION, WHITE)]
THEMES = ("light", "dark", "field")
def role(name, theme):
    for r in ROLES:
        if r[0] == name: return r[1 + THEMES.index(theme)]
    raise KeyError(name)

# Data colors. Measured data is ink. A second series is Ion / O blue (the gradient's cool end as an ink), a third is
# Slate / Haze. No warm series: Ember is the caution ink, and no data line may look like a status. More: small multiples.
SERIES = {"light": [VOID, ION, "#566079"], "dark": [PAPER, O_BLUE, "#98A1B8"]}   # ink, O, Slate/Haze: no warm series, Ember is the caution ink
SERIES["field"] = SERIES["light"]
# Sequential and diverging ramps from the spectral classes (never the gradient: its stops have equal lightness).
SPECTRAL = {"O": "#768DF5", "B": "#AABFFF", "A": "#CAD7FF", "F": "#F8F7FF", "G": "#FFF4EA", "K": "#FFD2A1", "M": "#DA7C30"}
RAMPS = {"cool": ["F", "A", "B", "O"], "warm": ["G", "K", "M"], "diverging": ["O", "B", "F", "K", "M"]}

# Contrast checks: (foreground role, background roles, minimum ratio). WCAG 2.2 AA is the floor (4.5:1 text, 3:1 graphics);
# the field theme aims at NASA-STD-3001's 6:1 for characters.
CHECKS = [
    ("ink", ("canvas", "surface"), {"light": 7.0, "dark": 7.0, "field": 10.0}),
    ("ink-muted", ("canvas", "surface"), {"light": 4.5, "dark": 4.5, "field": 7.0}),
    ("action", ("canvas", "surface"), {"light": 4.5, "dark": 4.5, "field": 4.5}),
    ("focus", ("canvas", "surface"), {"light": 3.0, "dark": 3.0, "field": 3.0}),
    ("rule-strong", ("canvas", "surface"), {"light": 3.0, "dark": 3.0, "field": 3.0}),
    ("danger", ("canvas", "surface"), {"light": 4.5, "dark": 4.5, "field": 6.0}),
    ("caution", ("canvas", "surface"), {"light": 4.5, "dark": 4.5, "field": 4.5}),
    ("ok", ("canvas", "surface"), {"light": 4.5, "dark": 4.5, "field": 4.5}),
    ("predicted", ("canvas", "surface"), {"light": 4.5, "dark": 4.5, "field": 6.0}),
]
def check_contrast():
    """Every pair the rules rely on. Returns rows for the docs; raises if any pair is under its minimum."""
    rows, bad = [], []
    for fg, bgs, mins in CHECKS:
        for t in THEMES:
            for bg in bgs:
                r = contrast(role(fg, t), role(bg, t))
                rows.append((t, fg, bg, role(fg, t), role(bg, t), r, mins[t]))
                if r < mins[t] - 1e-9: bad.append(f"{t}: {fg} {role(fg, t)} on {bg} {role(bg, t)} = {r:.2f} < {mins[t]}")
    for name, fill, on in FILLS:
        r = contrast(fill, on); rows.append(("all", name, "text", on, fill, r, 4.5))
        if r < 4.5: bad.append(f"{name}: {on} on {fill} = {r:.2f}")
    for t in THEMES:
        for c in SERIES[t]:
            for bg in ("canvas", "surface"):
                r = contrast(c, role(bg, t))
                if r < 3.0: bad.append(f"series {c} on {t} {bg} = {r:.2f} < 3 (chart lines need 3:1)")
    if bad: raise SystemExit("product color contrast:\n  " + "\n  ".join(bad))
    return rows

# Color-vision check (Machado et al. 2009, severity 1): the signal inks must stay apart for protan, deutan and tritan
# viewers. Distances are OKLab x 100. Status never relies on color alone, so this is a second line of defense.
_CVD = {"protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
        "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
        "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900))}
def _lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def _rgb(h): return [_lin(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5)]
def _oklab(rgb):
    r, g, b = rgb
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)
def oklch(h):
    L, a, b = _oklab(_rgb(h)); return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360
def _sim(h, kind):
    M = _CVD[kind]; c = _rgb(h)
    return _oklab([min(1.0, max(0.0, sum(M[i][j] * c[j] for j in range(3)))) for i in range(3)])
def cvd_distance(a, b):
    """Smallest OKLab distance (x 100) between two colors under normal, protan, deutan and tritan vision."""
    d = [math.dist(_oklab(_rgb(a)), _oklab(_rgb(b)))] + [math.dist(_sim(a, k), _sim(b, k)) for k in _CVD]
    return 100 * min(d)
CVD_MIN = 4.0
def check_cvd():
    rows = []
    for t in ("light", "dark"):
        keys = ["action", "danger", "caution", "ok", "predicted"]
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                d = cvd_distance(role(a, t), role(b, t)); rows.append((t, a, b, d))
                if d < CVD_MIN: raise SystemExit(f"product colors: {t} {a}/{b} only {d:.1f} apart under color-vision simulation")
    return rows

# ================================================================ 2. the rest of the foundations
FONTS = {"display": "'Cascadia Mono', ui-monospace, Menlo, monospace",
         "text": "'Archivo', system-ui, -apple-system, 'Segoe UI', sans-serif",
         "mono": "'Cascadia Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace"}
# Type sizes in px. Headings and readouts step by root 2, the ISO 3098 lettering series (2.5, 3.5, 5, 7, 10, 14 mm) x 4;
# body and small text sit between, at 16 and 14.
TYPE = [  # (token, size, line height, family, weight, case, tracking em, use)
    ("label",    12, 16, "mono",    400, "upper", 0.06, "Field labels, column heads, title-block cells, sheet numbers"),
    ("small",    14, 20, "text",    400, "none",  0,    "Captions, helper text, sources, footnotes"),
    ("body",     16, 24, "text",    400, "none",  0,    "Running text and controls"),
    ("lead",     20, 28, "text",    400, "none",  0,    "The one-sentence summary under a page title"),
    ("subtitle", 20, 24, "display", 600, "none",  0,    "Sheet names and sub-screen titles"),
    ("heading",  14, 20, "display", 600, "upper", 0.04, "Section heads inside a sheet"),
    ("title",    28, 32, "display", 600, "none",  -0.005, "Page and screen titles"),
    ("display",  40, 44, "display", 600, "none",  -0.01, "The one big title on a landing page"),
    ("hero",     56, 60, "display", 600, "none",  -0.01, "Print covers and splash only"),
    ("readout",  28, 32, "mono",    400, "none",  0,    "A single headline value (apogee, charge mass)"),
    ("readout-l", 40, 44, "mono",   400, "none",  0,    "The value a screen exists to show"),
    ("code",     14, 20, "mono",    400, "none",  0,    "Code, commands, file names, part numbers"),
]
SPACE = [0, 2, 4, 8, 12, 16, 24, 32, 48, 64, 96]          # px; 4 px base, 8 px rhythm
LINES = {"thin": 1, "thick": 2, "heavy": 4}                 # ISO 128 widths in the ratio 1 : 2 : 4
DASH = {"dashed": "8 4", "chain": "24 3 1 3", "dotted": "1 3"}   # at 1-2 px: hidden line, long-dash dot, dots
CHAMFER = {"s": 4, "m": 8}                                  # 45 degree corner cuts, px
MOTION = {"quick": 100, "base": 160, "slow": 240}            # ms
EASE = {"standard": "cubic-bezier(0.2, 0, 0, 1)", "exit": "cubic-bezier(0.3, 0, 1, 1)"}
TARGET = {"web": 24, "touch": 44, "field": 96, "glove": 128, "field-pointer": 64}
# minimum targets: CSS px (WCAG 2.5.8) / pt or dp (Apple, Material) / pt for pad controls on a touch screen (about 15 mm,
# MIL-STD-1472H) / pt for the one critical control used with gloves (about 20 mm) / px for pad controls with a mouse
MEASURE = 68                                                 # max line length, characters
FLASH = {"warning": (3.0, 0.5), "advisory": (0.8, 0.7)}      # Hz, duty: NASA-STD-3001 Vol 2 rates, the only two allowed

def _hex_rgb(h): return [int(h[i:i + 2], 16) for i in (1, 3, 5)]
def rgb565(h):
    r, g, b = _hex_rgb(h); return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

# ================================================================ 3. token files
def dtcg_color(h):
    r, g, b = _hex_rgb(h)
    return {"colorSpace": "srgb", "components": [round(r / 255, 4), round(g / 255, 4), round(b / 255, 4)], "hex": h}

def tokens_primitives():
    t = {"$description": "FusionSpace primitives (DTCG 2025.10). Brand colors from color/fusion-space-tokens.json plus the "
                         "product signal colors. Themes alias these in light/dark/field.tokens.json."}
    t["$extensions"] = {"co.fusionspace": {"license": "Apache-2.0", "copyright": COPY}}
    t["core"] = {k.lower(): {"$type": "color", "$value": dtcg_color(v)} for k, v in CORE.items()}
    t["core"]["steel"] = {"$type": "color", "$value": dtcg_color(STEEL), "$description": "Control borders on dark"}
    t["brand"] = {"ion": {"$type": "color", "$value": dtcg_color(ION)}, "ember": {"$type": "color", "$value": dtcg_color(EMBER)},
                  "m-orange": {"$type": "color", "$value": dtcg_color(M_ORANGE)}, "o-blue": {"$type": "color", "$value": dtcg_color(O_BLUE)},
                  "gradient": {"$type": "gradient", "$value": [{"color": dtcg_color(c), "position": float(o)} for o, c in build.STOPS],
                               "$description": "Identity only, always left to right. Never a status, never a data scale."}}
    t["signal"] = {}
    for k, (name, use, fill, on, light, dark) in SIGNALS.items():
        d = {"$description": f"{name}: {use}"}
        if fill: d["fill"] = {"$type": "color", "$value": dtcg_color(fill)}; d["on-fill"] = {"$type": "color", "$value": dtcg_color(on)}
        d["ink-light"] = {"$type": "color", "$value": dtcg_color(light)}; d["ink-dark"] = {"$type": "color", "$value": dtcg_color(dark)}
        t["signal"][name.lower()] = d
    t["spectral"] = {k.lower(): {"$type": "color", "$value": dtcg_color(v)} for k, v in SPECTRAL.items()}
    t["font"] = {k: {"$type": "fontFamily", "$value": [x.strip().strip("'") for x in v.split(",")]} for k, v in FONTS.items()}
    t["space"] = {str(v): {"$type": "dimension", "$value": {"value": v, "unit": "px"}} for v in SPACE}
    t["line"] = {k: {"$type": "dimension", "$value": {"value": v, "unit": "px"}} for k, v in LINES.items()}
    t["chamfer"] = {k: {"$type": "dimension", "$value": {"value": v, "unit": "px"}} for k, v in CHAMFER.items()}
    t["duration"] = {k: {"$type": "duration", "$value": {"value": v, "unit": "ms"}} for k, v in MOTION.items()}
    t["easing"] = {"standard": {"$type": "cubicBezier", "$value": [0.2, 0, 0, 1]}, "exit": {"$type": "cubicBezier", "$value": [0.3, 0, 1, 1]}}
    t["type"] = {}
    for name, size, lh, fam, w, case, tr, use in TYPE:
        t["type"][name] = {"$type": "typography", "$description": use,
                           "$value": {"fontFamily": "{font.%s}" % fam, "fontSize": {"value": size, "unit": "px"},
                                      "lineHeight": round(lh / size, 4), "fontWeight": w, "letterSpacing": {"value": round(tr * size, 2), "unit": "px"}}}
    return t

def _ref(h):
    """Alias a hex to its primitive token where one exists."""
    for k, v in CORE.items():
        if v.upper() == h.upper(): return "{core.%s}" % k.lower()
    if h.upper() == STEEL: return "{core.steel}"
    for n, v in (("ion", ION), ("ember", EMBER), ("m-orange", M_ORANGE), ("o-blue", O_BLUE)):
        if v.upper() == h.upper(): return "{brand.%s}" % n
    for k, (name, use, fill, on, light, dark) in SIGNALS.items():
        for part, v in (("fill", fill), ("ink-light", light), ("ink-dark", dark)):
            if v and v.upper() == h.upper(): return "{signal.%s.%s}" % (name.lower(), part)
    return None

def tokens_theme(theme):
    t = {"$description": f"FusionSpace semantic colors, {theme} theme (DTCG 2025.10; aliases resolve against primitives.tokens.json)."}
    t["$extensions"] = {"co.fusionspace": {"license": "Apache-2.0", "copyright": COPY}}
    t["color"] = {}
    for name, l, d, fld, use in ROLES:
        h = {"light": l, "dark": d, "field": fld}[theme]
        t["color"][name] = {"$type": "color", "$value": _ref(h) or dtcg_color(h), "$description": use}
    for name, fill, on in FILLS:
        t["color"][name] = {"$type": "color", "$value": _ref(fill) or dtcg_color(fill)}
        t["color"]["on-" + name] = {"$type": "color", "$value": _ref(on) or dtcg_color(on)}
    t["color"]["series"] = {str(i + 1): {"$type": "color", "$value": _ref(c) or dtcg_color(c)} for i, c in enumerate(SERIES[theme])}
    return t

def css_tokens():
    """product/tokens/fusionspace-ui.css: semantic custom properties for light, dark (system or data-theme) and field."""
    def block(theme):
        L = [f"  --fs-{n}: {role(n, theme)};" for n, *_ in ROLES]
        L += [f"  --fs-{n}: {fill};\n  --fs-on-{n}: {on};" for n, fill, on in FILLS]
        L += [f"  --fs-series-{i + 1}: {c};" for i, c in enumerate(SERIES[theme])]
        return "\n".join(L)
    head = [f"/* {SPDX} · {COPY} */", f"/* FusionSpace product tokens. Generated by tools/build/kit_product.py; edit there, not here. */",
            "/* Themes: light (default), dark (follows the system unless data-theme is set), field (outdoor, high contrast). */",
            "/* Use: <html data-theme=\"light|dark|field\"> to force one; no attribute follows prefers-color-scheme. */", ""]
    static = [":root {", "  color-scheme: light dark;"]
    static += [f"  --fs-font-{k}: {v};" for k, v in FONTS.items()]
    for name, size, lh, fam, w, case, tr, use in TYPE:
        static.append(f"  --fs-type-{name}: {w} {size}px/{lh}px var(--fs-font-{fam});" + (f"  /* + uppercase, {tr}em tracking */" if case == "upper" else ""))
    static += [f"  --fs-space-{v}: {v}px;" for v in SPACE if v]
    static += [f"  --fs-line-{k}: {v}px;" for k, v in LINES.items()]
    static += [f"  --fs-chamfer-{k}: {v}px;" for k, v in CHAMFER.items()]
    static += [f"  --fs-dur-{k}: {v}ms;" for k, v in MOTION.items()] + [f"  --fs-ease-{k}: {v};" for k, v in EASE.items()]
    static += [f"  --fs-target-{k}: {v}px;" for k, v in TARGET.items()]
    static += [f"  --fs-measure: {MEASURE}ch;", f"  --fs-gradient: {build.css_gradient()};",
               "  --fs-hatch: repeating-linear-gradient(-45deg, var(--fs-ink-faint) 0 1px, transparent 1px 6px);", "}"]
    body = (head + static + ["", ":root, :root[data-theme=\"light\"] {", block("light"), "}",
            "@media (prefers-color-scheme: dark) {", "  :root:not([data-theme]) {", "\n".join("  " + x for x in block("dark").split("\n")), "  }", "}",
            ":root[data-theme=\"dark\"] {", "  color-scheme: dark;", block("dark"), "}",
            ":root[data-theme=\"field\"] {", "  color-scheme: light;", block("field"), "}",
            ":root[data-theme=\"light\"] { color-scheme: light; }", "",
            "/* Print: always the light values, whatever the theme (browsers don't print page backgrounds, and dark inks fail on white). */",
            "@media print {", "  :root, :root[data-theme] {", "    color-scheme: light;", "\n".join("  " + x for x in block("light").split("\n")).replace("--fs-canvas: #F3F4F7", "--fs-canvas: #FFFFFF"), "  }", "}"])
    return "\n".join(body) + "\n"

def swift_tokens():
    ident = lambda n: re.sub(r"-(\w)", lambda m: m.group(1).upper(), n)
    names = [r[0] for r in ROLES]
    L = [f"// {SPDX} · {COPY}", "// FusionSpace product colors for SwiftUI. Generated by tools/build/kit_product.py; edit there, not here.",
         "// FS.<role> follows the system: light, dark, and the field theme when Increase Contrast is on in light appearance.",
         "// For a screen that must be in the field theme (countdown, arming, recovery), read FS.palette(for: .field, ...) or set",
         "// .environment(\\.fsTheme, .field) and use the palette from the environment (see FSPaletteReader below).",
         "import SwiftUI", "#if canImport(UIKit)", "import UIKit", "#endif", "",
         "public enum FSTheme: Sendable { case system, light, dark, field }", "",
         "public struct FSPalette: Sendable {"]
    L += [f"    public let {ident(n)}: Color" for n in names]
    L += ["}", "", "public enum FS {"]
    for t in THEMES:
        args = ", ".join(f"{ident(n)}: Color(hex: 0x{role(n, t)[1:]})" for n in names)
        L.append(f"    public static let {t}Palette = FSPalette({args})")
    L += ["", "    /// The palette for a theme; .system resolves from the color scheme and contrast.",
          "    public static func palette(for theme: FSTheme, scheme: ColorScheme, contrast: ColorSchemeContrast) -> FSPalette {",
          "        switch theme {",
          "        case .light: return lightPalette",
          "        case .dark: return darkPalette",
          "        case .field: return fieldPalette",
          "        case .system: return scheme == .dark ? darkPalette : (contrast == .increased ? fieldPalette : lightPalette)",
          "        }", "    }", "", "    // Semantic roles that follow the system (light, dark, field on Increase Contrast in light)"]
    for name, l, d, f, use in ROLES:
        L.append(f"    /// {use}")
        L.append(f"    public static let {ident(name)} = dynamic(light: 0x{l[1:]}, dark: 0x{d[1:]}, increasedContrast: 0x{f[1:]})")
    L.append("    // Signal fills: the same on every background, like a safety sign")
    for name, fill, on in FILLS:
        i_ = ident(name)
        L.append(f"    public static let {i_} = Color(hex: 0x{fill[1:]})")
        L.append(f"    public static let on{i_[0].upper() + i_[1:]} = Color(hex: 0x{on[1:]})")
    L += ["    /// Identity only, always leading to trailing. Never a status or a data scale.",
          "    public static let gradient = LinearGradient(colors: [" + ", ".join(f"Color(hex: 0x{c[1:]})" for _, c in build.STOPS) + "], startPoint: .leading, endPoint: .trailing)",
          "",
          "    // Type: Cascadia Mono for titles, section heads, labels, readouts and codes; Archivo for prose in content; controls and",
          "    // list text stay in the system font. All scale with Dynamic Type.",
          "    public static func title() -> Font { .custom(\"CascadiaMono-SemiBold\", size: 28, relativeTo: .title) }",
          "    public static func heading() -> Font { .custom(\"CascadiaMono-SemiBold\", size: 14, relativeTo: .headline) }   // with .textCase(.uppercase)",
          "    public static func label() -> Font { .custom(\"CascadiaMono-Regular\", size: 12, relativeTo: .caption) }      // with .textCase(.uppercase)",
          "    public static func readout(_ size: CGFloat = 28, relativeTo style: Font.TextStyle = .title) -> Font { .custom(\"CascadiaMono-Regular\", size: size, relativeTo: style).monospacedDigit() }",
          "    public static func prose() -> Font { .custom(\"Archivo-Regular\", size: 17, relativeTo: .body) }",
          "",
          f"    public static let fieldTarget: CGFloat = {TARGET['field']}   // pt, controls used at the pad (about 15 mm)",
          f"    public static let gloveTarget: CGFloat = {TARGET['glove']}   // pt, the one critical control used with gloves (about 20 mm)",
          "",
          "    static func dynamic(light: UInt32, dark: UInt32, increasedContrast: UInt32) -> Color {",
          "        #if canImport(UIKit)",
          "        return Color(UIColor { t in",
          "            if t.userInterfaceStyle == .dark { return UIColor(hex: dark) }",
          "            return UIColor(hex: t.accessibilityContrast == .high ? increasedContrast : light)",
          "        })",
          "        #else",
          "        return Color(hex: light)",
          "        #endif",
          "    }",
          "}", "",
          "private struct FSThemeKey: EnvironmentKey { static let defaultValue: FSTheme = .system }",
          "extension EnvironmentValues {",
          "    /// The FusionSpace theme for this part of the view tree (.system unless a screen forces .field).",
          "    public var fsTheme: FSTheme {",
          "        get { self[FSThemeKey.self] }",
          "        set { self[FSThemeKey.self] = newValue }",
          "    }",
          "}", "",
          "/// Hands its content the palette for the current theme, color scheme and contrast.",
          "public struct FSPaletteReader<Content: View>: View {",
          "    @Environment(\\.fsTheme) private var theme",
          "    @Environment(\\.colorScheme) private var scheme",
          "    @Environment(\\.colorSchemeContrast) private var contrast",
          "    private let content: (FSPalette) -> Content",
          "    public init(@ViewBuilder content: @escaping (FSPalette) -> Content) { self.content = content }",
          "    public var body: some View { content(FS.palette(for: theme, scheme: scheme, contrast: contrast)) }",
          "}", "",
          "extension Color {",
          "    init(hex: UInt32) { self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255) }",
          "}",
          "#if canImport(UIKit)",
          "extension UIColor {",
          "    convenience init(hex: UInt32) { self.init(red: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255, blue: CGFloat(hex & 0xFF) / 255, alpha: 1) }",
          "}",
          "#endif", ""]
    return "\n".join(L)

def kotlin_tokens():
    ident = lambda n: re.sub(r"-(\w)", lambda m: m.group(1).upper(), n)
    L = [f"// {SPDX} · {COPY}", "// FusionSpace product colors for Jetpack Compose. Generated by tools/build/kit_product.py; edit there, not here.",
         "// A static brand scheme: no dynamic color for anything that carries meaning (Material allows a static scheme).",
         "package co.fusionspace.design", "",
         "import androidx.compose.material3.darkColorScheme",
         "import androidx.compose.material3.lightColorScheme",
         "import androidx.compose.runtime.Immutable",
         "import androidx.compose.runtime.staticCompositionLocalOf",
         "import androidx.compose.ui.graphics.Color", "",
         "@Immutable", "data class FsColors("]
    names = [r[0] for r in ROLES] + [f[0] for f in FILLS] + ["on-" + f[0] for f in FILLS]
    L += [f"    val {ident(n)}: Color," for n in names] + [")", ""]
    def inst(theme):
        vals = [role(n, theme) for n, *_ in ROLES] + [f[1] for f in FILLS] + [f[2] for f in FILLS]
        return [f"val {theme.capitalize()}FsColors = FsColors("] + [f"    {ident(n)} = Color(0xFF{v[1:]})," for n, v in zip(names, vals)] + [")", ""]
    for t in THEMES: L += inst(t)
    L += ["val LocalFsColors = staticCompositionLocalOf { LightFsColors }", "",
          "/** Material 3 roles mapped from the FusionSpace roles. Use with MaterialTheme(colorScheme = ...). */"]
    for t, fn in (("light", "lightColorScheme"), ("dark", "darkColorScheme")):
        c = lambda n: f"Color(0xFF{role(n, t)[1:]})"
        L += [f"val Fs{t.capitalize()}Scheme = {fn}(",
              f"    primary = {c('action')}, onPrimary = {c('on-action')},",
              f"    background = {c('canvas')}, onBackground = {c('ink')},",
              f"    surface = {c('surface')}, onSurface = {c('ink')}, onSurfaceVariant = {c('ink-muted')},",
              f"    outline = {c('rule-strong')}, outlineVariant = {c('rule')},",
              f"    error = {c('danger')},",
              ")", ""]
    L += [f"const val FS_FIELD_TARGET_DP = {TARGET['field']}  // controls used at the pad (about 15 mm)",
          f"const val FS_GLOVE_TARGET_DP = {TARGET['glove']}  // the one critical control used with gloves (about 20 mm)", ""]
    return "\n".join(L)

def c_tokens():
    L = [f"/* {SPDX} · {COPY} */", "/* FusionSpace product colors for firmware (TFT, LVGL). Generated by tools/build/kit_product.py; edit there. */",
         "#ifndef FUSIONSPACE_UI_H", "#define FUSIONSPACE_UI_H", "",
         "/* Screens on a device use the dark roles: emissive panels at the pad read best as light marks on Void,",
         "   and Void pixels draw no power on OLED. RGB888 for LVGL (lv_color_hex), RGB565 for TFT_eSPI and friends. */", ""]
    for name, l, d, f, use in ROLES:
        n = name.upper().replace("-", "_")
        L.append(f"#define FS_{n}_RGB888 0x{d[1:]}u   /* {use} */")
        L.append(f"#define FS_{n}_RGB565 0x{rgb565(d):04X}u")
    for name, fill, on in FILLS:
        n = name.upper().replace("-", "_")
        L.append(f"#define FS_{n}_RGB888 0x{fill[1:]}u")
        L.append(f"#define FS_{n}_RGB565 0x{rgb565(fill):04X}u")
        L.append(f"#define FS_ON_{n}_RGB888 0x{on[1:]}u")
        L.append(f"#define FS_ON_{n}_RGB565 0x{rgb565(on):04X}u")
    L += ["", "/* Flash rates (NASA-STD-3001 Vol 2): the only two allowed. Period ms and on-time ms. */"]
    for k, (hz, duty) in FLASH.items():
        per = round(1000 / hz); L.append(f"#define FS_FLASH_{k.upper()}_PERIOD_MS {per}u\n#define FS_FLASH_{k.upper()}_ON_MS {round(per * duty)}u")
    L += ["", "#endif", ""]
    return "\n".join(L)

def build_tokens():
    rows = check_contrast(); cvd = check_cvd()
    wr("tokens/primitives.tokens.json", json.dumps(tokens_primitives(), indent=2, ensure_ascii=False) + "\n")
    for t in THEMES: wr(f"tokens/{t}.tokens.json", json.dumps(tokens_theme(t), indent=2, ensure_ascii=False) + "\n")
    wr("tokens/fusionspace-ui.css", css_tokens())
    wr("tokens/FusionSpaceColors.swift", swift_tokens())
    wr("tokens/FusionSpaceColors.kt", kotlin_tokens())
    wr("tokens/fusionspace_ui.h", c_tokens())
    return rows, cvd

# ================================================================ 4. example flight (for charts and mock-ups)
def example_flight(seed=7):
    """A made-up dual-deploy flight on a 54 mm J motor, flown twice by a 1-D model: once as the prediction, once with a
    heavier rocket, more drag and baro noise as the "measured" log. Only for drawing examples; the numbers are plausible,
    not real. Returns dict of arrays (s, ft, ft/s, g) and events."""
    import numpy as np
    rng = np.random.default_rng(seed)
    def fly(mass_kg, cd, noise):
        dt = 0.01; t = 0.0; h = 0.0; v = 0.0; out = []; ev = {}
        burn = 1.8; thrust_avg = 390.0; prop = 0.36; area = math.pi * 0.0285 ** 2
        drogue_cda, main_cda, main_ft = 0.08, 1.6, 700.0
        deployed = None
        while t < 400:
            m = mass_kg + prop * max(0.0, 1 - t / burn)
            thrust = thrust_avg * (1.18 - 0.36 * (t / burn)) if t < burn else 0.0
            rho = 1.225 * math.exp(-h / 8500.0)
            if deployed is None: cda = cd * area
            elif deployed == "drogue": cda = drogue_cda
            else: cda = main_cda
            drag = 0.5 * rho * v * abs(v) * cda
            a = (thrust - drag) / m - 9.80665
            if h <= 0 and v <= 0 and t < burn: a = max(a, 0.0)
            v += a * dt; h += v * dt; t += dt
            if "burnout" not in ev and t >= burn: ev["burnout"] = t
            if deployed is None and t > burn and v <= 0: deployed = "drogue"; ev["apogee"] = t; ev["drogue"] = t + 0.4
            if deployed == "drogue" and h * 3.28084 <= main_ft and v < 0: deployed = "main"; ev["main"] = t
            if t > 1 and h <= 0: ev["landing"] = t; out.append((t, 0.0, v, a)); break
            out.append((t, h, v, a))
        arr = np.array(out)
        ft = arr[:, 1] * 3.28084; fts = arr[:, 2] * 3.28084; g = arr[:, 3] / 9.80665 + 1.0
        if noise:
            ft = ft + rng.normal(0, 2.5, len(ft)); g = g + rng.normal(0, 0.15, len(g))
        return {"t": arr[:, 0], "alt": ft, "vel": fts, "acc": g, "events": ev}
    pred = fly(2.9, 0.46, False); meas = fly(3.0, 0.52, True)
    meas["events"]["liftoff"] = 0.0; pred["events"]["liftoff"] = 0.0
    return pred, meas

def chart_svg(pred, meas, width=880, standalone_theme=None, title="Altitude, speed and acceleration against time"):
    """Stacked panels with one time axis (product/data.md): altitude (measured solid ink, predicted dashed Nebula with a
    hatched +/- band), vertical speed, acceleration. Events are dotted lines with numbered balloons. With standalone_theme,
    colors are written in (for PNG previews); otherwise the classes in fusionspace.css color it."""
    import numpy as np
    left, right, top = 56, 16, 64
    ph, gap = [190, 120, 120], 40
    height = top + sum(ph) + gap * (len(ph) - 1) + 40
    tmax = max(meas["t"][-1], pred["t"][-1]) * 1.02
    X = lambda t: left + (width - left - right) * t / tmax
    o = [f'<svg class="fs-chart" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}">']
    if standalone_theme:
        c = lambda r: role(r, standalone_theme)
        o.append("<style>" + f"text{{fill:{c('ink-muted')};font:12px 'Cascadia Mono',monospace}} .t-ink{{fill:{c('ink')};paint-order:stroke;stroke:{c('canvas')};stroke-width:4px;stroke-linejoin:round}} .grid{{stroke:{c('rule')};stroke-width:1}} "
                 f".axis{{stroke:{c('rule-strong')};stroke-width:1}} .measured{{fill:none;stroke:{c('ink')};stroke-width:2;stroke-linejoin:round}} "
                 f".predicted{{fill:none;stroke:{c('predicted')};stroke-width:2;stroke-dasharray:8 4}} .band{{fill:{c('predicted')};fill-opacity:.10}} "
                 f".reference{{fill:none;stroke:{c('ink-muted')};stroke-width:1;stroke-dasharray:24 3 1 3}} .event{{stroke:{c('ink-muted')};stroke-width:1;stroke-dasharray:1 3}} "
                 f".balloon circle{{fill:{c('canvas')};stroke:{c('ink')};stroke-width:1}} .balloon text{{fill:{c('ink')};font-size:12px;text-anchor:middle}} "
                 f".limit{{stroke:{c('danger')};stroke-width:2}}</style>")
        o.append(f'<rect width="{width}" height="{height}" fill="{c("canvas")}"/>')
    order = [("liftoff", "Liftoff"), ("burnout", "Burnout"), ("apogee", "Apogee"), ("drogue", "Drogue out"), ("main", "Main out"), ("landing", "Landing")]
    ev = meas["events"]
    # balloons along the top, with leaders down through every panel
    y0 = top; y1 = top + sum(ph) + gap * (len(ph) - 1)
    placed = []
    for i, (k, _) in enumerate(order):
        x = X(ev[k]); bx = x
        while any(abs(bx - p) < 26 for p in placed): bx += 26
        placed.append(bx)
        o.append(f'<line class="event" x1="{x:.1f}" y1="{y0 - (4 if bx != x else 39)}" x2="{x:.1f}" y2="{y1}"/>')
        if bx != x: o.append(f'<line class="event" x1="{x:.1f}" y1="{y0 - 4}" x2="{bx:.1f}" y2="{y0 - 39}"/>')
        o.append(f'<g class="balloon"><circle cx="{bx:.1f}" cy="{y0 - 48}" r="11"/><text x="{bx:.1f}" y="{y0 - 43.8}">{i + 1}</text></g>')
    panels = [("ALTITUDE · ft AGL", "alt", True), ("VERTICAL SPEED · ft/s", "vel", False), ("ACCELERATION · g", "acc", False)]
    y = top
    for (label, key, with_pred), h in zip(panels, ph):
        vals = np.concatenate([meas[key], pred[key]]) if with_pred else meas[key]
        lo, hi = float(vals.min()), float(vals.max())
        if key == "alt": lo = max(lo, 0.0)
        span = hi - lo; step = 10 ** math.floor(math.log10(span / 3)); step *= 5 if span / step > 15 else 2 if span / step > 7 else 1
        lo = math.floor(lo / step) * step; hi = math.ceil(hi / step) * step
        Y = lambda v, lo=lo, hi=hi, y=y, h=h: y + h - h * (v - lo) / (hi - lo)
        o.append(f'<text x="{left}" y="{y - 12}" class="t-ink">{label}</text>')
        v = lo
        while v <= hi + 1e-9:
            o.append(f'<line class="grid" x1="{left}" x2="{width - right}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>')
            lab = f"{v:,.0f}" if abs(v) >= 1 or v == 0 else f"{v:.1f}"
            o.append(f'<text x="{left - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{lab.replace("-", "−")}</text>')
            v += step
        if lo < 0 < hi: o.append(f'<line class="reference" x1="{left}" x2="{width - right}" y1="{Y(0):.1f}" y2="{Y(0):.1f}"/>')
        o.append(f'<line class="axis" x1="{left}" x2="{left}" y1="{y}" y2="{y + h}"/>')
        if with_pred:
            t = pred["t"]; p = pred[key]; band = 0.04 * p + 8
            up = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(t[::10], (p + band)[::10]))
            dn = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(t[::10][::-1], (p - band)[::10][::-1]))
            o.append(f'<polygon class="band" points="{up} {dn}"/>')
            o.append('<polyline class="predicted" points="' + " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(t[::5], p[::5])) + '"/>')
        t = meas["t"]; m = meas[key]
        o.append('<polyline class="measured" points="' + " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(t[::5], m[::5])) + '"/>')
        y += h + gap
    yb = y - gap
    o.append(f'<line class="axis" x1="{left}" x2="{width - right}" y1="{yb}" y2="{yb}"/>')
    tstep = 10 if tmax > 60 else 5
    tt = 0
    while tt <= tmax:
        o.append(f'<line class="axis" x1="{X(tt):.1f}" x2="{X(tt):.1f}" y1="{yb}" y2="{yb + 4}"/><text x="{X(tt):.1f}" y="{yb + 17}" text-anchor="middle">{tt}</text>')
        tt += tstep
    o.append(f'<text x="{width - right}" y="{yb + 34}" text-anchor="end">TIME SINCE LIFTOFF · s</text>')
    o.append("</svg>")
    return "\n".join(o)

# ================================================================ 5. web reference: stylesheet, fonts, specimen, examples
import kit_icons
FONT_FILES = [("Archivo", 400, "normal", "Archivo-Regular"), ("Archivo", 600, "normal", "Archivo-SemiBold"),
              ("Archivo", 400, "italic", "Archivo-Italic"), ("Cascadia Mono", 400, "normal", "CascadiaMono-Regular"),
              ("Cascadia Mono", 600, "normal", "CascadiaMono-SemiBold")]
# Latin, Latin-1, general punctuation, super/subscripts, letterlike, arrows, math operators, box drawing, geometric shapes
SUBSET = "U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2070-209F,U+20AC,U+2100-214F,U+2190-21FF,U+2200-22FF,U+2500-257F,U+25A0-25FF"

def build_fonts():
    """product/web/fonts/: WOFF2 subsets (Latin plus the technical symbols: ±, ×, ·, µ, °, ², arrows, box drawing) and
    fonts.css. Needs fontTools with brotli; skipped with a warning otherwise (the pages then use the TTFs in type/fonts)."""
    try:
        from fontTools import subset
        import brotli  # noqa: F401
    except ImportError:
        print("WARN product: fontTools/brotli missing, no WOFF2 fonts"); return False
    os.makedirs(out("web/fonts"), exist_ok=True)
    css = ["/* FusionSpace web fonts: WOFF2 subsets of the OFL fonts in type/fonts (licenses next to them there).",
           "   Generated by tools/build/kit_product.py. Preload at most the two you use above the fold. */"]
    for fam, w, style, stem in FONT_FILES:
        src = os.path.join(build.ROOT, "type", "fonts", stem + ".ttf")
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]; opts.name_IDs = ["*"]; opts.notdef_outline = True
        opts.drop_tables += ["DSIG"]
        f_ = subset.load_font(src, opts); s_ = subset.Subsetter(opts)
        s_.populate(unicodes=subset.parse_unicodes(SUBSET)); s_.subset(f_)
        if "head" in f_: f_["head"].modified = f_["head"].created
        subset.save_font(f_, out(f"web/fonts/{stem}.woff2"), opts)
        css.append(f"@font-face {{ font-family: '{fam}'; font-style: {style}; font-weight: {w}; font-display: swap; "
                   f"src: url('fonts/{stem}.woff2') format('woff2'); unicode-range: {SUBSET}; }}")
    # Metric-matched fallbacks so text doesn't jump when the web font arrives (horizontal metrics only on Safari 17+).
    css.append("@font-face { font-family: 'Archivo Fallback'; src: local('Arial'); size-adjust: 101%; }")
    css.append("@font-face { font-family: 'Cascadia Mono Fallback'; src: local('Menlo'), local('Consolas'); size-adjust: 100%; }")
    for stem in ("OFL-Archivo.txt", "OFL-CascadiaMono.txt"):
        shutil.copy(os.path.join(build.ROOT, "type", "fonts", stem), out(f"web/fonts/{stem}"))
    wr("web/fonts.css", "\n".join(css) + "\n")
    return True

def build_stylesheet():
    comp = open(os.path.join(SRC, "web", "components.css"), encoding="utf-8").read()
    if comp.startswith("/* SPDX"): comp = comp.split("\n", 1)[1]          # the tokens part already carries the SPDX line
    s = css_tokens() + "\n" + comp
    wr("web/fusionspace.css", s)
    return s

def _logo(prefix):
    """The header lockup in one color (currentColor): Void on light, Paper on dark. The strip carries the gradient."""
    L = open(os.path.join(build.OUT, "logo/lockup/fusion-space-horizontal-void.svg"), encoding="utf-8").read()
    return build.inline(L, prefix, "height:24px;width:auto").replace("#0B0F1C", "currentColor")

THEME_JS = """<script>
(function () {
  var root = document.documentElement, key = "fs-theme";
  function set(t) { if (t === "auto") root.removeAttribute("data-theme"); else root.setAttribute("data-theme", t);
    document.querySelectorAll("[data-set-theme]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.setTheme === t)); });
    try { localStorage.setItem(key, t); } catch (e) {} }
  var saved = root.getAttribute("data-theme-default") || "auto"; try { saved = localStorage.getItem(key) || saved; } catch (e) {}
  set(saved);
  document.addEventListener("click", function (e) { var b = e.target.closest("[data-set-theme]"); if (b) set(b.dataset.setTheme); });
})();
</script>"""
EXAMPLE_NOTE = ('<p class="fs-small fs-muted fs-hatch" style="margin-top:16px;padding:6px 10px;border:1px solid var(--fs-rule-strong);max-width:none">'
                '<span style="background:var(--fs-canvas);padding:0 4px">Example screen. The layout is the point; the numbers are made up.</span></p>')
THEME_SWITCH = ('<div class="fs-seg" role="group" aria-label="Theme">' + "".join(
    f'<button type="button" data-set-theme="{t}" aria-pressed="false">{n}</button>' for t, n in (("auto", "Auto"), ("light", "Light"), ("dark", "Dark"), ("field", "Field"))) + "</div>")

def _units(body):
    """Unit symbols in table heads stay as written: 'Time · s' must not become 'TIME · S'."""
    body = re.sub(r'(<th[^>]*>)([^<]*?) · ([^<]+)</th>', r'\1\2 · <span class="u">\3</span></th>', body)
    # on a phone, say that a wide table scrolls (the hint is hidden above 640 px)
    return body.replace('<div class="fs-table-wrap"', '<p class="fs-scroll-hint" aria-hidden="true">Wide table: scroll it sideways.</p><div class="fs-table-wrap"')

def page(title, body, rel="", desc="", nav=None, theme_attr="", example=False):
    nav = nav or [("index.html", "Specimen"), ("examples/home.html", "Home"), ("examples/charge.html", "Charge"),
                  ("examples/flight-report.html", "Flight report"), ("examples/window.html", "Window")]
    links = "".join(f'<a href="{rel}{h}"{" aria-current=\"page\"" if t == title.split(" · ")[0] else ""}>{t}</a>' for h, t in nav)
    return f"""<!doctype html>
<html lang="en"{theme_attr}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="{PAPER}" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="{VOID}" media="(prefers-color-scheme: dark)">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="{rel}../../logo/favicon/favicon.svg">
<link rel="stylesheet" href="{rel}fonts.css">
<link rel="stylesheet" href="{rel}fusionspace.css">
</head>
<body>
<div class="fs-strip"></div>
<div class="fs-page">
<header class="fs-header">
  <a class="fs-logo" href="{rel}index.html" aria-label="FusionSpace product system">{_logo("hdr")}</a>
  <nav class="fs-nav" aria-label="Pages">{links}</nav>
  {THEME_SWITCH}
</header>
<main>
{EXAMPLE_NOTE if example else ""}{_units(body)}
</main>
</div>
{THEME_JS}
</body>
</html>
"""

def ico(name, cls="fs-icon"): return kit_icons.inline(name, cls)
def status(state, word, icon=None):
    icon = icon or {"danger": "danger", "caution": "caution", "ok": "ok", "info": "info", "off": "minus", "stale": "clock", "predicted": "simulate"}[state]
    return f'<span class="fs-status" data-state="{state}">{ico(icon, "")}{word}</span>'
def sheet(n, total, name, body, desc=""):
    d = f'<p class="fs-small fs-muted">{desc}</p>' if desc else ""
    return (f'<section class="fs-sheet" id="{re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")}"><div class="fs-sheet-rail"><span class="fs-sheet-no">SHEET {n} / {total}</span>'
            f'<h2>{name}</h2>{d}</div><div class="fs-sheet-body">{body}</div></section>')
def titleblock(cells):
    mark = build.inline(open(os.path.join(build.OUT, "logo/mark/fusion-space-mark.svg"), encoding="utf-8").read(), "tbm" + str(len(cells)), "height:20px;width:auto")
    body = f'<div class="mark wide"><span class="k">Owner</span><span class="v" style="display:flex;gap:8px;align-items:center">{mark}FusionSpace</span></div>'
    body += "".join(f'<div{" class=\"wide\"" if len(v) > 26 else ""}><span class="k">{k}</span><span class="v">{v}</span></div>' for k, v in cells)
    return f'<footer class="fs-titleblock" aria-label="Title block">{body}</footer>'
def note(kind, head, text, icon=None):
    """A note panel. DANGER, WARNING and CAUTION carry the safety-alert triangle (ANSI Z535); NOTICE carries no symbol."""
    icon = icon or {"note": "info", "caution": "caution", "warning": "caution", "danger": "caution", "notice": "", "trust": "dimension"}[kind]
    if kind == "notice": icon = ""
    return (f'<aside class="fs-note" data-kind="{kind}"><div class="fs-note-head">{ico(icon, "") if icon else ""}{head}</div>'
            f'<div class="fs-note-body">{text}</div></aside>')
def readout(label, value, unit, qual="", kind="", size=""):
    return (f'<div class="fs-readout"{f" data-kind={chr(34)}{kind}{chr(34)}" if kind else ""}{f" data-size={chr(34)}{size}{chr(34)}" if size else ""}>'
            f'<span class="fs-label">{label}</span><span class="fs-value"><span>{value}</span><span class="u">{unit}</span></span>'
            + (f'<span class="fs-qual">{qual}</span>' if qual else "") + "</div>")
def num(v, dp=0):
    """US-style number for the screen: commas between groups of three, a real minus sign."""
    s = f"{abs(v):,.{dp}f}"
    return ("−" if v < 0 else "") + s

def specimen(contrast_rows):
    T = 8
    # 1 color
    def sw(h, label=""):
        return f'<span style="display:inline-block;width:28px;height:20px;background:{h};border:1px solid var(--fs-rule);vertical-align:middle"></span> <code>{h}</code>{label}'
    rows = ""
    for name, l, d, fld, use in ROLES:
        cr = lambda t: contrast(role(name, t), role("canvas", t))
        ratios = "—" if name in ("canvas", "surface", "on-action") else f"{cr('light'):.1f} · {cr('dark'):.1f} · {cr('field'):.1f}"
        rows += (f'<tr><td style="white-space:nowrap"><code>--fs-{name}</code></td><td>{sw(l)}</td><td>{sw(d)}</td><td>{sw(fld)}</td>'
                 f'<td class="n">{ratios}</td><td class="fs-small">{use}</td></tr>')
    roles = (f'<div class="fs-table-wrap"><table class="fs-table"><caption>Semantic roles. Contrast is against the canvas of the same theme '
             f'(WCAG 2 ratio, light · dark · field). Use roles in code, never hex values.</caption><thead><tr><th>Role</th><th>Light</th><th>Dark</th><th>Field</th>'
             f'<th class="n">Contrast</th><th>Use</th></tr></thead><tbody>{rows}</tbody></table></div>')
    chips = " ".join([status("danger", "Armed"), status("caution", "Near limit"), status("ok", "Cont", "continuity"), status("info", "Advisory"),
                      status("off", "Not used"), status("stale", 'Stale · <span class="u">4 h</span>'), status("predicted", "Simulated")])
    sig = "".join(f'<tr><td><b>{n}</b></td><td>{SIGNALS[k][1]}</td><td>{sw(SIGNALS[k][2]) if SIGNALS[k][2] else "none: data only"}</td>'
                  f'<td>{sw(SIGNALS[k][4])}</td><td>{sw(SIGNALS[k][5])}</td></tr>' for k, n in SIGNAL_NAMES.items())
    ramps = "".join(f'<div class="fs-stack" style="gap:6px"><span class="fs-label">{k} · {" → ".join(v)}</span><div style="display:flex;height:20px;border:1px solid var(--fs-rule)">'
                    + "".join(f'<span style="flex:1;background:{SPECTRAL[c]}"></span>' for c in v) + "</div></div>" for k, v in RAMPS.items())
    s1 = (f'<p>Two kinds of color that never mix. <b>Brand</b> (the gradient, the spectral classes, the two-tone cones) says who made it. '
          f'<b>Signal</b> (four reserved colors) says what state something is in, and appears only when there is something to say. '
          f'The gradient is never a status, a button or a data scale.</p>{roles}'
          f'<h3>Signal colors</h3><div class="fs-table-wrap"><table class="fs-table"><thead><tr><th>Name</th><th>Means</th><th>Fill (every theme)</th><th>Ink on light</th><th>Ink on dark</th></tr></thead><tbody>{sig}</tbody></table></div>'
          f'<div class="fs-row">{chips}</div><p class="fs-small fs-muted">Every chip has a word and a shape as well as a color. Danger is light text on deep red and caution is dark text on amber: '
          f'the polarity differs, so they stay apart for every kind of color vision and in grayscale.</p>'
          f'<h3>Data ramps</h3><div class="fs-grid">{ramps}</div><p class="fs-small fs-muted">From the spectral classes. Cool and warm are sequential; O to M through F is diverging. '
          f'The gradient isn\'t a ramp: its four stops have the same lightness, so it carries no order.</p>')
    # 2 type
    trs = "".join(f'<tr><td><code>{n}</code></td><td class="n">{sz}/{lh}</td><td style="font:var(--fs-type-{n});{"text-transform:uppercase;letter-spacing:" + str(tr) + "em;" if case == "upper" else ""}">'
                  f'{"5,104 ft AGL" if n.startswith("readout") else "Apogee 5,104 ft" if n in ("title", "display", "hero") else "Ejection charge" if n in ("label", "heading") else "FS-VEGA-001 rev B" if n == "code" else "Size the charge, then ground-test it."}</td>'
                  f'<td class="fs-small fs-muted">{use}</td></tr>' for n, sz, lh, fam, w, case, tr, use in TYPE)
    s2 = (f'<p>Cascadia Mono for anything you read as data or as a drawing: titles, labels, numbers, codes. Archivo for anything you read as prose. '
          f'Headings and readouts step by √2, like drawing lettering (ISO 3098). Capitals only where a drawing would use them: labels, title-block cells, sheet numbers, state words.</p>'
          f'<div class="fs-table-wrap"><table class="fs-table"><thead><tr><th>Token</th><th class="n">px</th><th>Sample</th><th>Use</th></tr></thead><tbody>{trs}</tbody></table></div>')
    # 3 lines
    def ln(y, cls, label, extra=""):
        return f'<line x1="0" x2="300" y1="{y}" y2="{y}" class="{cls}" {extra}/><text x="316" y="{y + 4}">{label}</text>'
    lines = (f'<svg class="fs-chart" viewBox="0 0 720 300" role="img" aria-label="Line types">'
             '<defs><pattern id="fs-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="6" class="hatch-line"/></pattern></defs>'
             + ln(16, "measured", "THICK 2 px · measured data, outlines, the sheet edge")
             + ln(46, "axis", "THIN 1 px · axes, control borders", 'style="stroke:var(--fs-ink)"')
             + ln(76, "predicted", "DASHED 8 4 · predicted, simulated, forecast")
             + ln(106, "reference", "CHAIN 24 3 1 3 · references: ground, rail, limits, center lines")
             + ln(136, "event", "DOTTED 1 3 · events, with a numbered balloon")
             + '<rect x="0" y="160" width="300" height="40" class="hatch-fill" style="stroke:var(--fs-rule-strong)"/><text x="316" y="184">HATCH 45° · unavailable, out of range, uncertain</text>'
             + '<g class="balloon"><circle cx="12" cy="236" r="9"/><text x="12" y="239.5">3</text></g><line x1="21" y1="236" x2="60" y2="236" class="axis" style="stroke:var(--fs-ink)"/>'
             + '<line x1="60" y1="236" x2="88" y2="264" class="axis" style="stroke:var(--fs-ink)"/><circle cx="88" cy="264" r="2.5" style="fill:var(--fs-ink)"/>'
             + '<text x="316" y="240">BALLOON + LEADER · a dot on a surface, an arrow on an edge</text>'
             + '<line x1="0" y1="284" x2="300" y2="284" class="axis" style="stroke:var(--fs-ink)"/><line x1="0" y1="276" x2="0" y2="292" class="axis" style="stroke:var(--fs-ink)"/><line x1="300" y1="276" x2="300" y2="292" class="axis" style="stroke:var(--fs-ink)"/>'
             + '<text x="150" y="278" text-anchor="middle" class="t-ink">300 px</text><text x="316" y="288">DIMENSION · extension lines, value above the line</text></svg>')
    s3 = (f'<p>Lines carry meaning the way they do on a drawing (ISO 128): two widths in a 1 : 2 ratio, and a line type for each kind of information. '
          f'A predicted value is always dashed as well as colored, so it survives printing in black.</p>{lines}')
    # 4 controls
    s4 = (f'<div class="fs-row"><button class="fs-btn">Run simulation</button><button class="fs-btn" data-variant="secondary">Export CSV</button>'
          f'<button class="fs-btn" data-variant="quiet">Show the math</button><button class="fs-btn" disabled>No log loaded</button></div>'
          f'<div class="fs-grid">'
          f'<div class="fs-field"><label for="d">Airframe inner diameter</label><div class="fs-input-group"><input class="fs-input" id="d" inputmode="decimal" value="3.90" autocomplete="off"><span class="fs-unit">in</span></div><span class="fs-help">Inside the tube, not the outside.</span></div>'
          f'<div class="fs-field"><label for="m">Motor</label><select class="fs-select" id="m"><option>J350W-L</option><option>J420R-L</option><option>K535W-L</option></select></div>'
          f'<div class="fs-field" data-invalid><label for="p">Shear pins</label><div class="fs-input-group"><input class="fs-input" id="p" inputmode="numeric" value="0" aria-describedby="pe" aria-invalid="true"><span class="fs-unit">× 2-56</span></div>'
          f'<span class="fs-error" id="pe">{ico("danger", "")}At least one pin, or switch to friction fit.</span></div></div>'
          f'<div class="fs-row"><div class="fs-seg" role="group" aria-label="Units"><button type="button" aria-pressed="true">ft</button><button type="button" aria-pressed="false">m</button></div>'
          f'<label class="fs-check"><input type="checkbox" checked> Dual deploy</label><span class="fs-tag">FS · SW · TOOL 002</span><span class="fs-tag" data-tone="action">REV 1.4.0</span></div>'
          f'<div class="fs-tabs" role="tablist"><button role="tab" aria-selected="true">Flight</button><button role="tab" aria-selected="false">Channels</button><button role="tab" aria-selected="false">Raw log</button></div>'
          f'<p class="fs-small fs-muted">Square corners, 1 px borders, no shadows. The primary button is ink, not a color: color is saved for links, focus and signals. '
          f'Numbers are typed into text fields with <code>inputmode="decimal"</code>, with the unit fixed beside the value. Controls used at the pad are {TARGET["field"]} px tall on touch screens and {TARGET["field-pointer"]} px with a mouse.</p>'
          f'<div><button class="fs-btn" data-size="field">{ico("download", "")}Save flight card</button></div>')
    # 5 data
    pred, meas = example_flight()
    ev = meas["events"]; ap = float(meas["alt"].max()); pap = float(pred["alt"].max())
    s5 = (f'<div class="fs-readouts">{readout("Apogee · measured", num(ap), "ft AGL", "Barometric, from the flight log")}'
          f'{readout("Apogee · predicted", num(pap), "ft AGL", f"±{num(0.04 * pap + 8)} ft, hpr-sim 0.9 · −{(1 - ap / pap) * 100:.1f}% vs measured", "predicted")}'
          f'{readout("Max speed", num(float(meas["vel"].max())), "ft/s", "Mach 0.58 at 1.8 s")}'
          f'{readout("Main at", num(700), "ft AGL", "Set 700 ft, fired at 71.3 s")}</div>'
          f'{chart_svg(pred, meas)}'
          f'<div class="fs-table-wrap"><table class="fs-table"><caption>Events. Times from liftoff; altitudes above the pad.</caption><thead><tr><th></th><th>Event</th><th class="n">Time · s</th><th class="n">Altitude · ft AGL</th><th>Source</th></tr></thead><tbody>'
          + "".join(f'<tr><td><span class="fs-balloon">{i + 1}</span></td><td>{n}</td><td class="n">{ev[k]:.2f}</td><td class="n">{num(0.0 if k in ("liftoff", "landing") else float(meas["alt"][min(len(meas["alt"]) - 1, int(ev[k] / 0.01))]))}</td><td class="fs-small fs-muted">{src}</td></tr>'
                    for i, (k, n, src) in enumerate([("liftoff", "Liftoff", "Accelerometer"), ("burnout", "Burnout", "Accelerometer"), ("apogee", "Apogee", "Barometer"),
                                                     ("drogue", "Drogue out", "Channel 1 fired"), ("main", "Main out", "Channel 2 fired"), ("landing", "Landing", "Barometer, still for 2 s")]))
          + '</tbody></table></div>')
    # 6 status and notes
    s6 = (f'<div class="fs-grid">{note("note", "Note", "<p>Times are from liftoff, detected when acceleration first passed 3 g.</p>")}'
          f'{note("caution", "Caution", "<p>Ground-test this charge before you fly it. The estimate assumes a sealed bay.</p>")}'
          f'{note("warning", "Warning", "<p>Channel 2 is armed. Its ejection charge can fire and cause serious injury. Keep clear of the airframe ends.</p>")}'
          f'{note("notice", "Notice", "<p>Importing a new log replaces the unsaved notes on this flight.</p>", "info")}'
          f'{note("trust", "How far to trust it", "<p>An estimate from a model, not a measurement, and never a go/no-go verdict. Checked against 37 flown charges: within 12% on 33.</p>")}</div>'
          f'<div class="fs-hazard" style="max-width:420px"><div class="fs-stack" style="padding:16px"><span class="fs-label">Channel 2 · main</span>'
          f'<div class="fs-row"><button class="fs-btn" data-variant="danger" data-size="field">Arm channel 2…</button><button class="fs-btn" data-variant="secondary" data-size="field">Safe</button></div>'
          f'<span class="fs-small fs-muted">Arming is two actions: this opens a confirmation that is held for 2 s. The physical switch must already be on. '
          f'Commanded: SAFE · Confirmed: SAFE (2 s ago)</span></div></div>'
          f'<div class="fs-stack" style="max-width:420px"><span class="fs-label">Uploading log · 62%</span><div class="fs-progress"><span style="--value:62%"></span></div>'
          f'<span class="fs-label">Waiting for GPS fix</span><div class="fs-progress" data-indeterminate><span></span></div></div>'
          f'<div class="fs-empty"><span class="fs-label">No flight loaded</span><span>Drop a log file here, or pick one.</span><button class="fs-btn" data-variant="secondary">Choose file</button></div>')
    # 7 icons
    icons = "".join(f'<div style="display:grid;gap:6px;justify-items:center;padding:12px 4px;border:1px solid var(--fs-rule)">{kit_icons.inline(n, "")[:4]} width="24" height="24"{kit_icons.inline(n, "")[4:]}<span class="fs-small fs-muted" style="font:12px/16px var(--fs-font-mono)">{n}</span></div>'
                    for g, ns in kit_icons.GROUPS for n in ns)
    s7 = (f'<p>{len(kit_icons.ICONS)} icons on a 24 px grid: 1.5 px strokes, square ends, 45° and 90° angles, drawn from the real objects. '
          f'Files in <code>product/icons/</code>: one SVG each, <code>sprite.svg</code>, and Android vector drawables.</p><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:8px">{icons}</div>')
    s8 = ("<p>The title block closes every page, report, printout and about screen. It answers: what is this, which version, from whom, when, "
          "in which units, from what data, and how finished it is.</p>"
          + titleblock([("Title", "Product system specimen"), ("Designation", "FS · SPEC 001"), ("Rev", "A"), ("Date", "2026-10-04"),
                        ("Units", "px, ms"), ("Status", "IN PREPARATION"), ("Sheet", f"{T} / {T}")]))
    body = (f'<section style="padding:48px 0 32px;display:grid;gap:16px"><span class="fs-tag">FS · SPEC 001</span><h1 style="font:var(--fs-type-display)">Product system</h1>'
            f'<p class="fs-lead">How FusionSpace tools, apps and boards look and behave. The rules are in <code>product/</code>; this page shows each part working, '
            f'in light, dark and the outdoor field theme.</p></section>'
            + sheet(1, T, "Color", s1) + sheet(2, T, "Type", s2) + sheet(3, T, "Lines", s3) + sheet(4, T, "Controls", s4)
            + sheet(5, T, "Data", s5) + sheet(6, T, "Status and notes", s6) + sheet(7, T, "Icons", s7) + sheet(8, T, "Title block", s8))
    return page("Specimen · FusionSpace product system", body, example=True, desc="The FusionSpace product system: color, type, lines, controls, data, status, icons.")

TOOLS = [  # the drawing register on the example home page: (designation, name, what it is, status, where)
    ("FS · SW · TOOL 001", "HPR Motor Finder", "AeroTech, Cesaroni and Loki motor stock and pricing across major U.S. vendors.", "RELEASED", "motor.fusionspace.co"),
    ("FS · SW · TOOL 002", "Charge", "Black-powder ejection-charge sizing, with every constant shown and a ground-test log.", "RELEASED", "charge.fusionspace.co"),
    ("FS · SW · TOOL 003", "Window", "Launch-weather board for US high-power and model rocketry.", "RELEASED", "window.fusionspace.co"),
    ("FS · SW · TOOL 004", "Muster", "Motor-hardware compatibility: every reload a case flies, and what it needs.", "RELEASED", "muster.fusionspace.co"),
]
def ex_home():
    rows = "".join(f'<tr><td><span class="fs-tag">{d}</span></td><td><a href="#"><b>{n}</b></a><div class="fs-small fs-muted">{w}</div></td>'
                   f'<td>{status("ok", "Released", "check") if s == "RELEASED" else status("off", "In preparation", "edit")}</td><td class="fs-mono fs-small">{u}</td></tr>' for d, n, w, s, u in TOOLS)
    body = (f'<section style="padding:56px 0 40px;display:grid;gap:20px;max-width:760px"><span class="fs-tag">FS · SITE 001</span>'
            f'<h1 style="font:var(--fs-type-display)">Free tools for high‑power rocketry.</h1>'
            f'<p class="fs-lead">Free and open source. Each tool shows its working, says how far to trust it, and works offline at the field.</p>'
            f'<div class="fs-row"><a class="fs-btn" href="#register">See the tools</a><a class="fs-btn" data-variant="secondary" href="#">Source on GitHub {ico("external", "")}</a></div></section>'
            + sheet(1, 2, "Register", f'<div class="fs-table-wrap" id="register"><table class="fs-table"><caption>Every tool, numbered like a drawing. Released tools are maintained; in preparation means usable but changing.</caption>'
                    f'<thead><tr><th>No.</th><th>Title</th><th>Status</th><th>Where</th></tr></thead><tbody>{rows}</tbody></table></div>')
            + sheet(2, 2, "Principles", '<dl class="fs-stack" style="max-width:var(--fs-measure)">'
                    + "".join(f'<div style="border-top:1px solid var(--fs-rule);padding-top:12px;display:grid;gap:4px"><dt><h3>{h}</h3></dt><dd style="margin:0">{t}</dd></div>' for h, t in (
                        ("Shows its working", "Every formula, constant and source is one click away. No black boxes."),
                        ("Says how far to trust it", "Estimates are labeled as estimates, with their spread. Never a go/no-go verdict."),
                        ("Works at the field", "Offline once loaded, readable in sun, big targets for cold hands."),
                        ("No accounts, no tracking", "Your logs stay in your browser unless you export them."))) + "</dl>")
            + titleblock([("Title", "FusionSpace tools"), ("Designation", "FS · SITE 001"), ("Rev", "C"), ("Date", "2026-10-04"), ("Contact", "NeerDPatel@FusionSpace.co"), ("Status", "RELEASED")]))
    return page("Home · example", body, rel="../", example=True, desc="Example: the FusionSpace home page as a drawing register.")

def ex_charge():
    D, L, P = 3.9, 12.0, 15.0
    V = math.pi / 4 * D * D * L
    g = 0.00052 * P * V
    form = (f'<form class="fs-stack" onsubmit="return false"><div class="fs-grid" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr))">'
            f'<div class="fs-field"><label for="id">Inner diameter</label><div class="fs-input-group"><input class="fs-input" id="id" inputmode="decimal" value="{D:.2f}"><span class="fs-unit">in</span></div></div>'
            f'<div class="fs-field"><label for="len">Bay length</label><div class="fs-input-group"><input class="fs-input" id="len" inputmode="decimal" value="{L:.1f}"><span class="fs-unit">in</span></div><span class="fs-help">From the bulkhead to the coupler, empty.</span></div>'
            f'<div class="fs-field"><label for="psi">Target pressure</label><div class="fs-input-group"><input class="fs-input" id="psi" inputmode="decimal" value="{P:.0f}"><span class="fs-unit">psi</span></div><span class="fs-help">15 psi is a common start for 3 × 2-56 nylon pins.</span></div>'
            f'<div class="fs-field"><label for="bp">Powder</label><select class="fs-select" id="bp"><option>FFFFg black powder</option><option>FFFg black powder</option><option>Pyrodex P</option></select></div></div>'
            f'<div class="fs-row"><div class="fs-seg" role="group" aria-label="Separation by"><button type="button" aria-pressed="true">Pressure</button><button type="button" aria-pressed="false">Shear pins + friction</button></div>'
            f'<label class="fs-check"><input type="checkbox" checked> Add a backup charge (+25%)</label></div></form>')
    result = (f'<div class="fs-stack fs-sticky"><div class="fs-panel fs-stack" style="border:2px solid var(--fs-ink)">'
              f'{readout("Primary charge", f"{g:.2f}", "g", "FFFFg black powder, rounded up to 0.05 g on the scale: <b>" + f"{math.ceil(g / 0.05) * 0.05:.2f}" + " g</b>")}'
              f'{readout("Backup", f"{g * 1.25:.2f}", "g", "Primary + 25%", size="m")}'
              f'<details><summary class="fs-btn" data-variant="quiet" style="display:inline-flex">Show the math</summary><pre>V     = π/4 × D² × L = π/4 × ({D:.2f} in)² × {L:.1f} in = {V:.1f} in³\ngrams = 0.00052 × P × V\n      = 0.00052 × {P:.0f} psi × {V:.1f} in³\n      = {g:.3f} g</pre>'
              f'<p class="fs-small fs-muted">0.00052 g per psi per in³ is the ideal-gas yield of black powder at 3307 °R (R = 22.16 ft·lbf/(lbm·°R)), with no losses: the same as the common rule of 0.006 g × D² × L at 15 psi.</p></details></div>'
              f'{note("trust", "How far to trust it", "<p>An ideal-gas estimate. Real bays leak and real powder varies, so the charge that separates on the ground is the one to fly. In this example log, ground tests needed 0.9 to 1.3 times the estimate.</p>")}'
              f'{note("caution", "Caution", "<p>Ground-test before every first flight, and after any change to the bay, pins or powder.</p>")}</div>')
    body = (f'<section style="padding:40px 0 24px;display:grid;gap:12px"><div class="fs-row"><span class="fs-tag">FS · SW · TOOL 002</span>{status("ok", "Released", "check")}</div>'
            f'<h1>Charge</h1><p class="fs-lead">Size a black-powder ejection charge, then prove it on the ground.</p></section>'
            + sheet(1, 2, "Size", f'<div class="fs-split"><div class="fs-stack">{form}</div>{result}</div>')
            + sheet(2, 2, "Ground tests", '<div class="fs-table-wrap"><table class="fs-table"><caption>Your bench log, kept in this browser. Export it with the flight card.</caption><thead><tr><th>Date</th><th class="n">Charge · g</th><th class="n">× estimate</th><th>Result</th><th>Note</th></tr></thead><tbody>'
                    f'<tr><td class="fs-mono">2026-09-12</td><td class="n">1.00</td><td class="n">{1.00 / g:.2f}</td><td>{status("caution", "Partial", "caution")}</td><td class="fs-small">Nose cone moved 2 in, chute stayed in.</td></tr>'
                    f'<tr><td class="fs-mono">2026-09-12</td><td class="n">1.20</td><td class="n">{1.20 / g:.2f}</td><td>{status("ok", "Separated", "ok")}</td><td class="fs-small">Full separation, shock cord taut.</td></tr>'
                    f'<tr><td class="fs-mono">2026-09-19</td><td class="n">1.20</td><td class="n">{1.20 / g:.2f}</td><td>{status("ok", "Separated", "ok")}</td><td class="fs-small">Repeat with flight pins.</td></tr></tbody></table></div>'
                    '<div class="fs-row"><button class="fs-btn" data-variant="secondary">Add a test</button><button class="fs-btn" data-variant="secondary">' + ico("print", "") + 'Print flight card</button></div>')
            + titleblock([("Title", "Charge"), ("Designation", "FS · SW · TOOL 002"), ("Rev", "1.4.0"), ("Date", "2026-10-04"), ("Units", "in, psi, g"),
                          ("Data", "Constants set 2026-09"), ("Status", "RELEASED")]))
    return page("Charge · example", body, rel="../", example=True, desc="Example: an ejection-charge calculator in the FusionSpace product system.")

def ex_flight_report():
    """A flight report for the example project's flight computer: readouts, the stacked chart, channels, the source."""
    pred, meas = example_flight(); ev = meas["events"]
    ap, pap = float(meas["alt"].max()), float(pred["alt"].max())
    chan = (f'<div class="fs-table-wrap"><table class="fs-table"><thead><tr><th>Channel</th><th>Set to</th><th>Continuity</th><th>Fired</th><th class="n">At · s</th><th class="n">At · ft AGL</th></tr></thead><tbody>'
            f'<tr><td class="fs-mono">1 · DROGUE</td><td>Apogee + 0.4 s</td><td>{status("ok", "Cont", "continuity")}</td><td>{status("ok", "Fired", "check")}</td><td class="n">{ev["drogue"]:.2f}</td><td class="n">{num(ap)}</td></tr>'
            f'<tr><td class="fs-mono">2 · MAIN</td><td>700 ft descending</td><td>{status("ok", "Cont", "continuity")}</td><td>{status("ok", "Fired", "check")}</td><td class="n">{ev["main"]:.2f}</td><td class="n">{num(700)}</td></tr>'
            f'<tr><td class="fs-mono">3 · —</td><td class="fs-muted">Not used</td><td>{status("off", "Not used")}</td><td>{status("off", "Not used")}</td><td class="n fs-muted">—</td><td class="n fs-muted">—</td></tr></tbody></table></div>'
            '<p class="fs-small fs-muted">An unused channel is gray and says so. Red is only for a real fault, so a fault is never lost among false alarms.</p>')
    body = (f'<section style="padding:40px 0 24px;display:grid;gap:12px"><div class="fs-row"><span class="fs-tag">FS-VEGA-001 · FLIGHT 03</span>{status("ok", "Released", "check")}</div>'
            f'<h1>Flight 03 · J350W-L</h1><p class="fs-lead">Dual deploy, nominal. Apogee {num(pap - ap)} ft ({(1 - ap / pap) * 100:.1f}%) under the prediction, outside its ±{num(0.04 * pap + 8)} ft spread: the rocket flew heavier than its design file says.</p></section>'
            + sheet(1, 3, "Flight", f'<div class="fs-readouts">{readout("Apogee", num(ap), "ft AGL", "Barometer, 20 Hz")}'
                    f'{readout("Predicted", num(pap), "ft AGL", f"±{num(0.04 * pap + 8)} ft · hpr-sim 0.9, from the design file", "predicted")}'
                    f'{readout("Max speed", num(float(meas["vel"].max())), "ft/s", "Mach 0.58")}{readout("Descent · main", f"{abs(float(meas['vel'][-60])):.0f}", "ft/s", "Under the main, just before landing")}</div>'
                    + chart_svg(pred, meas) + '<p class="fs-small fs-muted">Solid: measured. Dashed with a band: hpr-sim\'s prediction and its spread. Dotted lines with balloons: events, in order: 1 liftoff, 2 burnout, 3 apogee, 4 drogue out, 5 main out, 6 landing.</p>')
            + sheet(2, 3, "Channels", chan)
            + sheet(3, 3, "Source", '<dl class="fs-titleblock" style="margin-top:0">' + "".join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in (
                ("File", "vega-flight-03.csv"), ("Logger", "Barometer 20 Hz, accelerometer 100 Hz"), ("Filter", "None; raw samples"), ("Pad elevation", "4,000 ft MSL"),
                ("Imported", "2026-10-04 14:22"), ("Hash", "sha256 9f3c…b21e"))) + "</dl>")
            + titleblock([("Title", "Flight 03 report"), ("Designation", "FS-VEGA · REPORT 003"), ("Rev", "A"), ("Date", "2026-10-04"), ("Units", "ft, ft/s, g, s"), ("Status", "RELEASED")]))
    return page("Flight report · example", body, rel="../", example=True, desc="Example: a flight report from a flight computer's log, in the FusionSpace product system.")

def ex_window():
    aloft = [(0, 12, 19, 270), (1000, 16, None, 275), (3000, 22, None, 280), (6000, 31, None, 285), (9000, 38, None, 290)]
    rows = "".join(f'<tr><td>{status("predicted", "Forecast", "simulate") if h else status("info", "Measured", "windsock")}</td><td class="n">{num(h)}</td><td class="n">{w}</td>'
                   f'<td class="n">{g if g else "—"}</td><td class="n">{d}°</td></tr>' for h, w, g, d in aloft)
    body = (f'<section style="padding:40px 0 24px;display:grid;gap:12px"><div class="fs-row"><span class="fs-tag">FS · SW · TOOL 003</span>{status("stale", 'Stale · upper air <span class="u">4 h</span>')}</div>'
            f'<h1>Window · Example field</h1><p class="fs-lead">Surface wind under the 20 mph limit, gusting close to it. Ceiling under the waiver. No verdict: your RSO decides.</p></section>'
            + sheet(1, 2, "Now", f'<div class="fs-readouts">{readout("Surface wind", "12", "mph", "Gusts 19 mph · from 270° · measured 2:10 PM")}'
                    f'{readout("Ceiling", num(6500), "ft AGL", "Under the waiver: 8,000 ft AGL")}{readout("Temperature", "71", "°F", "Density altitude 5,620 ft")}'
                    f'{readout("Upper winds", "31", "mph", "At 6,000 ft · issued 10:00 AM, 4 h old", "stale")}</div>'
                    f'{note("caution", "Caution", "<p>Gusts of 19 mph are within 1 mph of the NAR and Tripoli 20 mph limit.</p>")}')
            + sheet(2, 2, "Aloft", f'<div class="fs-table-wrap"><table class="fs-table"><caption>Winds by height. Forecast rows are model output, dashed in charts and tagged here.</caption>'
                    f'<thead><tr><th>Kind</th><th class="n">Height · ft AGL</th><th class="n">Wind · mph</th><th class="n">Gust · mph</th><th class="n">From</th></tr></thead><tbody>{rows}</tbody></table></div>'
                    f'<div class="fs-row"><button class="fs-btn" data-size="field">{ico("refresh", "")}Refresh</button><button class="fs-btn" data-variant="secondary" data-size="field">{ico("print", "")}Print for the pad</button></div>')
            + titleblock([("Title", "Window · Example field"), ("Designation", "FS · SW · TOOL 003"), ("Rev", "2.1.0"), ("Date", "2026-10-04 14:10"), ("Units", "mph, ft, °F"),
                          ("Data", "Surface: station obs. Aloft: model forecast"), ("Status", "RELEASED")]))
    return page("Window · example", body, rel="../", example=True, desc="Example: a launch-weather board in the field theme.", theme_attr=' data-theme="field" data-theme-default="field"')


# ================================================================ 6. documents (source/product/*.md -> product/*.md)
REV = "A"
SILK = {"text_mm": 1.2, "line_mm": 0.15, "label_mm": 2.3}   # dense silkscreen text and stroke; labels read while handling
def _md_hex(h): return f"`{h}`"
def table_signals():
    return "\n".join(f"| **{n}** | {SIGNALS[k][1]} | {_md_hex(SIGNALS[k][2]) if SIGNALS[k][2] else 'none: data only'} | "
                     f"{_md_hex(SIGNALS[k][3]) if SIGNALS[k][3] else '–'} | {_md_hex(SIGNALS[k][4])} | {_md_hex(SIGNALS[k][5])} |" for k, n in SIGNAL_NAMES.items())
def table_roles():
    return "\n".join(f"| `{n}` | {_md_hex(l)} | {_md_hex(d)} | {_md_hex(f_)} | {use} |" for n, l, d, f_, use in ROLES)
def list_fills(): return "; ".join(f"`{n}` {fill} with `on-{n}` {on}" for n, fill, on in FILLS)
def min_cvd(): return f"{min(d for *_, d in check_cvd()):.1f}"
def min_field_text(): return f"{min(contrast(role(r, 'field'), role('canvas', 'field')) for r in ('ink', 'ink-muted')):.1f}"
def table_contrast():
    L = []
    for t, fg, bg, a, b, r, mn in check_contrast():
        if t == "all": L.append(f"| all | text on `{fg}` | {b} | {r:.2f} | {mn:g} |")
        elif bg == "canvas": L.append(f"| {t} | `{fg}` {a} | {bg} {b} | {r:.2f} | {mn:g} |")
    return "\n".join(L)
def table_series():
    return "\n".join(f"| {i + 1} | {_md_hex(a)} | {_md_hex(b)} |" for i, (a, b) in enumerate(zip(SERIES["light"], SERIES["dark"])))
def table_type():
    return "\n".join(f"| `{n}` | {sz} / {lh} px | {'Cascadia Mono' if fam != 'text' else 'Archivo'} | {w} | {'capitals' if case == 'upper' else 'as written'} | {use} |"
                     for n, sz, lh, fam, w, case, tr, use in TYPE)
def doc_context():
    import kit_icons as ki
    ctx = {k: v for k, v in globals().items() if not k.startswith("_")}
    import kit_mobile
    ctx.update({"MOBILE": kit_mobile, "ICONS": ki.ICONS, "M_ORANGE": M_ORANGE, "O_BLUE": O_BLUE, "VOID": VOID, "PAPER": PAPER, "ION": ION, "EMBER": EMBER})
    return ctx
def render_md(text, ctx):
    def sub(m):
        e = m.group(1).strip()
        try:
            return str(eval(e, ctx))
        except SyntaxError:
            e, spec = e.rsplit(":", 1)          # {{ value:format }}
            return format(eval(e, ctx), spec)
    out_ = re.sub(r"\{\{(.+?)\}\}", sub, text)
    assert "{{" not in out_, "unrendered placeholder"
    return out_
def build_docs():
    ctx = doc_context()
    for fn in sorted(os.listdir(SRC)):
        if fn.endswith(".md"):
            wr(fn, render_md(open(os.path.join(SRC, fn), encoding="utf-8").read(), ctx))

# ================================================================ 7. framework themes: Tailwind v4, mdBook
def tailwind_theme():
    names = [r[0] for r in ROLES] + [f[0] for f in FILLS] + ["on-" + f[0] for f in FILLS]
    L = [f"/* {SPDX} · {COPY} */", "/* FusionSpace theme for Tailwind CSS v4. Generated by tools/build/kit_product.py; edit there, not here.",
         "   Use instead of Tailwind's default theme:",
         "     @import \"tailwindcss/preflight\" layer(base);",
         "     @import \"tailwindcss/utilities\" layer(utilities);",
         "     @import \"./fusionspace.css\";",
         "     @import \"./tailwind-theme.css\";",
         "   The default palette, radii and shadows are removed, so bg-indigo-500, rounded-xl and shadow-lg don't exist here. */",
         "@theme inline {",
         "  --color-*: initial;",
         "  --radius-*: initial;",
         "  --shadow-*: initial;",
         "  --inset-shadow-*: initial;",
         "  --drop-shadow-*: initial;",
         "  --blur-*: initial;",
         "  --font-*: initial;",
         "  --color-transparent: transparent;",
         "  --color-current: currentColor;"]
    L += [f"  --color-{n}: var(--fs-{n});" for n in names]
    L += [f"  --color-series-{i + 1}: var(--fs-series-{i + 1});" for i in range(len(SERIES["light"]))]
    L += ["  --font-text: var(--fs-font-text);", "  --font-mono: var(--fs-font-mono);", "  --font-display: var(--fs-font-display);",
          "  --font-sans: var(--fs-font-text);"]
    L += [f"  --spacing: 4px;"]
    for n, sz, lh, fam, w, case, tr, use in TYPE:
        L.append(f"  --text-{n}: {sz}px;"); L.append(f"  --text-{n}--line-height: {lh}px;")
    L += [f"  --radius-chamfer-{k}: {v}px;" for k, v in CHAMFER.items()]
    L += [f"  --ease-standard: {EASE['standard']};", f"  --ease-exit: {EASE['exit']};", "}"]
    return "\n".join(L) + "\n"

def mdbook_css():
    """mdBook (hpr-sim's docs): override the theme variables of mdBook's light and dark themes, add the fonts and the strip."""
    def vars_(t):
        r = lambda n: role(n, t)
        return (f"  --bg: {r('canvas')}; --fg: {r('ink')}; --sidebar-bg: {r('surface')}; --sidebar-fg: {r('ink')};\n"
                f"  --sidebar-non-existant: {r('ink-faint')}; --sidebar-active: {r('action')}; --sidebar-spacer: {r('rule')};\n"
                f"  --scrollbar: {r('rule-strong')}; --icons: {r('ink-muted')}; --icons-hover: {r('ink')}; --links: {r('action')};\n"
                f"  --inline-code-color: {r('ink')}; --theme-popup-bg: {r('surface')}; --theme-popup-border: {r('rule-strong')};\n"
                f"  --theme-hover: {r('rule')}; --quote-bg: {r('surface')}; --quote-border: {r('rule-strong')};\n"
                f"  --table-border-color: {r('rule')}; --table-header-bg: {r('surface')}; --table-alternate-bg: {r('canvas')};\n"
                f"  --searchbar-border-color: {r('rule-strong')}; --searchbar-bg: {r('surface')}; --searchbar-fg: {r('ink')};\n"
                f"  --searchbar-shadow-color: transparent; --searchresults-header-fg: {r('ink-muted')}; --searchresults-border-color: {r('rule')};\n"
                f"  --searchresults-li-bg: {r('surface')}; --search-mark-bg: {SIGNALS['caution'][2]};\n"
                f"  --code-bg: {r('surface')};")
    return f"""/* {SPDX} · {COPY} */
/* FusionSpace theme for mdBook. Generated by tools/build/kit_product.py.
   book.toml:
     [output.html]
     additional-css = ["theme/fusionspace-mdbook.css", "theme/fonts.css"]
     default-theme = "light"
     preferred-dark-theme = "navy"
   Copy this file, product/web/fonts.css and product/web/fonts/ into the book's theme/ folder. */
.light, .rust {{
{vars_("light")}
}}
.navy, .coal, .ayu {{
{vars_("dark")}
}}
html {{ font-family: {FONTS['text']}; }}
body::before {{ content: ""; position: fixed; top: 0; left: 0; right: 0; height: 4px; background: {build.css_gradient()}; z-index: 1000; }}
code, pre, kbd, .hljs {{ font-family: {FONTS['mono']} !important; font-variant-numeric: tabular-nums slashed-zero; }}
h1, h2, h3, .menu-title {{ font-family: {FONTS['display']}; font-weight: 600; letter-spacing: 0; }}
h2 {{ border-top: 2px solid var(--fg); padding-top: 0.6em; }}
table {{ border-collapse: collapse; }}
table thead th {{ font-family: {FONTS['mono']}; font-size: 0.75em; text-transform: uppercase; letter-spacing: 0.06em; border-bottom: 2px solid var(--fg); }}
table td, table th {{ border-left: 0; border-right: 0; }}
blockquote {{ border-left: 0; border: 1px solid var(--quote-border); padding: 0.6em 1em; }}
.sidebar .chapter li.chapter-item a.active {{ box-shadow: inset 2px 0 0 var(--links); }}
pre, code, .theme-popup, .searchbar {{ border-radius: 0 !important; }}
"""

# ================================================================ 8. command line (product/cli/)
CLI_ROLES = [  # (name, SGR, anstyle expression, use)
    ("HEADING", "1", "Style::new().bold()", "section titles, table headers, the first line of a result"),
    ("LITERAL", "1;34", "AnsiColor::Blue.on_default().bold()", "commands, flags and values to type"),
    ("PLACEHOLDER", "34", "AnsiColor::Blue.on_default()", "<FILE>, <MOTOR> in help"),
    ("OK", "32", "AnsiColor::Green.on_default()", "CONT, passed, fired"),
    ("CAUTION", "33", "AnsiColor::Yellow.on_default()", "values near a limit"),
    ("WARNING", "1;33", "AnsiColor::Yellow.on_default().bold()", "warning:"),
    ("DANGER", "1;31", "AnsiColor::Red.on_default().bold()", "error:, NO CONT, failed checks"),
    ("PREDICTED", "35", "AnsiColor::Magenta.on_default()", "simulated or forecast values beside measured ones"),
    ("MUTED", "2", "Style::new().dimmed()", "separators and decoration only"),
]
def cli_rust():
    L = [f"// {SPDX} · {COPY}", "//! FusionSpace terminal styles for Rust command-line tools (clap 4, anstyle, anstream).",
         "//! Generated by tools/build/kit_product.py in the fusionspace-design repository; edit there, not here.",
         "//! ANSI roles only: the user's terminal theme decides the actual colors. See product/cli.md.",
         "//!",
         "//! Cargo.toml: clap = { version = \"4\", features = [\"derive\"] }, anstyle = \"1\", anstream = \"0.6\"",
         "//!",
         "//! ```ignore",
         "//! #[derive(clap::Parser)]",
         "//! #[command(styles = fs_style::CLAP_STYLES)]",
         "//! struct Cli { #[arg(long, value_enum, default_value_t = fs_style::ColorWhen::Auto)] color: fs_style::ColorWhen }",
         "//! // after parsing:",
         "//! fs_style::color_choice(cli.color).write_global();",
         "//! anstream::eprintln!(\"{}warning:{} the main opens late\", fs_style::WARNING, fs_style::WARNING.render_reset());",
         "//! ```",
         "", "use anstyle::{AnsiColor, Style};", "use clap::builder::styling::Styles;", ""]
    for n, sgr, expr, use in CLI_ROLES:
        L.append(f"/// {use[0].upper() + use[1:]}.")
        L.append(f"pub const {n}: Style = {expr};")
    L += ["/// `error:` prefix.", "pub const ERROR: Style = DANGER;", "/// `help:` prefix.", "pub const HELP: Style = LITERAL;",
          "/// `note:` prefix.", "pub const NOTE: Style = HEADING;", "",
          "/// clap's help and error styles in the FusionSpace roles.",
          "pub const CLAP_STYLES: Styles = Styles::styled()",
          "    .header(HEADING)", "    .usage(HEADING)", "    .literal(LITERAL)", "    .placeholder(PLACEHOLDER)",
          "    .error(ERROR)", "    .valid(OK)", "    .invalid(WARNING);", "",
          "/// The `--color` flag.",
          "#[derive(Clone, Copy, Debug, PartialEq, Eq, clap::ValueEnum)]",
          "pub enum ColorWhen {", "    Auto,", "    Always,", "    Never,", "}", "",
          "/// Resolve color: the flag, then NO_COLOR, then FORCE_COLOR / CLICOLOR_FORCE, then auto (anstream checks the",
          "/// stream is a terminal and TERM isn't dumb). anstream doesn't read FORCE_COLOR itself, so it is read here.",
          "pub fn color_choice(flag: ColorWhen) -> anstream::ColorChoice {",
          "    match flag {",
          "        ColorWhen::Always => return anstream::ColorChoice::Always,",
          "        ColorWhen::Never => return anstream::ColorChoice::Never,",
          "        ColorWhen::Auto => {}",
          "    }",
          "    let set = |k: &str| std::env::var_os(k).is_some_and(|v| !v.is_empty());",
          "    if set(\"NO_COLOR\") {",
          "        return anstream::ColorChoice::Never;",
          "    }",
          "    if set(\"FORCE_COLOR\") || std::env::var(\"CLICOLOR_FORCE\").is_ok_and(|v| !v.is_empty() && v != \"0\") {",
          "        return anstream::ColorChoice::Always;",
          "    }",
          "    anstream::ColorChoice::Auto",
          "}", "",
          "/// True when the brand banner may use 24-bit color.",
          "pub fn truecolor() -> bool {",
          "    std::env::var(\"COLORTERM\").is_ok_and(|v| v == \"truecolor\" || v == \"24bit\")",
          "}", ""]
    return "\n".join(L)

PY_STYLE = '''# SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
"""FusionSpace terminal styles for Python command-line tools. No dependencies.
Generated by tools/build/kit_product.py in the fusionspace-design repository; edit there, not here. See product/cli.md.

    from fs_style import S, paint, use_color
    color = use_color(sys.stderr, flag=args.color)          # "auto" | "always" | "never"
    print(paint("warning:", S.WARNING, color), "the main opens late", file=sys.stderr)
"""
import os, sys

class S:
    """ANSI roles: the user's terminal theme decides the actual colors."""
%ROLES%
    ERROR = DANGER
    HELP = LITERAL
    NOTE = HEADING
    RESET = "\\x1b[0m"

def use_color(stream=sys.stdout, flag="auto"):
    """The flag, then NO_COLOR, then FORCE_COLOR / CLICOLOR_FORCE, then: a terminal, and TERM isn't dumb."""
    if flag in ("always", "never"):
        return flag == "always"
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR") or os.environ.get("CLICOLOR_FORCE", "0") not in ("", "0"):
        return True
    return hasattr(stream, "isatty") and stream.isatty() and os.environ.get("TERM") != "dumb"

def paint(text, style, color=True):
    return f"{style}{text}{S.RESET}" if color else text

def truecolor():
    """True when the brand banner may use 24-bit color."""
    return os.environ.get("COLORTERM") in ("truecolor", "24bit")
'''
def cli_python():
    roles = "\n".join(f"    {n} = \"\\x1b[{sgr}m\"   # {use}" for n, sgr, _, use in CLI_ROLES)
    return PY_STYLE.replace("%ROLES%", roles)

def cli_sample():
    """Example `hpr sim` output in the FusionSpace style: (plain text, ANSI text). The flight is the made-up example."""
    pred, meas = example_flight(); ev = pred["events"]
    ap_m = float(pred["alt"].max()) / 3.28084; v_ms = float(pred["vel"].max()) / 3.28084
    ft = lambda m: m * 3.28084
    H, W, B, D, R = "\x1b[1m", "\x1b[1;33m", "\x1b[1;34m", "\x1b[2m", "\x1b[0m"
    rows = [
        f"{B}${R} hpr sim vega.ork --motor J350W-L",
        f"{H}vega.ork: FS-VEGA-001 rev B, configuration \"J350W-L, dual deploy\"{R}",
        "flown with hpr 0.9.2: 6-DOF, standard atmosphere, wind 4 m/s from 270°",
        "",
        f"apogee            {ap_m:.0f} m ({ft(ap_m):.0f} ft) AGL at {ev['apogee']:.1f} s",
        f"max speed         {v_ms:.0f} m/s ({ft(v_ms):.0f} ft/s), Mach {v_ms / 340.3:.2f} at {ev['burnout']:.1f} s",
        "rail exit         24.1 m/s (79 ft/s), above the 15 m/s guideline",
        "stability         1.9 cal at rail exit, 2.4 cal at burnout",
        f"landing           {ev['landing']:.1f} s, {abs(float(pred['vel'][-60])) / 3.28084:.1f} m/s ({abs(float(pred['vel'][-60])):.0f} ft/s) under the main, 412 m (1352 ft) downwind",
        "",
        f"{H}channel           set to                          fires (simulated){R}",
        f"1 DROGUE          apogee + 0.4 s                  {ev['drogue']:.1f} s at {ap_m:.0f} m",
        f"2 MAIN            213 m (700 ft) descending       {ev['main']:.1f} s at 213 m",
        "3 -               not used",
        "",
        f"{W}warning:{R} rail exit assumes a 1.5 m (59 in) rail; pass --rail to set yours",
        f"{H}how far to trust it:{R} within 3% of OpenRocket on this design; on 12 real flights hpr's apogee was within 8%",
        f"{D}(an example: these numbers are made up to show the layout){R}",
    ]
    plain = [re.sub(r"\x1b\[[0-9;]*m", "", a) for a in rows]
    return plain, rows

def ansi_svg(lines, theme, cw=14 * 1200 / 2048, lh=20, pad=20):     # cw: Cascadia Mono advance (1200 of 2048 units) at 14 px
    """Draw ANSI-colored lines as the FusionSpace terminal theme shows them (16-color SGR codes only)."""
    pal = {"30": theme["black"], "31": theme["red"], "32": theme["green"], "33": theme["yellow"], "34": theme["blue"],
           "35": theme["magenta"], "36": theme["cyan"], "37": theme["white"]}
    width = int(pad * 2 + cw * max(len(re.sub(r"\x1b\[[0-9;]*m", "", l)) for l in lines)); height = pad * 2 + lh * len(lines)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         f'<rect width="100%" height="100%" fill="{theme["background"]}"/>']
    for i, line in enumerate(lines):
        x = pad; y = pad + lh * i + 14; bold = dim = False; col = theme["foreground"]
        for part in re.split(r"(\x1b\[[0-9;]*m)", line):
            m = re.fullmatch(r"\x1b\[([0-9;]*)m", part)
            if m:
                for c in (m.group(1) or "0").split(";"):
                    if c == "0": bold = dim = False; col = theme["foreground"]
                    elif c == "1": bold = True
                    elif c == "2": dim = True
                    elif c in pal: col = pal[c]
                continue
            if not part: continue
            weight = ' font-weight="600"' if bold else ""; op = ' opacity="0.55"' if dim else ""
            o.append(f'<text x="{x:.1f}" y="{y}" fill="{col}"{weight}{op} font-family="Cascadia Mono" font-size="14" xml:space="preserve">{html.escape(part)}</text>')
            x += cw * len(part)
    o.append("</svg>")
    return "\n".join(o)

def build_cli():
    wr("cli/fs_style.rs", cli_rust()); wr("cli/fs_style.py", cli_python())
    plain, ansi = cli_sample()
    wr("cli/sample-output.txt", "\n".join(plain) + "\n")
    import kit_targets
    p_ = wr("cli/preview.svg", ansi_svg(ansi, kit_targets.TERM))
    subprocess.run(["rsvg-convert", "-z", "2", "-o", out("cli/preview.png"), p_], check=True); os.remove(p_)

# ================================================================ 9. device screens (product/embedded/)
class BDF:
    """A bitmap font from a BDF file (Spleen, BSD-2, in source/product/embedded/fonts)."""
    def __init__(self, path):
        txt = open(path, "rb").read().decode("latin-1")
        self.ascent = int(re.search(r"FONT_ASCENT (\d+)", txt).group(1))
        self.glyphs = {}
        for c in re.findall(r"STARTCHAR.*?ENDCHAR", txt, re.S):
            enc = int(re.search(r"ENCODING (-?\d+)", c).group(1))
            dw = int(re.search(r"DWIDTH (\d+)", c).group(1))
            w, h, xo, yo = map(int, re.search(r"BBX (-?\d+) (-?\d+) (-?\d+) (-?\d+)", c).group(1, 2, 3, 4))
            rows = re.search(r"BITMAP\n(.*?)\nENDCHAR", c + "\n", re.S)
            rows = rows.group(1).split() if rows else []
            bits = [[(int(r, 16) >> (len(r) * 4 - 1 - i)) & 1 for i in range(w)] for r in rows]
            self.glyphs[enc] = (dw, w, h, xo, yo, bits)
        self.height = self.ascent + int(re.search(r"FONT_DESCENT (\d+)", txt).group(1))
    def width(self, s): return sum(self.glyphs.get(ord(ch), self.glyphs[32])[0] for ch in s)

class Screen:
    """A 1-bit frame buffer with the few drawing calls the mock-ups need."""
    def __init__(self, w, h):
        import numpy as np
        self.w, self.h = w, h; self.px = np.zeros((h, w), dtype=bool)
    def rect(self, x, y, w, h, fill=False, on=True):
        if fill: self.px[y:y + h, x:x + w] = on
        else:
            self.px[y, x:x + w] = on; self.px[y + h - 1, x:x + w] = on; self.px[y:y + h, x] = on; self.px[y:y + h, x + w - 1] = on
    def hline(self, x0, x1, y, dotted=False):
        for x in range(x0, x1):
            if not dotted or x % 2 == 0: self.px[y, x] = True
    def text(self, x, y, s, font, on=True, anchor="left"):
        if anchor == "right": x -= font.width(s)
        elif anchor == "middle": x -= font.width(s) // 2
        base = y + font.ascent
        for ch in s:
            dw, w, h, xo, yo, bits = font.glyphs.get(ord(ch), font.glyphs[32])
            top = base - (h + yo)
            for r, row in enumerate(bits):
                for c, b in enumerate(row):
                    if b and 0 <= top + r < self.h and 0 <= x + xo + c < self.w: self.px[top + r, x + xo + c] = on
            x += dw
        return x
    def png(self, path, scale=1, lit=(230, 232, 239), dark=(0, 0, 0), gap=False):
        from PIL import Image
        import numpy as np
        im = np.zeros((self.h * scale, self.w * scale, 3), dtype=np.uint8); im[:] = dark
        big = np.kron(self.px, np.ones((scale, scale), dtype=bool))
        im[big] = lit
        if gap and scale >= 3:
            im[scale - 1::scale, :, :] = (im[scale - 1::scale, :, :] * 0.7).astype(np.uint8)
            im[:, scale - 1::scale, :] = (im[:, scale - 1::scale, :] * 0.7).astype(np.uint8)
        Image.fromarray(im).save(path)

def _fonts():
    d = os.path.join(SRC, "embedded", "fonts")
    return {k: BDF(os.path.join(d, f"spleen-{k}.bdf")) for k in ("5x8", "6x12", "8x16", "16x32")}

def oled_screens():
    """128 x 64 monochrome screens for a flight computer: SAFE on the pad, ARMED with a fault, in flight, after landing, and
    after landing with a charge that didn't fire."""
    F = _fonts(); s5, s6, s8, s16 = F["5x8"], F["6x12"], F["8x16"], F["16x32"]
    def status_row(sc, state, inverted):
        w = s6.width(state) + 6
        sc.rect(1, 1, w, 13, fill=inverted)
        if not inverted: sc.rect(1, 1, w, 13)
        sc.text(4, 2, state, s6, on=not inverted)
        sc.text(125, 3, "7.9V  SAT 9", s5, anchor="right")
        sc.hline(0, 128, 15)
    def bottom(sc, left, sheet):
        sc.hline(0, 128, 54, dotted=True)
        sc.text(2, 56, left, s5); sc.text(125, 56, sheet, s5, anchor="right")
    def channel(sc, y, n, name, state, fault=False):
        sc.text(2, y, f"{n} {name}", s6)
        w = s6.width(state) + 4
        if fault:                                # a fault is an outline box with "!": the inverted box means ARMED only
            state = "!" + state; w = s6.width(state) + 4
            sc.rect(125 - w, y - 1, w + 2, 12); sc.text(127 - w, y, state, s6)
        else: sc.text(125, y, state, s6, anchor="right")
    out_ = {}
    sc = Screen(128, 64); status_row(sc, "SAFE", False)
    channel(sc, 18, 1, "DROGUE", "CONT"); channel(sc, 30, 2, "MAIN", "CONT"); channel(sc, 42, 3, "-", "NOT USED")
    bottom(sc, "MODE  BEEP", "1/4"); out_["safe"] = sc
    sc = Screen(128, 64); status_row(sc, "ARMED", True)
    channel(sc, 18, 1, "DROGUE", "CONT"); channel(sc, 30, 2, "MAIN", "NO CONT", fault=True); channel(sc, 42, 3, "-", "NOT USED")
    bottom(sc, "SAFE: SWITCH OFF", "1/4"); out_["armed-fault"] = sc
    sc = Screen(128, 64); status_row(sc, "COAST", True)
    sc.text(2, 18, "T+6.2s", s6); sc.text(125, 18, "ALT ft AGL", s5, anchor="right")
    sc.text(125, 22, "3412", s16, anchor="right")
    bottom(sc, "V +412 ft/s", "2/4"); out_["flight"] = sc
    sc = Screen(128, 64); status_row(sc, "LANDED", False)
    sc.text(2, 18, "APOGEE", s6); sc.text(125, 18, "ft AGL", s5, anchor="right")
    sc.text(125, 22, "5104", s16, anchor="right")
    # the beep readout, drawn: 5 short, 1 short, zero = one long, 4 short, then two long to end the number
    x = 2; y = 58
    for digit in "5104":
        if digit == "0": sc.rect(x, y, 7, 3, fill=True); x += 10
        else:
            for _ in range(int(digit)): sc.rect(x, y, 2, 3, fill=True); x += 4
            x += 4
    sc.rect(x, y, 7, 3, fill=True); sc.rect(x + 10, y, 7, 3, fill=True)      # end of the number: two long tones
    sc.text(125, 56, "1+2 FIRED", s5, anchor="right"); out_["landed"] = sc
    # after landing with a charge that didn't fire: that comes first, before the altitude
    sc = Screen(128, 64); status_row(sc, "LANDED", False)
    sc.rect(0, 17, 128, 15, fill=True); sc.text(64, 19, "UNFIRED 2 MAIN", s6, on=False, anchor="middle")
    sc.text(2, 36, "APOGEE", s6); sc.text(125, 34, "5104", s8, anchor="right")
    sc.hline(0, 128, 54, dotted=True); sc.text(2, 56, "DISARM BEFORE HANDLING", s5); out_["landed-unfired"] = sc
    return out_

def tft_screen_svg():
    """240 x 240 color ground-station screen (dark roles): recovery, with the rocket's bearing and distance."""
    c = lambda r: role(r, "dark")
    mono = "font-family=\"Cascadia Mono\""
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240"><rect width="240" height="240" fill="{c("canvas")}"/>']
    o.append(f'<rect x="0" y="0" width="240" height="22" fill="{c("surface")}"/><text x="8" y="15" {mono} font-size="11" font-weight="600" fill="{c("ink")}">RECOVERY</text>')
    o.append(f'<text x="232" y="15" {mono} font-size="10" fill="{c("ink-muted")}" text-anchor="end">3.9 V  SAT 11  LINK 0.4 s</text>')
    o.append(f'<line x1="0" y1="22.5" x2="240" y2="22.5" stroke="{c("rule")}"/>')
    cx, cy, R = 70, 108, 50
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{c("rule-strong")}"/>')
    for a in range(0, 360, 30):
        r0 = R - (6 if a % 90 == 0 else 3)
        o.append(f'<line x1="{cx + r0 * math.sin(math.radians(a)):.1f}" y1="{cy - r0 * math.cos(math.radians(a)):.1f}" x2="{cx + R * math.sin(math.radians(a)):.1f}" y2="{cy - R * math.cos(math.radians(a)):.1f}" stroke="{c("ink-muted")}"/>')
    o.append(f'<text x="{cx}" y="{cy - R - 4}" {mono} font-size="9" fill="{c("ink-muted")}" text-anchor="middle">N</text>')
    b = math.radians(62); tip = (cx + (R - 10) * math.sin(b), cy - (R - 10) * math.cos(b))
    o.append(f'<line x1="{cx}" y1="{cy}" x2="{tip[0]:.1f}" y2="{tip[1]:.1f}" stroke="{c("ink")}" stroke-width="2"/>')
    o.append(f'<rect x="{tip[0] - 4:.1f}" y="{tip[1] - 4:.1f}" width="8" height="8" transform="rotate(45 {tip[0]:.1f} {tip[1]:.1f})" fill="{c("ink")}"/>')
    o.append(f'<rect x="{cx - 3}" y="{cy - 3}" width="6" height="6" fill="{c("ink")}"/>')
    o.append(f'<text x="136" y="50" {mono} font-size="9" fill="{c("ink-muted")}" letter-spacing="0.5">DISTANCE</text>')
    o.append(f'<text x="136" y="80" {mono} font-size="28" fill="{c("ink")}">1352</text><text x="210" y="80" {mono} font-size="11" fill="{c("ink-muted")}">ft</text>')
    o.append(f'<text x="136" y="104" {mono} font-size="9" fill="{c("ink-muted")}" letter-spacing="0.5">BEARING</text>')
    o.append(f'<text x="136" y="128" {mono} font-size="20" fill="{c("ink")}">062° T</text>')
    o.append(f'<text x="136" y="150" {mono} font-size="9" fill="{c("ink-muted")}">landed 18 s ago</text>')
    o.append(f'<line x1="0" y1="172.5" x2="240" y2="172.5" stroke="{c("rule")}"/>')
    o.append(f'<text x="8" y="190" {mono} font-size="10" fill="{c("ink-muted")}">40.86512, -119.06274</text>')
    o.append(f'<rect x="8" y="198" width="84" height="16" fill="{SIGNALS["ok"][2]}"/><text x="14" y="210" {mono} font-size="10" font-weight="600" fill="{WHITE}">GPS LOCKED</text>')
    o.append(f'<text x="232" y="232" {mono} font-size="9" fill="{c("ink-muted")}" text-anchor="end">3/4</text>')
    o.append('</svg>')
    return "\n".join(o)

LV_STYLES = """/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel */
/* FusionSpace styles for LVGL 9 (also LVGL 8: the lv_style_set_* calls are the same). Generated by
   tools/build/kit_product.py. Square corners, 1 px borders, no shadows, the dark roles from fusionspace_ui.h.

   Use: fs_lvgl_styles_init(); then lv_obj_add_style(obj, &fs_style_panel, 0); and so on, or apply them in a theme's
   apply callback built on the simple theme (lv_theme_simple_init). */
#include "lvgl.h"
#include "fusionspace_ui.h"

lv_style_t fs_style_screen, fs_style_panel, fs_style_button, fs_style_button_pressed, fs_style_label_muted,
           fs_style_state_safe, fs_style_state_armed, fs_style_chip_ok, fs_style_chip_caution, fs_style_chip_danger;

static void base(lv_style_t *s)
{
    lv_style_init(s);
    lv_style_set_radius(s, 0);
    lv_style_set_shadow_width(s, 0);
}

void fs_lvgl_styles_init(void)
{
    base(&fs_style_screen);
    lv_style_set_bg_color(&fs_style_screen, lv_color_hex(FS_CANVAS_RGB888));
    lv_style_set_bg_opa(&fs_style_screen, LV_OPA_COVER);
    lv_style_set_text_color(&fs_style_screen, lv_color_hex(FS_INK_RGB888));

    base(&fs_style_panel);
    lv_style_set_bg_color(&fs_style_panel, lv_color_hex(FS_SURFACE_RGB888));
    lv_style_set_bg_opa(&fs_style_panel, LV_OPA_COVER);
    lv_style_set_border_color(&fs_style_panel, lv_color_hex(FS_RULE_RGB888));
    lv_style_set_border_width(&fs_style_panel, 1);
    lv_style_set_pad_all(&fs_style_panel, 8);

    base(&fs_style_button);                      /* primary: ink fill, canvas text */
    lv_style_set_bg_color(&fs_style_button, lv_color_hex(FS_INK_RGB888));
    lv_style_set_bg_opa(&fs_style_button, LV_OPA_COVER);
    lv_style_set_text_color(&fs_style_button, lv_color_hex(FS_CANVAS_RGB888));
    lv_style_set_border_width(&fs_style_button, 0);
    lv_style_set_pad_hor(&fs_style_button, 16);
    lv_style_set_pad_ver(&fs_style_button, 8);

    base(&fs_style_button_pressed);              /* pressed: the action color */
    lv_style_set_bg_color(&fs_style_button_pressed, lv_color_hex(FS_ACTION_RGB888));
    lv_style_set_text_color(&fs_style_button_pressed, lv_color_hex(FS_ON_ACTION_RGB888));

    base(&fs_style_label_muted);
    lv_style_set_text_color(&fs_style_label_muted, lv_color_hex(FS_INK_MUTED_RGB888));

    base(&fs_style_state_safe);                  /* SAFE: an outline box */
    lv_style_set_border_color(&fs_style_state_safe, lv_color_hex(FS_INK_RGB888));
    lv_style_set_border_width(&fs_style_state_safe, 1);
    lv_style_set_pad_hor(&fs_style_state_safe, 4);

    base(&fs_style_state_armed);                 /* ARMED: an inverted box in the danger fill */
    lv_style_set_bg_color(&fs_style_state_armed, lv_color_hex(FS_DANGER_FILL_RGB888));
    lv_style_set_bg_opa(&fs_style_state_armed, LV_OPA_COVER);
    lv_style_set_text_color(&fs_style_state_armed, lv_color_hex(FS_ON_DANGER_FILL_RGB888));
    lv_style_set_pad_hor(&fs_style_state_armed, 4);

    base(&fs_style_chip_ok);
    lv_style_set_bg_color(&fs_style_chip_ok, lv_color_hex(FS_OK_FILL_RGB888));
    lv_style_set_bg_opa(&fs_style_chip_ok, LV_OPA_COVER);
    lv_style_set_text_color(&fs_style_chip_ok, lv_color_hex(FS_ON_OK_FILL_RGB888));
    lv_style_set_pad_hor(&fs_style_chip_ok, 4);

    base(&fs_style_chip_caution);
    lv_style_set_bg_color(&fs_style_chip_caution, lv_color_hex(FS_CAUTION_FILL_RGB888));
    lv_style_set_bg_opa(&fs_style_chip_caution, LV_OPA_COVER);
    lv_style_set_text_color(&fs_style_chip_caution, lv_color_hex(FS_ON_CAUTION_FILL_RGB888));
    lv_style_set_pad_hor(&fs_style_chip_caution, 4);

    base(&fs_style_chip_danger);
    lv_style_set_bg_color(&fs_style_chip_danger, lv_color_hex(FS_DANGER_FILL_RGB888));
    lv_style_set_bg_opa(&fs_style_chip_danger, LV_OPA_COVER);
    lv_style_set_text_color(&fs_style_chip_danger, lv_color_hex(FS_ON_DANGER_FILL_RGB888));
    lv_style_set_pad_hor(&fs_style_chip_danger, 4);
}
"""
LV_H = """/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel */
/* FusionSpace styles for LVGL. Generated by tools/build/kit_product.py. */
#ifndef FS_LVGL_STYLES_H
#define FS_LVGL_STYLES_H
#include "lvgl.h"
extern lv_style_t fs_style_screen, fs_style_panel, fs_style_button, fs_style_button_pressed, fs_style_label_muted,
                  fs_style_state_safe, fs_style_state_armed, fs_style_chip_ok, fs_style_chip_caution, fs_style_chip_danger;
void fs_lvgl_styles_init(void);
#endif
"""

def build_embedded():
    from PIL import Image
    os.makedirs(out("embedded"), exist_ok=True)
    scr = oled_screens()
    for k, sc in scr.items():
        sc.png(out(f"embedded/oled-128x64-{k}.png")); sc.png(out(f"embedded/oled-128x64-{k}@4x.png"), scale=4, gap=True)
    p_ = wr("embedded/tft-240x240-recovery.svg", tft_screen_svg())
    subprocess.run(["rsvg-convert", "-o", out("embedded/tft-240x240-recovery.png"), p_], check=True)
    subprocess.run(["rsvg-convert", "-z", "2", "-o", out("embedded/tft-240x240-recovery@2x.png"), p_], check=True)
    wr("embedded/fs_lvgl_styles.c", LV_STYLES); wr("embedded/fs_lvgl_styles.h", LV_H)
    shutil.copy(os.path.join(SRC, "embedded", "fonts", "LICENSE-Spleen.txt"), out("embedded/LICENSE-Spleen.txt"))
    # preview: the OLED screens at 4x in three columns, then the TFT screen at 2x
    pad, lab = 24, 22
    keys = ("safe", "armed-fault", "flight", "landed", "landed-unfired")
    tiles = [(k, Image.open(out(f"embedded/oled-128x64-{k}@4x.png"))) for k in keys]
    tw, th = tiles[0][1].size
    tft = Image.open(out("embedded/tft-240x240-recovery@2x.png")).convert("RGB")
    cols = 3; rows = 2
    W = pad * (cols + 2) + tw * cols + tft.width; H = max(pad * (rows + 1) + (th + lab) * rows, pad * 2 + lab + tft.height)
    from PIL import ImageDraw, ImageFont
    im = Image.new("RGB", (W, H), tuple(_hex_rgb(PAPER))); d = ImageDraw.Draw(im)
    try: font = ImageFont.truetype(os.path.join(build.ROOT, "type", "fonts", "CascadiaMono-Regular.ttf"), 14)
    except OSError: font = ImageFont.load_default()
    names = {"safe": "128 x 64 OLED · SAFE on the pad", "armed-fault": "ARMED (inverted) · channel 2 fault (outline)", "flight": "In flight · coast",
             "landed": "Landed · apogee and its beep code", "landed-unfired": "Landed · a charge that didn't fire"}
    for i, (k, t) in enumerate(tiles):
        x = pad + (i % cols) * (tw + pad); y = pad + (i // cols) * (th + lab + pad)
        d.text((x, y), names[k], fill=tuple(_hex_rgb("#566079")), font=font); im.paste(t, (x, y + lab))
    x = pad * (cols + 1) + tw * cols; d.text((x, pad), "240 x 240 TFT · ground station, recovery", fill=tuple(_hex_rgb("#566079")), font=font)
    im.paste(tft, (x, pad + lab))
    im.save(out("embedded/preview.png"))

# ================================================================ 10. boards (product/hardware/)
TB_W, TB_H = 34.0, 11.0          # board title block, mm
def titleblock_footprint(side):
    """KiCad footprint: a framed title block for the board silkscreen, with the mark and two lines of text that read the
    board's title-block fields (${TITLE}, ${REVISION}, ${ISSUE_DATE}). Back side is mirrored, as KiCad expects."""
    import kit_targets
    lay = f"{side}.SilkS"; mir = side == "B"
    X = lambda x: -x if mir else x
    polys, bb = kit_targets.mark_polys_mm(7.0, 0.15)
    mw = bb[2] - bb[0]; mh = bb[3] - bb[1]
    x0, y0 = -TB_W / 2, -TB_H / 2; c = 1.5                     # chamfer, top right
    outline = [(x0, y0), (x0 + TB_W - c, y0), (x0 + TB_W, y0 + c), (x0 + TB_W, y0 + TB_H), (x0, y0 + TB_H)]
    L = [f'(footprint "FusionSpace_TitleBlock_{side}" (version 20240108) (generator "fusionspace-kit") (layer "F.Cu")',
         f'  (descr "FusionSpace board title block, {TB_W:g} x {TB_H:g} mm, {lay}: the mark, ${{TITLE}}, rev ${{REVISION}}, ${{ISSUE_DATE}}")',
         "  (attr board_only exclude_from_pos_files exclude_from_bom)",
         f'  (property "Reference" "TB**" (at 0 {-TB_H / 2 - 1.5:.2f}) (layer "{side}.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))',
         f'  (property "Value" "FusionSpace_TitleBlock_{side}" (at 0 {TB_H / 2 + 1.5:.2f}) (layer "{side}.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))']
    for (ax, ay), (bx, by) in zip(outline, outline[1:] + outline[:1]):
        L.append(f'  (fp_line (start {X(ax):.3f} {ay:.3f}) (end {X(bx):.3f} {by:.3f}) (stroke (width 0.3) (type solid)) (layer "{lay}"))')
    sep = x0 + 2 + mw + 1.5
    L.append(f'  (fp_line (start {X(sep):.3f} {y0:.3f}) (end {X(sep):.3f} {y0 + TB_H:.3f}) (stroke (width 0.15) (type solid)) (layer "{lay}"))')
    L.append(f'  (fp_line (start {X(sep):.3f} {y0 + TB_H / 2:.3f}) (end {X(x0 + TB_W):.3f} {y0 + TB_H / 2:.3f}) (stroke (width 0.15) (type solid)) (layer "{lay}"))')
    ox = x0 + 1.25 - bb[0]; oy = y0 + (TB_H - mh) / 2 - bb[1]
    for poly in polys:
        pts = " ".join(f"(xy {X(x + ox):.4f} {y + oy:.4f})" for x, y in poly)
        L.append(f'  (fp_poly (pts {pts}) (stroke (width 0) (type solid)) (fill solid) (layer "{lay}"))')
    just = "left mirror" if mir else "left"
    tx = sep + 1.0
    for txt, yy in (("${TITLE}", y0 + TB_H / 4), ("REV ${REVISION}  ${ISSUE_DATE}", y0 + 3 * TB_H / 4)):
        L.append(f'  (fp_text user "{txt}" (at {X(tx):.3f} {yy:.3f}) (layer "{lay}") (effects (font (size {SILK["text_mm"]} {SILK["text_mm"]}) (thickness {SILK["line_mm"]})) (justify {just})))')
    L.append(")")
    return "\n".join(L) + "\n", (sep, mw, mh, polys, bb, ox, oy)

def titleblock_preview():
    """How the title block looks on a matte black board with white silk, filled in with example values."""
    _, (sep, mw, mh, polys, bb, ox, oy) = titleblock_footprint("F")
    k = 24; pad = 4.0; W, H = (TB_W + 2 * pad) * k, (TB_H + 2 * pad) * k
    T = lambda x, y: ((x + TB_W / 2 + pad) * k, (y + TB_H / 2 + pad) * k)
    x0, y0 = -TB_W / 2, -TB_H / 2; c = 1.5; silk = "#F3F4F7"
    pts = [(x0, y0), (x0 + TB_W - c, y0), (x0 + TB_W, y0 + c), (x0 + TB_W, y0 + TB_H), (x0, y0 + TB_H)]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}"><rect width="100%" height="100%" fill="#16181D"/>']
    o.append('<polygon points="' + " ".join(f"{T(x, y)[0]:.1f},{T(x, y)[1]:.1f}" for x, y in pts) + f'" fill="none" stroke="{silk}" stroke-width="{0.3 * k:.1f}"/>')
    a, b = T(sep, y0), T(sep, y0 + TB_H); o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{silk}" stroke-width="{0.15 * k:.1f}"/>')
    a, b = T(sep, y0 + TB_H / 2), T(x0 + TB_W, y0 + TB_H / 2); o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{silk}" stroke-width="{0.15 * k:.1f}"/>')
    for poly in polys:
        o.append('<polygon points="' + " ".join(f"{T(x + ox, y + oy)[0]:.1f},{T(x + ox, y + oy)[1]:.1f}" for x, y in poly) + f'" fill="{silk}"/>')
    for txt, yy in (("FS-VEGA-004", y0 + TB_H / 4), ("REV B  2026-10", y0 + 3 * TB_H / 4)):
        p_ = T(sep + 1.0, yy)
        o.append(f'<text x="{p_[0]:.1f}" y="{p_[1] + 0.42 * SILK["text_mm"] * k:.1f}" font-family="Cascadia Mono" font-size="{SILK["text_mm"] * k * 1.05:.1f}" fill="{silk}">{html.escape(txt)}</text>')
    o.append("</svg>")
    return "\n".join(o)

def build_hardware():
    for side in ("F", "B"):
        wr(f"hardware/FusionSpace.pretty/FusionSpace_TitleBlock_{side}.kicad_mod", titleblock_footprint(side)[0])
    p_ = wr("hardware/preview.svg", titleblock_preview())
    subprocess.run(["rsvg-convert", "-o", out("hardware/preview.png"), p_], check=True); os.remove(p_)
    wr("hardware/README.md", f"""# Board title block

`FusionSpace.pretty` holds a {TB_W:g} × {TB_H:g} mm title block for the board silkscreen: a 0.3 mm frame with the brand's
45° corner, the mark (7 mm), and two lines of {SILK["text_mm"]} mm text with a {SILK["line_mm"]} mm stroke. Put
`FusionSpace_TitleBlock_B` on the back of every board (`_F` if the back is full).

The text reads the board's title-block fields, so the silkscreen always matches the drawing: set them in KiCad under
File → Board Setup → Title Block (or Page Settings):

| Field | Example | Shows |
|---|---|---|
| Title | `FS-VEGA-004` | the board's part number |
| Revision | `B` | `REV B` |
| Issue date | `2026-10` | the date beside the revision |

Checked with KiCad 10.0.6 (October 5, 2026): both footprints load, and on a test board with Title `FS-VEGA-004`, Revision `B` and
Issue date `2026-10` the plotted silkscreen reads `FS-VEGA-004` and `REV B  2026-10`. If an older KiCad leaves the variables
unresolved, place two text items with the same text over the empty frame.

Rules for the rest of the board: `product/hardware.md`.
""")

# ================================================================ 11. rockets (product/rockets/)
FLUO = "#FF5A1F"                 # stands in for fluorescent orange on screen; order a fluorescent film or paint, not this hex
LIVERY_OD_IN = [1.64, 2.26, 3.1, 4.0, 6.17]
def livery_svg(od_in, length=220.0):
    """An unrolled wrap for one airframe: circumference across, a length of the tube down. Designation band, roll pattern,
    the two-tone mark, an overlap strip, and separate CG/CP and contact decals beside it. Units: mm, drawn 1:1."""
    od = od_in * 25.4; circ = math.pi * od; lap = 6.0; m = 12.0
    side = 70.0                                       # decal column on the right
    W = m + circ + lap + m + side + m; Hh = m + length + 8 + 26 + m
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}mm" height="{Hh:.1f}mm" viewBox="0 0 {W:.2f} {Hh:.2f}">',
         f'<rect width="{W:.2f}" height="{Hh:.2f}" fill="#FFFFFF"/>',
         '<defs><pattern id="lap" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="3" stroke="#98A1B8" stroke-width="0.3"/></pattern></defs>']
    x0, y0 = m, m
    T = lambda s, x, y, size, fill=VOID, anchor="start", weight=400: (f'<text x="{x:.2f}" y="{y:.2f}" font-family="Cascadia Mono" font-size="{size:.2f}" '
                                                                     f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{html.escape(s)}</text>')
    # body: Void
    o.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{circ:.2f}" height="{length:.2f}" fill="{VOID}"/>')
    # designation band near the top: white text on Void, repeated twice around
    band_y = y0 + 18; band_h = max(10.0, od * 0.16)
    o.append(f'<rect x="{x0:.2f}" y="{band_y:.2f}" width="{circ:.2f}" height="{band_h:.2f}" fill="{VOID}" stroke="#FFFFFF" stroke-width="0.4"/>')
    for i in range(2):
        o.append(T("FS-VEGA-001 REV B", x0 + circ * (i + 0.5) / 2, band_y + band_h * 0.68, band_h * 0.5, "#FFFFFF", "middle", 600))
    # roll pattern: four quadrants, alternating white and fluorescent orange, near the bottom (above the fin can)
    rp_h = min(90.0, length * 0.4); rp_y = y0 + length - rp_h
    for i in range(4):
        o.append(f'<rect x="{x0 + circ * i / 4:.2f}" y="{rp_y:.2f}" width="{circ / 4:.2f}" height="{rp_h:.2f}" fill="{"#FFFFFF" if i % 2 == 0 else FLUO}"/>')
    # quadrant marks along the top edge (0, 90, 180, 270 degrees)
    for i in range(4):
        x = x0 + circ * i / 4
        o.append(f'<line x1="{x:.2f}" y1="{y0 - 4:.2f}" x2="{x:.2f}" y2="{y0:.2f}" stroke="{VOID}" stroke-width="0.3"/>{T(f"{90 * i}°", x + 1, y0 - 1.5, 2.5)}')
    # the mark, two-tone, once, in the second quadrant between the band and the roll pattern
    import kit
    a = kit.art_mark(100.0); mh = min(25.0, (rp_y - band_y - band_h) * 0.6)
    defs, body = a.render("twotone-on-dark", "lv")
    sc = mh / a.h; mx = x0 + circ * 0.375 - a.w * sc / 2; my = band_y + band_h + ((rp_y - band_y - band_h) - mh) / 2
    o.append(f'<defs>{defs}</defs><g transform="translate({mx:.2f},{my:.2f}) scale({sc:.4f})">{body}</g>')
    # overlap strip
    o.append(f'<rect x="{x0 + circ:.2f}" y="{y0:.2f}" width="{lap:.2f}" height="{length:.2f}" fill="url(#lap)" stroke="#98A1B8" stroke-width="0.2"/>')
    o.append(f'<g transform="rotate(-90 {x0 + circ + lap / 2 + 0.9:.2f} {y0 + length / 2:.2f})">' + T("OVERLAP", x0 + circ + lap / 2 + 0.9, y0 + length / 2, 2.4, "#566079", "middle") + "</g>")
    # dimensions: circumference across the bottom
    dy = y0 + length + 5
    o.append(f'<line x1="{x0:.2f}" y1="{dy:.2f}" x2="{x0 + circ:.2f}" y2="{dy:.2f}" stroke="{VOID}" stroke-width="0.25"/>'
             f'<line x1="{x0:.2f}" y1="{dy - 2:.2f}" x2="{x0:.2f}" y2="{dy + 2:.2f}" stroke="{VOID}" stroke-width="0.25"/>'
             f'<line x1="{x0 + circ:.2f}" y1="{dy - 2:.2f}" x2="{x0 + circ:.2f}" y2="{dy + 2:.2f}" stroke="{VOID}" stroke-width="0.25"/>')
    o.append(T(f"π × {od:.1f} = {circ:.1f} mm (+ {lap:g} mm overlap)", x0 + circ / 2, dy - 1.2, 2.8, VOID, "middle"))
    # decals column: CG, CP, contact label, pyro warning
    cx = x0 + circ + lap + m; cy = y0
    def cg(x, y, r=6):
        return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="#FFFFFF" stroke="{VOID}" stroke-width="0.6"/>'
                f'<path d="M{x:.2f} {y:.2f} L{x:.2f} {y - r:.2f} A{r} {r} 0 0 1 {x + r:.2f} {y:.2f} Z" fill="{VOID}"/>'
                f'<path d="M{x:.2f} {y:.2f} L{x:.2f} {y + r:.2f} A{r} {r} 0 0 1 {x - r:.2f} {y:.2f} Z" fill="{VOID}"/>')
    def cp(x, y, r=6):
        return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="#FFFFFF" stroke="{VOID}" stroke-width="0.6"/><circle cx="{x:.2f}" cy="{y:.2f}" r="{r * 0.3:.2f}" fill="{VOID}"/>'
    o.append(T("DECALS", cx, cy + 3, 3, "#566079"))
    o.append(cg(cx + 8, cy + 14) + T("CG", cx + 17, cy + 15.5, 4, VOID, weight=600))
    o.append(cp(cx + 40, cy + 14) + T("CP", cx + 49, cy + 15.5, 4, VOID, weight=600))
    ly = cy + 28
    o.append(f'<rect x="{cx:.2f}" y="{ly:.2f}" width="{side:.2f}" height="30" fill="#FFFFFF" stroke="{VOID}" stroke-width="0.4"/>')
    o.append(f'<rect x="{cx:.2f}" y="{ly:.2f}" width="{side:.2f}" height="6" fill="{VOID}"/>' + T("IF FOUND · REWARD", cx + 2, ly + 4.4, 3.2, "#FFFFFF", weight=600))
    for i, s_ in enumerate(("NAME ______________________", "PHONE _____________________", "EMAIL _____________________", "FS-VEGA-001 REV B")):
        o.append(T(s_, cx + 2, ly + 11 + i * 5.2, 2.8))
    wy = ly + 36
    o.append(f'<rect x="{cx:.2f}" y="{wy:.2f}" width="{side:.2f}" height="22" fill="url(#hz{od_in:g})" />'.replace(f"#hz{od_in:g}", "hz"))
    o.insert(3, f'<defs><pattern id="hz" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="4" height="8" fill="{SIGNALS["caution"][2]}"/><rect x="4" width="4" height="8" fill="{VOID}"/></pattern></defs>')
    o.append(f'<rect x="{cx + 2.5:.2f}" y="{wy + 2.5:.2f}" width="{side - 5:.2f}" height="17" fill="#FFFFFF"/>')
    o.append(f'<rect x="{cx + 2.5:.2f}" y="{wy + 2.5:.2f}" width="{side - 5:.2f}" height="5.5" fill="{SIGNALS["danger"][2]}"/>' + T("WARNING", cx + 4.5, wy + 6.6, 3.2, "#FFFFFF", weight=600))
    o.append(T("LIVE PYRO WHEN ARMED", cx + 4.5, wy + 12.3, 2.9) + T("Switch off before opening", cx + 4.5, wy + 16.8, 2.6, "#566079"))
    # title block along the bottom right
    ty = Hh - m - 22; tx = W - m - 120
    o.append(f'<rect x="{tx:.2f}" y="{ty:.2f}" width="120" height="22" fill="#FFFFFF" stroke="{VOID}" stroke-width="0.5"/>')
    cells = [("TITLE", f"Livery wrap, {od:.1f} mm OD", 0, 0, 70), ("DESIGNATION", "FS-VEGA-001", 70, 0, 50),
             ("SCALE", "1 : 1", 0, 11, 25), ("UNITS", "mm", 25, 11, 20), ("COLORS", "Void · white · fluo orange", 45, 11, 75)]
    for k_, v, cx_, cy_, w_ in cells:
        o.append(f'<rect x="{tx + cx_:.2f}" y="{ty + cy_:.2f}" width="{w_}" height="11" fill="none" stroke="{VOID}" stroke-width="0.2"/>')
        o.append(T(k_, tx + cx_ + 1.5, ty + cy_ + 3.3, 2.0, "#566079") + T(v, tx + cx_ + 1.5, ty + cy_ + 8.4, 3.0))
    o.append(T("Print at 100 %. Measure the tube: wrap width = π × OD + overlap.", m, Hh - m - 2, 2.8, "#566079"))
    o.append("</svg>")
    return "\n".join(o), od

def build_rockets():
    os.makedirs(out("rockets"), exist_ok=True)
    for od_in in LIVERY_OD_IN:
        s_, od = livery_svg(od_in)
        name = f"livery-{od:.0f}mm"
        p_ = wr(f"rockets/{name}.svg", s_)
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", out(f"rockets/{name}.pdf"), p_], check=True)
    subprocess.run(["rsvg-convert", "-w", "1600", "-o", out("rockets/preview.png"), out(f"rockets/livery-{2.26 * 25.4:.0f}mm.svg")], check=True)
    wr("rockets/README.md", "# Livery wrap sheets\n\nUnrolled wraps for common airframe outside diameters, drawn 1:1 in millimeters (SVG and PDF): "
       + ", ".join(f"{d:g} in ({d * 25.4:.0f} mm)" for d in LIVERY_OD_IN) + ".\n\n"
       "Each has the designation band (twice around, so it reads from any side), a four-quadrant roll pattern above the fin "
       "can, the two-tone mark once, an overlap strip, and a column of separate decals: CG and CP symbols to place at your "
       "measured and computed stations, a contact label, and a pyro warning for the av-bay.\n\n"
       f"Orange is shown as `{FLUO}` on screen; order fluorescent orange vinyl or paint, which no screen or CMYK print can show. "
       "Replace the example designation with yours in the SVG (it's live text), and check the wrap width against your tube "
       "before cutting: π × outside diameter plus the overlap.\n\nRules: `product/rockets.md`.\n")

# ================================================================ 12. the guide's Products sheet
PRINCIPLES = [("Drawn, not decorated", "Every screen is a sheet from a drawing set: line types, title blocks, balloons. No ornament."),
              ("Show the working", "Formula, constants, inputs, sources and dates one step from every result."),
              ("Say how far to trust it", "Measured, predicted or copied, with its spread. Never a go/no-go verdict."),
              ("Built for the field", "Offline, readable in sun, usable with gloves, printable in black."),
              ("Quiet until it matters", "Four reserved signal colors, always with a word and a shape. Unused is gray, never red."),
              ("One sweep", "The gradient once per view, as identity: never a button, a status or a data scale."),
              ("Numbered like parts", "Every product has a designation and a revision, on screen and on the part."),
              ("Native where it counts", "The platform owns behavior; FusionSpace owns content.")]
GUIDE_CSS = (".fsp-chip{display:inline-flex;align-items:center;gap:6px;padding:3px 8px;font-family:var(--mono);font-size:11px;font-weight:600;"
             "letter-spacing:.06em;text-transform:uppercase}.fsp-row{display:flex;flex-wrap:wrap;gap:8px}.fsp-shot{display:block;border:1px solid var(--rule);width:100%;height:auto;aspect-ratio:4/3;object-fit:cover;object-position:top}"
             ".fsp-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}@media (max-width:640px){.fsp-grid{grid-template-columns:1fr}}"
             ".fsp-grid figure{margin:0}.fsp-grid figcaption{font-family:var(--mono);font-size:11px;color:var(--muted);margin-top:6px}")
def guide_sheet(n, total):
    chips = "".join(f'<span class="fsp-chip" style="background:{SIGNALS[k][2]};color:{SIGNALS[k][3]}">{w}</span>' for k, w in (("danger", "Armed"), ("caution", "Caution"), ("ok", "Continuity")))
    chips += f'<span class="fsp-chip" style="border:1px dashed {SIGNALS["predicted"][4]};color:var(--ink)">Predicted · Nebula</span>'
    rules = "".join(f'<div><h3>{i + 1} · {h}</h3><p>{t}</p></div>' for i, (h, t) in enumerate(PRINCIPLES))
    rows = "".join(f"<tr><td>product/{p}</td><td>{d}</td></tr>" for p, d in (
        ("README.md", "Start here: the reading order, the idea in one paragraph, how a project points here."),
        ("principles.md · foundations.md", "The eight principles; color roles, signals, themes, type, space, lines, motion, icons."),
        ("data.md · writing.md", "Numbers, units, readouts, charts, maps, telemetry; voice, errors, signal words."),
        ("web.md · cli.md · mobile.md · desktop.md", "Sites, tools and PWAs; command-line tools; iOS and Android; macOS, Windows and Linux."),
        ("embedded.md · hardware.md · rockets.md", "Flight computers and devices; boards, enclosures and labels; airframes and livery."),
        ("review.md", "The FusionSpace test, template smells, release checklists, sources."),
        ("tokens/ · web/ · icons/ · cli/ · mobile/ · embedded/ · hardware/ · rockets/ · desktop/", "Tokens for every platform and the reference parts.")))
    shots = "".join(f'<figure><img class="fsp-shot" src="../product/{p}" alt="{a}" loading="lazy"><figcaption>{a}</figcaption></figure>' for p, a in (
        ("web/previews/charge-light.png", "Charge, a tool page"), ("web/previews/flight-report-dark.png", "A flight report, dark theme"),
        ("embedded/preview.png", "Device screens"), ("rockets/preview.png", "Livery wrap, 57 mm"),
        ("mobile/preview.png", "Phones: four screens on iOS and Android"), ("mobile/glance/ios-live-activity.png", "A flight as a Live Activity")))
    return f'''
  <section class="sheet" id="products">
    <div class="sheet-head"><span class="sheet-no">SHEET {n} / {total}</span><h2>Products</h2><p class="muted" style="font-size:14px">How FusionSpace tools, apps, devices and rockets are designed. The rules are in <code>product/</code>.</p></div>
    <div class="sheet-body">
      <p>The brand says who made it; the product system says how the thing behaves. FusionSpace products are drawn, not decorated: every screen is a sheet from a drawing set, with line types that mean what they mean on a drawing, a title block, and a designation like a part. They show their working, say how far to trust each number, and are built for a launch field.</p>
      <div class="rules" style="grid-template-columns:repeat(2,minmax(0,1fr))">{rules}</div>
      <h3 style="margin-top:8px">Signal colors</h3>
      <p>Four colors that mean a state, kept apart from the brand colors and used with a word and a shape: Flare for danger, Sodium for caution, Aurora for normal, Nebula for predicted. They follow the flight-deck and spacecraft standards (14 CFR 25.1322, FAA AC 25-11B, NASA-STD-3001).</p>
      <div class="fsp-row">{chips}</div>
      <div class="fsp-grid">{shots}</div>
      <table class="files"><tbody>{rows}</tbody></table>
      <p class="muted" style="font-size:14px">Open <code>product/web/index.html</code> for the specimen in light, dark and the outdoor field theme.</p>
    </div>
  </section>
'''

# ================================================================ 13. desktop packaging (product/desktop/)
APP_ID = "co.fusionspace.HprSim"        # example: reverse DNS of fusionspace.co plus the app's name
def build_desktop():
    from PIL import Image
    ico_svg = os.path.join(build.OUT, "logo/favicon/icon.svg"); fav_svg = os.path.join(build.OUT, "logo/favicon/favicon.svg")
    app_svg = os.path.join(build.OUT, "logo/favicon/app-icon.svg")
    tmp = os.path.join(build.TMP, "desktop"); os.makedirs(tmp, exist_ok=True)
    def png(src, n, dest):
        os.makedirs(os.path.dirname(dest), exist_ok=True); build.rast(src, dest, n, n); return dest
    # Windows: ICO (16 hinted, 24-48 from the small-size favicon art, 256 from the icon) and MSIX tiles
    imgs = [build.hinted_favicon().convert("RGBA")]
    for n in (24, 32, 48): imgs.append(Image.open(png(fav_svg, n, os.path.join(tmp, f"f{n}.png"))).convert("RGBA"))
    imgs.append(Image.open(png(ico_svg, 256, os.path.join(tmp, "i256.png"))).convert("RGBA"))
    os.makedirs(out("desktop/windows/msix"), exist_ok=True)
    imgs[-1].save(out("desktop/windows/app.ico"), format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (256, 256)], append_images=imgs[:-1])
    for n in (16, 24, 32, 48, 256):
        src = fav_svg if n <= 48 else ico_svg
        for suffix in ("", "_altform-unplated", "_altform-lightunplated"):
            png(src, n, out(f"desktop/windows/msix/Square44x44Logo.targetsize-{n}{suffix}.png"))
    for sc in (100, 200, 400):
        png(ico_svg, round(44 * sc / 100), out(f"desktop/windows/msix/Square44x44Logo.scale-{sc}.png"))
        png(app_svg, round(150 * sc / 100), out(f"desktop/windows/msix/Square150x150Logo.scale-{sc}.png"))
    png(ico_svg, 50, out("desktop/windows/msix/StoreLogo.scale-100.png"))
    # Linux: hicolor scalable and 256 px, a symbolic icon (one color; the desktop recolors it)
    os.makedirs(out("desktop/linux/hicolor/scalable/apps"), exist_ok=True)
    shutil.copy(ico_svg, out(f"desktop/linux/hicolor/scalable/apps/{APP_ID}.svg"))
    png(ico_svg, 256, out(f"desktop/linux/hicolor/256x256/apps/{APP_ID}.png"))
    import kit
    a = kit.art_mark(100.0); defs, body = a.render("void", "sym"); k = 14 / max(a.w, a.h)
    sym = (f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><g transform="translate({(16 - a.w * k) / 2:.3f},{(16 - a.h * k) / 2:.3f}) scale({k:.5f})">'
           + body.replace(VOID, "#2e3436") + "</g></svg>\n")
    os.makedirs(out("desktop/linux/hicolor/symbolic/apps"), exist_ok=True)
    with open(out(f"desktop/linux/hicolor/symbolic/apps/{APP_ID}-symbolic.svg"), "w") as fh: fh.write(sym)
    wr(f"desktop/linux/{APP_ID}.desktop", f"""[Desktop Entry]
# SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
# FusionSpace desktop entry template. Rename the file and every {APP_ID} to your app's id.
Type=Application
Name=hpr-sim
GenericName=Rocket flight simulator
Comment=High-power rocketry flight simulator
Exec=hpr-sim %F
Icon={APP_ID}
Terminal=false
Categories=Science;Engineering;Education;
Keywords=rocket;rocketry;simulator;flight;
StartupWMClass=hpr-sim
""")
    wr(f"desktop/linux/{APP_ID}.metainfo.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel -->
<!-- FusionSpace AppStream template. Brand colors: Flathub asks for colorful ones, so O blue (light) and M orange (dark). -->
<component type="desktop-application">
  <id>{APP_ID}</id>
  <name>hpr-sim</name>
  <summary>High-power rocketry flight simulator</summary>
  <developer id="co.fusionspace"><name>FusionSpace</name></developer>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>Apache-2.0</project_license>
  <url type="homepage">https://fusionspace.co</url>
  <launchable type="desktop-id">{APP_ID}.desktop</launchable>
  <description>
    <p>Simulates hobby and high-power rocket flights, shows how far to trust each result, and works offline.</p>
  </description>
  <branding>
    <color type="primary" scheme_preference="light">{O_BLUE}</color>
    <color type="primary" scheme_preference="dark">{M_ORANGE}</color>
  </branding>
  <content_rating type="oars-1.1"/>
</component>
""")
    wr("desktop/linux/99-fusionspace.rules", """# SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
# FusionSpace devices: let the logged-in user open their serial ports without joining dialout or uucp.
# Install to /etc/udev/rules.d/ (packages: /usr/lib/udev/rules.d/), then: sudo udevadm control --reload && sudo udevadm trigger
# Set the vendor and product ids to your device's. Open-source hardware can get a free product id under pid.codes (vendor 1209).
SUBSYSTEM=="tty", ATTRS{idVendor}=="1209", ATTRS{idProduct}=="0001", MODE="0660", TAG+="uaccess"
""")
    wr("desktop/README.md", f"""# Desktop packaging

Icons and templates for FusionSpace apps on Windows and Linux; macOS icons are in `kit/apps/macos/` (build the `.icon` in Icon
Composer). The example app id is `{APP_ID}`: rename it for each app. Rules in `product/desktop.md`.

| Path | What |
|---|---|
| `windows/app.ico` | 16 (pixel-hinted), 24, 32, 48 and 256 px |
| `windows/msix/` | MSIX assets: Square44x44 scales and target sizes (with the light and dark unplated variants Windows needs), Square150x150, StoreLogo |
| `linux/hicolor/` | `scalable/apps/{APP_ID}.svg`, `256x256/apps/{APP_ID}.png`, `symbolic/apps/{APP_ID}-symbolic.svg` |
| `linux/{APP_ID}.desktop` | Desktop entry template |
| `linux/{APP_ID}.metainfo.xml` | AppStream metadata template, with the brand colors Flathub asks for |
| `linux/99-fusionspace.rules` | udev rule so users can open the device's serial port |
""")

# ================================================================ build
def shoot(rel_html, dest, width=1280, scheme="light", full=True, height=900):
    """PNG preview of a built page (Playwright). Returns False if Playwright isn't installed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    with sync_playwright() as p_:
        b = p_.chromium.launch(); pg = b.new_page(viewport={"width": width, "height": height}, color_scheme=scheme, device_scale_factor=1)
        pg.goto("file://" + out(rel_html)); pg.wait_for_timeout(400)
        os.makedirs(os.path.dirname(out(dest)), exist_ok=True); pg.screenshot(path=out(dest), full_page=full); b.close()
    return True

def build_icons():
    for n in kit_icons.ICONS: wr(f"icons/{n}.svg", kit_icons.svg(n) + "\n")
    for n in kit_icons.ICONS: wr(f"icons/android/fs_{n.replace('-', '_')}.xml", kit_icons.vector_drawable(n))
    wr("icons/sprite.svg", '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n' + "\n".join(kit_icons.symbol(n) for n in kit_icons.ICONS) + "\n</svg>\n")
    # contact sheet for the README: every icon at 48 px and at 24 px
    cols, cw, chh = 10, 132, 108
    names = [n for _, ns in kit_icons.GROUPS for n in ns]; rows = math.ceil(len(names) / cols)
    W, H = cols * cw, rows * chh + 16
    sv = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="{PAPER}"/>']
    for i, n in enumerate(names):
        x, y = (i % cols) * cw, (i // cols) * chh + 8
        sv.append(f'<g transform="translate({x + 22},{y + 6}) scale(2)" color="{VOID}"><g {kit_icons.ATTRS}>{kit_icons.ICONS[n]}</g></g>')
        sv.append(f'<g transform="translate({x + 84},{y + 18})" color="{VOID}"><g {kit_icons.ATTRS}>{kit_icons.ICONS[n]}</g></g>')
        sv.append(f'<text x="{x + 22}" y="{y + 80}" font-family="Cascadia Mono" font-size="11" fill="#566079">{n}</text>')
    sv.append("</svg>")
    p_ = wr("icons/preview.svg", "\n".join(sv) + "\n")
    subprocess.run(["rsvg-convert", "-o", out("icons/preview.png"), p_], check=True); os.remove(p_)

def build_web():
    build_fonts(); build_stylesheet()
    wr("web/tailwind-theme.css", tailwind_theme())
    wr("web/mdbook/fusionspace-mdbook.css", mdbook_css())
    pred, meas = example_flight()
    for th in ("light", "dark"):
        p_ = wr(f"web/previews/chart-{th}.svg", chart_svg(pred, meas, standalone_theme=th))
        subprocess.run(["rsvg-convert", "-w", "1320", "-o", out(f"web/previews/chart-{th}.png"), p_], check=True)
    wr("web/index.html", specimen(None))
    for n, fn in (("home", ex_home), ("charge", ex_charge), ("flight-report", ex_flight_report), ("window", ex_window)):
        wr(f"web/examples/{n}.html", fn())
    shots = [("web/index.html", "web/previews/specimen-light.png", 1280, "light"), ("web/index.html", "web/previews/specimen-dark.png", 1280, "dark"),
             ("web/examples/home.html", "web/previews/home-light.png", 1280, "light"), ("web/examples/home.html", "web/previews/home-dark.png", 1280, "dark"),
             ("web/examples/charge.html", "web/previews/charge-light.png", 1280, "light"), ("web/examples/charge.html", "web/previews/charge-phone.png", 390, "light"),
             ("web/examples/flight-report.html", "web/previews/flight-report-dark.png", 1280, "dark"), ("web/examples/flight-report.html", "web/previews/flight-report-light.png", 1280, "light"),
             ("web/examples/window.html", "web/previews/window-field.png", 1280, "light"), ("web/examples/window.html", "web/previews/window-phone.png", 390, "light")]
    ok = all(shoot(a, b, w, sc) for a, b, w, sc in shots)
    if not ok: print("WARN product: no Playwright, web previews skipped")

FOLDER_READMES = {
    "tokens/README.md": "# Tokens\n\nEvery value in `product/foundations.md`, generated by `tools/build/kit_product.py`. Copy the file for your platform into the project; "
                        "don't edit the copy, change the build and copy again.\n\n| File | For |\n|---|---|\n"
                        "| `primitives.tokens.json` + `light`, `dark`, `field.tokens.json` | Design Tokens Community Group format 2025.10 (Style Dictionary 5 and others) |\n"
                        "| `fusionspace-ui.css` | Web custom properties; the full stylesheet is `../web/fusionspace.css` |\n"
                        "| `FusionSpaceColors.swift` | SwiftUI |\n| `FusionSpaceColors.kt` | Jetpack Compose |\n| `fusionspace_ui.h` | Firmware (RGB888, RGB565, flash timings) |\n",
    "icons/README.md": "# Icons\n\nOne SVG per icon (24 x 24, `currentColor`, 1.5 px strokes), `sprite.svg` with every icon as a `<symbol id=\"fs-name\">`, and `android/` with each as a VectorDrawable (`fs_name.xml`, tinted by the theme). "
                       "Rules in `product/foundations.md#icons`.\n\n![Icons](preview.png)\n",
    "web/README.md": "# Web\n\n| File | What |\n|---|---|\n| `fusionspace.css` | Tokens and every component |\n| `tailwind-theme.css` | Tailwind v4 theme with the defaults removed |\n"
                     "| `fonts.css`, `fonts/` | WOFF2 subsets of Archivo and Cascadia Mono (SIL OFL) |\n| `index.html` | The specimen |\n"
                     "| `examples/` | Home (a drawing register), Charge, a flight report, Window |\n| `mdbook/` | mdBook theme |\n| `previews/` | Screenshots used in the docs |\n\nRules in `product/web.md`.\n",
    "embedded/README.md": "# Device screens\n\n| File | What |\n|---|---|\n| `oled-128x64-*.png` | 1:1 frame buffers (and `@4x` previews): SAFE, ARMED with a fault, in flight, landed |\n"
                          "| `tft-240x240-recovery.*` | A color ground-station screen in the dark roles |\n| `fs_lvgl_styles.c/.h` | LVGL styles (checked against LVGL 9.3) |\n\n"
                          "Text on the OLED screens is Spleen (BSD-2, `LICENSE-Spleen.txt`), which u8g2 includes. Rules in `product/embedded.md`.\n",
    "cli/README.md": "# Command line\n\n`fs_style.rs` (Rust: clap, anstyle, anstream) and `fs_style.py` (Python, no dependencies) put the ANSI roles from "
                     "`product/cli.md` into code. `sample-output.txt` is the example in `preview.png`.\n",
}

def build_product():
    rows, cvd = build_tokens()
    import kit_mobile
    build_icons(); build_web(); build_cli(); build_embedded(); build_hardware(); build_rockets(); build_desktop(); kit_mobile.build_mobile(); build_docs()
    for k, v in FOLDER_READMES.items(): wr(k, v)
    return {"contrast": rows, "cvd": cvd}

if __name__ == "__main__":
    r = build_product()
    for t, fg, bg, a, b, ratio, mn in r["contrast"]: print(f"{t:6s} {fg:14s} on {bg:8s} {a} / {b}  {ratio:5.2f}  (min {mn})")
    for t, a, b, d in r["cvd"]: print(f"cvd {t:5s} {a:9s} {b:9s} {d:5.1f}")
