# Board title block

`FusionSpace.pretty` holds a 34 × 11 mm title block for the board silkscreen: a 0.3 mm frame with the brand's
45° corner, the mark (7 mm), and two lines of 1.2 mm text with a 0.15 mm stroke. Put
`FusionSpace_TitleBlock_B` on the back of every board (`_F` if the back is full).

The text reads the board's title-block fields, so the silkscreen always matches the drawing: set them in KiCad under
File → Board Setup → Title Block (or Page Settings):

| Field | Example | Shows |
|---|---|---|
| Title | `FS-VEGA-004` | the board's part number |
| Revision | `B` | `REV B` |
| Issue date | `2026-10` | the date beside the revision |

Checked with KiCad 10.0.6 (October 5, 2026): both footprints load, and on a test board with Title `FS-VEGA-004`, Revision `B` and
Issue date `2026-10` the plotted silkscreen reads `FS-VEGA-004` and `REV B  2026-10`. If an older KiCad leaves the variables
unresolved, place two text items with the same text over the empty frame.

Rules for the rest of the board: `product/hardware.md`.
