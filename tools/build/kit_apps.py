"""FusionSpace kit: native app icons and store art (kit/apps/).

Sizes and safe zones (checked October 2, 2026):
  iOS / iPadOS   one 1024 x 1024 icon, square, no transparency (the system applies the rounded mask). Xcode 26's Icon
                 Composer builds layered icons (background + foreground, with Dark and Tinted appearances) from separate layers.
  macOS          1024 x 1024 canvas; the icon body is an 824 x 824 rounded square (radius about 185) centered, with room for a shadow.
  Android        adaptive icon: 108 dp square layers (432 px at xxxhdpi); the launcher mask shows the inner 72 dp and
                 anything important must sit inside the central 66 dp circle. Separate foreground, background and monochrome layers.
  Google Play    512 x 512 icon (32-bit PNG, full square: Play rounds the corners) and a 1024 x 500 feature graphic (no alpha).
"""
import os
from PIL import Image
import build, kit
from kit import KIT, note, out, save_svg, png, svg_open, layer, text, background, theme, art_mark, art_horizontal, f, VOID, PAPER, WHITE, TAGLINE

def cluster(S, r_frac, mode="color", prefix="a", cx=None, cy=None):
    """Cluster centered on (cx, cy) with its farthest point r_frac x S from the center."""
    a = art_mark(200); k = build.app_frac() * (r_frac / build.APP_SAFE_R) * S / max(a.w, a.h)
    cx = S / 2 if cx is None else cx; cy = S / 2 if cy is None else cy
    return a.place(mode, prefix, cx - a.w * k / 2, cy - a.h * k / 2, k)

def icon(S, r_frac, bg=VOID, mode="color", rx=0, title="FusionSpace app icon", inset=0.0):
    defs, g = cluster(S, r_frac, mode)
    s = svg_open(S, S, title, page=PAPER) + f'<defs id="defs">{defs}</defs>\n'
    if bg: s += layer("Background", f'<rect x="{f(inset)}" y="{f(inset)}" width="{f(S - 2 * inset)}" height="{f(S - 2 * inset)}" rx="{f(rx)}" fill="{bg}"/>\n')
    return s + layer("Mark", g + "\n") + "</svg>\n"

