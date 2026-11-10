# Principles

Three levels and eight rules that decide everything else in `product/`. When a specific rule is missing or unclear, these
settle it.

FusionSpace makes engineering tools, mostly for high-power rocketry: calculators, simulators, flight reports, flight computers,
boards and rockets. The people using them are measuring, building and flying real hardware, often outdoors, sometimes next to
live energetics. The design follows from that: the products look like what they are, careful engineering documents, and they
behave like good instruments.

## Three levels

How much of the drawing a piece wears depends on what it is. A record is a drawing, so it carries the whole sheet. A tool
keeps what the drawing means and leaves off what it wears. A page that meets people first leads with the product's own
work and shows almost none of the drawing. IBM's Carbon system splits its type the same way, into a productive set for
tools and an expressive set for pages that introduce.

| | Front | Tool | Record |
|---|---|---|---|
| What it is | A landing page, the top of a README, a store listing | A calculator, an app screen, documentation | A flight report, an export, a printed card, a board, a CAD drawing |
| Leads with | The product's own output: a flight it flew, a check it passed | The inputs and the result | The readouts and the data |
| Sections | Each shaped by what it holds | Parts under a 2 px rule, numbered only when they're steps | Numbered sheets with a rail |
| Designation and status | On the about page, if anywhere | In the about box | In the footer line |
| Ends with | One line: a sentence, links | One line: version, data date, units | One line: designation, revision, date, status |

Every level shares one frame and one type: the same header, intro, headings in Archivo's wide cut, sentence-case labels
in Archivo, numbers in Cascadia Mono, the same spacing and the same footer line. Pages made by one person should look it.
The levels differ only in the parts a page uses: a record numbers its sheets, in the drawing's lettering, and its footer
line carries its designation and status. No page wears its designation as a tag over its title. Every level also keeps the line types, the trust notes, the signal colors and their
words, units on screen, the field theme, and the two-step arming. Those carry meaning, not style. The platform pages ([`mobile.md`](mobile.md),
[`desktop.md`](desktop.md), [`watch.md`](watch.md)) describe tools, and are being moved to these levels. Where one still
differs, this page settles it.

**Shape each page from its content.** A sequence is drawn as a timeline, a program's output as a terminal, a check
against real flights as its chart. A page whose sections all look alike is a template, whatever it's dressed in. A front
page shows the product's real output, never made-up numbers, because its reader is deciding whether to trust it. Spend
the boldness in one place on a page, and keep the rest quiet.

**Test:** with the logo covered, does the page still show what the product does, with its own data?

## 1. Drawn, not decorated

The visual language comes from engineering drawings (ISO 128 lines, ISO 7200 title blocks, ISO 3098 lettering) because
that is the language of the work itself, not a style picked for effect. Every line, rule and mark has a job. A record is a
sheet from a drawing set; tools and front pages keep the drawing's meaning and leave off its frame (Three levels, above).

- Two line widths in a 1 : 2 ratio, and a line type for each kind of information: solid for measured, dashed for predicted,
  chain (long dash, dot) for references, dotted for events, 45° hatching for unavailable or uncertain areas. These hold at
  every level.
- On a record, sections are sheets: a 2 px rule along the top edge, a sheet number, a name.
- A drawing or a board ends in a title block, and an app's about box holds the same fields. A web page ends with its
  footer line at every level.
- Callouts are balloons and leaders, the way a drawing points at a feature.
- No ornament: no glows, blobs, glass, shadows, decorative gradients, stock 3D, sparkles.

**Test:** could this element be on a released drawing? If it has no job, remove it.

## 2. Show the working

A FusionSpace tool never hands over a number without the way to check it. The formula, the constants, the inputs as read, the
data source and its date are always one step away ("Show the math", a Source sheet, a `--explain` flag).

- Results sit next to the inputs that made them, not on a separate page.
- Every constant has a source. Every dataset has an "as of" time.
- Exports (CSV, JSON, the printed card) carry the same provenance as the screen.

**Test:** could someone check this result by hand from what's on screen?

## 3. Say how far to trust it

Every figure a tool produces is an estimate from a model, a measurement from a sensor, or a value copied from someone else. The
product says which, and how good it is. It never turns an estimate into a verdict.

- Predicted values are visibly different from measured ones: dashed lines, the Nebula color, a SIM or FORECAST tag, a spread
  (± or a band).
- Precision matches knowledge: 5,104 ft, not 5,103.87 ft, for a barometric apogee.
- A "How far to trust it" note sits on every result that someone might fly on: what it was checked against, and how well it
  matched.
- No go/no-go verdicts. The motor's printed data, the manufacturer's manual and the range safety officer (RSO) are authoritative. The tool informs them.

**Test:** would a careful flyer be misled about how certain this is?

## 4. Built for the field

The tools are used at the bench, but also on a dry lake bed in full sun, in the cold, with gloves, with one hand, and with no
signal. Design for the worst place it will be used.

