# Screen masks

The display outline of each simulator, taken from Xcode 27's screenshot mask (`simctl io screenshot --mask=alpha`) on
October 6, 2026: white inside the screen, black outside, at the device's pixel size. Apple's corners are continuous
curves, not circular arcs, so the build uses these instead of a radius: `tools/build/kit_clip.py` checks every drawn screen
against its mask, and the contact sheets cut each screen to it. Shape only; no device artwork.

| File | Device | Pixels | Scale |
|---|---|---|---|
| `iphone-17-pro.png` | iPhone 17 Pro (402 × 874 pt) | 1206 × 2622 | 3 |
| `apple-watch-ultra-49mm.png` | Apple Watch Ultra 4, 49 mm (211 × 257 pt) | 422 × 514 | 2 |
| `apple-watch-se-40mm.png` | Apple Watch SE 3, 40 mm (162 × 197 pt) | 324 × 394 | 2 |
