# Desktop packaging

Icons and templates for FusionSpace apps on Windows and Linux; macOS icons are in `kit/apps/macos/` (build the `.icon` in Icon
Composer). The example app id is `co.fusionspace.HprSim`: rename it for each app. Rules in `product/desktop.md`.

| Path | What |
|---|---|
| `windows/app.ico` | 16 (pixel-hinted), 24, 32, 48 and 256 px |
| `windows/msix/` | MSIX assets: Square44x44 scales and target sizes (with the light and dark unplated variants Windows needs), Square150x150, StoreLogo |
| `linux/hicolor/` | `scalable/apps/co.fusionspace.HprSim.svg`, `256x256/apps/co.fusionspace.HprSim.png`, `symbolic/apps/co.fusionspace.HprSim-symbolic.svg` |
| `linux/co.fusionspace.HprSim.desktop` | Desktop entry template |
| `linux/co.fusionspace.HprSim.metainfo.xml` | AppStream metadata template, with the brand colours Flathub asks for |
| `linux/99-fusionspace.rules` | udev rule so users can open the device's serial port |
