"""Real-screen captures: product/mobile/devices/ and product/watch/devices/.

The reference code in product/ runs in the sample apps (source/product/samples/apple, source/product/samples/android), and
their screenshots from simulators and emulators are kept in source/product/devices/<platform>/ with a devices.json saying
what each one is. This copies them into product/, cuts each to its real screen outline (Apple's screenshot mask, the circle
of a round watch) and makes a contact sheet per folder, next to the drawn mock-ups they prove.
"""
import os, re, sys, json, shutil
import build, kit_product as kp, kit_mobile as km
from build import VOID, PAPER

SRC = os.path.join(kp.SRC, "devices")
PHONE = ("ios-", "phone-")
WATCH = ("watch-", "wear-")

def _load(platform):
    p = os.path.join(SRC, platform, "devices.json")
    if not os.path.exists(p): return []
    rows = json.load(open(p, encoding="utf-8"))
    for r in rows:
        r["platform"] = platform
        r["device"] = r["device"].split(" (")[0].replace("pixel_10", "Pixel 10").replace("wearos_large_round", "Wear OS large round").replace("wearos_small_round", "Wear OS small round")
    return [r for r in rows if os.path.exists(os.path.join(SRC, platform, r["file"]))]

ORDER = ["ios-pad", "ios-track", "ios-home-widgets-light", "ios-home-widgets-dark", "ios-island-pad", "ios-island-flight", "ios-lock-pad", "ios-lock-flight",
         "phone-pad", "phone-track", "phone-live-update", "phone-live-update-android16",
         "watch-ultra-find", "watch-ultra-find-aod", "watch-ultra-pad", "watch-ultra-unfired", "watch-ultra-face", "watch-ultra-face-aod",
         "watch-se40-find", "watch-se40-find-aod", "watch-se40-pad", "watch-se40-unfired", "watch-se40-face", "watch-se40-face-aod",
         "wear-find", "wear-find-ambient", "wear-pad", "wear-unfired", "wear-tile-find", "wear-small-find"]
def _rank(r):
    stem = r["file"][:-4]
    return ORDER.index(stem) if stem in ORDER else len(ORDER)

def _tile(path, h, row):
    """A capture scaled to height h, cut to its screen: the alpha mask Apple's simulator writes, a circle for a round watch,
    or the full rectangle (an Android phone's screencap has no corner mask; it is shown whole, with its outline). A Dynamic
    Island capture is cut to the top of the screen, at half size."""
    from PIL import Image
    im = Image.open(path)
    if row["file"].startswith("ios-island"):
        im = im.crop((0, 0, im.width, round(im.width * 0.15)))
        w, h2 = im.width // 2, im.height // 2
        crop = os.path.join(build.TMP, "island-" + row["file"]); im.save(crop)
        return _masked(crop, w, h2, im.getchannel("A").resize((w, h2), Image.LANCZOS))
    w = round(im.width * h / im.height)
    if row["platform"] == "apple" and "A" in im.getbands():            # Apple's capture carries the screen mask in alpha
        return _masked(path, w, h, im.getchannel("A").resize((w, h), Image.LANCZOS))
    return km.screen_tile(path, w, h, None, radius=0, circle=row["file"].startswith("wear-"), pad=10, gap=6)

def _masked(path, w, h, m):
    """The capture cut by its own mask m (PIL "L", w x h), with a 2 px case line drawn 6 px outside it."""
    from PIL import Image, ImageFilter, ImageChops
    pad, gap, line = 10, 6, 2
    im = Image.open(path).convert("RGB").resize((w, h), Image.LANCZOS)
    big = Image.new("L", (w + 2 * pad, h + 2 * pad), 0); big.paste(m, (pad, pad))
    grow = lambda img, n: img.filter(ImageFilter.MaxFilter(2 * n + 1)) if n else img
    ring = ImageChops.subtract(grow(big, gap + line), grow(big, gap))
    tile = Image.new("RGB", big.size, tuple(kp._hex_rgb(PAPER)))
    tile.paste(Image.new("RGB", big.size, tuple(kp._hex_rgb(VOID))), (0, 0), ring)
    tile.paste(im, (pad, pad), m)
    return tile

