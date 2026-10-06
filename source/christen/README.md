# Christen

Name a FusionSpace project after an IAU-approved star. `FS · SW · TOOL 007`, version 1.0.0.

Every FusionSpace project takes the name of a star the International Astronomical Union has approved, and the star's code:
Vega becomes `FS-VEGA`. Christen draws one at random, or from a narrower list: one constellation, a range of brightness
(vmag), or names up to a number of letters. It skips names already in use.

## Use it

| Where | How |
|---|---|
| Any browser: macOS, Windows, Linux, iPhone, iPad, Android | Open `christen.html`. It is one file with everything inside, so it works from disk, offline, or sent to a phone. |
| Terminal: macOS, Linux | `python3 christen.py` |
| Terminal: Windows | `py christen.py` (Python from python.org or the Microsoft Store) |
| Phones, in a terminal | `python3 christen.py` in a-Shell (iOS) or Termux (Android) |

Both files work on their own and do the same things. `christen.py ui` opens `christen.html` when the two sit together, and
the page can download `christen.py`.

```
christen                                  draw a star
christen -n 5 -c Orion --vmag ..3         five stars in Orion, vmag 3 or brighter
christen --vmag 2..5 --max-letters 6      vmag 2 to 5, six letters or fewer
christen --skip Vega,Rigel                not these
christen list --sort vmag                 every star, brightest first (--csv, --json, --plain)
christen show Vega                        one star, by name or code
christen constellations                   the constellations with named stars
christen update                           read the IAU list now
```

`--json` prints one JSON document; `--plain` prints names only, for scripts. Colors follow the terminal's theme and turn off
with `NO_COLOR` or `--color never`. Exit codes: 0 done, 1 no match or no list, 2 a wrong command line.

## The star list

The names come from the IAU's own list: the [Current List of IAU Star Names](https://iauarchive.eso.org/public/themes/naming_stars/#n4)
on its Naming Stars page, with each star's designation, constellation, vmag, J2000 position and approval date.

- **Command line.** A copy is built in. `christen update` reads the list from the IAU again and keeps it in the user cache
  (`~/Library/Caches/christen` on macOS, `~/.cache/christen` on Linux, `%LOCALAPPDATA%\FusionSpace\christen` on Windows).
  When the copy is over 30 days old, the next run reads it again on its own; if the IAU can't be reached, it carries on
  with the copy it has. `--offline` (or `CHRISTEN_OFFLINE=1`) skips this.
- **Browser.** A copy is built in. Browsers can't read the IAU page directly (the IAU doesn't allow it), so the page checks
  `iau-star-names.json` in this folder on GitHub, and uses it when it is newer.
- **This repository.** `python3 source/christen/christen.py update --out source/christen/iau-star-names.json` reads the
  list, then a build puts it into every file here.

`iau-star-names.json` and `iau-star-names.csv` here are the list as built in.

## How far to trust it

The list is read from the IAU's page as published. The page heads its table "as of January 1st, 2021", and it includes
approvals up to April 2022, so newer names may be missing until the IAU updates it. The reader checks the table's columns
and its size, and keeps the last good copy if either looks wrong. The IAU names stars, not products: search a name before it
goes on a board, a box or a domain.

## Design and license

Follows the FusionSpace product system (`product/`): `web.md` for the page, `cli.md` for the command line.
The code is Apache-2.0 (`tools/LICENSE`); the FusionSpace name and logo are not covered by it (`TRADEMARKS.md`).
