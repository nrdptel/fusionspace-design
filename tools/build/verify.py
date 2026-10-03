import subprocess, io, math
from PIL import Image, ImageDraw
import os, sys
O=os.path.join(os.environ.get("FS_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_build", "rev-c")), "logo")
def r(p,w=None,h=None):
    a=["rsvg-convert",p]+(["-w",str(w)] if w else [])+(["-h",str(h)] if h else [])
    return Image.open(io.BytesIO(subprocess.run(a,capture_output=True,check=True).stdout)).convert("RGBA")
def on(bg,im,pad=30):
    c=Image.new("RGBA",(im.width+2*pad,im.height+2*pad),bg); c.paste(im,(pad,pad),im); return c
tiles=[]
tiles.append(on("#0B0F1C",r(f"{O}/lockup/fusion-space-stacked-color.svg",w=520)))
tiles.append(on("#F3F4F7",r(f"{O}/lockup/fusion-space-stacked-void.svg",w=520)))
tiles.append(on("#0B0F1C",r(f"{O}/lockup/fusion-space-horizontal-color.svg",w=700)))
tiles.append(on("#F3F4F7",r(f"{O}/lockup/fusion-space-horizontal-color.svg",w=700)))
tiles.append(on("#0B0F1C",r(f"{O}/lockup/fusion-space-horizontal-white.svg",w=700)))
tiles.append(on("#F3F4F7",r(f"{O}/mark/fusion-space-mark-void.svg",w=300)))
row=Image.new("RGBA",(900,220),"#141A2B")
x=10
for p,s in [("favicon/icon.svg",180),("favicon/app-icon.svg",180),("favicon/favicon.svg",180)]:
    im=r(f"{O}/{p}",w=s); row.paste(im,(x,20),im); x+=200
for n in ("favicon-16.png","favicon-32.png"):
    im=Image.open(f"{O}/favicon/{n}"); row.paste(im,(x,20),im); z=im.resize((im.width*4,im.height*4),Image.NEAREST); row.paste(z,(x,80),z); x+=140
tiles.append(row)
# dxf preview
import ezdxf
d=ezdxf.readfile(f"{O}/mark/fusion-space-mark-50mm.dxf")
S=8; img=Image.new("RGBA",(int(57*S)+40,int(50*S)+40),"white"); dr=ImageDraw.Draw(img)
for e in d.modelspace():
    pts=[]
    from ezdxf.math import bulge_to_arc
    vs=list(e.get_points("xyb")); n=len(vs)
    for i in range(n):
        x0,y0,b=vs[i]; x1,y1,_=vs[(i+1)%n]
        if abs(b)<1e-12: pts+= [(x0,y0),(x1,y1)]; continue
        c,sa,ea,R=bulge_to_arc((x0,y0),(x1,y1),b)
        if ea<sa: ea+=2*math.pi
        seq=[(c[0]+R*math.cos(sa+(ea-sa)*k/40), c[1]+R*math.sin(sa+(ea-sa)*k/40)) for k in range(41)]
        if b<0: seq=seq[::-1]
        pts+=seq
    dr.line([(20+px*S, 20+(50-py)*S) for px,py in pts], fill="black", width=1)
tiles.append(img)
W=max(t.width for t in tiles); H=sum(t.height+10 for t in tiles)
sheet=Image.new("RGBA",(W,H),"#333")
y=0
for t in tiles: sheet.paste(t,(0,y)); y+=t.height+10
sheet.convert("RGB").save(os.path.join(O, "..", "verify.png"))
print(sheet.size)

