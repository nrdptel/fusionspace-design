#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
"""Christen: name a FusionSpace project after an IAU-approved star.

One file, no dependencies, Python 3.8 or later: macOS, Linux, Windows, and phones with a Python app (a-Shell, Termux).
The star list is the IAU's own (https://iauarchive.eso.org/public/themes/naming_stars/#n4). A copy is built in, and
`christen update` reads the list again from the IAU; it is also read again on its own when the copy is over 30 days old.

    christen                              draw a star
    christen -n 5 -c Orion --vmag ..3     five bright stars in Orion
    christen list --max-letters 5         every short name
    christen show Vega                    one star
    christen update                       read the IAU list now
    christen ui                           open christen.html, the same tool in a browser

Edit source/christen/christen.py in the fusionspace-design repository; tools/christen/christen.py is built from it.
"""
import argparse, datetime, difflib, html, json, os, random, re, sys, unicodedata, urllib.request

VERSION = "1.0.0"
DESIGNATION = "FS · SW · TOOL 007"
IAU_URL = "https://iauarchive.eso.org/public/themes/naming_stars/"
IAU_LIST = IAU_URL + "#n4"
DOCS = "https://github.com/nrdptel/fusionspace-design/tree/main/tools/christen"
REFRESH_DAYS = 30
FIELDS = ["name", "designation", "id", "con", "component", "wds", "vmag", "ra", "dec", "approved"]
HEADERS = {"IAU Name": "name", "Designation": "designation", "ID": "id", "Const.": "con", "#": "component",
           "WDS_J": "wds", "Vmag": "vmag", "RA(J2000)": "ra", "Dec(J2000)": "dec", "Approval Date": "approved"}

# The 88 IAU constellations, by their official three-letter abbreviation.
CONSTELLATIONS = {
    "And": "Andromeda", "Ant": "Antlia", "Aps": "Apus", "Aqr": "Aquarius", "Aql": "Aquila", "Ara": "Ara", "Ari": "Aries",
    "Aur": "Auriga", "Boo": "Boötes", "Cae": "Caelum", "Cam": "Camelopardalis", "Cnc": "Cancer", "CVn": "Canes Venatici",
    "CMa": "Canis Major", "CMi": "Canis Minor", "Cap": "Capricornus", "Car": "Carina", "Cas": "Cassiopeia",
    "Cen": "Centaurus", "Cep": "Cepheus", "Cet": "Cetus", "Cha": "Chamaeleon", "Cir": "Circinus", "Col": "Columba",
    "Com": "Coma Berenices", "CrA": "Corona Australis", "CrB": "Corona Borealis", "Crv": "Corvus", "Crt": "Crater",
    "Cru": "Crux", "Cyg": "Cygnus", "Del": "Delphinus", "Dor": "Dorado", "Dra": "Draco", "Equ": "Equuleus",
    "Eri": "Eridanus", "For": "Fornax", "Gem": "Gemini", "Gru": "Grus", "Her": "Hercules", "Hor": "Horologium",
    "Hya": "Hydra", "Hyi": "Hydrus", "Ind": "Indus", "Lac": "Lacerta", "Leo": "Leo", "LMi": "Leo Minor", "Lep": "Lepus",
    "Lib": "Libra", "Lup": "Lupus", "Lyn": "Lynx", "Lyr": "Lyra", "Men": "Mensa", "Mic": "Microscopium",
    "Mon": "Monoceros", "Mus": "Musca", "Nor": "Norma", "Oct": "Octans", "Oph": "Ophiuchus", "Ori": "Orion",
    "Pav": "Pavo", "Peg": "Pegasus", "Per": "Perseus", "Phe": "Phoenix", "Pic": "Pictor", "Psc": "Pisces",
    "PsA": "Piscis Austrinus", "Pup": "Puppis", "Pyx": "Pyxis", "Ret": "Reticulum", "Sge": "Sagitta",
    "Sgr": "Sagittarius", "Sco": "Scorpius", "Scl": "Sculptor", "Sct": "Scutum", "Ser": "Serpens", "Sex": "Sextans",
    "Tau": "Taurus", "Tel": "Telescopium", "Tri": "Triangulum", "TrA": "Triangulum Australe", "Tuc": "Tucana",
    "UMa": "Ursa Major", "UMi": "Ursa Minor", "Vel": "Vela", "Vir": "Virgo", "Vol": "Volans", "Vul": "Vulpecula"}

