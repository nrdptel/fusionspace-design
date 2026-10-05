"""FusionSpace kit: GitHub extras (profile README, labels, badges, how-to) and the example project."""
import os, json
import build, kit
from kit import KIT, TAGLINE, SCOPE, DISCIPLINES, SITE, SITE_URL, GITHUB_URL, note, out

LABELS = [  # GitHub issue labels in brand colours (hex without #)
    ("bug", "B34F0C", "Something is broken"), ("feature", "3350D6", "New capability"), ("enhancement", "768DF5", "Improve something that works"),
    ("docs", "A188CB", "Documentation"), ("hardware", "DA7C30", "PCBs, wiring, mechanical, machining"), ("firmware", "D07D7A", "Embedded and flight software"),
    ("test", "566079", "Tests, verification, CI"), ("question", "98A1B8", "Needs an answer"), ("blocked", "0B0F1C", "Waiting on something else"),
    ("good first issue", "D6DAE4", "Small and well-scoped"), ("wontfix", "2A3248", "Decided against")]
BADGES = [("FusionSpace", "Rev C", "0B0F1C", "3350D6"), ("status", "active", "3350D6", "0B0F1C"), ("status", "prototype", "B34F0C", "0B0F1C"),
          ("status", "archived", "566079", "0B0F1C")] + [(t, d.split(" and ")[0].lower(), "0B0F1C", "566079") for t, d in DISCIPLINES]

def q(x): return x.replace("-", "--").replace("_", "__").replace(" ", "%20")
def badge(l, m, c, lc): return f"![{l}: {m}](https://img.shields.io/badge/{q(l)}-{q(m)}-{c}?style=flat-square&labelColor={lc})"

PROFILE = """<!-- GitHub profile README for FusionSpace. Create a repo named exactly like your username, add this as README.md,
     and copy readme-banner-dark.png / readme-banner-light.png into it (paths below assume the repo root). -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="readme-banner-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="readme-banner-light.png">
  <img alt="FusionSpace · {tagline}" src="readme-banner-dark.png" width="100%">
</picture>

### Hi, I'm Neer.

{role}. [FusionSpace]({site_url}) is everything I make, under one name: {scope}. Each project is named after a star.

| Project | What | Status |
|---|---|---|
| [FS-VEGA]({github}/vega) | One-line description | {active} |
| [FS-ACHERNAR]({github}/achernar) | One-line description | {proto} |

<details><summary>Discipline tags</summary>

| Tag | Meaning |
|---|---|
{tags}

</details>
"""

HOWTO = """# GitHub setup with the FusionSpace kit

1. **Avatar**: upload `avatar-dark-500.png` (Settings → Profile → Profile picture). Use the same for an organization.
2. **Profile README**: follow `profile-README.md` (a repo named after your username, plus the two banner PNGs).
3. **Each repository**:
   - Social preview: Settings → General → Social preview → upload `social-preview-dark.png`, or a per-project one made with
     `python3 tools/build/project.py --name <Star> --tag <TAG> --desc "..."` (example in `kit/projects/example-vega/`).
   - README header: copy the project's `readme-banner-dark.png` and `-light.png` into `.github/brand/` and start from its
     `README-starter.md` (or use the brand banners here with `README-snippet.md`).
   - Labels: `./apply-labels.sh owner/repo` (needs the GitHub CLI, `gh`). Colours come from the palette; see `labels.json`.
   - Badges: `badges.md`.
   - Topics: add `fusionspace` plus the discipline (e.g. `embedded`, `pcb`, `cnc`, `game`) so projects are easy to filter.
4. **GitHub Pages or a docs site**: use `kit/web/` for the icon set and `kit/software/docs-theme/` (MkDocs Material or Docusaurus) for the look; `color/fusion-space-tokens.css` has the raw colours.
"""

def build_github_extras():
    Gd = f"{KIT}/github"; G = "Profiles & social"
    build.wr(f"{Gd}/badges.md", "# FusionSpace README badges (shields.io, brand colours)\n\nCopy the lines you need.\n\n"
             + "\n".join(f"{badge(*b)}\n```\n{badge(*b)}\n```\n" for b in BADGES))
    build.wr(f"{Gd}/labels.json", json.dumps([{"name": n, "color": c, "description": d} for n, c, d in LABELS], indent=2) + "\n")
    build.wr(f"{Gd}/apply-labels.sh", "#!/usr/bin/env bash\n# Create or update the FusionSpace issue labels in a repo: ./apply-labels.sh owner/repo   (needs the GitHub CLI, gh)\n"
             "set -euo pipefail\nREPO=\"$1\"\n" + "".join(f'gh label create "{n}" --repo "$REPO" --color {c} --description "{d}" --force\n' for n, c, d in LABELS))
    os.chmod(out(f"{Gd}/apply-labels.sh"), 0o755)
    tags = "\n".join(f"| `{t}` | {d} |" for t, d in DISCIPLINES)
    build.wr(f"{Gd}/profile-README.md", PROFILE.format(tagline=TAGLINE, role=kit.ROLE, scope=SCOPE, tags=tags, github=GITHUB_URL, site_url=SITE_URL,
             active=badge("status", "active", "3350D6", "0B0F1C"), proto=badge("status", "prototype", "B34F0C", "0B0F1C")))
    build.wr(f"{Gd}/HOW-TO.md", HOWTO)
    for p, what, use in [("profile-README.md", "profile README template with light/dark banner and project table", "github.com/<you>/<you>"),
                         ("HOW-TO.md", "step-by-step GitHub setup with these files", "Start here for GitHub"),
                         ("labels.json / apply-labels.sh", "issue labels in brand colours, applied with the GitHub CLI", "Any repo"),
                         ("badges.md", "shields.io badges in brand colours (status, discipline)", "READMEs")]:
        note(f"{Gd}/{p}", G, what, "", use)

def build_example_project():
    import project
    p = project.Project("Vega", tag="EMB", desc="Example project: flight software for a two-stage sounding rocket.")
    d = out(f"{KIT}/projects/example-vega")
    project.make(p, d)
    note(f"{KIT}/projects/example-vega/", "Per-project", "example output of tools/build/project.py (social preview, README banners, OG, YouTube thumbnail, title slides, report covers, starter README)",
         "", "Run project.py for each new project; see HOW-TO-USE.md inside")

# The site's tools keep their own names (code FS, tag SW, numbered in the site's order); descriptions as on fusionspace.co
# (checked 3 October 2026).
SITE_TOOLS = [
    ("HPR Motor Finder", "AeroTech, Cesaroni & Loki motor stock and pricing, aggregated across major U.S. vendors."),
    ("Charge", "Black-powder ejection-charge calculator for high-power rocketry."),
    ("Window", "Launch-weather board for US high-power and model rocketry."),
    ("Muster", "Motor-hardware compatibility for high-power rocketry."),
]

def build_naming_option():
    """Full project kits for the site's tools, each under its own name: designation FS · SW · TOOL 00n."""
    import project
    for n, (name, desc) in enumerate(SITE_TOOLS, 1):
        p = project.Project(name, code="FS", tag="SW", kind="Tool", number=f"{n:03d}", desc=desc)
        d = f"{KIT}/projects/{p.slug}"
        project.make(p, out(d))
        note(f"{d}/", "Per-project", f"{name}: project kit (social preview, README banners, OG, YouTube thumbnail, title slides, report covers, starter README); {p.designation}",
             "", "the tool's repo, its page on fusionspace.co, talks and reports")