- Offline once loaded. Nothing needed at the pad depends on a connection.
- A field theme: white canvas, darker text, stronger rules, for a screen in sunlight. Every page offers it, at every
  level: it's part of what FusionSpace is.
- Controls used at the pad are at least 96 pt (about 15 mm) on a touch screen, and the one critical control used
  with gloves 128 pt (about 20 mm); critical ones sit in the lower half of a phone screen.
- Everything that matters prints well in black on white: flight cards, checklists, charge logs.
- Units are always on screen, and ft AGL is the default altitude for US flyers, always labeled.

**Test:** can this be read in sunlight at arm's length, and used with a glove on?

## 5. Quiet until it matters

Color that means something is rare, so that when it appears it is noticed. The standards for cockpits and spacecraft agree on
this (14 CFR 25.1322, FAA AC 25-11B, NASA-STD-3001): red for warnings, amber for cautions, a small set of coded colors, and
never color alone.

- Four signal colors, reserved: Flare (danger), Sodium (caution), Aurora (normal), Nebula (predicted). Nothing else uses them.
- Normal is mostly neutral ink. Aurora confirms a positive state where confirmation matters (continuity, a charge that fired,
  a value back within limits). ARMED is Flare: live energetics are a danger state, however routine.
- An unused channel or an empty field is gray and says "Not used", never red. False alarms train people to ignore real ones.
- Every status has a word and a shape as well as a color. It reads in grayscale, on e-paper, and with any color vision.
- Only two flash rates exist, and only for "act now": 3 Hz for warnings, 0.8 Hz
  for low priority.

**Test:** with the color turned off, is every state still clear?

## 6. One sweep

The brand appears once per view, and gets out of the way. The Fusion gradient is identity, and in a product it has one place:
the thin strip along the top edge. The logo in a product's header is one color (Void on light, Paper on dark); the gradient
lockup is for splash screens, covers and anywhere the logo stands alone. The gradient is never a button, a status, a
series in a comparison, a text effect or a background.

- One gradient strip per view, along the top.
- A front page may draw its one figure of the product's own work in the gradient: the line, and a faded area under it.
  The flight HPR Sim flew is FusionSpace's signature as much as the logo is. Once per page, and never a series beside
  others, where the gradient would read as data.
- The logo follows the brand rules exactly (clear space, minimum sizes, one-color Void on light under 32 px tall).
- Interactive color is Ion (O blue on dark), one accent, used for links, selection and focus. The primary button is ink.

**Test:** is the gradient doing anything other than saying "FusionSpace made this"?

## 7. Numbered like parts

Everything FusionSpace makes has a designation and a revision, like a part on a drawing: `FS · SW · TOOL 002`, `FS-VEGA-001
rev B`, `FS-VEGA · ELEC · BOARD 004`. The designation is how a printout, a board, a screenshot and a bug report find each other.

- Software shows its designation and version in its footer line or about screen; hardware carries both on silkscreen or a
  label. No page wears it as a tag over its title.
- On a record, status uses drawing words: IN PREPARATION, RELEASED, WITHDRAWN. A front page says it in words ("out now",
  "planned for 0.2").
- Hardware revisions are letters (skip I, O, Q, S, X, Z); software uses semantic versions; both are shown together when they
  meet (firmware 1.4.0 on board rev B).

**Test:** if this were printed and found in a drawer a year from now, could you tell what it is and which version?

## 8. Native where it counts

A FusionSpace iPhone app behaves like an iPhone app; an Android app like an Android app; a Mac, Windows or Linux app like a
good app on that desktop; a CLI like a good Unix tool. The
platform owns behavior (navigation, gestures, controls, text scaling, back, accessibility). FusionSpace owns content: color
roles, data display, numbers and units, line types, icons for the domain, the voice.

- System bars and controls stay standard; the drawing language lives in the content.
- Text scales with the user's setting on every platform.
- The terminal's own 16 colors, not brand RGB, in command-line output.

**Test:** would someone who knows the platform find anything surprising about how it works?

## What FusionSpace doesn't look like

These are the marks of a template, and they say nothing about the work. Avoid them (the full list, with sources, is in
[`review.md`](review.md)):

- A centered hero with a gradient headline, a glow or a starfield behind it.
- Indigo or violet buttons; a gradient button.
- Rows of three rounded cards, each with an icon on top.
- Large corner radii and soft drop shadows; frosted glass.
- Colored left borders on boxes; dots and pills used as decoration.
- Emoji or sparkle icons; shimmering "thinking" text while something loads.
- Status shown by color alone.
- The same section repeated down a page: text on one side and a boxed figure on the other, five times over.
- A wall of identical cards, where a list or a table would do.
- A small capitals label over every heading, and numbers (01, 02, 03) on things that aren't steps.
- Monospace for small labels on a front page or a tool, and middle-dot strings (A · B · C) used as decoration.

The defense isn't a different trend. It's provenance: every choice here has a reason in rocketry, engineering drawing or
human-factors research, written down next to the rule.
