# SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
# keep.py <capture.png> [app|home|lock] ["what it shows"]: copies a capture from the capture folder into
# source/product/devices/apple, adds or updates its row in devices.json (device, OS and size from the image and the
# simulator), and records its element frames in elements.json from <capture>.tree.txt (tools/build/kit_devices.py), which
# the build's clipping check tests against the screen's outline. Faces take no mode: their trees misplace corner slots.
import json, os, shutil, subprocess, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); APPLE = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.abspath(os.path.join(APPLE, "..", "..", "..", ".."))
OUT = os.environ.get("FS_OUT", os.path.join(APPLE, "build", "captures")); DEST = os.path.join(REPO, "source", "product", "devices", "apple")
f = os.path.basename(sys.argv[1]); mode = sys.argv[2] if len(sys.argv) > 2 else ""; shows = sys.argv[3] if len(sys.argv) > 3 else None
DEVICES = {"ios": ("iPhone 17 Pro", 3), "watch-ultra": ("Apple Watch Ultra 4 (49mm)", 2), "watch-se40": ("Apple Watch SE 3 (40mm)", 2)}
key = next(k for k in DEVICES if f.startswith(k)); device, scale = DEVICES[key]
runtimes = subprocess.run(["xcrun", "simctl", "list", "runtimes"], capture_output=True, text=True).stdout
line = next((l for l in runtimes.splitlines() if l.startswith("iOS 27" if key == "ios" else "watchOS 27")), "")
osv = f"{line.split(' (')[0]} ({line.split(' - ')[1].rstrip(')')})" if " - " in line else ""        # "iOS 27.0 (24A434)"
shutil.copy(os.path.join(OUT, f), os.path.join(DEST, f))
im = Image.open(os.path.join(DEST, f))
path = os.path.join(DEST, "devices.json"); rows = json.load(open(path, encoding="utf-8"))
old = next((r for r in rows if r["file"] == f), {})
row = {"file": f, "device": device, "os": old.get("os", osv), "size_px": list(im.size), "scale": scale,
       "size_pt": [im.width // scale, im.height // scale], "shows": shows or old.get("shows", ""), "simulator": old.get("simulator", "Xcode 27.0"),
       "mask": "alpha (simctl io screenshot --mask=alpha)", "captured": __import__("datetime").date.today().isoformat()}
rows = [r for r in rows if r["file"] != f] + [row] if not old else [row if r["file"] == f else r for r in rows]
with open(path, "w", encoding="utf-8") as fh: json.dump(rows, fh, indent=1, ensure_ascii=False); fh.write("\n")
if mode:
    tree = os.path.join(OUT, f[:-4] + ".tree.txt")
    subprocess.run([sys.executable, os.path.join(REPO, "tools", "build", "kit_devices.py"), "elements", f, tree, mode], check=True)
print("kept", f)