# The build puts the IAU list here, so this file works on its own. Without it, iau-star-names.json next to this file is read.
CATALOG = None


# ---------------------------------------------------------------- terminal styles (product/cli/fs_style.py)
class S:
    HEADING = "\x1b[1m"
    LITERAL = "\x1b[1;34m"
    WARNING = "\x1b[1;33m"
    DANGER = "\x1b[1;31m"
    MUTED = "\x1b[2m"
    RESET = "\x1b[0m"

def use_color(stream, flag="auto"):
    """The flag, then NO_COLOR, then FORCE_COLOR / CLICOLOR_FORCE, then: a terminal, and TERM isn't dumb."""
    if flag in ("always", "never"):
        return flag == "always"
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR") or os.environ.get("CLICOLOR_FORCE", "0") not in ("", "0"):
        return True
    return hasattr(stream, "isatty") and stream.isatty() and os.environ.get("TERM") != "dumb"

class Out:
    def __init__(self, color="auto"):
        for s in (sys.stdout, sys.stderr):                 # star names and Bayer letters on a Windows console
            try: s.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError): pass
        self.c_out, self.c_err = use_color(sys.stdout, color), use_color(sys.stderr, color)
    def paint(self, text, style, err=False):
        return f"{style}{text}{S.RESET}" if (self.c_err if err else self.c_out) else text
    def note(self, text):
        print(self.paint("note:", S.HEADING, True), text, file=sys.stderr)
    def warn(self, text):
        print(self.paint("warning:", S.WARNING, True), text, file=sys.stderr)


class Fail(Exception):
    """An error for the user: the message, an optional help line, and the exit code."""
    def __init__(self, message, help=None, code=1, kind="input"):
        super().__init__(message); self.help, self.code, self.kind = help, code, kind


# ---------------------------------------------------------------- the IAU list
def parse_iau(page):
    """The star table on the IAU's Naming Stars page, as a catalog. Stops if the table isn't the one expected."""
    i = page.find('id="dtHorizontalExample"')
    if i < 0:
        raise Fail("the IAU page has no star table any more", f"open {IAU_LIST} and check; the copy you have is kept")
    t = page[i:page.index("</table>", i)]
    clean = lambda c: html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
    heads = [clean(h) for h in re.findall(r"<th[^>]*>(.*?)</th>", t, re.S)]
    if [HEADERS.get(h) for h in heads] != FIELDS:
        raise Fail(f"the IAU table's columns changed: {', '.join(heads)}", "the copy you have is kept; report this so the reader can be updated")
    stars = []
    for tr in re.split(r"<tr[^>]*>", t)[1:]:
        cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if not cells:
            continue
        if len(cells) < len(FIELDS):                       # two cells run together with a tab (Proxima Centauri)
            cells = [p.strip() for c in cells for p in c.split("\t")]
        if len(cells) != len(FIELDS):
            raise Fail(f"can't read the IAU row for {cells[0] if cells else '?'}: {len(cells)} cells", "the copy you have is kept")
        row = [None if c in ("", "_", "-", "–") else c for c in cells]
        for k in (6, 7, 8):
            row[k] = float(row[k]) if row[k] is not None else None
        stars.append(row)
    names = [s[0] for s in stars]
    if len(stars) < 300 or len(set(names)) != len(names):
        raise Fail(f"the IAU table looks wrong: {len(stars)} rows, {len(names) - len(set(names))} repeated names", "the copy you have is kept")
    m = re.search(r"<h2[^>]*>([^<]*List of IAU-approved Star Names[^<]*)</h2>", page)
    return {"source": "IAU, Naming Stars: Current List of IAU Star Names", "url": IAU_LIST,
            "heading": re.sub(r"\s*\(click on headers to sort\)", "", clean(m.group(1))) if m else None,
            "read": datetime.date.today().isoformat(), "count": len(stars), "fields": FIELDS,
            "stars": sorted(stars, key=lambda s: fold(s[0]))}

