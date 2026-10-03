"""Assemble the mark tuner into one self-contained page.

    python3 tools/mark-tuner/src/assemble.py            # writes tools/mark-tuner/index.html
    python3 tools/mark-tuner/src/assemble.py --artifact # also writes artifact.html (no doctype/head; for publishing)

app.html holds the page; geo.js is the port of tools/build/geo.py (+ lockup/icon geometry from build.py);
wm-*.txt are the outlined wordmark paths from the Rev B lockups in source/ that build.py reads."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
rd = lambda n: open(os.path.join(HERE, n), encoding="utf-8").read()
out = (rd("app.html").replace("/*__GEO__*/", rd("geo.js"))
       .replace("__WM_S__", rd("wm-stacked.txt")).replace("__WM_H__", rd("wm-horizontal.txt")))
head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<link rel="icon" href="../../logo/favicon/favicon.svg">\n')
i = out.index('<div class="strip">')
open(os.path.join(HERE, "..", "index.html"), "w", encoding="utf-8").write(head + out[:i] + "</head>\n<body>\n" + out[i:] + "</body>\n</html>\n")
if "--artifact" in sys.argv:
    hook = os.path.join(HERE, "artifact-hook.js")     # optional, local only: the hosted copy's save handler (sets dl)
    if os.path.exists(hook): out = out.replace("/*__SAVE_HOOK__*/", rd("artifact-hook.js").strip())
    open(os.path.join(HERE, "artifact.html"), "w", encoding="utf-8").write(out)
print("wrote tools/mark-tuner/index.html")