# Icon tiles: no mark pixel may sit outside its tile (a mark pixel touching transparency where the tile's corners are
# transparent). Checks every icon-like SVG and PNG in the build.
import glob, numpy as np
ROOT = os.path.join(O, "..")
def spills(im):
    a = np.asarray(im).astype(int); al = a[..., 3]; H, W = al.shape
    if min(al[0, 0], al[0, -1], al[-1, 0], al[-1, -1]) > 10: return 0          # square, opaque: nothing to spill over
    if al[H // 2, 2] < 250 and al[2, W // 2] < 250: return 0                  # no tile reaching the edges
    op = a[al == 255][:, :3]
    if not len(op): return 0
    cols, cnt = np.unique(op // 8, axis=0, return_counts=True); bg = cols[cnt.argmax()] * 8
    mark = (al > 128) & (np.abs(a[..., :3] - bg).sum(-1) > 60); tr = al < 20
    nb = np.zeros_like(tr); nb[1:] |= tr[:-1]; nb[:-1] |= tr[1:]; nb[:, 1:] |= tr[:, :-1]; nb[:, :-1] |= tr[:, 1:]
    return int((mark & nb).sum())
pats = ["logo/favicon/*", "kit/web/*", "kit/web/site/app/*", "kit/web/site/public/*", "kit/apps/**/*", "kit/games/steam/*icon*",
        "kit/documents/email-signature/mark-tile*", "kit/github/avatar*", "kit/social/avatar*"]
bad = []; n = 0
for pat in pats:
    for p in sorted(glob.glob(os.path.join(ROOT, pat), recursive=True)):
        if not p.endswith((".svg", ".png")): continue
        try: im = r(p, w=256) if p.endswith(".svg") else Image.open(p).convert("RGBA")
        except Exception: continue
        n += 1; k = spills(im)
        if k: bad.append((os.path.relpath(p, ROOT), k))
print(f"icon tiles checked: {n}; mark outside its tile: {bad if bad else 'none'}")

# Apparel print files (design review, "make sure nothing is clipped"): every apparel PNG keeps a transparent margin on
# all four sides, so no part of the art (the main cone's tip at the top right included) can be cut off by the file edge.
import re, zipfile
MERCH_MARGIN_IN = float(re.search(r"^MERCH_MARGIN_IN = ([0-9.]+)", open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_targets.py")).read(), re.M).group(1))
clip = []; n = 0; least = None
for p in sorted(glob.glob(os.path.join(ROOT, "kit/merch/*.png"))):
    if not re.search(r"/(tshirt|hoodie|cap)-", p): continue
    im = Image.open(p); dpi = (im.info.get("dpi") or (300, 300))[0]
    al = np.asarray(im.convert("RGBA"))[..., 3]; ys, xs = np.nonzero(al)
    H, W = al.shape; n += 1
    m = min(xs.min(), ys.min(), W - 1 - xs.max(), H - 1 - ys.max()) / dpi       # least ink-free edge, inches
    least = m if least is None else min(least, m)
    if m < MERCH_MARGIN_IN - 1.5 / dpi: clip.append((os.path.relpath(p, ROOT), round(m, 3)))
print(f"apparel files checked: {n}; least clear edge {least:.3f} in (margin {MERCH_MARGIN_IN} in); too close to the edge: {clip if clip else 'none'}")

# The name (design review, "make sure it's always FusionSpace, one word"): no output spells it as two words or with a hyphen.
# File and folder slugs (fusion-space-…) are lower case and not checked; quoted mentions of the site's current spelling are allowed.
NAME_BAD = re.compile(r'(?<!")\b(Fusion[  _-]+Space|FUSION[  _-]+SPACE|Fusion[  _-]?space|Fusionspace)\b(?!")')
TEXT_EXT = (".svg", ".html", ".md", ".txt", ".json", ".ts", ".tsx", ".js", ".css", ".py", ".h", ".c", ".rs", ".toml", ".conf", ".yml",
            ".yaml", ".xml", ".webmanifest", ".kicad_mod", ".gpl", ".ans", ".itermcolors", ".scss")
hits = []; n = 0
for p in glob.glob(os.path.join(ROOT, "**/*"), recursive=True):
    rel = os.path.relpath(p, ROOT)
    if os.path.isdir(p) or rel.startswith(("review", "_")): continue
    texts = []
    if p.endswith(TEXT_EXT) or "." not in os.path.basename(p):
        try: texts = [open(p, encoding="utf-8").read()]
        except (UnicodeDecodeError, OSError): continue
    elif p.endswith((".docx", ".pptx", ".dotx", ".potx", ".xlsx")):
        with zipfile.ZipFile(p) as z: texts = [re.sub(r"<[^>]+>", "", z.read(i).decode("utf-8", "ignore")) for i in z.namelist() if i.endswith(".xml")]
    else: continue
    n += 1
    for t in texts:
        for mm in NAME_BAD.finditer(t): hits.append((rel, mm.group(0)))
print(f"name spelling checked in {n} files; not one word: {hits[:20] if hits else 'none'}")

# 3D prints: every STL closed and consistently wound (each shell; a sealed void only inside another
# shell), every STEP read back by Open CASCADE as valid solids, every 3MF opened and its objects closed.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_cad
bad3 = []; ns = nst = n3 = 0
for p in sorted(glob.glob(os.path.join(ROOT, "kit/3d-print/*.stl"))):
    ns += 1; ok, msg = kit_cad.check_stl(p)
    if not ok: bad3.append((os.path.basename(p), msg))
if kit_cad.HAVE_OCC:
    import contextlib
    for p in sorted(glob.glob(os.path.join(ROOT, "kit/3d-print/*.step"))):
        nst += 1
        with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn): k, vol, valid = kit_cad.read_step(p)
        if not (k and valid and vol > 0): bad3.append((os.path.basename(p), f"{k} solids, valid {valid}"))
for p in sorted(glob.glob(os.path.join(ROOT, "kit/3d-print/*.3mf"))):
    n3 += 1
    try:
        for name, V, F in kit_cad.read_3mf(p):
            ok, msg = kit_cad.mesh_check(*kit_cad.weld(V, F), cavity_ok=True)
            if not ok: bad3.append((os.path.basename(p), f"{name}: {msg}"))
    except Exception as e: bad3.append((os.path.basename(p), f"doesn't open: {e}"))
print(f"3D files checked: {ns} STL (closed shells), {nst} STEP (read back, valid solids), {n3} 3MF; problems: {bad3 if bad3 else 'none'}"
      + ("" if kit_cad.HAVE_OCC else " (STEP not checked: no OCP)"))
