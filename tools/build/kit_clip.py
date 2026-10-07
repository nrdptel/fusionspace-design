"""Clipping check for drawn screens (product/mobile/, product/watch/): the build stops if anything is cut by an edge or a corner.

The page reports every text run (one rect per line of every text node, SVG text included) and every box that carries
meaning (status chips, tags, state boxes, buttons, with their own corner radius); this module tests each against:

- its frame's shape: the device's real screen outline (a mask taken from the simulator, source/product/devices/masks/:
  Apple's corners are continuous curves, not arcs), a circle (Wear OS), or a rounded rectangle (widgets, cards), inset by
  a margin;
- on phone screens, the visible content area: below the status bar and the app's top bar, above the tab bar, navigation
  bar, fixed bottom panel and home indicator. Content may not run under a bar and look finished.

A box is tested along its own rounded outline (a capsule's corners are round), text by its rectangle.
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
