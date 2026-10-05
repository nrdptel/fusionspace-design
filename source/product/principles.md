# Principles

Eight rules that decide everything else in `product/`. When a specific rule is missing or unclear, these settle it.

FusionSpace makes engineering tools, mostly for high-power rocketry: calculators, simulators, log analysers, flight computers,
boards and rockets. The people using them are measuring, building and flying real hardware, often outdoors, sometimes next to
live energetics. The design follows from that: the products look like what they are, careful engineering documents, and they
behave like good instruments.

## 1. Drawn, not decorated

Every FusionSpace screen, page and printout is a sheet from a drawing set. The visual language comes from engineering drawings
(ISO 128 lines, ISO 7200 title blocks, ISO 3098 lettering) because that is the language of the work itself, not a style picked
for effect. Every line, rule and mark has a job.

- Two line widths in a 1 : 2 ratio, and a line type for each kind of information: solid for measured, dashed for predicted,
  chain (long dash, dot) for references, dotted for events, 45° hatching for unavailable or uncertain areas.
- Sections are sheets: a 2 px rule along the top edge, a sheet number, a name.
- Every page, report and about screen ends in a title block.
- Callouts are balloons and leaders, the way a drawing points at a feature.
- No ornament: no glows, blobs, glass, shadows, decorative gradients, stock 3D, sparkles.

**Test:** could this element be on a released drawing? If it has no job, remove it.

## 2. Show the working

A FusionSpace tool never hands over a number without the way to check it. The formula, the constants, the inputs as read, the
data source and its date are always one step away ("Show the maths", a Source sheet, a `--explain` flag).

- Results sit next to the inputs that made them, not on a separate page.
- Every constant has a source. Every dataset has an "as of" time.
- Exports (CSV, JSON, the printed card) carry the same provenance as the screen.

**Test:** could someone check this result by hand from what's on screen?

## 3. Say how far to trust it

Every figure a tool produces is an estimate from a model, a measurement from a sensor, or a value copied from someone else. The
product says which, and how good it is. It never turns an estimate into a verdict.

- Predicted values are visibly different from measured ones: dashed lines, the Nebula colour, a SIM or FORECAST tag, a spread
  (± or a band).
- Precision matches knowledge: 5 104 ft, not 5 103.87 ft, for a barometric apogee.
- A "How far to trust it" note sits on every result that someone might fly on: what it was checked against, and how well it
  matched.
- No go/no-go verdicts. The motor's printed data, the manufacturer's manual and the range safety officer (RSO) are authoritative. The tool informs them.

**Test:** would a careful flyer be misled about how certain this is?

## 4. Built for the field

The tools are used at the bench, but also on a dry lake bed in full sun, in the cold, with gloves, with one hand, and with no
signal. Design for the worst place it will be used.

- Offline once loaded. Nothing needed at the pad depends on a connection.
- A field theme: white canvas, darker text, stronger rules, for a screen in sunlight.
- Controls used at the pad are at least {{TARGET['field']}} pt (about 15 mm) on a touch screen, and the one critical control used
  with gloves {{TARGET['glove']}} pt (about 20 mm); critical ones sit in the lower half of a phone screen.
- Everything that matters prints well in black on white: flight cards, checklists, charge logs.
- Units are always on screen, and ft AGL is the default altitude for US flyers, always labelled.

**Test:** can this be read in sunlight at arm's length, and used with a glove on?

## 5. Quiet until it matters

Colour that means something is rare, so that when it appears it is noticed. The standards for cockpits and spacecraft agree on
this (14 CFR 25.1322, FAA AC 25-11B, NASA-STD-3001): red for warnings, amber for cautions, a small set of coded colours, and
never colour alone.

- Four signal colours, reserved: Flare (danger), Sodium (caution), Aurora (normal), Nebula (predicted). Nothing else uses them.
- Normal is mostly neutral ink. Aurora confirms a positive state where confirmation matters (continuity, a charge that fired,
  a value back within limits). ARMED is Flare: live energetics are a danger state, however routine.
- An unused channel or an empty field is grey and says "Not used", never red. False alarms train people to ignore real ones.
- Every status has a word and a shape as well as a colour. It reads in greyscale, on e-paper, and with any colour vision.
- Only two flash rates exist, and only for "act now": {{FLASH['warning'][0]:g}} Hz for warnings, {{FLASH['advisory'][0]:g}} Hz
  for low priority.

**Test:** with the colour turned off, is every state still clear?

## 6. One sweep

The brand appears once per view, and gets out of the way. The Fusion gradient is identity, and in a product it has one place:
the thin strip along the top edge. The logo in a product's header is one colour (Void on light, Paper on dark); the gradient
lockup is for splash screens, covers and anywhere the logo stands alone. The gradient is never a button, a status, a chart
series, a text effect or a background.

- One gradient strip per view, along the top.
- The logo follows the brand rules exactly (clear space, minimum sizes, one-colour Void on light under 32 px tall).
- Interactive colour is Ion (O blue on dark), one accent, used for links, selection and focus. The primary button is ink.

**Test:** is the gradient doing anything other than saying "FusionSpace made this"?

## 7. Numbered like parts

Everything FusionSpace makes has a designation and a revision, like a part on a drawing: `FS · SW · TOOL 002`, `FS-VEGA-001
rev B`, `FS-VEGA · ELEC · BOARD 004`. The designation is how a printout, a board, a screenshot and a bug report find each other.

- Software shows its designation and version in its title block or about screen; hardware carries both on silkscreen or a
  label.
- Status uses drawing words: IN PREPARATION, RELEASED, WITHDRAWN.
- Hardware revisions are letters (skip I, O, Q, S, X, Z); software uses semantic versions; both are shown together when they
  meet (firmware 1.4.0 on board rev B).

**Test:** if this were printed and found in a drawer a year from now, could you tell what it is and which version?

## 8. Native where it counts

A FusionSpace iPhone app behaves like an iPhone app; an Android app like an Android app; a Mac, Windows or Linux app like a
good app on that desktop; a CLI like a good Unix tool. The
platform owns behaviour (navigation, gestures, controls, text scaling, back, accessibility). FusionSpace owns content: colour
roles, data display, numbers and units, line types, icons for the domain, the voice.

- System bars and controls stay standard; the drawing language lives in the content.
- Text scales with the user's setting on every platform.
- The terminal's own 16 colours, not brand RGB, in command-line output.

**Test:** would someone who knows the platform find anything surprising about how it works?

## What FusionSpace doesn't look like

These are the marks of a template, and they say nothing about the work. Avoid them (the full list, with sources, is in
[`review.md`](review.md)):

- A centred hero with a gradient headline, a glow or a starfield behind it.
- Indigo or violet buttons; a gradient button.
- Rows of three rounded cards, each with an icon on top.
- Large corner radii and soft drop shadows; frosted glass.
- Coloured left borders on boxes; dots and pills used as decoration.
- Emoji or sparkle icons; shimmering "thinking" text while something loads.
- Status shown by colour alone.

The defence isn't a different trend. It's provenance: every choice here has a reason in rocketry, engineering drawing or
human-factors research, written down next to the rule.
