# iOS and Android

FusionSpace apps (a launch-weather board, an ejection-charge calculator, flight-computer setup over Bluetooth, flight reports
from a flight computer's log, a recovery tracker) are used at the bench and at the field. The rule is principle 8: **the platform owns behavior, FusionSpace owns
content.** An iPhone app should feel like an iPhone app, and still be unmistakably a FusionSpace instrument once you look at
what it shows.

Tokens: [`tokens/FusionSpaceColors.swift`](tokens/FusionSpaceColors.swift) and
[`tokens/FusionSpaceColors.kt`](tokens/FusionSpaceColors.kt). App icons: `kit/apps/` (iOS Icon Composer layers, Android
adaptive layers with a monochrome layer, macOS, Google Play).

## What the platform owns

- **Navigation and chrome.** Tab bars, toolbars, navigation bars, sheets, back, gestures, search, menus, alerts. On iOS 26 and
  27 these are Liquid Glass and stay standard (Apple's branding guidance: keep brand color in the content layer, beneath the
  glass). On Android, Material 3 components with edge-to-edge layout and predictive back, which apps targeting Android 16
  can't opt out of.
- **Controls.** System switches, steppers, pickers, text fields, date pickers. Restyle color and type through the platform's
  theming, not by rebuilding the control.
- **Text scaling.** Dynamic Type on iOS (test at the largest accessibility size) and font scaling to 200% on Android. Body
  text and controls use the system font (SF Pro, Roboto) so they scale and read like the rest of the phone.
- **Accessibility.** VoiceOver and TalkBack labels, Bold Text, Reduce Motion, Increase Contrast, Smart Invert.
- **Haptics.** The system patterns only (success, warning, error, selection), and only to confirm a physical-feeling action
  (arming, a value locked in).

## What FusionSpace owns

- **Color roles.** The app's tint is the action role (Ion on light, O blue on dark). One prominent, tinted primary action per
  screen at most. Signal colors exactly as in [`foundations.md`](foundations.md#color), with the same fills on every theme.
  Android uses a **static** brand scheme (`FsLightScheme`, `FsDarkScheme`): Material allows it, and anything carrying meaning
  must not shift with the wallpaper. Dynamic color may be offered as a setting for chrome only.
- **Type in content.** Cascadia Mono for titles, section heads, labels, readouts and codes; Archivo for longer prose in
  content (help, descriptions); controls and list text in the system font. All scaled with `relativeTo:` (iOS) and `sp`
  (Android) so they follow the user's text size. Fonts ship in the app
  bundle (SIL OFL).
- **Data display.** Readouts, charts, tables, units and line types as in [`data.md`](data.md). Charts with Swift Charts or
  Compose Canvas/Vico, styled to the chart rules, with an audio graph (iOS) or a semantics summary (Android).
- **The sheet and the title block** inside scrolling content: 2 px top rules on sections, `SHEET n / N` labels, the title block
  as the About screen (designation, version, build, data versions, licenses).
- **Domain icons** from [`icons/`](icons/), as SF Symbols custom symbols (drawn on the SF Symbols template from the 24 px
  masters) and the Android vector drawables in `icons/android/`. System actions use SF Symbols and Material Symbols.

## Field use

- **Theme.** Follow the system appearance. The field theme is an app-level theme: on iOS set `.environment(\.fsTheme, .field)`
  and read colors through `FSPaletteReader`; on Android provide `FieldFsColors` through `LocalFsColors`. Increase Contrast in
  light appearance (iOS) and the high-contrast setting (Android) turn it on too. Countdown, arming and recovery screens use it by
  default, and a Field switch is offered everywhere else. Dark has no separate high-contrast set: its text already clears 7 : 1.
- **Targets.** 44 × 44 pt (iOS) and 48 × 48 dp (Android) minimum; **{{TARGET['field']}} pt/dp** (about 15 mm) for controls used
  at the pad and **{{TARGET['glove']}} pt/dp** (about 20 mm) for the one critical control used with gloves, which is what
  MIL-STD-1472H asks of touchscreens in the field. Critical controls sit in the lower half of the screen, reachable with a
  thumb.
- **Irreversible and energetic actions** (arm, fire, erase a log, flash firmware) take two separate actions: a hold or slide to
  confirm, with an accessible alternative that is still two steps (a button that opens a confirmation). A touchscreen is never the only way to make a pyro channel
  safe; the hardware switch is.
- **Commanded and confirmed** state shown separately for anything sent to hardware ([`data.md`](data.md#live-telemetry)).
- **Offline first.** Weather, map tiles, motor data and simulations are saved before the trip, each with its "as of" time.
  Nothing at the pad needs a connection.
- **Screen awake** only on countdown and tracking screens (`isIdleTimerDisabled`, `FLAG_KEEP_SCREEN_ON`), released on leaving.
- **Heat.** Phones dim or shut down in desert sun (iPhones are rated to 35 °C ambient). Dark-on-light field theme, no
  needless GPU work, and a warning when the system reports thermal throttling.

## Bluetooth devices

Pairing with a FusionSpace flight computer or tracker uses the system picker: **AccessorySetupKit** on iOS 18 and later,
**Companion Device Manager** on Android (no location permission needed), filtered by the device's service UUID. Show the
device's designation and board revision (`FS-VEGA-004 rev B`) and firmware version once connected, and its signal
strength and link age at all times.

## Glanceable surfaces

- **Live Activities** (iOS) and **Live Updates** (Android 16) carry a launch countdown and flight tracking: T-minus, then
  altitude and phase (pad, boost, coast, apogee, drogue, main, landed), then distance and bearing to the rocket. The Dynamic
  Island is always black: use the dark roles there. Activities run up to 8 hours; updates are small (4 KB on iOS).
- **Widgets** show one readout (next launch window, surface wind with its age), and must read in tinted, clear and monochrome
  modes: the readout and its unit are text, never color.

## App icons

From `kit/apps/`: one layered master (the mark on a Void tile), built in Icon Composer for iOS with all six appearances
(default, dark, clear light and dark, tinted light and dark), and an Android adaptive icon with its own monochrome layer, so
Android's automatic theming doesn't draw one. Per-tool apps add nothing to the mark; the tool's name is the app's name.

## Checklist

- [ ] System navigation, controls and gestures, unmodified except for tint and fonts.
- [ ] Every text style scales; tested at the largest size and at 200%.
- [ ] Colors from `FS` / `FsColors` only; static scheme on Android.
- [ ] Field theme on Increase Contrast; field-size targets on pad screens.
- [ ] Every status has a word and a shape; every value has a unit; every prediction is labeled.
- [ ] Two actions for anything that arms, fires or erases; commanded vs confirmed shown.
- [ ] Works in airplane mode after the pre-trip sync.
- [ ] About screen is a title block with designation, version, build and data versions.
