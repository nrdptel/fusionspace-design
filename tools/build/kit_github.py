"""FusionSpace kit: GitHub extras (profile README, labels, badges, how-to) and the example project."""
import os, json
import build
from kit import KIT, TAGLINE, DISCIPLINES, SITE, SITE_URL, GITHUB_URL, note, out

LABELS = [  # GitHub issue labels in brand colors (hex without #)
    ("bug", "B34F0C", "Something is broken"), ("feature", "3350D6", "New capability"), ("enhancement", "768DF5", "Improve something that works"),
    ("docs", "A188CB", "Documentation"), ("hardware", "DA7C30", "PCBs, wiring, mechanical, machining"), ("firmware", "D07D7A", "Embedded and flight software"),
    ("test", "566079", "Tests, verification, CI"), ("question", "98A1B8", "Needs an answer"), ("blocked", "0B0F1C", "Waiting on something else"),
    ("good first issue", "D6DAE4", "Small and well-scoped"), ("wontfix", "2A3248", "Decided against")]
BADGES = [("FusionSpace", "Rev C", "0B0F1C", "3350D6"), ("status", "active", "3350D6", "0B0F1C"), ("status", "prototype", "B34F0C", "0B0F1C"),
          ("status", "archived", "566079", "0B0F1C")] + [(t, d.split(" and ")[0].lower(), "0B0F1C", "566079") for t, d in DISCIPLINES]

def q(x): return x.replace("-", "--").replace("_", "__").replace(" ", "%20")
def badge(l, m, c, lc): return f"![{l}: {m}](https://img.shields.io/badge/{q(l)}-{q(m)}-{c}?style=flat-square&labelColor={lc})"

# The README on github.com/nrdptel, word for word (October 19, 2026), with what fusionspace.co lists, in the maintainer's own
# voice (product/writing.md#voice): no item opens with a bold label. The banners are the @2x ones: GitHub's sanitizer drops
# srcset's 1x/2x descriptors, so the large file is the only source. Lists, not tables: a table scrolls sideways on a phone.
PROFILE = """<picture>
  <source media="(prefers-color-scheme: dark)" srcset="readme-banner@2x-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="readme-banner@2x-light.png">
  <img alt="FusionSpace · {tagline}" src="readme-banner@2x-dark.png" width="100%">
</picture>

### Hi, I'm Neer.

I'm a software engineer in Auburn, Alabama. Under the name [FusionSpace]({site_url}) I make free, open-source
software for hobby and high-power rockets: [HPR Sim](https://hpr.fusionspace.co/the-simulator.html), a flight simulator,
and the suite I'm building around it.

#### FusionSpace HPR

It's one suite for hobby and high-power rockets, written in Rust and licensed MIT or Apache-2.0. Every product's source
and releases live in [fusionspace-eridanus]({github}/fusionspace-eridanus).

HPR Sim is released: version [0.1.0]({github}/fusionspace-eridanus/releases/tag/v0.1.0), from 2026-10-08. It's a 6-DOF
flight simulator: a Rust library, the `hpr` command and a Python package. It reads OpenRocket designs, flies Monte Carlo
dispersions, and publishes [how far to trust it](https://hpr.fusionspace.co/trusting-a-simulation.html).
[Guide](https://hpr.fusionspace.co/the-simulator.html) · [Docs](https://hpr.fusionspace.co/) ·
[PyPI](https://pypi.org/project/fusionspace-hpr/) · [crates.io](https://crates.io/crates/fusionspace-hpr)

To try it, run `pip install fusionspace-hpr` for Python, or `cargo install fusionspace-hpr-cli --locked` for the `hpr`
command. The rest of the suite is in preparation:

- the Analyzer, for 0.2, will read a flight computer's log and set the flight beside its simulation;
- the Competition Kit, for 0.4, will hold challenge rules, presets and submission packs for student rocketry competitions;
- the app, with a preview in 0.5 and then 1.0, will do design, simulation and flight replay on the desktop, the web and
  phones;
- after 1.0 come the Motor Designer, the Recovery Designer and Avionics.

#### Web tools

These four browser tools came before FusionSpace HPR. Each keeps working at its own address until its rebuild inside HPR
ships.

- [HPR Motor Finder](https://motor.fusionspace.co) shows AeroTech, Cesaroni and Loki motor stock and prices across U.S.
  vendors, matched to ThrustCurve. [Source]({github}/Hobby-Rocket-Motor-Finder)
- [Charge](https://charge.fusionspace.co) sizes black-powder ejection charges, every constant shown, with a log of your
  ground tests. [Source]({github}/fusionspace-charge)
- [Window](https://window.fusionspace.co) gives launch weather at any U.S. field: surface wind, winds aloft, storms, cloud
  ceiling and a few days ahead. [Source]({github}/fusionspace-window)
- [Muster](https://muster.fusionspace.co) shows which reloads, closures and spacers fit each reloadable motor case, and
  the parts to buy. [Source]({github}/fusionspace-muster)

#### How they're built

- Show the working. Formulas, constants and sources are there to read, not hidden.
- Say how far to trust it. An estimate says it's an estimate and shows its spread. You never get a go/no-go verdict.
- Work at the field. Readable in sun, with big targets for cold hands. HPR Sim's core needs no network.
- No accounts, no tracking.

Every FusionSpace site, tool and app follows one brand and product system,
[fusionspace-design]({github}/fusionspace-design). The front page's source is
[fusionspace-site]({github}/fusionspace-site).
"""

