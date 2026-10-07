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
graphics (check_svgs: every visible line of text inside the canvas and off the other text) and the real-screen captures
(check_captures: no text cut short with "…", and every element of ours inside the screen's own outline).
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
