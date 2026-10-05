# Board title block

`FusionSpace.pretty` holds a 34 × 11 mm title block for the board silkscreen: a 0.3 mm frame with the brand's
45° corner, the mark (7 mm), and two lines of 1.2 mm text with a 0.15 mm stroke. Put
`FusionSpace_TitleBlock_B` on the back of every board (`_F` if the back is full).

The text reads the board's title-block fields, so the silkscreen always matches the drawing: set them in KiCad under
File → Board Setup → Title Block (or Page Settings):

| Field | Example | Shows |
|---|---|---|
| Title | `FS-VEGA · ELEC · 004` | the board's designation |
| Revision | `B` | `REV B` |
| Issue date | `2026-10` | the date beside the revision |

If your KiCad version doesn't resolve these variables inside a footprint, place two text items on the board with the same
text (`${TITLE}`, `REV ${REVISION}  ${ISSUE_DATE}`) over the empty frame. The footprints were written to KiCad 8's format
and haven't been opened in KiCad yet; check the first board in the 3D viewer before ordering.

Rules for the rest of the board: `product/hardware.md`.
