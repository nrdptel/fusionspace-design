# FusionSpace for games

- `splash/`: studio splash screens (stacked lockup) at 1280×720, 1920×1080 and 3840×2160, dark and light. Show for 2–3 s at start-up,
  or use the animated version in `kit/video/`.
- `steam/`: templates at the current Steamworks sizes (checked October 2026: header 920×430, small 462×174, main 1232×706,
  vertical 748×896, optional page background 1438×810; library capsule 600×900, library header 920×430, library hero 3840×1240,
  transparent library logo 1280×720). Each has a "Game title (edit me)" text layer. Steam allows only the game's title on capsules
  (no studio logo, taglines or quotes) and wants the title to nearly fill the small capsule, so the templates carry just the title
  and a faint mark. Put key art on the Background layer. Keep anything important in the hero's centre (Steam crops it). `shortcut-icon-256.png` and `app-icon-184.jpg` are ready as-is.
- `itch/`: itch.io cover template (630×500, and 2×).
- Engines: use `kit/logo/png/` for in-game logos (transparent PNG at many sizes) and `kit/web/icon-*.png` for app icons.
