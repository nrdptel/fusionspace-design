# Review

Checklists for before something ships, and the test for whether it looks like FusionSpace or like a template.

## The FusionSpace test

Ask these of any screen, page, board or printout. Each "no" is a fix.

1. **Drawn?** Does every line, rule, color and mark have a job? Does it wear as much of the drawing as its level calls for
   (front, tool or record), and no more? Does it share the frame and type every other page has?
2. **Working shown?** Can the result be checked from what's on screen: inputs, formula, constants, sources, dates?
3. **Trust stated?** Is every figure marked as measured, predicted, forecast or copied, with its spread? Is there no verdict?
4. **Field-ready?** Readable in sun at arm's length, usable with a glove, working offline, printable in black?
5. **Quiet?** With color turned off, is every state still clear? Is red used only for danger, and nothing unused shown red?
6. **One sweep?** Does the gradient appear once, as identity, and nowhere else?
7. **Numbered?** Is the designation, revision or version on it, where its level puts it?
8. **Native?** Would someone who knows the platform find anything odd about how it behaves?

## Template smells

What critics and designers have cataloged, in 2024 to 2026, as the marks of a default template or generated UI. Adrian
Krebs's 2026 check of 1,590 Show HN landing pages found heavy matches on 22% of them and mild ones on another 32%. None of
these are FusionSpace:

| Smell | Instead |
|---|---|
| Indigo or violet primary buttons (Tailwind's `indigo-500`, which its author has since apologized for) | Ink buttons; Ion only for links and focus |
| A centered hero with a gradient headline and a glow, blob or starfield behind it | The product's own output, with a left-aligned headline, one or two sentences and two buttons |
| A badge or pill above the headline ("New", "Now in beta") | Nothing above the headline; status said in words where it matters |
| Rows of three cards with an icon on top of each | A table, a register, a timeline or prose: the form the content has |
| The same section repeated down a page, text on one side and a boxed figure on the other | Each section shaped by what it holds |
| A small capitals label over every heading; 01, 02, 03 on things that aren't steps | The heading alone; numbers only on steps |
| Monospace for small labels and captions | Monospace for code and readouts, and a record's sheet numbers |
| Large radii (`rounded-2xl`) and soft drop shadows | Square corners, 1 px rules, no shadows |
| Frosted glass and blur | Solid surfaces, separated by rules |
| Colored left borders on boxes | A note panel with its signal word |
| Status dots and pills as decoration ("Live" on everything) | Status only where it changes something, with a word |
| Emoji navigation, sparkle icons ✨, shimmering "thinking" text | The icon set; plain progress |
| Inter or Geist everywhere; the default `font-sans` | Archivo, set wide for headings, and Cascadia Mono for data |
| Cream backgrounds with orange accents and a serif, as a "warm" alternative | Paper or Void, ink, one accent |
| Stock 3D renders and abstract illustrations | Real photos and drawings of the hardware, plots of real data |
| Gradient text, gradient buttons, gradient borders | The gradient once, as the strip or the logo |

Note the overlaps, and why FusionSpace's versions are different: the gradient passes through a lavender near the
"template purple", but it comes from star colors and is used only as identity; capitals and monospace appear on the lists, but
here they are confined to a record's own parts, where a drawing uses them (sheet numbers, a drawing's title block),
and to state words.
The same goes for the gradient on a front page's figure: it draws the product's own output, once.

## Before release

### Every product

