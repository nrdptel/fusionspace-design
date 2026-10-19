# Writing

How FusionSpace products talk: on screens, in errors, in READMEs and docs, on labels and in commit messages. The voice is an
engineer explaining their own work to another engineer: plain, specific, honest about limits, and never selling.

## Voice

Write as one person explaining their own work to another flyer: plain, specific, honest about limits, calm, and
respectful of a capable reader. FusionSpace's tools are one maintainer's work, and their pages should read that way.

- Keep it plain: short sentences, common words, active voice, and contractions where you'd say them. "The charge fired
  at 18.0 s", not "Successful deployment was achieved".
- Be specific: numbers with units, names of things, sources. "Within 0.02% of OpenRocket's landing speed on 33 of 37
  flights", not "highly accurate".
- Be honest about limits: say what isn't done, isn't checked, or isn't known, once, in the same tone as what is. "Its
  online fetch is not tested automatically."
- Stay calm: no exclamation marks, no hype words (`powerful` as praise, `seamless`, `revolutionary`, `effortless`,
  `magic`), no jokes in errors or warnings, no emoji.
- Respect the reader, a capable flyer. Explain, don't scold. Safety notes give the reason: "Ground-test before flight:
  real bays leak, and powder varies."

The rules below come from a read-through of hpr-sim's pages on October 18, 2026, which found them correct but generic,
and from [a survey of plain technical writing](https://github.com/nrdptel/fusionspace-eridanus/blob/main/docs/research/plain-voice-docs.md).
Each shows a passage from hpr-sim's pages as it stood on October 19, 2026, then the same passage in this voice. hpr-sim's
[writing guide](https://hpr.fusionspace.co/writing.html#voice) holds the same section.

### Where "I" goes

Use "I" where a person is talking: a README, a landing page, a page that says why something exists, a guide, release
notes. It's one person's work, so there's no company "we". The bottom line still comes first, and the why follows it, in
the maintainer's words. Reference pages stay impersonal: a model's equations, a file format, a command's options, a
glossary. There the program is the subject, and "you" gives the steps, as it does in a tutorial or a how-to.

*Before*, in hpr-sim's contributing guide: "Publishing packages, creating releases and tags, and changing repository
settings are the maintainer's to do."

*After*: "Only I publish packages, create releases and tags, or change the repository's settings."

### Plain words

Use the plain word. Leave out the words that tell a reader something is "easy" or "quick": what's "quick" for you may
not be for them. Never use a stock phrase; hpr-sim's check holds a list of them and fails its build on one (The check,
below).

*Before*, in hpr-sim's *Pick a motor*: "Flying a few more motors is quick: change `--motor` and `--delay` and run
again."

*After*: "To fly a few more motors, change `--motor` and `--delay` and run it again."

### Short sentences

Aim for about 20 words a sentence, and use contractions where you'd say them: "isn't", "doesn't", "it's". A sentence
that carries five things is better as a few sentences, or as a list.

*Before*, in hpr-sim's README: "Flight in six degrees of freedom (6-DOF: three of position, three of rotation), with
variable mass: aerodynamics from subsonic to supersonic, the standard atmosphere or a measured one, winds that change
with height, staging, clusters and air starts, and recovery with drift."

*After*: "It flies a rocket in six degrees of freedom (6-DOF), three of position and three of rotation, with its mass
changing in flight. The aerodynamics run from subsonic to supersonic. The air is the standard atmosphere or a measured one, with
winds that change with height. It covers staging, clusters and air starts, and recovery with drift."

### Say it once

Say a thing once, where it belongs. Don't announce what a section covers, point back to what was said ("as
mentioned"), or recap it at the end (`In summary`). The heading and the first sentence already say what a section is
about.

*Before*, in hpr-sim's OpenRocket format page: "This section compares HPR Sim's whole flights with OpenRocket 24.12's on
the 54 configurations of OpenRocket's example designs that HPR Sim can fly, in 15 of the examples."

*After*: "HPR Sim's whole flights are compared with OpenRocket 24.12's on 54 configurations. They're the configurations
of OpenRocket's example designs that HPR Sim can fly, in 15 of the examples."

### Paragraphs and lists

Write a thought as a paragraph. Use a list for what really is a list: steps, options, parts. Give a list as many items
as there are, not three of the same shape because three sounds finished. A bold label opens an item only where a reader
scans for it, as in a list of options or a model page's *In short* box, whose items still count toward the limit. A line
that opens with a bold label reads like a form.

*Before*, in hpr-sim's README: "**Status: RELEASED.** Version 0.1.0, released October 8, 2026; work toward 0.2 goes on
here."

*After*: "Version 0.1.0 came out on October 8, 2026, and work toward 0.2 goes on here."

### Labels

Say what a thing is before its label, and use a label (a milestone or a decision number) only where the reader needs to
follow it. A sentence that opens with one sends the reader to look it up before they know why.

*Before*, in hpr-sim's *Accuracy*: "Neither set is held out: both were seen during development, so neither is a blind
test until M2.7 holds flights out, predicted before their logs are read."

*After*: "Neither set is held out. Both were seen during development, so neither is a blind test. That waits for flights
predicted before their logs are read, which is planned work (held-out flights)."

### Honest, once

Honesty stays exactly as strict (How far to trust it, below): what was checked, against what, and where it stops. Say it
once and plainly, like someone who checked. Put a hedge on the claim it qualifies, not on every clause around it.

*Before*, in hpr-sim's simulator tour: "Here the drag may read high, so the apogee may read low: for a field's ceiling,
the side that flatters (Trusting a simulation)."

*After*: "Here the drag may read high. If it does, the apogee reads low, the side that flatters a field's ceiling
(Trusting a simulation)."

### The limits

hpr-sim's `cargo xtask voice` counts these on each page, per 100 words, and its report marks a page over a limit. A page
over one is where to look first; it doesn't fail the build.

| Counted | What it counts | Limit per 100 words |
|---|---|---:|
| Bold-label items | a list item that opens with bold text | 0.5 |
| Labels | a milestone, decision or lesson number, linked or not | 0.5 |
| Sentences over 25 words | in paragraphs and list items | 0.5 |
| Hedges | may, might, could, possibly, perhaps, probably, likely, seems, appears and the like | 1.0 |
| Stacked hedges | a sentence holding two or more hedges | 0.1 |
| Minimizers | simply, just, easy, easily, quick, quickly | 0.1 |
| Signposts | "in this section", "as mentioned", "let's", "in short," and the like | 0.1 |
| First person on a reference page | "I", "me", "my" and their forms (I'm, mine, myself) on a model, format, command or glossary page | 0 |

Hedges leave out a capital "May" and "could not". Minimizers leave out "just" before a word of place or time ("just
below") and "how quick" or "how quickly", which measure something there. Quoted words aren't read for hedges,
minimizers, signposts or first person, though the stock list reads them.

The sentence limit comes from hpr-sim's target: fewer than 10% of sentences over 25 words, at about 20 words a sentence.
That's 0.5 per 100 words. On a page of shorter sentences the limit is stricter than 10%, so the report prints each page's
share too. A bold-label limit of 0.5 still allows a list of ten options on a 2,000-word page, but not a bold label on
every item of every list. Labels get one every 200 words, because each one sends the reader off to look it up.

Hedges get 1.0, because a single hedge is often the honest word. That's about the top of the range the survey measured
on one engineer's blog: 2.2 to 11.9 per 1,000 words, on a mostly different list of hedges. Stacked hedges, minimizers and
signposts get one every 1,000 words. Each adds little: a second hedge, a word that calls a step easy, a sentence that
points back at the page. Use one only on purpose.

First person on a reference page gets 0, because the program is the subject there. The limits were set against hpr-sim's
pages as they stood on October 19, 2026, when most of them were over the sentence and bold-label limits.

Who's talking has no limit: "I", "we", "you" and contractions per 100 words. For scale, the survey found 1.0 to 3.5
contractions per 100 words on most personal pages and 0 to 0.25 on reference pages. One author wrote about 3 "I" per
100 words on a blog and none on the project's reference pages.

### The check

`cargo xtask voice` in hpr-sim reads any path it's given (Markdown, HTML or text) and prints, per page, each count above
against its limit. Of what it counts, it fails only on its stock-phrase list: 41 entries in 9 groups, each named by a
published list (a style guide, a study, or Wikipedia's pages on word choice and on signs of generated writing) or by these
writing rules:

- puffery: `seamless`, `cutting-edge`
- inflated words: `pivotal`, `testament`
- words that spread with generated text: `delve`, `showcase`
- buzz verbs: `leverages`, `utilize`
- note-that phrases: `please note`
- vague sources: `research has shown`
- wordy phrases: `in order to`, `a number of`
- recaps: `in conclusion`
- chat residue: `I hope this helps`

The list leaves out words that have a technical sense in hpr-sim: robust, deploy, streamline (a streamlined body), boost and powerful (a more powerful motor).
Terms such as `magic bytes` and `seamless tube` pass. The list is in
[hpr-sim's `xtask/src/voice.rs`](https://github.com/nrdptel/fusionspace-eridanus/blob/main/xtask/src/voice.rs), each
entry with its sources and a test that fails without it. Voice is partly taste, so a cold reader checks each rewritten
page against these rules too.

## How far to trust it

Every result someone might fly on carries a short note in a fixed shape. It's the most FusionSpace thing a screen can say.

> **How far to trust it.** An estimate from an ideal-gas model, not a measurement. Checked against 23 ground tests logged in
> this tool: they needed 0.9 to 1.3 times the estimate. The charge that separates on the ground is the one to fly.

1. What kind of figure it is (estimate, measurement, copied value).
2. What it was checked against, with numbers.
3. What to rely on instead, when it matters.

Never a go/no-go verdict. The motor's printed data, the manufacturer's manual and the RSO are authoritative.

## On screens

- **Titles say what the screen is for**, in sentence case: "Size a charge", "Flight 03 · J350W-L".
- **Labels are nouns, controls are verbs.** `INNER DIAMETER` (a field), "Run simulation" (a button). A button says what will
  happen, never "OK", "Submit" or "Click here". Confirmation buttons repeat the action: "Arm channel 2", "Delete log".
- **Help text is one sentence** under the field, about the thing people get wrong: "Inside the tube, not the outside."
- **Empty states** say what goes here and how to get it: "No flight loaded. Drop a log file here, or pick one."
- **Status words** are short and fixed. Use exactly these, in capitals on chips and devices:
  - Devices and channels: `ARMED`, `SAFE`, `CONT`, `NO CONT`, `FIRED`, `UNFIRED`, `NOT USED`.
  - Data: `MEASURED`, `SIMULATED`, `FORECAST`, `STALE`, `NEAR LIMIT`, `OVER LIMIT`, `ADVISORY`, `NO FIX`, `GPS LOCKED`.
  - Ground tests: `SEPARATED`, `PARTIAL`, `NO SEPARATION`.
  - Document status: `IN PREPARATION`, `RELEASED`, `WITHDRAWN`.
- **Signal words** on notes, labels and in manuals are ANSI Z535's, with its meanings, and no others ("Heads up" and
  "Important" are not signal words):
  - `DANGER`: a hazard that **will** cause death or serious injury if not avoided.
  - `WARNING`: a hazard that **could** cause death or serious injury. Live ejection charges and armed electronics are WARNING.
  - `CAUTION`: a hazard that could cause minor or moderate injury.
  - `NOTICE`: no injury, but damage or loss: a lost rocket, an overwritten log, a cooked battery. No safety-alert symbol.
  - `NOTE`: information, no hazard.

  DANGER, WARNING and CAUTION carry the safety-alert triangle. On screens, DANGER and WARNING use the Flare panel and CAUTION
  the Sodium panel (two alert colors, as on a flight deck); on physical labels follow Z535's own colors (DANGER red,
  WARNING orange, CAUTION yellow, NOTICE blue).
- **Dates and times:** `October 4, 2026` in prose; `2026-10-04` in tables, file names, title blocks and data. Clock times on
  screen follow the device's 12- or 24-hour setting (12-hour, `2:10 PM MDT`, is the US default) and always carry the zone;
  logs and exports use ISO 8601.

## Errors

An error says what happened, why if known, and what to do next, in that order. It names the thing by the name the user gave it.

```
Can't read vega-flight-03.csv: line 1 has no time column.
The log reader looks for a column named time, t or Time (s). Rename the column, or pick it under Columns.
```

- No blame ("You entered an invalid value"), no long apologies, no codes without words.
- In a form, the error goes under the field it's about, in danger ink with the danger icon, and the field gets a 2 px danger
  border. Check on leaving the field, not on every keystroke.
- In a CLI, follow [`cli.md`](cli.md#errors).

## Notes and warnings in documents

Manuals, READMEs and assembly guides use the same signal words as the screens, as a panel above the text (the safety-label
layout), with the hazard, the consequence and the avoidance:

> **WARNING** · Pyro outputs are live when the switch is on. Connecting an e-match with the switch on can fire it. Turn the
> switch off and short the terminals before you connect anything.

## Names

- **FusionSpace**, one word, always.
- **A project takes a constellation; its products take its stars.** A project is one of the IAU's 88 constellations, and
  its code is the IAU abbreviation in capitals: Lyra is `FS-LYR`. A constellation has one project. Each product in the
  project takes one of that constellation's IAU-approved star names as its **internal name**, with the star's code: Vega
  is `FS-VEGA`. Choose a constellation with named stars to spare for the products to come; Callsign
  (`tools/callsign`) draws one, and draws the star for each new product.
- **The internal name never changes.** Repositories, folders, drawings, part numbers, boards, firmware, issue trackers and
  designations use it, so they still match after a rename.
- **The external name** is what customers read: the product's screens, its page, the store, the box. It is the star's
  name or a different one (`FS-VEGA` could ship as Vega, or as a name of its own). An external name is never another
  star's name. Where both appear (the about screen, a title block), the external name leads and the code follows:
  `Vega · FS-VEGA · EMB · FIRMWARE 002`.
- **Project Ara** (`FS-ARA`) is the brand repository: Callsign is `FS-CERVANTES · SW · TOOL 001` and the Mark Tuner is
  `FS-INQUILL · SW · TOOL 001`, with their names unchanged as external names.
- **Today's other tools** (HPR Motor Finder, Charge, Window, Muster) came before this rule. They keep their names, which
  become their external names, and their designations (`FS · SW · TOOL 002`) until each moves into a project with a star
  of its own.
- **Designations** follow one grammar: `<code> · [<tag> ·] <kind> <number>`. The code is `FS` for things that belong to
  FusionSpace as a whole, `FS-<CON>` for a project's and `FS-<STAR>` for a product's; the optional tag is a discipline (SW,
  EMB, ELEC, MECH, MFG, AERO, GAME); the kind is a plain noun (TOOL, BOARD, FLIGHT, REPORT, SPEC, SITE); numbers are three
  digits. Examples: `FS-VEGA · ELEC · BOARD 004`, `FS-LYR · SPEC 001`, `FS · SPEC 001`, `FS · SW · TOOL 002`. Drawing and
  part numbers are shorter: `FS-VEGA-001`, with the revision after it (`rev B`).
- Rocketry terms as the community uses them: e-match, ejection charge, shear pins, drogue, main, av-bay, motor (not engine),
  waiver, AGL. Spell out the role names once per page: range safety officer (RSO), launch control officer (LCO).

## Mechanics

- **Spelling:** US English everywhere: prose, screens, labels, manuals, code comments (color, center, meter, license,
  analyze, gray, catalog). FusionSpace is a US brand making tools for US flyers first. A product or command name keeps the
  spelling it shipped with.
- **Punctuation:** commas, colons and periods; no em dashes. An en dash only in ranges (`5,100–5,500 ft`). A middle dot with
  spaces (` · `) separates fields on one line: `FS · SW · TOOL 002`, `ALTITUDE · ft AGL`.
- **Numbers and units** as in [`data.md`](data.md#numbers).
- **Lists:** a list when there are three or more parallel items; otherwise a sentence.
- **Links** say where they go: "the Accuracy page", not "here".

## READMEs and docs

A project README opens with the banner from `kit/projects/<name>/README-starter.md`, then answers, in order:

1. What it is, in one sentence.
2. What works today and what doesn't (and how far to trust what does).
3. How to install it and get a first result.
4. Where the details are.
5. License, and the designation and version.

hpr-sim's README and its "Start here" page are the model: the status is at the top, the limits are stated, and every claim
links to its evidence.

## Commit messages

One line saying what changed and why, in the present tense ("Add the ground-test log export"), then detail if it helps. The
designation or component first when it isn't obvious: `Charge: round the backup charge up to 0.05 g`.