HOWTO = """# GitHub setup with the FusionSpace kit

1. **Avatar**: upload `avatar-dark-500.png` (Settings → Profile → Profile picture). Use the same for an organization.
2. **Profile README**: `profile-README.md` is the README of a repo named after your username; put
   `readme-banner@2x-dark.png` and `readme-banner@2x-light.png` beside it.
3. **Each repository**:
   - Social preview: Settings → General → Social preview → upload the project's `social-preview-dark.png` from
     `kit/projects/` (HPR is `achernar/`; the four web tools and fusionspace.co each have their own), or make one with
     `python3 tools/build/project.py --star <Star> [--name <external name>] --tag <TAG> --desc "..."` (example in `kit/projects/example-vega/`).
   - README header: copy the project's `readme-banner-dark.png` and `-light.png` into `.github/brand/` and start from its
     `README-starter.md` (or use the brand banners here with `README-snippet.md`).
   - Labels: `./apply-labels.sh owner/repo` (needs the GitHub CLI, `gh`). Colors come from the palette; see `labels.json`.
   - Badges: `badges.md`.
   - Topics: add `fusionspace` plus the discipline (e.g. `embedded`, `pcb`, `cnc`, `game`) so projects are easy to filter.
4. **GitHub Pages or a docs site**: use `kit/web/` for the icon set and `kit/software/docs-theme/` (MkDocs Material or Docusaurus) for the look; `color/fusion-space-tokens.css` has the raw colors.
"""

def build_github_extras():
    Gd = f"{KIT}/github"; G = "Profiles & social"
    build.wr(f"{Gd}/badges.md", "# FusionSpace README badges (shields.io, brand colors)\n\nCopy the lines you need.\n\n"
             + "\n".join(f"{badge(*b)}\n```\n{badge(*b)}\n```\n" for b in BADGES))
    build.wr(f"{Gd}/labels.json", json.dumps([{"name": n, "color": c, "description": d} for n, c, d in LABELS], indent=2) + "\n")
    build.wr(f"{Gd}/apply-labels.sh", "#!/usr/bin/env bash\n# Create or update the FusionSpace issue labels in a repo: ./apply-labels.sh owner/repo   (needs the GitHub CLI, gh)\n"
             "set -euo pipefail\nREPO=\"$1\"\n" + "".join(f'gh label create "{n}" --repo "$REPO" --color {c} --description "{d}" --force\n' for n, c, d in LABELS))
    os.chmod(out(f"{Gd}/apply-labels.sh"), 0o755)
    build.wr(f"{Gd}/profile-README.md", PROFILE.format(tagline=TAGLINE, github=GITHUB_URL, site_url=SITE_URL))
    build.wr(f"{Gd}/HOW-TO.md", HOWTO)
    for p, what, use in [("profile-README.md", "the profile README: light/dark banner, FusionSpace HPR, the web tools and the principles", "github.com/nrdptel/nrdptel"),
                         ("HOW-TO.md", "step-by-step GitHub setup with these files", "Start here for GitHub"),
                         ("labels.json / apply-labels.sh", "issue labels in brand colors, applied with the GitHub CLI", "Any repo"),
                         ("badges.md", "shields.io badges in brand colors (status, discipline)", "READMEs")]:
        note(f"{Gd}/{p}", G, what, "", use)

def build_example_project():
    import project
    p = project.Project(star="Vega", tag="EMB", desc="Example product: flight software for a two-stage sounding rocket.")
    d = out(f"{KIT}/projects/example-vega")
    project.make(p, d)
    note(f"{KIT}/projects/example-vega/", "Per-project", "example output of tools/build/project.py (social preview, README banners, OG, YouTube thumbnail, title slides, report covers, starter README)",
         "", "Run project.py for each new product; see HOW-TO-USE.md inside")

# The site's tools came before the naming rule (a constellation per project, a star per product): until they move to it,
# they keep their own names (code FS, tag SW, numbered in the site's order); descriptions as on fusionspace.co
# (checked October 3, 2026).
SITE_TOOLS = [
    ("HPR Motor Finder", "AeroTech, Cesaroni & Loki motor stock and pricing, aggregated across major U.S. vendors."),
    ("Charge", "Black-powder ejection-charge calculator for high-power rocketry."),
    ("Window", "Launch-weather board for US high-power and model rocketry."),
    ("Muster", "Motor-hardware compatibility for high-power rocketry."),
]
SITE_DESC = "Open-source software for hobby and high-power rockets."      # as fusionspace.co says it

def build_naming_option():
    """Full project kits for the site's tools, each under its own name: designation FS · SW · TOOL 00n."""
    import project
    for n, (name, desc) in enumerate(SITE_TOOLS, 1):
        p = project.Project(name, code="FS", tag="SW", kind="Tool", number=f"{n:03d}", desc=desc)
        d = f"{KIT}/projects/{p.slug}"
        project.make(p, out(d))
        note(f"{d}/", "Per-project", f"{name}: project kit (social preview, README banners, OG, YouTube thumbnail, title slides, report covers, starter README); {p.designation}",
             "", "the tool's repo, its page on fusionspace.co, talks and reports")
    # The front page itself, under the designation in its title block.
    p = project.Project("fusionspace.co", code="FS", kind="Site", desc=SITE_DESC)
    d = f"{KIT}/projects/{p.slug}"
    project.make(p, out(d))
    note(f"{d}/", "Per-project", f"fusionspace.co: project kit (social preview, README banners, OG, YouTube thumbnail, title slides, report covers, starter README); {p.designation}",
         "", "the nrdptel/fusionspace-site repo")
