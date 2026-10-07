"""Clipping check for drawn screens (product/mobile/, product/watch/): the build stops if anything is cut by an edge or a corner.

The page reports every text run (one rect per line of every text node, SVG text included) and every box that carries
meaning (status chips, tags, state boxes, buttons, with their own corner radius); this module tests each against:

- its frame's shape: the device's real screen outline (a mask taken from the simulator, source/product/devices/masks/:
  Apple's corners are continuous curves, not arcs), a circle (Wear OS), or a rounded rectangle (widgets, cards), inset by
  a margin;
- on phone screens, the visible content area: below the status bar and the app's top bar, above the tab bar, navigation
  bar, fixed bottom panel and home indicator. Content may not run under a bar and look finished.

A box is tested along its own rounded outline (a capsule's corners are round), text by its rectangle.

The same module checks web pages (check_pages: no sideways scrolling, no text cut by a box, no text on text), SVG
graphics (check_svgs: every visible line of text inside the canvas and off the other text), the real-screen captures
(check_captures: no text cut short with "…", and every element of ours inside the screen's own outline) and the Office
templates (check_office: rendered by LibreOffice with the repo's fonts, every line inside its box, the page and the text
column, off other text, and no page pushed on).
"""
import os, math
import build

MASKS = os.path.join(build.SRC, "product", "devices", "masks")

JS = r"""
(cfg) => {
  const label = (el, txt) => (txt || el.textContent || el.getAttribute('aria-label') || el.tagName)
                               .toString().trim().replace(/\s+/g, ' ').slice(0, 40);
  const R = (r) => [r.left, r.top, r.right, r.bottom];
  const items = (root) => {
    const res = [];
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      if (!n.textContent.trim()) continue;
      const el = n.parentElement, cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) continue;
      const range = document.createRange(); range.selectNodeContents(n);
      for (const r of range.getClientRects()) if (r.width > 0.5 && r.height > 0.5) res.push({r: R(r), what: label(el, n.textContent), br: 0});
    }
    for (const el of root.querySelectorAll(cfg.boxes)) {
      const r = el.getBoundingClientRect();
      if (r.width > 0.5 && r.height > 0.5)
        res.push({r: R(r), what: label(el), br: Math.min(parseFloat(getComputedStyle(el).borderBottomLeftRadius) || 0, r.height / 2, r.width / 2)});
    }
    return res;
  };
  const frames = cfg.frames.map(f => [...document.querySelectorAll(f.selector)].map(el => ({
    selector: f.selector, rect: R(el.getBoundingClientRect()),
    radius: f.radius ?? (parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0), items: items(el)})));
  let content = null;
  if (cfg.content) {
    const c = document.querySelector(cfg.content.selector);
    if (c) {
      const top = Math.max(0, ...cfg.content.above.flatMap(s => [...document.querySelectorAll(s)]).map(e => e.getBoundingClientRect().bottom));
      const bottom = Math.min(innerHeight, ...cfg.content.below.flatMap(s => [...document.querySelectorAll(s)]).map(e => e.getBoundingClientRect().top));
      content = {top, bottom, items: items(c)};
    }
  }
  // overlays: buttons, bars and panels drawn over content. Text that isn't part of one may not sit under it.
  const over = [];
  for (const sel of (cfg.overlays || [])) for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect(), hidden = [];
    if (r.width < 0.5 || r.height < 0.5) continue;
    for (const [frameEl] of [[document.body]]) {
      const walker = document.createTreeWalker(frameEl, NodeFilter.SHOW_TEXT); let n;
      while ((n = walker.nextNode())) {
        if (!n.textContent.trim() || el.contains(n)) continue;
        const range = document.createRange(); range.selectNodeContents(n);
        for (const t of range.getClientRects()) {
          const ix = Math.min(t.right, r.right) - Math.max(t.left, r.left), iy = Math.min(t.bottom, r.bottom) - Math.max(t.top, r.top);
          if (ix > 1 && iy > 1) hidden.push(label(n.parentElement, n.textContent));
        }
      }
    }
    for (const h of hidden) over.push(`"${h}" sits under ${sel}`);
  }
  // text on text: two different text runs may not overlap (labels colliding in a map or chart, a value over its unit)
  const runs = [];
  for (const fsel of cfg.frames) for (const frameEl of document.querySelectorAll(fsel.selector)) {
    const walker = document.createTreeWalker(frameEl, NodeFilter.SHOW_TEXT); let n;
    while ((n = walker.nextNode())) {
      if (!n.textContent.trim()) continue;
      const cs = getComputedStyle(n.parentElement);
      if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) continue;
      const range = document.createRange(); range.selectNodeContents(n);
      for (const r of range.getClientRects()) if (r.width > 0.5 && r.height > 0.5) runs.push([n, r]);
    }
  }
  const clash = [];
  for (let i = 0; i < runs.length; i++) for (let j = i + 1; j < runs.length; j++) {
    const [a, ra] = runs[i], [b, rb] = runs[j];
    if (a === b) continue;
    // glyph boxes include line-gap; count it only when the ink areas overlap by more than a sliver
    const ix = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left), iy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
    if (ix > 2 && iy > Math.min(ra.height, rb.height) * 0.35)
      clash.push(`"${label(a.parentElement, a.textContent)}" overlaps "${label(b.parentElement, b.textContent)}"`);
  }
  return {frames: frames.flat(), content, over, clash};
}
"""

