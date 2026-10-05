# macOS, Windows and Linux

Desktop apps: the flight simulator with its design tree, 3D replay and Monte Carlo runs; the flight-log analyser; a
ground-station console talking to radios over USB; firmware and configuration tools for flight computers. These are long
sessions with dense data, real files and real hardware, on three platforms with three sets of rules.

The rule is the same as on phones (principle 8): **the platform owns behaviour and chrome, FusionSpace owns content.** A
FusionSpace Mac app has a proper menu bar and a Settings window; a Windows app has access keys and follows contrast themes; a
Linux app installs its icons where the desktop looks for them. Inside the window, the content is a FusionSpace drawing: sheets,
readouts, charts, line types, title blocks.

Packaging files: [`desktop/`](desktop/) (Windows ICO and MSIX tiles, Linux hicolor and symbolic icons, a `.desktop` entry,
AppStream metadata and a udev rule, all as templates). macOS icons: `kit/apps/macos/`.

## Choosing a toolkit

FusionSpace's engines are Rust (hpr-sim). The default shell is **Tauri 2**: native menus and file dialogs on all three
platforms, the content in the system web view (WebView2, WKWebView, WebKitGTK), so `product/web/fusionspace.css` applies as it
is and screen readers reach the content through each platform's web accessibility.

| Choice | Use it for | Watch for |
|---|---|---|
| **Tauri 2** (default) | Every user-facing desktop app | Test each release on the oldest supported macOS and on a stable Debian or Ubuntu WebKitGTK; WebGL2 for 3D, WebGPU only as an extra; serial and USB in Rust (`serialport`), not Web Serial |
| **egui** | Internal and bench tools only (a test-stand logger) | It doesn't look native; text scaling and contrast themes are manual |
| Electron | Only if a JavaScript core is unavoidable | Size; a Rust core then needs Node bindings |
| Qt 6 | Not planned | C++ and licensing |
| iced, Flutter desktop | No | No screen-reader support yet in iced; Flutter's native menu bar is macOS-only |

## What the platform owns

- **Window chrome.** The system title bar, traffic lights or caption buttons, and the platform's materials: Liquid Glass on
  macOS 26 and later (controls and sidebars only, never content), Mica on Windows 11 (the window's base layer, once), the
  Adwaita or Breeze header bar on Linux. No custom title bars, no brand-tinted toolbars, no imitation glass inside content.
- **Menus.** One command model, drawn natively:
  - **macOS:** the full menu bar in Apple's order (App, File, Edit, View, app menus, Window, Help). Every command is in a menu,
    including the ones in toolbars; items are disabled, not hidden. About, then Settings… (⌘,) in the App menu. A Window
    menu even with one window (Full Keyboard Access depends on it).
  - **Windows:** a menu bar per window with access keys (Alt shows them; F for File) and Ctrl accelerators.
  - **Linux:** a primary menu at the end of the header bar (F10), Ctrl+, for preferences, Ctrl+? for the shortcuts window,
    F1 for help.
  - A command palette (⌘⇧P / Ctrl+Shift+P) mirrors the menus; it is never the only way to a command.
- **Fonts in chrome.** Menus, title bars, settings, dialogs and notifications are in the system font (SF Pro, Segoe UI
  Variable, Adwaita Sans or the KDE font).
- **Selection and accent in chrome** follow the user's system accent (macOS lets an app's own accent through only when the
  user picks "multicolor"; GNOME and KDE apps follow the system accent). Inside content, `action` (Ion) stays the link and
  focus colour, and signal colours are never used for selection.
- **Settings** live in the platform's place: a Settings window on macOS (panes in a toolbar, the last pane restored), a
  Settings dialog on Windows, a preferences window on Linux. Don't repeat system settings (appearance, accessibility).
- **Files and state** live where the platform keeps them: `~/Library/Application Support/<app>` on macOS, `%APPDATA%` and
  `%LOCALAPPDATA%` on Windows, `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_STATE_HOME` on Linux.

## What FusionSpace owns

- **Content.** Sheets, readouts, tables, charts, line types, status chips, notes and title blocks, from
  [`foundations.md`](foundations.md) and [`data.md`](data.md), in Cascadia Mono and Archivo.
- **The About window is a title block:** designation, version, build, the data versions inside (motor database, atmosphere
  model), licences.
- **Domain icons** from [`icons/`](icons/) inside content; system icons (SF Symbols, Segoe Fluent Icons, Adwaita symbolic
  icons) in toolbars and menus where the platform has one for the action.

## Dense engineering views

- **Text sizes.** macOS has no Dynamic Type: its body text is 13 pt and the minimum 10 pt, and apps offer zoom (⌘+ / ⌘−).
  Windows' minimum is 12 px regular, 14 px semibold, and text scaling goes to 225 %, which custom-drawn text (plots, 3D labels)
  must follow by listening for the scale factor. In FusionSpace content: 12 px at least, 13 to 14 px for dense tables in
  Cascadia Mono with tabular figures, and ⌘/Ctrl +/− zoom everywhere.
- **Layout.** A sidebar (design tree or file list), the content, and an inspector (properties of the selection), as split
  views that collapse as the window narrows. Docking is optional and the layout is always restored. On Linux, support windows
  down to 1024 × 600.
