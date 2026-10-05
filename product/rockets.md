# Rockets

Airframes, livery, markings, recovery gear and flight cards. On a rocket, **visibility comes first and the brand second**: a
rocket you can't see in the sky or find in the brush isn't a FusionSpace rocket for long.

Livery sheets: [`rockets/`](rockets/) has an unrolled wrap, drawn 1:1, for common airframe outside diameters
(1.64, 2.26, 3.1, 4, 6.17 in), with the roll pattern, designation band, the mark, an overlap strip, and
CG, CP, contact and pyro-warning decals laid out to the tube's circumference. Decals:
`kit/production/rocket-decals/`. Remove Before Flight tags: `kit/production/remove-before-flight/`.

![Livery sheet for a 54 mm airframe](rockets/preview.png)

## Color

- **Hi-vis plus black.** Fluorescent orange or fluorescent pink with black is what flyers find easiest to track and recover; a
  solid color against sky (blue or overcast gray) and ground (brown, green, white lake bed) both. Chrome flashes when it
  catches the sun but otherwise takes on the colors around it; use it only as a small accent.
- **The FusionSpace scheme:** a black (Void) airframe with a fluorescent orange nose cone and fin can, white markings, and the
  roll pattern on the fins or the body above them. The brand shows in the two-tone mark (M orange and O blue cones) and the
  designation band, not in the body color. Where a fluorescent finish isn't possible, M orange `#DA7C30` is the
  nearest brand color.
- **Heat.** Black absorbs sun: on a desert field a black airframe and av-bay get hot enough to stress batteries and motors.
  Keep the rocket shaded until it goes to the pad. For summer flights at hot sites, fly the alternative scheme: a
  fluorescent orange (or white) airframe with black accents and the same markings.
- **Parachutes and streamers:** fluorescent orange or pink, never sky blue, white or camouflage colors.

## Roll pattern

Quadrants of black and white (or black and fluorescent orange) on the body tube, alternating around the circumference, so
on-board and ground video can measure roll, as the V-2 and Saturn V did. The wrap sheets lay out four quadrants per
circumference.

## Markings

| Marking | Where | Why |
|---|---|---|
| **Designation band** `FS-VEGA-001 rev B` | Around the body below the nose, Cascadia Mono capitals, white on black | Identifies the rocket on video, on the pad, and against its drawing |
| **The mark** (two-tone, `kit/production/rocket-decals/`) | Once, on the body or a fin, at least 25 mm tall | The brand, once |
| **CG and CP marks** | At their measured and computed stations, on the body tube | Tripoli requires the flyer to document the CP and show the CG at inspection; marked, the RSO sees them at a glance |
| **Contact label** | Inside the airframe and on the av-bay, and outside near the fins | A recovered rocket finds its owner. Not required by the NAR or Tripoli codes, but common practice |
| **Remove Before Flight** streamers | On every pin, shunt and cover that must be removed or switched at the pad | The aerospace convention: white capitals on red |
| **Pyro warning** | On the av-bay, next to the switch | `WARNING · LIVE PYRO WHEN ARMED` with the hazard border |

- **CG** uses the standard symbol, a circle with alternate quadrants filled; **CP** a circle with a dot. Draw them in black or
  white for contrast with the body. (OpenRocket colors CG blue and CP red; FusionSpace keeps red for danger, so on screen CG
  and CP are told apart by their shape.)
- The contact label reads: `IF FOUND` · name · phone · email · `REWARD`, and the designation. Keep it on the wrap sheets'
  template so it's never forgotten.

## Flight card

Every flight has a card, printed from the tools that planned it (Charge, hpr-sim), A6 or half-letter, in the title-block layout:
designation and flight number, motor (`J350W-L`, with its delay set), mass, CG and CP stations and the stability margin in
calibers, charges in grams for each channel, altimeter settings, expected apogee with its spread, the waiver, the flyer's
name and certification level, and boxes to tick for the pad checklist. It is designed to be read and signed by the range safety officer (RSO).

## Pad checklist

Printed on the back of the flight card, in the order the safety codes and good practice put it:

1. The launch control officer (LCO) says the range is open for your pad; the launch system is safe and its key is out.
2. Rocket on the rail, rail buttons on the rail, blast deflector in place.
3. Remove Before Flight pins pulled and counted (with a pull-pin switch, this is what turns the electronics on).
4. Electronics on (switch or key), in the order the manual gives; listen for the channel report.
5. Continuity confirmed on every configured channel; unused channels report NOT USED.
6. Igniter installed last, after all flight electronics are on (Tripoli).
7. Clear the pad; tell the LCO the rocket is ready.

**After a misfire:** wait as the LCO directs, then disarm the flight electronics before touching the rocket, and only then
remove the igniter.

**At recovery:** if the device reports UNFIRED, or you can't tell, treat the rocket as live. Approach from the side, keep
clear of the airframe ends, and switch the electronics off before handling it.