BOXES = (".fs-status, .fs-tag, .m-state .box, .w-box, .g-box, .g-boxs, .w-caution, .c-caution, .hold, .safe, "
         ".wt-btn, .lbtn, .chip, .lu-sem, .c-box, .m-tb, .m-map, .m-chart, .list, .m-phases")      # edge buttons (.edgebtn, .t-edge) take the bezel's own curve; their labels are checked
K = 1 - 1 / math.sqrt(2)          # how far a rounded corner's outline sits inside its bounding box, per unit radius

_mask_cache = {}
def _mask(name):
    if name not in _mask_cache:
        from PIL import Image
        _mask_cache[name] = Image.open(os.path.join(MASKS, name + ".png")).convert("L")
    return _mask_cache[name]

def _points(it):
    l, t, r, b = it["r"]; i = it["br"] * K
    return [(l + i, t + i), (r - i, t + i), (l + i, b - i), (r - i, b - i)]

def _inside(x, y, f, spec, margin):
    l, t, r, b = f["rect"]
    if spec.get("mask"):
        m = _mask(spec["mask"]); sx = m.width / (r - l); sy = m.height / (b - t)
        # inside the outline, and the margin inside too (test the four points one margin away)
        for dx, dy in ((0, 0), (-margin, 0), (margin, 0), (0, -margin), (0, margin)):
            px, py = int((x + dx - l) * sx), int((y + dy - t) * sy)
            if not (0 <= px < m.width and 0 <= py < m.height) or m.getpixel((px, py)) < 128: return False
        return True
    if spec.get("circle"):
        cx, cy, rad = (l + r) / 2, (t + b) / 2, min(r - l, b - t) / 2 - margin
        return (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad
    L, T, Rr, B, rad = l + margin, t + margin, r - margin, b - margin, max(0.0, f["radius"] - margin)
    if x < L - 0.5 or x > Rr + 0.5 or y < T - 0.5 or y > B + 0.5: return False
    cx = L + rad if x < L + rad else Rr - rad if x > Rr - rad else x
    cy = T + rad if y < T + rad else B - rad if y > B - rad else y
    return (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad + 0.5

def check(page, frames, content=None, margin=1, overlays=None):
    """frames: [{selector, radius? | circle? | mask?}]; content: {selector, above: [...], below: [...]}; overlays: selectors
    of things drawn over content (buttons, bars) that no other text may sit under. Returns problems."""
    got = page.evaluate(JS, {"frames": [{k: v for k, v in f.items() if k in ("selector", "radius")} for f in frames],
                             "content": content, "boxes": BOXES, "overlays": overlays or []})
    spec = {f["selector"]: f for f in frames}
    out = []
    for f in got["frames"]:
        s = spec[f["selector"]]
        for it in f["items"]:
            if not all(_inside(x, y, f, s, margin) for x, y in _points(it)):
                out.append(f'{f["selector"]}: "{it["what"]}" is cut by the {"round edge" if s.get("circle") else "edge or corner"}')
    c = got["content"]
    if c:
        for it in c["items"]:
            l, t, r, b = it["r"]
            if t < c["top"] - 0.5 or b > c["bottom"] + 0.5:
                out.append(f'content: "{it["what"]}" runs under a bar ({round(t)}-{round(b)} outside {round(c["top"])}-{round(c["bottom"])})')
    out += got["over"] + got["clash"]
    return list(dict.fromkeys(out))

def assert_clean(problems, where):
    if problems:
        raise SystemExit(f"clipping in {where}:\n  " + "\n  ".join(problems))

# ================================================================ web pages
PAGE_JS = r"""
() => {
  const out = [];
  const de = document.documentElement;
  if (de.scrollWidth > innerWidth + 1) {
    // the widest offenders, so the report says what to fix
    const wide = [...document.querySelectorAll('body *')].filter(e => {
      const r = e.getBoundingClientRect(); return r.right > innerWidth + 1 && r.width > 0 && getComputedStyle(e).position !== 'fixed';
    }).filter(e => !e.closest('[data-scroll-x], .fs-table-wrap, pre, .scroll-x')).slice(0, 4)
      .map(e => (e.className && e.className.baseVal === undefined ? '.' + String(e.className).split(' ')[0] : e.tagName.toLowerCase()) + ` (to ${Math.round(e.getBoundingClientRect().right)})`);
    if (wide.length) out.push(`page scrolls sideways: ${de.scrollWidth} > ${innerWidth}: ${wide.join(', ')}`);
  }
  const label = (el, t) => (t || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40);
  const runs = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
  while ((n = walker.nextNode())) {
    if (!n.textContent.trim()) continue;
    const el = n.parentElement; if (!el || el.closest('script, style, noscript, select, option, textarea')) continue;
    const cs = getComputedStyle(el);
    // only what the browser actually draws (closed <details>, display:none ancestors, hidden or transparent text)
    if (!el.checkVisibility({contentVisibilityAuto: true, opacityProperty: true, visibilityProperty: true})) continue;
    if (el.closest('details:not([open])') && !el.closest('summary')) continue;
    const range = document.createRange(); range.selectNodeContents(n);
    const rects = [...range.getClientRects()].filter(r => r.width > 0.5 && r.height > 0.5);
    if (!rects.length) continue;
    // cut by an ancestor that hides overflow (inside a horizontal scroller is fine: it scrolls)
    for (let a = el; a && a !== document.body; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (/(auto|scroll)/.test(s.overflowX + s.overflowY)) break;
      if (/(hidden|clip)/.test(s.overflowX + s.overflowY) || s.textOverflow === 'ellipsis') {
        const ar = a.getBoundingClientRect();
        if (rects.some(r => r.left < ar.left - 1 || r.right > ar.right + 1 || r.top < ar.top - 1 || r.bottom > ar.bottom + 1)) {
          out.push(`"${label(el, n.textContent)}" is cut by its container (${a.tagName.toLowerCase()}.${String(a.className).split(' ')[0]})`); break;
        }
      }
    }
    if (el.scrollWidth > el.clientWidth + 1 && /(hidden|clip)/.test(cs.overflowX) ) out.push(`"${label(el, n.textContent)}" overflows its own box`);
    // overlap: rotated SVG labels have loose axis-aligned boxes (skip them); text in a scroller counts only where it shows
    if (el instanceof SVGGraphicsElement) { const m = el.getCTM(); if (m && Math.abs(m.b) > 0.01) continue; }
    let sc = null;
    for (let a = el; a && a !== document.body; a = a.parentElement) { const s2 = getComputedStyle(a); if (/(auto|scroll)/.test(s2.overflowX + s2.overflowY)) { sc = a.getBoundingClientRect(); break; } }
    for (const r of rects) {
      if (!sc) { runs.push([n, r]); continue; }
      const L = Math.max(r.left, sc.left), T = Math.max(r.top, sc.top), Rr = Math.min(r.right, sc.right), B = Math.min(r.bottom, sc.bottom);
      if (Rr - L > 0.5 && B - T > 0.5) runs.push([n, {left: L, top: T, right: Rr, bottom: B, width: Rr - L, height: B - T}]);
    }
  }
  for (let i = 0; i < runs.length; i++) for (let j = i + 1; j < runs.length; j++) {
    const [a, ra] = runs[i], [b, rb] = runs[j];
    if (a === b) continue;
    const ix = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left), iy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
    if (ix > 2 && iy > Math.min(ra.height, rb.height) * 0.35) out.push(`"${label(a.parentElement, a.textContent)}" overlaps "${label(b.parentElement, b.textContent)}"`);
  }
  return [...new Set(out)];
}
"""

def check_page(page):
    """A web page: no sideways scrolling, no text cut by a box that hides overflow, no text on text."""
    return page.evaluate(PAGE_JS)

def check_pages(paths, widths=(320, 360, 390, 768, 1280), schemes=("light",)):
    """Run check_page on local HTML files at several widths; returns ["file @ width: problem", ...]."""
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as p_:
        b = p_.chromium.launch()
        for path in paths:
            for w in widths:
                for sc in schemes:
                    pg = b.new_page(viewport={"width": w, "height": 900}, color_scheme=sc)
                    pg.goto("file://" + os.path.abspath(path)); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(200)
                    out += [f"{os.path.relpath(path, build.ROOT)} @ {w}px{'' if sc == 'light' else ' ' + sc}: {x}" for x in check_page(pg)]
                    pg.close()
        b.close()
    return out

SVG_JS = r"""
() => {
  const svg = document.documentElement, c = svg.getBoundingClientRect(), out = [];
  const label = (t) => t.textContent.trim().replace(/\s+/g, ' ').slice(0, 40);
  const texts = [...document.querySelectorAll('text')].filter(t => t.textContent.trim() && t.checkVisibility({visibilityProperty: true})
                 && !t.closest('[opacity="0"]'));
  const boxes = texts.map(t => [t, t.getBoundingClientRect(), /rotate|matrix/.test((t.getAttribute('transform') || '') + (t.parentElement.getAttribute('transform') || ''))]);
  for (const [t, r] of boxes) {
    const cut = [r.left < c.left - 0.5 && 'left', r.top < c.top - 0.5 && 'top', r.right > c.right + 0.5 && 'right', r.bottom > c.bottom + 0.5 && 'bottom'].filter(Boolean);
    if (cut.length) out.push(`"${label(t)}" runs off the ${cut.join(' and ')} edge`);
  }
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const [a, ra, rota] = boxes[i], [b, rb, rotb] = boxes[j];
    if (rota || rotb || a.contains(b) || b.contains(a)) continue;
    const ix = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left), iy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
    if (ix > 1 && iy > Math.min(ra.height, rb.height) * 0.35) out.push(`"${label(a)}" overlaps "${label(b)}"`);
  }
  return [...new Set(out)];
}
"""

def check_svgs(paths):
    """Every visible <text> in each SVG inside its canvas and off the other text, measured in Chromium with the brand fonts;
    returns ["file: problem", ...]. Hidden layers (display:none, the trim and safe guides) are skipped."""
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as p_:
        b = p_.chromium.launch(); pg = b.new_page(viewport={"width": 1600, "height": 1200})
        for path in paths:
            pg.goto("file://" + os.path.abspath(path)); pg.evaluate("document.fonts.ready")
            out += [f"{os.path.relpath(path, build.ROOT)}: {x}" for x in pg.evaluate(SVG_JS)]
        b.close()
    return out

# ================================================================ real-screen captures
ELLIPSIS = __import__("re").compile(r"…|\.\.(\s|$)|\.\.\.")

def ocr(paths):
    """Text in images, read with macOS's Vision framework (tools/build/ocr_text.swift): {path: [(text, box px)]}, or None
    where it can't run (not a Mac, no Xcode)."""
    import sys, json, shutil, subprocess
    if sys.platform != "darwin" or not shutil.which("xcrun") or not paths: return None
    res = subprocess.run(["xcrun", "swift", os.path.join(build.ROOT, "tools", "build", "ocr_text.swift"), *paths],
                         capture_output=True, text=True)
    if res.returncode: print("WARN capture check: text recognition failed:", res.stderr.strip()[-300:]); return None
    out = {}
    for line in res.stdout.splitlines():
        d = json.loads(line); out[d["file"]] = [(l["text"], l["box"]) for l in d.get("lines", [])]
    return out

def _outline(x, y, w, h, r):
    """Points every ~1 pt along a rectangle's outline, its corners rounded by r (a capsule: r = h / 2)."""
    pts, n = [], lambda L: max(2, int(L))
    for k in range(n(w - 2 * r) + 1):
        px = x + r + (w - 2 * r) * k / n(w - 2 * r); pts += [(px, y), (px, y + h)]
    for k in range(n(h - 2 * r) + 1):
        py = y + r + (h - 2 * r) * k / n(h - 2 * r); pts += [(x, py), (x + w, py)]
    for cx, cy, a0 in ((x + r, y + r, 180), (x + w - r, y + r, 270), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90)):
        for k in range(10):
            a = math.radians(a0 + 90 * k / 9); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def check_captures(src):
    """The captures in src/<platform>/ (devices.json lists them): text recognition finds no line cut short with "…" (".." as
    read), and each element recorded in elements.json (frames in points from Device Hub's element tree) lies inside the
    screen's own outline, the alpha mask the simulator writes with the screenshot, along its whole border. An element out of
    view entirely (scrolled away) is skipped; one partly out of view is cut. Returns ["platform/file: problem", ...]."""
    import json
    from PIL import Image
    out, pngs = [], []
    for platform in sorted(os.listdir(src)):
        dj = os.path.join(src, platform, "devices.json")
        if not os.path.exists(dj): continue
        rows = {r["file"]: r for r in json.load(open(dj, encoding="utf-8"))}
        pngs += [os.path.join(src, platform, f) for f in sorted(rows) if os.path.exists(os.path.join(src, platform, f))]
        ej = os.path.join(src, platform, "elements.json")
        for f, spec in (json.load(open(ej, encoding="utf-8")).items() if os.path.exists(ej) else []):
            if f not in rows: out.append(f"{platform}/{f}: elements.json names a capture devices.json doesn't list"); continue
            im = Image.open(os.path.join(src, platform, f))
            W, H = rows[f]["size_pt"]; s = im.width / W
            alpha = im.getchannel("A") if "A" in im.getbands() else Image.new("L", im.size, 255)
            for e in spec["elements"]:
                x, y, w, h = e["rect"]
                if x >= W or y >= H or x + w <= 0 or y + h <= 0: continue                 # out of view: scrolled away
                pts = _outline(x + 0.5, y + 0.5, w - 1, h - 1, max(0, e.get("radius", 0) - 0.5))
                bad = [(px, py) for px, py in pts if not (0 <= px < W and 0 <= py < H) or alpha.getpixel((min(im.width - 1, int(px * s)), min(im.height - 1, int(py * s)))) < 128]
                if bad: out.append(f"{platform}/{f}: {e['what']} is cut by the screen's edge or corner near ({bad[0][0]:.0f}, {bad[0][1]:.0f}) pt")
    found = ocr(pngs)
    if found is not None and sum(len(v) for v in found.values()) < len(pngs):
        out.append(f"text recognition read almost nothing from {len(pngs)} captures: the '…' check can't be trusted")
    if found is None:
        print("WARN capture check: no text recognition here (needs macOS and Xcode); '…' not checked")
    else:
        for path, lines in found.items():
            for text, box in lines:
                if ELLIPSIS.search(text):
                    out.append(f"{os.path.relpath(path, src)}: text cut short with '…': \"{text}\" at ({box[0]:.0f}, {box[1]:.0f}) px")
    return out

# ================================================================ Office files
FONTS = os.path.join(build.ROOT, "type", "fonts")
OFFICE_PAGES = {"letterhead": 1, "report-template": 2}     # pages each Word template should come to; more means it overflowed

def office_pdf(paths, outdir):
    """Renders .docx/.pptx to PDF with LibreOffice into outdir, {path: pdf}, or None without LibreOffice. It runs with a
    private profile whose fonts folder holds the repo's own fonts (type/fonts), so what's measured is Cascadia Mono and
    Archivo, not a fallback (a headless LibreOffice doesn't reliably see the fonts installed on the Mac)."""
    import shutil, subprocess, glob
    office = shutil.which("soffice") or shutil.which("libreoffice")
    if not office or not paths: return None
    profile = os.path.join(outdir, "lo-profile")
    os.makedirs(os.path.join(profile, "user", "fonts"), exist_ok=True)
    for f in glob.glob(os.path.join(FONTS, "*.ttf")): shutil.copy(f, os.path.join(profile, "user", "fonts"))
    subprocess.run([office, f"-env:UserInstallation=file://{os.path.abspath(profile)}", "--headless", "--convert-to", "pdf",
                    "--outdir", outdir, *paths], check=True, capture_output=True, timeout=600)
    return {p: os.path.join(outdir, os.path.splitext(os.path.basename(p))[0] + ".pdf") for p in paths}

def _pdf_lines(pdf):
    """Every line of text in a PDF, from poppler's pdftotext -bbox-layout: [(page w, page h, [(x0, y0, x1, y1, text)])] in pt."""
    import subprocess, re, html
    x = subprocess.run(["pdftotext", "-bbox-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout
    pages = []
    for pg in re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', x, re.S):
        lines = []
        for ln in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', pg.group(3), re.S):
            words = " ".join(html.unescape(w) for w in re.findall(r"<word[^>]*>(.*?)</word>", ln.group(5), re.S))
            lines.append((*map(float, ln.group(1, 2, 3, 4)), words))
        pages.append((float(pg.group(1)), float(pg.group(2)), lines))
    return pages

def _pptx_frames(path):
    """For each slide, the frames (pt) of what holds text: its own text boxes and placeholders, tables and charts, and its
    layout's (footer, slide number). Shapes without text (a card's rectangle, a rule) don't count: text that spills out of
    its box onto a card is still out of its box."""
    import zipfile, re
    z = zipfile.ZipFile(path); emu = 12700.0
    xfrm = re.compile(r'<a:off x="(-?\d+)" y="(-?\d+)"/>\s*<a:ext cx="(\d+)" cy="(\d+)"/>')
    def frames(xml, layout=False):
        out = []
        for el in re.finditer(r"<p:(sp|graphicFrame)>(.*?)</p:\1>", xml, re.S):
            body = el.group(2); ph = re.search(r'<p:ph\b[^>]*?type="(\w+)"', body) or re.search(r"<p:ph\b", body)
            text = "<a:t>" in body or "<a:fld" in body
            # on a slide, only shapes with text (an empty placeholder pptxgenjs leaves behind draws nothing)
            if el.group(1) == "sp" and not layout and not text: continue
            if el.group(1) == "sp" and layout and not text and not ph: continue
            # a layout's title and body placeholders are only prompts: a slide that uses them has its own frame
            if layout and ph and (ph.groups()[0] if ph.groups() else None) not in ("sldNum", "ftr", "dt"): continue
            m = xfrm.search(body)
            if not m: continue
            x, y, w, h = (int(v) for v in m.groups())
            rows = [int(r) for r in re.findall(r'<a:tr h="(\d+)"', body)]
            if rows: h = max(h, sum(rows))           # a table is as tall as its rows, whatever its frame says
            out.append((x / emu, y / emu, w / emu, h / emu))
        return out
    n = len([f for f in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", f)])
    out = []
    for i in range(1, n + 1):
        xml = z.read(f"ppt/slides/slide{i}.xml").decode("utf-8")
        rels = z.read(f"ppt/slides/_rels/slide{i}.xml.rels").decode("utf-8")
        lay = re.search(r'Target="\.\./slideLayouts/(slideLayout\d+\.xml)"', rels)
        fr = frames(xml) + (frames(z.read(f"ppt/slideLayouts/{lay.group(1)}").decode("utf-8"), layout=True) if lay else [])
        out.append([(x, y, x + w, y + h) for x, y, w, h in fr if w > 0 and h > 0])
    return out

def _docx_columns(path):
    """The text column of a Word file (pt): left margin to page width minus the right margin, the widest of its sections."""
    import zipfile, re
    x = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    cols = []
    for s in re.finditer(r'<w:pgSz w:w="(\d+)"[^>]*/>.*?<w:pgMar ([^>]*)/>', x, re.S):
        mar = dict(re.findall(r'w:(\w+)="(-?\d+)"', s.group(2)))
        cols.append((int(mar["left"]) / 20, (int(s.group(1)) - int(mar["right"])) / 20))
    return min(c[0] for c in cols), max(c[1] for c in cols)

def check_office(paths, edge=18.0, slack=2.0):
    """The Office templates rendered by LibreOffice (office_pdf), every line of text measured: inside the page with at least
    `edge` pt to spare (no line cut by the paper's or slide's edge), off every other line (no text run into other text), on
    a slide inside a frame of that slide (text that overflows its box lands outside every frame), in a Word file inside the
    text column and within the expected page count (OFFICE_PAGES: overflowing text pushes a page on). Returns
    ["file p.N: problem", ...], or None where LibreOffice or poppler isn't installed."""
    import shutil, tempfile
    if not shutil.which("pdftotext"): return None
    with tempfile.TemporaryDirectory() as td:
        pdfs = office_pdf(paths, td)
        if pdfs is None: return None
        out = []
        for path, pdf in pdfs.items():
            name = os.path.basename(path)
            if not os.path.exists(pdf): out.append(f"{name}: LibreOffice made no PDF"); continue
            pages = _pdf_lines(pdf)
            if not pages or not any(p[2] for p in pages): out.append(f"{name}: no text found in the PDF"); continue
            slides = _pptx_frames(path) if path.endswith(".pptx") else None
            column = _docx_columns(path) if path.endswith(".docx") else None
            want = next((n for k, n in OFFICE_PAGES.items() if name.startswith(k)), None)
            if want is not None and len(pages) != want: out.append(f"{name}: {len(pages)} pages, expected {want} (text pushed onto another page?)")
            if slides is not None and len(slides) != len(pages): out.append(f"{name}: {len(pages)} pages for {len(slides)} slides")
            for n, (W, H, lines) in enumerate(pages, 1):
                where = f"{name} p.{n}"
                for x0, y0, x1, y1, t in lines:
                    if x0 < edge or y0 < edge or x1 > W - edge or y1 > H - edge:
                        out.append(f'{where}: "{t[:40]}" within {edge:.0f} pt of the edge ({x0:.0f}, {y0:.0f}, {x1:.0f}, {y1:.0f} of {W:.0f} × {H:.0f})')
                    if slides is not None and n <= len(slides) and not any(
                            fx0 - slack <= x0 and fy0 - slack <= y0 and x1 <= fx1 + slack and y1 <= fy1 + slack for fx0, fy0, fx1, fy1 in slides[n - 1]):
                        out.append(f'{where}: "{t[:40]}" runs out of its box ({x0:.0f}, {y0:.0f}, {x1:.0f}, {y1:.0f})')
                    if column is not None and (x0 < column[0] - slack or x1 > column[1] + slack):
                        out.append(f'{where}: "{t[:40]}" runs out of the text column ({x0:.0f}-{x1:.0f}, column {column[0]:.0f}-{column[1]:.0f})')
                for i, a in enumerate(lines):
                    for b in lines[i + 1:]:
                        ix = min(a[2], b[2]) - max(a[0], b[0]); iy = min(a[3], b[3]) - max(a[1], b[1])
                        if ix > 1 and iy > 1:
                            out.append(f'{where}: "{a[4][:30]}" runs into "{b[4][:30]}"')
        return out