def _sheet(rows, dest, h, title):
    """Rows of tiles, one row per device, each tile labeled with the screen and the device."""
    from PIL import Image, ImageDraw
    groups = {}
    for r in sorted(rows, key=_rank):
        key = r["device"] + (" · Dynamic Island" if r["file"].startswith("ios-island") else " · Lock Screen" if r["file"].startswith("ios-lock")
                             else " · Home Screen" if r["file"].startswith("ios-home")
                             else " · Watch face" if "-face" in r["file"]
                             else " · Android 16" if "android16" in r["file"] else "")
        groups.setdefault(key, []).append(r)
    f1, f2 = km._font(15, True), km._font(12)
    margin, gap, lab = 28, 22, 40
    tiles = {d: [(r, _tile(os.path.join(SRC, r["platform"], r["file"]), h, r)) for r in rs] for d, rs in groups.items()}
    W = margin * 2 + max(sum(t.width for _, t in ts) + gap * (len(ts) - 1) for ts in tiles.values())
    W = max(W, 900)
    H = margin * 2 + 30 + sum(lab + max(t.height for _, t in ts) + gap for ts in tiles.values())
    im = Image.new("RGB", (W, H), tuple(kp._hex_rgb(PAPER))); dr = ImageDraw.Draw(im)
    dr.text((margin, margin), title, fill=tuple(kp._hex_rgb(VOID)), font=f1)
    y = margin + 30
    for dev, ts in tiles.items():
        dr.text((margin, y), f'{dev} · {ts[0][0]["os"]}', fill=tuple(kp._hex_rgb(VOID)), font=f1)
        x = margin; rowh = max(t.height for _, t in ts)
        for r, t in ts:
            im.paste(t, (x, y + lab - 14))
            x += t.width + gap
        y += lab + rowh + gap
    os.makedirs(os.path.dirname(dest), exist_ok=True); im.save(dest, optimize=True)

README = """# Real screens

Screenshots of the reference code running in the sample apps on simulators and emulators, captured {date}. The drawn
mock-ups next to this folder show the intent; these show what the code actually does. Built by `tools/build/kit_devices.py`
from `source/product/devices/`, where `devices.json` records each capture's device, OS, size and what it shows.

![Real screens](preview.png)

| File | Device | Shows |
|---|---|---|
{rows}

The sample apps are in `source/product/samples/` (their READMEs list what running them found and fixed).
"""

# ------------------------------------------------------------------ element frames, for the clipping check
# Device Hub (Xcode 27's simulator UI, through Xcode's device tools) writes the element tree of what's on screen with each
# interaction. `python tools/build/kit_devices.py elements <capture.png> <tree.txt> <app|home|lock>` keeps the frames of
# our elements (in points) in source/product/devices/<platform>/elements.json, and kit_clip.check_captures tests each one
# against the capture's own screen outline. Watch faces aren't recorded: the tree doesn't place corner complications
# where the face draws them, so faces are checked by text recognition and by eye.
LINE = re.compile(r"^( *)([A-Za-z][A-Za-z ]*?), \{\{(-?[\d.]+), (-?[\d.]+)\}, \{([\d.]+), ([\d.]+)\}\}(.*)$")
CONTAINERS = {"Application", "Window", "NavigationBar", "Toolbar", "TabBar", "ScrollView", "Sheet", "Table", "CollectionView"}

def parse_tree(text):
    """The tree as (bundle, depth, type, (x, y, w, h), label, identifier) rows."""
    out, bundle = [], ""
    for line in text.splitlines():
        if line.startswith("Application bundle identifier:"): bundle = line.split(":", 1)[1].strip(); continue
        m = LINE.match(line)
        if not m: continue
        rest = m.group(7)
        lab = re.search(r"label: '(.*?)'(?=, [a-zA-Z]+[:,]|, [A-Z][a-z]+$|$)", rest)
        ident = re.search(r"identifier: '(.*?)'(?=, |$)", rest)
        out.append((bundle, len(m.group(1)), m.group(2), tuple(float(m.group(i)) for i in range(3, 7)),
                    lab.group(1) if lab else "", ident.group(1) if ident else ""))
    return out

