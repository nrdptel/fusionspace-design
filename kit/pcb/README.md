# FusionSpace logo for PCBs

- **KiCad**: add `FusionSpace.pretty` as a footprint library (Preferences → Manage Footprint Libraries → Add existing).
  Footprints: `FusionSpace_Mark_<size>mm_F` (front silkscreen), `_B` (back silkscreen, mirrored as KiCad expects), and `_FCu`
  (exposed copper with a matching F.Mask opening, so it comes out bare and takes the board finish: gold on ENIG, silver on HASL). Sizes: 4, 6, 8, 12, 20 mm tall.
- Feet are trimmed so every feature is at least 0.15 mm wide, the usual silkscreen minimum. Below 6 mm many fabs blur the
  tips; 8 mm and up is safest.
- **Other EDA tools** (EasyEDA, Altium, Fusion Electronics): import `svg/fusion-space-mark-<size>mm-silk.svg`, or use the
  1200 dpi 1-bit PNGs in `png/` (mark 10 mm, horizontal lockup 6 mm, stacked 14 mm tall) with KiCad's Image Converter.
- The wordmark has thin strokes: keep the cap height at least 1 mm (horizontal lockup at least 1.7 mm tall).
