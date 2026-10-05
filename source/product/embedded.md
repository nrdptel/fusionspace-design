# Flight computers and devices

Screens, lights, beepers, switches and buttons on FusionSpace hardware: flight computers, trackers, ground stations, pad
boxes. These are the products where a misread can cost a rocket or hurt someone, so the rules lean hardest on the standards
(NASA-STD-3001, MIL-STD-1472H, the NAR and Tripoli safety codes) and on what flyers say goes wrong with today's altimeters.

Firmware colour constants: [`tokens/fusionspace_ui.h`](tokens/fusionspace_ui.h). Mock-ups: [`embedded/`](embedded/). Boot
logos for every common display: `kit/embedded/`.

![Device screen mock-ups: SAFE, ARMED, flight, after landing](embedded/preview.png)

## Arming and safety

- **Arm with a physical switch** in the airframe (a screw switch, a key, a magnetic switch with its ON end marked, or a
  pull-pin with a Remove Before Flight streamer from `kit/production/remove-before-flight/`). Not a slide or toggle on the
  outside, where it can be knocked (PerfectFlite's manual says the same). The NAR code requires firing circuits to stay
  inhibited until the rocket is on the pad.
- **Arming from an app** is a second, separate action on top of the physical switch, never instead of it: a hold-to-confirm
  with the device's designation on screen. Arming over Wi-Fi or Bluetooth from more than a few metres away isn't offered.
- **SAFE is right of or below ARM** wherever both appear (NASA-STD-3001), and is always one action.
- **Commanded and confirmed** states are shown separately. The device reports its real state; the app never assumes.
- **Energetics live = Flare, flashing fast.** A red LED flashing at 3 Hz, the inverted ARMED box on a screen, and the continuous
  continuity report are reserved for "pyro outputs can fire". Nothing else uses them.

## Channels: three states, not two

Every pyro or deployment channel is always in one of three states, and each looks and sounds different:

| State | Screen | LED | Beep |
|---|---|---|---|
| **GO**: configured, continuity good | `1 DROGUE  CONT` in Aurora | green, steady | one short high tone |
| **FAULT**: configured, no continuity | `2 MAIN  NO CONT` inverted, Flare | red, 3 Hz | three long low tones |
| **NOT USED**: not configured | `3 —  NOT USED` muted | off | one short low tone |

An unused channel is never red (one popular altimeter app shows unused channels in red, "but that's o.k."; that trains people
to ignore red). Channels are always reported in the same order, 1 to n, and named with words, not just numbers: DROGUE, MAIN,
APOGEE BACKUP, AIRSTART.

## Beeps

Every vendor's beep code is different (the digit zero alone is ten beeps on one, a long beep on another, a low beep on a
third). FusionSpace devices use one published language and print it on a card in the box and in the manual:

- **Tones:** short 100 ms, long 400 ms, high about 3 kHz, low about 1.5 kHz; 150 ms between tones in a group, 600 ms between
  groups, 2 s before a sequence repeats.
- **Power on:** one long high tone = self-test passed; three long low = fault (and the screen or LED says which).
- **Channel report** (while armed, repeating): each channel in order, as in the table above, then the pause.
- **Numbers** (altitude after landing, battery voltage on request): each digit as that many short high tones, **zero as one long
  tone**, 600 ms between digits, and a long low tone to end the number. Altitude is in feet AGL unless set to metres, and the
  manual says which.
- Loud enough to hear in wind at 10 m (a common complaint is beepers that can't be heard on a breezy field): a piezo of 85 dB
  or more at 10 cm, mounted to an opening.

## Lights

| Pattern | Means |
|---|---|
| Green, steady | Powered, nominal (dim: a green LED at full brightness dazzles at night) |
| Green, one blink every 2 s | Powered, idle, logging (saves power on the pad) |
| Amber, 0.8 Hz | Needs attention: low battery, no GPS fix, link lost |
| Red, 3 Hz | Energetics live or a fault on a configured channel |
| Off | Not used, or off |

- Two flash rates only, synchronised across all LEDs on the device. No blue or white status LEDs: they aren't signal colours.
- Every LED is labelled on the silkscreen with what it means (`PWR`, `GPS`, `CH1`, `CH2`), not just a reference designator.

## Screens

- **Dark roles on emissive screens** (OLED, TFT): light marks on Void read well in shade and at night, and Void pixels draw no
  power on an OLED. **E-paper and transflective LCDs** use the light roles, and are the right choice for anything read in
  full sun at the pad (OLEDs wash out in direct sun).
- **Layout on an 8 px grid.** Top row: state word, battery voltage as a number, GPS satellites, link age. Middle: the one
  readout the screen exists for, in a large numeral font. Bottom row: what the buttons do, and the screen's sheet number
  (`SHT 2/5`).
- **States are boxes:** SAFE in an outline box, ARMED in an inverted (filled) box, so the difference shows in one bit of colour
  and from across a table.
- **Fonts:** a bitmap font at 1× (never a scaled-up one): Spleen (BSD-2, built into u8g2) at 5 × 8 and 6 × 12 for text, 8 × 16
  for headings, and one large numeral face for the readout. On TFTs with anti-aliasing, Cascadia Mono rendered with LVGL's
  font converter at 12, 16 and 28 px.
- **Burn-in.** A pad wait can last hours. Draw 1 px outlines rather than large filled areas, shift the whole screen by a pixel
  every few minutes, and dim after 60 s without input (never while ARMED).
- **E-paper:** fixed zones for partial refresh, a full refresh every 5 to 10 partial ones, never cut power mid-refresh, and
  always show when the screen was last updated. Below about 0 °C it slows down; say so.
- **Boot screen:** the mark from `kit/embedded/` for under a second, then the device's designation, board revision and firmware
  version, then the state. Never a boot animation that delays SAFE/ARMED information.
- **LVGL:** one custom theme built on the simple theme, with the colours from `fusionspace_ui.h`, square corners (radius 0),
  1 px borders, no shadows, and state styles (pressed, checked, disabled) shared across widgets.

## Buttons and switches

- Few physical buttons, each with one job, labelled on the enclosure with the result (`MODE`, `BEEP ALT`), not a symbol only.
- Long-press (2 s) for anything that changes configuration; nothing a button does can arm or fire.
- Switches that arm are guarded or recessed. No safety wire as a guard (MIL-STD-1472H).

## Ground stations and pad boxes

- The screen follows [`data.md`](data.md#live-telemetry): update rates, stale data with its age, T−/T+ time, commanded vs
  confirmed.
- Launch controllers follow the NAR and Tripoli codes: a removable safety interlock (key) in series with a momentary,
  spring-return launch switch; continuity shown per pad before arming; the key labelled and on a lanyard with a streamer.
- Labels on the box: function words in capitals (`ARM`, `LAUNCH`, `CONT`), a hazard border around the launch control.

## Serial and USB output

Firmware that prints to a serial console follows [`cli.md`](cli.md): a first line with the designation, board revision and
firmware version; a label column with units; `ERROR:` and `WARNING:` words; no colour unless asked; and a machine-readable mode
(CSV or JSON lines) for logging.