def _subtree(rows, i):
    d = rows[i][1]; j = i + 1
    while j < len(rows) and rows[j][1] > d: j += 1
    return rows[i:j]

def tree_elements(text, mode):
    """Our elements in a tree: everything the app shows (mode app), our widgets on the Home Screen (home), the Live Activity
    card on the Lock Screen (lock). Containers that span the screen and unlabelled boxes are left out."""
    rows, sel = parse_tree(text), []
    if mode == "app":
        sel = [r for r in rows if r[0].startswith("co.fusionspace")]
    else:
        for i, r in enumerate(rows):
            if mode == "home" and r[0] == "com.apple.springboard" and r[2] == "Icon" and r[5] == "FusionSpace": sel += _subtree(rows, i)
            if mode == "lock" and r[0] == "com.apple.springboard" and r[5].startswith("ListCell") \
                    and any("FLIGHT 04" in s[4] for s in _subtree(rows, i)) and not any(s[5].startswith("ListCell") for s in _subtree(rows, i)[1:]):
                sel += _subtree(rows, i)
    W = max((r[3][2] for r in rows if r[2] == "Window"), default=0)
    watch = 0 < W < 250                     # watchOS draws its buttons as capsules: tested along that outline, not the box
    els = []
    for b, d, typ, (x, y, w, h), lab, ident in sel:
        if typ in CONTAINERS or w < 0.5 or h < 0.5 or (W and w >= W * 0.95) or "scroll bar" in lab: continue
        if typ in ("Other", "Image") and not lab: continue            # unlabelled boxes, the system's icon-label shadows
        e = {"what": f"{typ} '{lab or ident}'", "rect": [round(x, 1), round(y, 1), round(w, 1), round(h, 1)]}
        if watch and typ == "Button": e["radius"] = round(h / 2, 1)
        if e not in els: els.append(e)
    return els

def record_elements(png, tree, mode):
    platform = os.path.basename(os.path.dirname(os.path.abspath(png))) if os.path.dirname(png) else "apple"
    path = os.path.join(SRC, platform, "elements.json")
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    data[os.path.basename(png)] = {"from": "Device Hub element tree", "mode": mode,
                                   "elements": tree_elements(open(tree, encoding="utf-8").read(), mode)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(data.items())), f, indent=1, ensure_ascii=False); f.write("\n")
    print(f"{os.path.basename(png)}: {len(data[os.path.basename(png)]['elements'])} elements")

def build_devices():
    rows = _load("apple") + _load("android")
    if not rows: print("WARN devices: no captures in source/product/devices"); return
    import kit_clip
    kit_clip.assert_clean(kit_clip.check_captures(SRC), "real-screen captures")
    for kind, prefixes, folder, h, title in (("phone", PHONE, "mobile/devices", 520, "Phones: the reference code running"),
                                             ("watch", WATCH, "watch/devices", 230, "Watches: the reference code running")):
        sel = [r for r in rows if r["file"].startswith(prefixes)]
        if not sel: continue
        for r in sel:
            dst = kp.out(f"{folder}/{r['file']}"); os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(SRC, r["platform"], r["file"]), dst)
        _sheet(sel, kp.out(f"{folder}/preview.png"), h, title)
        table = "\n".join(f'| `{r["file"]}` | {r["device"]}, {r["os"]} | {r.get("shows") or r.get("what", "")} |' for r in sel)
        kp.wr(f"{folder}/README.md", README.format(date=sel[0].get("captured", ""), rows=table))

if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "elements":
        record_elements(os.path.join(SRC, "apple", sys.argv[2]) if "/" not in sys.argv[2] else sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        build_devices()
