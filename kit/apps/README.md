# FusionSpace app icons and store art

Checked October 2, 2026 against Apple's and Google's current guidance.

| Folder | Files | Where |
|---|---|---|
| `ios/` | `AppIcon-1024.png` (opaque, square: iOS rounds it), `.svg` | Xcode asset catalog, App Store |
| `ios/icon-composer/` | `background.svg`, `foreground.svg`, `foreground-white.svg` | Icon Composer (Xcode 26): drop the layers in, set Dark and Tinted appearances (white foreground for Tinted/Clear) |
| `macos/` | `AppIcon-1024.png` and 16–512 px: rounded 824 px body on a 1024 canvas, with shadow | macOS apps, `.icns` (`iconutil`) |
| `android/` | `ic_launcher_foreground/background/monochrome` (432 px = 108 dp at xxxhdpi, plus SVGs), `ic_launcher.xml` | Adaptive icon (`mipmap-anydpi-v26`); the art sits inside the 66 dp safe circle, so every launcher mask keeps it whole |
| `google-play/` | `play-icon-512.png`, `feature-graphic-1024x500.png` | Play Console store listing |

Web and PWA icons are in `kit/web/`. Edit the feature graphic's text layer for a specific app (or generate per-project art with
`tools/build/project.py`).
