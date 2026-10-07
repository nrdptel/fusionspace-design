"""Callsign: tools/callsign/, the naming tool: a constellation for each project, one of its IAU-named stars for each product
(it replaces the star name picker).

Two files that each work on their own, made from source/callsign/:
- callsign.html: the tool in a browser, on any device. Everything is inside the one file (the product stylesheet, the WOFF2
  fonts, the one-color header lockup, the icons, the star list and callsign.py for download), so it works opened from disk,
  offline, or mailed to a phone.
- callsign.py: the same tool on the command line, Python 3.8+ with no dependencies, with the star list built in.
Next to them: the list as JSON (which the page checks for a newer copy) and CSV, and a README.

The star list is source/callsign/iau-star-names.json, read from the IAU by `python3 source/callsign/callsign.py update
--out source/callsign/iau-star-names.json`. The build never goes online, so two builds of the same sources match.
"""
import os, re, json, base64, shutil, importlib.util
import build, kit_icons, kit_product
from kit_product import THEME_SWITCH, THEME_JS, status, note, titleblock

D = "tools/callsign"
SRC = os.path.join(build.SRC, "callsign")
DATE = "2026-10-06"                                         # date of issue of this version (1.1.0: projects as constellations)
FONTS = (("Archivo", 400, "Archivo-Regular"), ("Archivo", 600, "Archivo-SemiBold"),
         ("Cascadia Mono", 400, "CascadiaMono-Regular"), ("Cascadia Mono", 600, "CascadiaMono-SemiBold"))

def _module():
    spec = importlib.util.spec_from_file_location("callsign_src", os.path.join(SRC, "callsign.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def _script_json(obj):
    """JSON that is safe inside a <script> element."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

def _fonts():
    faces = []
    for fam, w, stem in FONTS:
        data = base64.b64encode(open(os.path.join(build.OUT, "product/web/fonts", stem + ".woff2"), "rb").read()).decode()
        faces.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:swap;"
                     f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    faces.append("@font-face{font-family:'Archivo Fallback';src:local('Arial');size-adjust:101%}")
    faces.append("@font-face{font-family:'Cascadia Mono Fallback';src:local('Menlo'),local('Consolas');size-adjust:100%}")
    return "\n".join(faces)

def build_cli(m, cat):
    s = open(os.path.join(SRC, "callsign.py"), encoding="utf-8").read()
    line = "CATALOG = None\n"
    assert s.count(line) == 1 and "'''" not in m.dumps(cat)
    s = s.replace("# The build puts the IAU list here, so this file works on its own. Without it, iau-star-names.json next to this file is read.\n",
                  "# The IAU list, as built in. A newer copy (callsign update, or iau-star-names.json next to this file) is used instead.\n")
    s = s.replace(line, "CATALOG = json.loads(r'''" + m.dumps(cat) + "''')\n")
    s = s.replace("Edit source/callsign/callsign.py in the fusionspace-design repository; tools/callsign/callsign.py is built from it.",
                  "Built from source/callsign/callsign.py in the fusionspace-design repository; edit it there, not here.")
    return s

def build_page(m, cat, cli):
    s = open(os.path.join(SRC, "callsign.html"), encoding="utf-8").read()
    fav = base64.b64encode(open(os.path.join(build.OUT, "logo/favicon/favicon.svg"), "rb").read()).decode()
    css = open(os.path.join(build.OUT, "product/web/fusionspace.css"), encoding="utf-8").read()
    tb = titleblock([("Title", "Callsign"), ("Designation", m.DESIGNATION), ("Version", m.VERSION), ("Date", DATE),
                     ("Units", "vmag, degrees J2000"), ("Data", f"IAU star names, read {cat['read']}"), ("Status", "RELEASED"),
                     ("Notes", "Checks the repository for a newer list when online. Names in use stay in this browser.")])
    tb, n = re.subn(r'(<span class="k">Data</span><span class="v")', r'\1 data-tb="data"', tb)
    assert n == 1
    vals = {
        "favicon": "data:image/svg+xml;base64," + fav, "fonts": _fonts(), "stylesheet": css.strip(),
        "logo": kit_product._logo("hdr"), "theme_switch": THEME_SWITCH, "theme_js": THEME_JS,
        "designation": m.DESIGNATION, "status_released": status("ok", "Released", "check"),
        "note_check": note("note", "Note", "<p>The IAU names stars, not products. A star name is an internal name; if it is "
                                           "also to be the external name, search it before it goes on a box or a domain: "
                                           "someone may already use it.</p>"),
        "titleblock": tb, "catalog": _script_json(cat), "constellations": _script_json(m.CONSTELLATIONS), "cli": _script_json(cli),
    }
    s = re.sub(r"\{\{icon:([a-z-]+)\}\}", lambda g: kit_icons.inline(g.group(1), ""), s)
    for k, v in vals.items():
        assert s.count("{{" + k + "}}") == 1, k
        s = s.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[^}]*\}\}", s)
    assert not left, left
    return s

def build_callsign():
    m = _module()
    cat = json.load(open(os.path.join(SRC, "iau-star-names.json"), encoding="utf-8"))
    assert cat["fields"] == m.FIELDS and cat["count"] == len(cat["stars"]) >= 300
    unknown = {r[3] for r in cat["stars"]} - set(m.CONSTELLATIONS)
    assert not unknown, f"constellations missing from callsign.CONSTELLATIONS: {unknown}"
    assert len(m.CONSTELLATIONS) == 88
    cli = build_cli(m, cat)
    os.makedirs(os.path.join(build.OUT, D), exist_ok=True)
    build.wr(f"{D}/callsign.py", cli)
    os.chmod(os.path.join(build.OUT, D, "callsign.py"), 0o755)
    build.wr(f"{D}/callsign.html", build_page(m, cat, cli))
    build.wr(f"{D}/iau-star-names.json", m.dumps(cat))
    rows = ["name,code," + ",".join(m.FIELDS[1:])]
    q = lambda v: "" if v is None else (f'"{v}"' if any(c in str(v) for c in ',"') else str(v))
    rows += [",".join([q(r[0]), m.code(r[0])] + [q(v) for v in r[1:]]) for r in cat["stars"]]
    build.wr(f"{D}/iau-star-names.csv", "\n".join(rows) + "\n")
    shutil.copyfile(os.path.join(SRC, "README.md"), os.path.join(build.OUT, D, "README.md"))