def fetch_iau(timeout=20):
    req = urllib.request.Request(IAU_URL, headers={"User-Agent": f"christen/{VERSION} (FusionSpace; {DOCS})"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            page = r.read().decode("utf-8", "replace")
    except Exception as e:                                  # offline, DNS, TLS, timeouts: all mean "not now"
        reason = getattr(e, "reason", e)
        raise Fail(f"can't reach the IAU: {reason}", "the copy you have is kept; try again when you're online", kind="network")
    return parse_iau(page)

def cache_path():
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
        return os.path.join(base, "FusionSpace", "christen", "iau-star-names.json")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Caches/christen/iau-star-names.json")
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "christen", "iau-star-names.json")

def here(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)

def load_catalogs():
    """Every copy of the list there is, newest first: the cache (from christen update), the file next to this one, the built-in one."""
    found = []
    for where, path in (("cache", cache_path()), ("file", here("iau-star-names.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                c = json.load(fh)
            if c.get("fields") == FIELDS and c.get("stars"):
                found.append((where, path, c))
        except (OSError, ValueError):
            pass
    if CATALOG:
        found.append(("built in", None, CATALOG))
    found.sort(key=lambda f: f[2]["read"], reverse=True)    # stable: on a tie the cache wins
    return found

def dumps(catalog):
    """The list as JSON, a star per line, so a change to the list reads well in a diff."""
    lines = [f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in catalog.items() if k != "stars"]
    stars = ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in catalog["stars"])
    return "{\n" + ",\n".join(lines) + ',\n "stars": [\n' + stars + "\n ]\n}\n"

def save(catalog, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dumps(catalog))

def same_stars(a, b):
    return a["stars"] == b["stars"]

def catalog(args, out):
    found = load_catalogs()
    if not found:
        raise Fail("no star list: this copy of christen has none built in, and there's no iau-star-names.json next to it",
                   "run `christen update` to read the list from the IAU")
    where, path, c = found[0]
    checked = c.get("checked", c["read"])
    age = (datetime.date.today() - datetime.date.fromisoformat(checked[:10])).days
    if age > REFRESH_DAYS and not args.offline and not os.environ.get("CHRISTEN_OFFLINE") and not os.environ.get("CI"):
        if sys.stderr.isatty():
            out.note(f"the star list was last checked {age} days ago; reading it again from the IAU (--offline skips this)")
        try:
            new = fetch_iau(timeout=6)
            if same_stars(new, c):
                new["read"] = c["read"]
            new["checked"] = datetime.datetime.now().isoformat(timespec="seconds")
            try: save(new, cache_path())
            except OSError: pass
            if not same_stars(new, c):
                out.note(f"the IAU list changed: {c['count']} names before, {new['count']} now")
            c = new
        except Fail as e:
            if args.verbose: out.warn(str(e))
    return c


# ---------------------------------------------------------------- stars
def fold(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)).lower()

def code(name):
    """FS-<STAR>: capitals, no accents or apostrophes, words joined by hyphens. Barnard's Star is FS-BARNARDS-STAR."""
    s = fold(name).upper().replace("'", "").replace("’", "")
    return "FS-" + re.sub(r"[^A-Z0-9]+", "-", s).strip("-")

def letters(name):
    return sum(ch.isalpha() for ch in name)

def star(row):
    return dict(zip(FIELDS, row))

def con_name(abbr):
    return CONSTELLATIONS.get(abbr, abbr or "")

def find_con(text):
    """A constellation from its abbreviation or name, in any case, with or without accents."""
    key = fold(text.strip()).replace(" ", "")
    for abbr, name in CONSTELLATIONS.items():
        if key in (abbr.lower(), fold(name).replace(" ", "")):
            return abbr
    names = {fold(n): a for a, n in CONSTELLATIONS.items()}
    close = difflib.get_close_matches(fold(text.strip()), list(names), n=1, cutoff=0.6)
    hint = f"did you mean {CONSTELLATIONS[names[close[0]]]} ({names[close[0]]})? " if close else ""
    raise Fail(f"no constellation named {text}", hint + "`christen constellations` lists them", code=2, kind="usage")

def vmag_range(text):
    """'..3', '2..5', '-1.5..2', '4..', or one number (that magnitude or brighter)."""
    m = re.fullmatch(r"\s*([-+]?\d*\.?\d+)?\s*(\.\.)?\s*([-+]?\d*\.?\d+)?\s*", text.replace("−", "-"))
    if not m or not (m.group(1) or m.group(3)) or (m.group(2) is None and m.group(3)):
        raise argparse.ArgumentTypeError(f"{text!r} isn't a range: write ..3, 2..5, 4.. or --vmag=-1.5..2")
    lo = float(m.group(1)) if m.group(1) and m.group(2) else None
    hi = float(m.group(3)) if m.group(3) else (float(m.group(1)) if not m.group(2) else None)
    if lo is not None and hi is not None and lo > hi:
        raise argparse.ArgumentTypeError(f"{text!r}: the first number has to be the brighter one (smaller): {hi:g}..{lo:g}")
    return (lo, hi)

def describe(args):
    parts = []
    if args.cons: parts.append(" or ".join(con_name(a) for a in args.cons))
    lo, hi = args.vmag or (None, None)
    if lo is not None and hi is not None: parts.append(f"vmag {lo:g} to {hi:g}")
    elif hi is not None: parts.append(f"vmag {hi:g} or brighter")
    elif lo is not None: parts.append(f"vmag {lo:g} or fainter")
    if args.max_letters: parts.append(f"{args.max_letters} letters or fewer")
    if args.skip: parts.append(f"skipping {len(args.skip)}")
    return ", ".join(parts)

def matches(c, args):
    lo, hi = args.vmag or (None, None)
    skip = {fold(s) for s in args.skip}
    out = []
    for r in c["stars"]:
        s = star(r)
        if args.cons and s["con"] not in args.cons: continue
        if (lo is not None or hi is not None) and s["vmag"] is None: continue
        if lo is not None and s["vmag"] < lo: continue
        if hi is not None and s["vmag"] > hi: continue
        if args.max_letters and letters(s["name"]) > args.max_letters: continue
        if fold(s["name"]) in skip: continue
        out.append(s)
    return out

def no_match(c, args):
    msg = f"no star matches: {describe(args)}"
    if args.cons:
        inside = [star(r) for r in c["stars"] if star(r)["con"] in args.cons]
        mags = [s["vmag"] for s in inside if s["vmag"] is not None]
        if not inside:
            raise Fail(msg, "no IAU-named star is in that constellation; `christen constellations` lists the ones with names")
        b = min(inside, key=lambda s: s["vmag"] if s["vmag"] is not None else 99)
        raise Fail(msg, f"{len(inside)} named stars are in {' or '.join(con_name(a) for a in args.cons)}, vmag {min(mags):g} to {max(mags):g}; the brightest is {b['name']}")
    raise Fail(msg, "widen the vmag range or the name length")

def hms(ra):
    h = ra / 15; m = (h % 1) * 60; s = (m % 1) * 60
    return f"{int(h):02d}h {int(m):02d}m {s:04.1f}s"

def dms(dec):
    sign = "+" if dec >= 0 else "-"; d = abs(dec); m = (d % 1) * 60; s = (m % 1) * 60
    return f"{sign}{int(d):02d}° {int(m):02d}′ {int(round(s)) if round(s) < 60 else 59:02d}″"

def as_json(s):
    return {"name": s["name"], "code": code(s["name"]), "designation": s["designation"], "id": s["id"],
            "constellation": {"abbr": s["con"], "name": con_name(s["con"])}, "component": s["component"],
            "wds": s["wds"], "vmag": s["vmag"], "ra_deg": s["ra"], "dec_deg": s["dec"], "approved": s["approved"]}

def meta(c):
    return {k: c.get(k) for k in ("source", "url", "heading", "read", "count")}

def card(s, out):
    """One star, as label / value lines."""
    ident = ", ".join(x for x in (s["designation"], f"{s['id']} {s['con']}" if s["id"] else None) if x)
    lines = [("designation", ident), ("constellation", f"{con_name(s['con'])} ({s['con']})"),
             ("vmag", f"{s['vmag']:.2f}" if s["vmag"] is not None else "not given by the IAU"),
             ("position", f"RA {hms(s['ra'])}, Dec {dms(s['dec'])} (J2000)" if s["ra"] is not None else "not given"),
             ("approved", s["approved"] or "not given")]
    if s["wds"]: lines.insert(2, ("double star", f"WDS J{s['wds']}" + (f", component {s['component']}" if s["component"] else "")))
    print(out.paint(f"{s['name']:<16}", S.HEADING) + "  " + out.paint(code(s["name"]), S.HEADING))
    for k, v in lines:
        print(f"{k:<16}  {v}")

def table(stars, out):
    w = max([4] + [len(s["name"]) for s in stars]); wc = max([4] + [len(code(s["name"])) for s in stars])
    print(out.paint(f"{'name':<{w}}  {'code':<{wc}}  con  {'vmag':>5}  designation", S.HEADING))
    for s in stars:
        v = f"{s['vmag']:5.2f}" if s["vmag"] is not None else "    -"
        print(f"{s['name']:<{w}}  {code(s['name']):<{wc}}  {s['con']:<3}  {v}  {s['designation'] or ''}")


# ---------------------------------------------------------------- commands
def cmd_draw(c, args, out):
    pool = matches(c, args)
    if not pool: no_match(c, args)
    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()
    picked = rng.sample(pool, min(args.n, len(pool)))
    if args.json:
        print(json.dumps({"list": meta(c), "filters": describe(args) or None, "matched": len(pool),
                          "stars": [as_json(s) for s in picked]}, ensure_ascii=False, indent=2)); return
    if args.plain:
        print("\n".join(f"{s['name']}\t{code(s['name'])}" for s in picked)); return
    filt = describe(args)
    print(out.paint(f"drawn from {len(pool)} of {c['count']} IAU star names" + (f" ({filt})" if filt else "")
                    + f", list read {c['read']}", S.MUTED, True), file=sys.stderr)
    if args.n > len(pool):
        out.warn(f"asked for {args.n}, only {len(pool)} match")
    if len(picked) == 1: card(picked[0], out)
    else: table(picked, out)

def cmd_list(c, args, out):
    pool = matches(c, args)
    if not pool: no_match(c, args)
    key = {"name": lambda s: fold(s["name"]), "vmag": lambda s: (s["vmag"] is None, s["vmag"] or 0),
           "constellation": lambda s: (con_name(s["con"]), fold(s["name"])), "approved": lambda s: (s["approved"] or "", fold(s["name"]))}[args.sort]
    pool.sort(key=key)
    if args.json:
        print(json.dumps({"list": meta(c), "filters": describe(args) or None, "matched": len(pool),
                          "stars": [as_json(s) for s in pool]}, ensure_ascii=False, indent=2)); return
    if args.csv:
        import csv
        w = csv.writer(sys.stdout, lineterminator="\n")
        w.writerow(["name", "code"] + FIELDS[1:])
        for s in pool: w.writerow([s["name"], code(s["name"])] + ["" if s[k] is None else s[k] for k in FIELDS[1:]])
        return
    if args.plain:
        print("\n".join(s["name"] for s in pool)); return
    filt = describe(args)
    print(out.paint(f"{len(pool)} of {c['count']} IAU star names" + (f" ({filt})" if filt else "") + f", list read {c['read']}", S.MUTED, True), file=sys.stderr)
    table(pool, out)

def cmd_show(c, args, out):
    want = fold(" ".join(args.name)).replace("fs-", "", 1) if fold(" ".join(args.name)).startswith("fs-") else fold(" ".join(args.name))
    for r in c["stars"]:
        s = star(r)
        if want in (fold(s["name"]), fold(code(s["name"])[3:]).replace("-", " ")):
            if args.json: print(json.dumps({"list": meta(c), "star": as_json(s)}, ensure_ascii=False, indent=2))
            else: card(s, out)
            return
    close = difflib.get_close_matches(want, [fold(r[0]) for r in c["stars"]], n=3, cutoff=0.6)
    names = {fold(r[0]): r[0] for r in c["stars"]}
    raise Fail(f"no IAU star named {' '.join(args.name)}",
               ("did you mean " + " or ".join(names[x] for x in close) + "?") if close else "`christen list` shows every name")

def cmd_constellations(c, args, out):
    count = {}
    for r in c["stars"]: count[r[3]] = count.get(r[3], 0) + 1
    rows = sorted(CONSTELLATIONS.items(), key=lambda kv: fold(kv[1]))
    if args.json:
        print(json.dumps([{"abbr": a, "name": n, "stars": count.get(a, 0)} for a, n in rows], ensure_ascii=False, indent=2)); return
    print(out.paint(f"{'abbr':<4}  {'constellation':<20}  {'stars':>5}", S.HEADING))
    for a, n in rows:
        if count.get(a) or args.all:
            print(f"{a:<4}  {n:<20}  {count.get(a, 0):>5}")
    if not args.all:
        print(out.paint(f"{sum(1 for a in CONSTELLATIONS if not count.get(a))} constellations have no IAU-named star; --all shows them", S.MUTED, True), file=sys.stderr)

def cmd_update(c_old, args, out):
    if sys.stderr.isatty() and not args.json:
        print(out.paint(f"reading {IAU_LIST}", S.MUTED, True), file=sys.stderr)
    new = fetch_iau()
    old = c_old
    if old and same_stars(new, old):
        new["read"] = old["read"]
    new["checked"] = datetime.datetime.now().isoformat(timespec="seconds")
    path = args.out or cache_path()
    if args.out:                                            # a file for the repository: no machine-specific check time
        new.pop("checked")
    try:
        save(new, path)
    except OSError as e:
        raise Fail(f"can't write {path}: {e.strerror}", "pass --out with a folder you can write to")
    before = {r[0] for r in old["stars"]} if old else set()
    after = {r[0] for r in new["stars"]}
    added, gone = sorted(after - before, key=fold), sorted(before - after, key=fold)
    if args.json:
        print(json.dumps({"list": meta(new), "saved": path, "added": added, "removed": gone,
                          "changed": not (old and same_stars(new, old))}, ensure_ascii=False, indent=2)); return
    print(f"{'iau list':<16}  {new['count']} names, {new['heading'] or 'no date on the page'}")
    print(f"{'saved':<16}  {path}")
    if not old: print(f"{'changes':<16}  none to compare with")
    elif same_stars(new, old): print(f"{'changes':<16}  none since {old['read']}")
    else:
        print(f"{'changes':<16}  {len(added)} added, {len(gone)} removed, since {old['read']}")
        if added: print(f"{'added':<16}  " + ", ".join(added))
        if gone: print(f"{'removed':<16}  " + ", ".join(gone))

def cmd_ui(c, args, out):
    page = here("christen.html")
    if not os.path.exists(page):
        raise Fail(f"no christen.html next to {os.path.basename(__file__)}", f"download it from {DOCS} and keep the two files together")
    import pathlib, webbrowser
    webbrowser.open(pathlib.Path(page).as_uri())
    print(page)


def parser():
    common = argparse.ArgumentParser(add_help=False)
    g = common.add_argument_group("filters")
    g.add_argument("-c", "--constellation", action="append", default=[], metavar="NAME",
                   help="Orion, ori or Ori; repeat, or separate with commas, for several")
    g.add_argument("--vmag", type=vmag_range, metavar="RANGE",
                   help="visual magnitude, smaller is brighter: ..3 (3 or brighter), 2..5, 4.. (4 or fainter); a negative start needs =, as in --vmag=-1.5..2")
    g.add_argument("--max-letters", type=int, metavar="N", help="names with N letters or fewer (short names make short codes)")
    g.add_argument("--skip", action="append", default=[], metavar="NAMES", help="names already in use, separated with commas; repeat as needed")
    o = common.add_argument_group("output")
    o.add_argument("--json", action="store_true", help="one JSON document on stdout")
    o.add_argument("--plain", action="store_true", help="names only, one per line, for scripts")
    o.add_argument("--color", choices=("auto", "always", "never"), default="auto", help="color in the output (default auto; NO_COLOR is respected)")
    o.add_argument("--offline", action="store_true", help="don't read the IAU list again, even when the copy is over 30 days old")
    o.add_argument("--verbose", action="store_true", help="say why an automatic update failed")

    p = argparse.ArgumentParser(prog="christen", parents=[common],
        description="Name a FusionSpace project after an IAU-approved star.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n  christen                              draw a star\n"
               "  christen -n 5 -c Orion --vmag ..3     five bright stars in Orion\n"
               "  christen list --max-letters 5         every name of five letters or fewer\n"
               "  christen show Vega                    one star\n"
               "  christen update                       read the IAU list now\n"
               "  christen ui                           the same tool in a browser\n\n"
               f"star list: {IAU_LIST}\ndocs: {DOCS}")
    p.add_argument("--version", action="store_true", help="the version, and which star list is in use")
    sub = p.add_subparsers(dest="cmd", metavar="command")
    d = sub.add_parser("draw", parents=[common], help="draw stars at random (the default)", description="Draw stars at random from the IAU list.")
    for q in (p, d):
        q.add_argument("-n", type=int, default=1, metavar="N", help="how many to draw (default 1), never the same one twice")
        q.add_argument("--seed", type=int, help="the same seed draws the same stars from the same list")
    l = sub.add_parser("list", parents=[common], help="every star that matches", description="Every IAU star name that matches the filters.")
    l.add_argument("--sort", choices=("name", "vmag", "constellation", "approved"), default="name")
    l.add_argument("--csv", action="store_true", help="CSV on stdout, with every column")
    s = sub.add_parser("show", parents=[common], help="one star, by name or code", description="One star, by its name or its FS code.")
    s.add_argument("name", nargs="+")
    k = sub.add_parser("constellations", parents=[common], help="constellations and how many named stars each has")
    k.add_argument("--all", action="store_true", help="include the constellations with no named star")
    u = sub.add_parser("update", parents=[common], help="read the star list from the IAU now", description=f"Read the star list from {IAU_LIST}.")
    u.add_argument("--out", metavar="FILE", help="write the list here instead of the cache")
    sub.add_parser("ui", parents=[common], help="open christen.html, the same tool in a browser")
    return p

def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    args.cmd = args.cmd or "draw"
    out = Out(args.color)
    try:
        if getattr(args, "n", 1) < 1: raise Fail("-n has to be 1 or more", code=2, kind="usage")
        args.cons = [find_con(x) for v in args.constellation for x in v.split(",") if x.strip()]
        args.skip = [x.strip() for v in args.skip for x in v.split(",") if x.strip()]
        if args.max_letters is not None and args.max_letters < 1: raise Fail("--max-letters has to be 1 or more", code=2, kind="usage")
        if args.cmd == "update":
            found = load_catalogs()
            cmd_update(found[0][2] if found else None, args, out); return 0
        c = catalog(args, out)
        if args.version:
            print(f"christen {VERSION} ({DESIGNATION})\nstar list: {c['count']} IAU names, read {c['read']} from {c['url']}"); return 0
        {"draw": cmd_draw, "list": cmd_list, "show": cmd_show, "constellations": cmd_constellations, "ui": cmd_ui}[args.cmd](c, args, out)
        return 0
    except Fail as e:
        if getattr(args, "json", False):
            print(json.dumps({"error": {"kind": e.kind, "code": e.code, "message": str(e), "help": e.help}}, ensure_ascii=False, indent=2))
        else:
            print(out.paint("error:", S.DANGER, True), e, file=sys.stderr)
            if e.help: print(out.paint("help:", S.LITERAL, True), e.help, file=sys.stderr)
        return e.code
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        return 0

if __name__ == "__main__":
    sys.exit(main())