- [ ] Passes the FusionSpace test above.
- [ ] Colors from tokens only; contrast as in [`foundations.md`](foundations.md#contrast).
- [ ] Every value has a unit; every prediction is labeled and dashed; every dataset has an "as of".
- [ ] A "How far to trust it" note on every result someone might fly on.
- [ ] Status by word + shape + color; unused is gray; red only for danger.
- [ ] Footer line (or about screen, or a drawing's title block) with designation, version, date, units, data sources, status.
- [ ] Copy edited to [`writing.md`](writing.md): no hype, no em dashes, signal words exact.
- [ ] Logo per the brand rules (clear space, minimum size, one-color on light under 32 px).

### Web and PWA

- [ ] WCAG 2.2 AA: contrast, 24 px targets, visible focus, 320 px reflow, reduced motion, forced colors.
- [ ] Light, dark and field themes checked; prints legibly on one page per sheet.
- [ ] Works offline after the first visit; update toast instead of a forced reload; data exportable.
- [ ] LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 on a mid-range phone.
- [ ] No default palette, radius or shadow left from a framework.

### Command line

- [ ] Results on stdout, everything else on stderr; `--json` with a published schema.
- [ ] `NO_COLOR`, `--color`, non-terminal output all respected; no color, banner or progress in piped output.
- [ ] Errors say what, where and what to do; exit codes documented.

### iOS and Android

- [ ] The checklist in [`mobile.md`](mobile.md#checklist).
- [ ] Apple's accessibility audit (`performAccessibilityAudit` in a UI test) passes on every screen; on Android, the
      Accessibility Scanner or Compose's accessibility checks.
- [ ] Every screen looked at, on the smallest supported device, at the default text size, the largest non-accessibility
      size and the largest accessibility size (Android: font scale 2.0): nothing cut, truncated ("…"), split mid-word, or
      separated from its unit; at the largest sizes it scrolls instead.

### Apple Watch and Wear OS

- [ ] The checklist in [`watch.md`](watch.md#checklist).
- [ ] The accessibility audit on the watch app, on the smallest watch (SE 40 mm, Wear OS small round).

### macOS, Windows and Linux

- [ ] The checklist in [`desktop.md`](desktop.md#checklist).

### Devices and boards

- [ ] Physical arming; app arming is a second, two-action step; SAFE right of or below ARM; commanded vs confirmed shown.
- [ ] Energetics behavior as in [`embedded.md`](embedded.md#energetics-behavior): outputs off at power-up and reset,
  continuity current far under no-fire, lockouts, ground-test mode, backup, UNFIRED reported first after landing.
- [ ] Channel states on screen, LEDs and beeps as in the table; a fault never looks like ARMED; zero is a long tone; 95 dB at
  10 cm and heard at 10 m; the beep card printed.
- [ ] Two flash rates only; no blue or white status LEDs; every LED labeled.
- [ ] Silkscreen at least 1.2 mm; pyro terminals boxed and named; board title block on the back.
- [ ] Connectors that could be swapped dangerously are keyed differently.

### Rockets

- [ ] Hi-vis nose and fin can, hi-vis recovery; roll pattern; designation band.
- [ ] CG and CP marked; contact label inside and out; Remove Before Flight streamers on every pin.
- [ ] Flight card printed and filled in.

## Sources

The rules cite these; the research notes behind them are kept with the project's records.

- Human factors and displays: 14 CFR §25.1322; FAA AC 25-11B; NASA-STD-3001 Vol 2 Rev F, appendix F; NASA Human Integration
  Design Handbook; MIL-STD-1472H; FAA Human Factors Design Standard; ISA-101 (process HMIs).
- Drawings and signs: ISO 128, ISO 3098, ISO 7200, ASME Y14.5, ISO 2768, ANSI Z535, ISO 3864, the SI Brochure (9th edition).
- Rocketry: NAR High Power Rocketry Safety Code; Tripoli Unified Safety Code; NFPA 1127; manuals for the Featherweight Raven and
  Blue Raven, Altus Metrum, Eggtimer, PerfectFlite StratoLogger, Missile Works RRC3, Entacore AIM; ThrustCurve.org.
- Web and CLI: WCAG 2.2; web.dev (Core Web Vitals, install criteria, offline cookbook); MDN; GOV.UK Design System; WebKit
  blog; clig.dev; no-color.org; force-color.org; GitHub CLI accessibility; clap and anstream documentation.
- Desktop: Apple HIG for macOS (menu bar, toolbars, settings, app icons); Microsoft's Windows app design guidance (Mica,
  title bar, typography, text scaling, contrast themes, access keys, app icons, code signing); GNOME HIG and libadwaita; KDE
  HIG; freedesktop icon theme, desktop entry and base directory specifications; Flathub requirements; Tauri 2 documentation.
- Mobile: Apple Human Interface Guidelines (branding, color, typography, accessibility, Live Activities, widgets, app icons);
  Material 3 (color, motion, type scale); Android developer guides (edge-to-edge, adaptive icons, companion devices).
- Data: W. S. Cleveland, banking to 45°; Padilla, Kay and Hullman on uncertainty visualization; Chartability; Paul Tol's
  color schemes; Machado, Oliveira and Fernandes (2009) color-vision simulation; RocketPy's Monte Carlo analysis.
- Design: Adrian Krebs, "Design slop" (2026); IBM Carbon's productive and expressive type sets; Adam Wathan on `indigo-500`;
  Pentagram's Oxide identity; Linear's 2024 redesign; the NASA Graphics Standards Manual (1975); Dieter Rams's principles;
  Teenage Engineering's OP-1.
- Tokens: Design Tokens Community Group format 2025.10; Style Dictionary.
