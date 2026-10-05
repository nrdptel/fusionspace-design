# Writing

How FusionSpace products talk: on screens, in errors, in READMEs and docs, on labels and in commit messages. The voice is an
engineer explaining their own work to another engineer: plain, specific, honest about limits, and never selling.

## Voice

- **Plain.** Short sentences, common words, active voice. "The charge fired at 18.0 s", not "Successful deployment was
  achieved".
- **Specific.** Numbers with units, names of things, sources. "Within 0.02 % of OpenRocket's landing speed on 33 of 37
  flights", not "highly accurate".
- **Honest about limits.** Say what isn't done, isn't checked, or isn't known, in the same tone as what is. "Its online fetch
  is not tested automatically."
- **Calm.** No exclamation marks, no hype words (powerful, seamless, revolutionary, effortless, magic), no jokes in errors or
  warnings, no emoji.
- **Respectful.** The reader is a capable flyer. Explain, don't scold. Safety notes give the reason: "Ground-test before
  flight: real bays leak, and powder varies."

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
  the Sodium panel (two alert colours, as on a flight deck); on physical labels follow Z535's own colours (DANGER red,
  WARNING orange, CAUTION yellow, NOTICE blue).
- **Dates:** `4 October 2026` in prose; `2026-10-04` in tables, file names, title blocks and data. Times in 24-hour with the
  zone.

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

- **FusionSpace**, one word, always. Products keep their short names (Charge, Window, Muster) and their
  designations (`FS · SW · TOOL 002`).
- Projects are named after IAU-approved stars and take the star's code: `FS-VEGA`.
- **Designations** follow one grammar: `<code> · [<tag> ·] <kind> <number>`. The code is `FS` for things that belong to
  FusionSpace as a whole and `FS-<STAR>` for a project's; the optional tag is a discipline (SW, EMB, ELEC, MECH, MFG, AERO,
  GAME); the kind is a plain noun (TOOL, BOARD, FLIGHT, REPORT, SPEC, SITE); numbers are three digits. Examples:
  `FS · SW · TOOL 002`, `FS-VEGA · ELEC · BOARD 004`, `FS · SPEC 001`. Drawing and part numbers are shorter:
  `FS-VEGA-001`, with the revision after it (`rev B`).
- Rocketry terms as the community uses them: e-match, ejection charge, shear pins, drogue, main, av-bay, motor (not engine),
  waiver, AGL. Spell out the role names once per page: range safety officer (RSO), launch control officer (LCO).

## Mechanics

- **Spelling:** British in prose (colour, centre, metre, licence, analyse), as in the brand and hpr-sim documents. Code
  identifiers, file formats and platform APIs keep their own spelling (`color`, `center`). A product or command name keeps the
  spelling it shipped with.
- **Punctuation:** commas, colons and full stops; no em dashes. An en dash only in ranges (`5 100–5 500 ft`). A middle dot with
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
5. Licence, and the designation and version.

hpr-sim's README and its "Start here" page are the model: the status is at the top, the limits are stated, and every claim
links to its evidence.

## Commit messages

One line saying what changed and why, in the present tense ("Add the ground-test log export"), then detail if it helps. The
designation or component first when it isn't obvious: `Charge: round the backup charge up to 0.05 g`.