- **Tables and property grids** use the toolkit's native list and table controls where there are any, so selection follows
  the accent and contrast themes; otherwise they follow [`data.md`](data.md#tables).
- **High-DPI.** Plots and 3D render at the device pixel ratio; drawing lines (rules, axes, chain lines) are one device pixel
  for the thin weight and two for thick.
- **Units** are an app setting (US or SI, with the altitude reference), with an override per document.

## Documents

Rocket designs, flight logs and sessions are documents:

- Autosave, and a crash-recovery journal in the platform's state directory, so nothing is lost when the app or the machine
  stops. On reopening, offer what was recovered.
- Undo and Redo name what they undo ("Undo Change Fin Count"), across the whole document.
- Duplicate rather than Save As (macOS); Open Recent everywhere; the document's title in the window title, and a mark for
  unsaved changes.
- A file a FusionSpace app writes carries the app's designation and version, like a title block ([`data.md`](data.md#files-and-exports)).

## Hardware: serial, USB and radios

- **Firmware:** FusionSpace devices enumerate as USB CDC-ACM, so Windows binds its built-in driver and nothing needs
  installing (FTDI and CP210x bridges need vendor drivers).
- **macOS:** ship outside the App Store as a Developer ID app, notarised, not sandboxed (a sandboxed app needs the serial and
  USB entitlements).
- **Linux:** ship a udev rule ([`desktop/linux/99-fusionspace.rules`](desktop/linux/99-fusionspace.rules)) with the packages,
  and when a port can't be opened, show a "No permission" panel that explains the `dialout` (Debian, Ubuntu, Fedora) or
  `uucp` (Arch) group, with the exact command. A Flatpak build needs `--device=all` for serial ports, and its description
  says why.
- The ground-station rules in [`embedded.md`](embedded.md#ground-stations-and-pad-boxes) and
  [`data.md`](data.md#live-telemetry) apply: link age, stale data, commanded and confirmed state. Arming over a desktop
  connection follows the same two-action rule as everywhere else.

## Icons and packaging

One master: the mark on its Void tile (`logo/favicon/app-icon.svg`), no baked shadows or highlights, recognisable at 16 px.

| Platform | Files | Notes |
|---|---|---|
| macOS | `kit/apps/macos/`; build the `.icon` in Icon Composer with all appearances (default, dark, clear, tinted) | A square, full-bleed source; the system applies the shape. An icon that sticks out of the shape gets a grey plate |
| Windows | [`desktop/windows/app.ico`](desktop/windows/) (16, 24, 32, 48, 256) and the MSIX tiles, including the unplated targets | Without unplated targets Windows draws the icon smaller on a plate |
| Linux | [`desktop/linux/`](desktop/linux/): hicolor `scalable/apps/<app-id>.svg`, a 256 px PNG, and `<app-id>-symbolic.svg` | App ids are reverse DNS of fusionspace.co: `co.fusionspace.Loft` |

- Flathub asks for "colourful" brand colours in the metadata, not black or white: use O blue `{{O_BLUE}}` for light and
  M orange `{{M_ORANGE}}` for dark, as in the AppStream template.
- Screenshots for stores are taken on each platform, in its default appearance.

## Updates and signing

- **macOS:** Developer ID, hardened runtime, notarised with `notarytool` and stapled. Updates with the Tauri updater or
  Sparkle 2 (EdDSA signatures).
- **Windows:** the Microsoft Store (MSIX, signed for free), or Azure Artifact Signing where eligible, otherwise an OV
  certificate; SmartScreen reputation builds over time.
- **Linux:** Flathub or distribution packages update themselves; an AppImage uses the Tauri updater.
- Update signing keys are backed up offline (losing the key strands every installed copy). Updates are announced in the app,
  never forced mid-session, and every app works fully offline.

## Accessibility

- Each platform's accessibility API: VoiceOver (NSAccessibility), Narrator, NVDA and JAWS (UI Automation), Orca (AT-SPI). In
  a Tauri app that means real HTML semantics and ARIA in the content.
- Everything works from the keyboard: Full Keyboard Access on macOS, access keys on Windows, a logical Tab order everywhere,
  and a visible focus ring (2 px, 3 : 1).
- **Windows contrast themes:** map every colour, plots and 3D included, to the system colour pairs (window and text,
  highlight, button, grey text for disabled only, hotlight for links only); signal colours then show as their shapes and
  words. Never hard-code colours there. The web content does this with `forced-colors`.
- macOS Increase Contrast, GNOME high contrast (the portal's `contrast` key) and Windows text scaling are all honoured; the
  field theme is available as an app setting.
- Reduce Motion (and the portal's `reduced-motion`): no auto-orbiting replay cameras, no animated transitions; playback runs
  only when the user starts it.
- Targets at least 24 × 24 px; 28 pt controls on macOS.

## Checklist

- [ ] Native title bar, menus, dialogs, settings window; every command in a menu; standard shortcuts untouched.
- [ ] System font and accent in chrome; FusionSpace content inside; no brand-tinted chrome.
- [ ] Autosave and crash recovery; named undo; units as a setting.
- [ ] Serial devices open without a driver install on Windows; the udev rule shipped and the permission panel written on Linux.
- [ ] Icons for all three platforms, including Windows unplated targets and the Linux symbolic icon.
- [ ] Signed and notarised; updates signed with a backed-up key; works offline.
- [ ] Tested with VoiceOver, Narrator and Orca, keyboard only, a Windows contrast theme, 225 % text scaling and Reduce Motion.
- [ ] The About window is a title block.