def build_apps():
    D = f"{KIT}/apps"; G = "App icons & store art"
    # iOS: square, opaque, Apple masks it. Same framing as the apple-touch-icon (farthest point on the 0.40 circle).
    src = save_svg(f"{D}/ios/AppIcon-1024.svg", icon(1024, 0.40, title="FusionSpace iOS app icon"))
    png(src, f"{D}/ios/AppIcon-1024.png", 1024, 1024)
    Image.open(out(f"{D}/ios/AppIcon-1024.png")).convert("RGB").save(out(f"{D}/ios/AppIcon-1024.png"))   # no alpha channel
    # Icon Composer layers (iOS 26 / macOS 26): background color + foreground art on transparent. The tinted appearance
    # is made by the system from the foreground's luminance, so a white foreground is supplied too.
    save_svg(f"{D}/ios/icon-composer/foreground.svg", icon(1024, 0.40, bg=None, title="FusionSpace icon foreground (Icon Composer)"))
    save_svg(f"{D}/ios/icon-composer/foreground-white.svg", icon(1024, 0.40, bg=None, mode="white", title="FusionSpace icon foreground, white (tinted/clear)"))
    save_svg(f"{D}/ios/icon-composer/background.svg", svg_open(1024, 1024, "FusionSpace icon background", page=VOID)
             + layer("Background", f'<rect width="1024" height="1024" fill="{VOID}"/>\n') + "</svg>\n")
    # macOS: rounded body 824 x 824 inside a 1024 canvas; art kept inside the body's own 0.40 circle
    body = 824; inset = (1024 - body) / 2
    defs, g = cluster(1024, 0.40 * body / 1024, "color", "m")
    s = (svg_open(1024, 1024, "FusionSpace macOS app icon", page=PAPER) + f'<defs id="defs">{defs}'
         f'<filter id="sh" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceAlpha" stdDeviation="12"/><feOffset dy="10" result="b"/><feComponentTransfer in="b" result="s"><feFuncA type="linear" slope="0.30"/></feComponentTransfer><feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>\n'
         + layer("Body", f'<rect x="{f(inset)}" y="{f(inset)}" width="{body}" height="{body}" rx="185" fill="{VOID}" filter="url(#sh)"/>\n')
         + layer("Mark", g + "\n") + "</svg>\n")
    src = save_svg(f"{D}/macos/AppIcon-1024.svg", s); png(src, f"{D}/macos/AppIcon-1024.png", 1024, 1024)
    for z in (16, 32, 64, 128, 256, 512): png(src, f"{D}/macos/AppIcon-{z}.png", z, z)
    # Android adaptive icon: 432 px layers (108 dp at 4x). Art inside the 66 dp safe circle (radius 0.3056 of the layer).
    R = 33 / 108
    src = save_svg(f"{D}/android/ic_launcher_foreground.svg", icon(432, R * 0.98, bg=None, title="FusionSpace adaptive icon foreground (108 dp)"))
    png(src, f"{D}/android/ic_launcher_foreground.png", 432, 432)
    src = save_svg(f"{D}/android/ic_launcher_background.svg", svg_open(432, 432, "FusionSpace adaptive icon background", page=VOID)
                   + layer("Background", f'<rect width="432" height="432" fill="{VOID}"/>\n') + "</svg>\n")
    png(src, f"{D}/android/ic_launcher_background.png", 432, 432)
    src = save_svg(f"{D}/android/ic_launcher_monochrome.svg", icon(432, R * 0.98, bg=None, mode="white", title="FusionSpace adaptive icon monochrome (themed icons)"))
    png(src, f"{D}/android/ic_launcher_monochrome.png", 432, 432)
    build.wr(f"{D}/android/ic_launcher.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- res/mipmap-anydpi-v26/ic_launcher.xml. Put the three PNGs in res/mipmap-xxxhdpi/ (or import the SVGs as vector drawables). -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
    <monochrome android:drawable="@mipmap/ic_launcher_monochrome"/>
</adaptive-icon>
''')
    # mask preview: what launchers show (circle, squircle, rounded square) — for review only
    fg = Image.open(out(f"{D}/android/ic_launcher_foreground.png")).convert("RGBA")
    bgc = Image.new("RGBA", fg.size, VOID); bgc.alpha_composite(fg)
    from PIL import ImageDraw
    tiles = []
    for shape in ("circle", "squircle", "rounded"):
        m = Image.new("L", (432, 432), 0); dr = ImageDraw.Draw(m); v0, v1 = 72, 360        # the visible 72 dp viewport
        if shape == "circle": dr.ellipse((v0, v0, v1, v1), fill=255)
        elif shape == "squircle": dr.rounded_rectangle((v0, v0, v1, v1), radius=110, fill=255)
        else: dr.rounded_rectangle((v0, v0, v1, v1), radius=48, fill=255)
        t = Image.new("RGBA", (432, 432), (0, 0, 0, 0)); t.paste(bgc, (0, 0), m); tiles.append(t.crop((v0 - 8, v0 - 8, v1 + 8, v1 + 8)))
    sheet = Image.new("RGBA", (sum(t.width for t in tiles) + 40, tiles[0].height + 20), (243, 244, 247, 255)); x = 10
    for t in tiles: sheet.alpha_composite(t, (x, 10)); x += t.width + 10
    sheet.save(out(f"{D}/android/adaptive-masks-preview.png"))
    # Google Play: 512 icon (full square, Play rounds it) and 1024 x 500 feature graphic (no alpha)
    src = save_svg(f"{D}/google-play/play-icon-512.svg", icon(512, 0.40, title="FusionSpace Google Play icon"))
    png(src, f"{D}/google-play/play-icon-512.png", 512, 512); os.remove(src)
    w, h = 1024, 500; t = theme(True)
    bdefs, bg = background(w, h, True, "fg", cell=h / 5, strip="bottom", strip_h=h / 60)
    a = art_horizontal(); k = 0.24 * h / a.h
    ldefs, lg = a.place("color", "fgl", (w - a.w * k) / 2, h * 0.40 - a.h * k / 2, k)
    s = (svg_open(w, h, "FusionSpace Google Play feature graphic", page=VOID) + f'<defs id="defs">{bdefs}{ldefs}</defs>\n' + bg + layer("Brand", lg + "\n")
         + layer("Text (edit me)", text(w / 2, h * 0.40 + a.h * k / 2 + 64, TAGLINE.upper(), 24, t["label"], anchor="middle", label="Tagline or app name (edit me)", spacing=2.4)) + "</svg>\n")
    src = save_svg(f"{D}/google-play/feature-graphic-1024x500.svg", s); png(src, f"{D}/google-play/feature-graphic-1024x500.png", w, h)
    Image.open(out(f"{D}/google-play/feature-graphic-1024x500.png")).convert("RGB").save(out(f"{D}/google-play/feature-graphic-1024x500.png"))
    build.wr(f"{D}/README.md", """# FusionSpace app icons and store art

Checked October 2, 2026 against Apple's and Google's current guidance.

| Folder | Files | Where |
|---|---|---|
| `ios/` | `AppIcon-1024.png` (opaque, square: iOS rounds it), `.svg` | Xcode asset catalog, App Store |
| `ios/icon-composer/` | `background.svg`, `foreground.svg`, `foreground-white.svg` | Icon Composer (Xcode 26): drop the layers in, set Dark and Tinted appearances (white foreground for Tinted/Clear) |
| `macos/` | `AppIcon-1024.png` and 16–512 px: rounded 824 px body on a 1024 canvas, with shadow | macOS apps, `.icns` (`iconutil`) |
| `android/` | `ic_launcher_foreground/background/monochrome` (432 px = 108 dp at xxxhdpi, plus SVGs), `ic_launcher.xml` | Adaptive icon (`mipmap-anydpi-v26`); the art sits inside the 66 dp safe circle, so every launcher mask keeps it whole |
| `google-play/` | `play-icon-512.png`, `feature-graphic-1024x500.png` | Play Console store listing |

Web and PWA icons are in `kit/web/`. Edit the feature graphic's text layer for a specific app (or generate per-project art with
`tools/build/project.py`).
""")
    note(f"{D}/ios/AppIcon-1024.png/.svg", G, "iOS app icon, opaque square (iOS applies the mask)", "1024", "Xcode, App Store")
    note(f"{D}/ios/icon-composer/", G, "Icon Composer layers: background, foreground, white foreground", "1024, vector", "Xcode 26 layered icons (Dark, Tinted)")
    note(f"{D}/macos/AppIcon-*.png", G, "macOS app icon: rounded body with shadow", "16–1024", "macOS apps, .icns")
    note(f"{D}/android/ic_launcher_*", G, "Android adaptive icon layers and XML", "432 (108 dp)", "Android launcher, themed icons")
    note(f"{D}/android/adaptive-masks-preview.png", G, "how launchers crop the adaptive icon (circle, squircle, rounded square)", "", "Checking only")
    note(f"{D}/google-play/play-icon-512.png", G, "Google Play icon, full square", "512", "Play Console")
    note(f"{D}/google-play/feature-graphic-1024x500.png/.svg", G, "Google Play feature graphic", "1024 × 500", "Play Console")
