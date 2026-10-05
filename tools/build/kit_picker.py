"""Star name picker: tools/star-name-picker/ (index.html and the cleaned IAU catalog as CSV).

The page and the catalog are kept in source/star-name-picker/. The build puts the current horizontal lockup (the
approved proportions, outlined wordmark) in the header, so the picker follows any change to the logo, and loads Cascadia
Mono and Archivo from type/fonts/ instead of a web font service. Colors, the gradient strip and the rest of the page are
as in the source."""
import os, re, shutil
import build

D = "tools/star-name-picker"
FONTS = "../../type/fonts/"
FONT_FACES = "".join(
    f'@font-face{{font-family:"{fam}";src:url("{FONTS}{fn}") format("truetype");font-weight:{w};font-style:{st};font-display:swap}}\n'
    for fam, fn, w, st in (("Archivo", "Archivo-Regular.ttf", 400, "normal"), ("Archivo", "Archivo-Italic.ttf", 400, "italic"),
                           ("Archivo", "Archivo-Medium.ttf", 500, "normal"), ("Archivo", "Archivo-SemiBold.ttf", 600, "normal"),
                           ("Cascadia Mono", "CascadiaMono-Regular.ttf", 400, "normal"),
                           ("Cascadia Mono", "CascadiaMono-Medium.ttf", 500, "normal"),
                           ("Cascadia Mono", "CascadiaMono-SemiBold.ttf", 600, "normal")))

def build_picker():
    s = build.rd("star-name-picker/index.html")
    lockup = open(os.path.join(build.OUT, "logo/lockup/fusion-space-horizontal-color.svg"), encoding="utf-8").read()
    logo = build.inline(lockup, "lk", "height:28px;width:auto;display:block", extra=' role="img" aria-label="FusionSpace"')
    reps = [
        ("<title>Star Name Picker</title>", "<title>Star Name Picker · FusionSpace</title>"),
        ('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n', ""),
        (re.search(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n', s).group(0), ""),
        ("<style>\n", "<style>\n" + FONT_FACES),
        (".brand svg{height:28px;width:auto;flex:none}\n", ".brand svg{height:28px;width:auto;flex:none;display:block}\n"),
        (re.search(r"\.wm\{[^}]*\}\n", s).group(0), ""),
        (re.search(r'<svg viewBox="0 0 109\.35 100".*?<span class="wm">FusionSpace</span>', s, re.S).group(0), logo),
    ]
    for a, b in reps:
        assert s.count(a) == 1, a[:60]
        s = s.replace(a, b)
    assert "googleapis" not in s and "Fusion Space" not in s
    build.wr(f"{D}/index.html", s)
    shutil.copyfile(os.path.join(build.SRC, "star-name-picker", "iau-star-names.csv"), os.path.join(build.OUT, D, "iau-star-names.csv"))
