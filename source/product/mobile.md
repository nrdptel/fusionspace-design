# iOS and Android

FusionSpace apps (a launch-weather board, an ejection-charge calculator, flight-computer setup over Bluetooth, flight reports
from a flight computer's log, a recovery tracker) are used at the bench and at the field. The rule is principle 8: **the platform owns behavior, FusionSpace owns
content.** An iPhone app should feel like an iPhone app, and still be unmistakably a FusionSpace instrument once you look at
what it shows.

Tokens: [`tokens/FusionSpaceColors.swift`](tokens/FusionSpaceColors.swift) and
[`tokens/FusionSpaceColors.kt`](tokens/FusionSpaceColors.kt). Reference parts: [`mobile/`](mobile/) (four screens on both
platforms, the glanceable surfaces, and the content layer as SwiftUI and Compose code). App icons: `kit/apps/` (iOS Icon
Composer layers, Android adaptive layers with a monochrome layer, macOS, Google Play).

![Pad, Track, a flight report and a device, on iOS and Android](mobile/preview.png)

## What the platform owns

- **Navigation and chrome.** Tab bars, toolbars, navigation bars, sheets, back, gestures, search, menus, alerts. On iOS 26 and
  27 these are Liquid Glass and stay standard (Apple's branding guidance: keep brand color in the content layer, beneath the
  glass). iOS 27 ignores the old opt-out (`UIDesignRequiresCompatibility`), and people set the glass from clear to tinted
  with a slider, so never put a meaning in what shows through it. On Android, Material 3 components with edge-to-edge
  layout and predictive back, which apps targeting Android 16 can't opt out of; apps targeting Android 17 also can't refuse
  resizing on large screens.
- **Controls.** System switches, steppers, pickers, text fields, date pickers. Restyle color and type through the platform's
  theming, not by rebuilding the control.
- **Text scaling.** Dynamic Type on iOS (test at the largest accessibility size) and font scaling to 200% on Android. Body
  text and controls use the system font (SF Pro, Roboto) so they scale and read like the rest of the phone.
- **Accessibility.** VoiceOver and TalkBack labels, Bold Text, Reduce Motion, Increase Contrast, Smart Invert, and Android
  16's outline text (which replaced high-contrast text). A readout is one element: label, value, unit spoken in words
  ("feet above ground level"), qualifier.
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
- **Domain icons** from [`icons/`](icons/): on iOS and watchOS the ready-made SF Symbols custom symbols in
  [`icons/sf-symbols/FusionSpaceSymbols.xcassets`](icons/sf-symbols/) (`Image("fs.rocket")`, `Tab("Pad", image:
  "fs.launch-rail", …)`, `FS.icon(_:)`, small, medium and large scales); on Android the vector drawables in `icons/android/`.
  System actions use SF Symbols and Material Symbols.

## Screens

The four reference screens in [`mobile/screens/`](mobile/screens/) show where the line between platform and content falls.
Each is drawn on an {{MOBILE.DEVICES['ios']['name']}} ({{MOBILE.DEVICES['ios']['w']}} × {{MOBILE.DEVICES['ios']['h']}} pt, {{MOBILE.DEVICES['ios']['os']}}) and a {{MOBILE.DEVICES['android']['name']}}
({{MOBILE.DEVICES['android']['w']}} × {{MOBILE.DEVICES['android']['h']}} dp, {{MOBILE.DEVICES['android']['os']}}) with the same content.

- **Pad** (field theme): checks and channels as sheets, then, fixed at the bottom where a thumb reaches, the device's state
  (`SAFE` in an outline box, commanded and confirmed) above the two controls that change it: **Hold to arm**, held for
  {{MOBILE.HOLD_S}} s with the device's designation on it, its progress shown as a fill and a bar, and **SAFE**, one tap, to its
  right. Both are {{TARGET['glove']}} pt/dp tall. Below them, "Arm with a confirmation instead": the accessible alternative, still two
  steps.
- **Track** (dark): the phase strip (done in ink, now inverted, next faint), the two numbers that matter under the main,
  the offline map (tiles dated, GPS fix shown, predicted landing dashed in Nebula), then distance, bearing in degrees true,
  and the coordinates with a copy button.
- **Flight report** (light): the same numbers as the web report, as readouts, an altitude chart with the prediction's band
  and numbered events, and the channels.
- **Device** (light): settings are system lists, with the platform's shapes and type, headed by FusionSpace labels;
  nothing there can fire a channel. The About sheet is the title block.

Titles, labels and readouts are Cascadia Mono on both platforms; list rows, buttons and prose are the system font. The large
title is the platform's (a large navigation title on iOS, the top app bar's title on Android) set in Cascadia Mono through
its theming, not a custom bar. On iOS 26 and later that is `ToolbarItem(placement: .largeTitle)`: `UINavigationBarAppearance`
fonts are not applied to large titles on iOS 27.

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
- **Screen awake** only on countdown and tracking screens (`isIdleTimerDisabled`, `Modifier.keepScreenOn()` in Compose), released
  on leaving: `fsKeepsScreenOn()` in [`mobile/swiftui/FSComponents.swift`](mobile/swiftui/FSComponents.swift) does it on iOS.
- **Heat.** Phones dim or shut down in desert sun (iPhones are rated to 35 °C ambient). Dark-on-light field theme, no
  needless GPU work, and a warning when the system reports thermal throttling.

## Bluetooth devices

Pairing with a FusionSpace flight computer or tracker uses the system picker: **AccessorySetupKit** on iOS 18 and later,
**Companion Device Manager** on Android (no location permission needed), filtered by the device's service UUID. Show the
device's designation and board revision (`FS-VEGA-004 rev B`) and firmware version once connected, and its signal
strength and link age at all times.

## Glanceable surfaces

Drawn in [`mobile/glance/`](mobile/glance/); worked through in code in `FSFlightActivity.swift`, `FSWindWidget.swift` and
`FsLiveUpdate.kt`.

- **Live Activities** (iOS) and **Live Updates** (Android) carry a launch countdown and flight tracking: T-minus to the time
  the flier set (and saying so), then altitude and phase (pad, boost, coast, apogee, drogue, main, landed), then distance and
  bearing to the rocket, and after landing whether every charge fired. Every value carries its age; past its stale limit it
  says so.
- **iOS sizes.** Lock Screen {{MOBILE.GLANCE['la_w']}} pt wide (14 pt margins) and {{MOBILE.GLANCE['la_h'][0]}} to {{MOBILE.GLANCE['la_h'][1]}} pt tall;
  Dynamic Island {{MOBILE.GLANCE['di_compact']}} pt across in compact and {{MOBILE.GLANCE['di_w']}} pt expanded on iPhone 17 Pro. The island is
  always black: use the dark roles there. Compact: the countdown or the phase on the left (`T−4:45`, `MAIN`), and on the
  right one number with its unit, or at the pad the state in its box (`SAFE` outlined, `ARMED` inverted). Minimal: live data with its unit, not a logo. Activities run up to 8 hours and stay
  4 more on the Lock Screen; attributes and state together stay under 4 KB. The same activity appears on its own in the
  Apple Watch Smart Stack, CarPlay and the Mac menu bar; give the Watch a `.small` layout.
- **Android Live Updates** are promoted ongoing notifications: `POST_PROMOTED_NOTIFICATIONS` in the manifest,
  `setRequestPromotedOngoing(true)` (API 36.1, Android 16 QPR2; the extra on 36.0), a title, no custom views and no
  colorized background. The status-bar chip takes {{MOBILE.GLANCE['chip_chars']}} characters at most (`612 ft`). On Android 16 use
  `ProgressStyle` with the flight's phases as segments, apogee and main as points and the rocket as the tracker; on
  Android 17 use `MetricStyle` (up to three values with units) and its semantic styles, which match the signal colors:
  `SAFE` for Aurora, `CAUTION` for Sodium, `DANGER` for Flare, `INFO` for the action color. Wear OS 7 can bridge Live Updates
  to the watch (not on every watch, and without `MetricStyle`): see [`watch.md`](watch.md).
- **Widgets** show one readout (next launch window, surface wind with its age; a medium widget adds a second column, such as
  the ceiling and the winds aloft, each with its own age, a forecast hours old marked stale), and must read in tinted, clear and vibrant
  modes, where the system draws everything in one tint: the readout and its unit are text, the value is the accent group
  (`widgetAccentable()`), and a caution is a word and a triangle in an outline, never only a Sodium fill. Android widgets
  use the static FusionSpace scheme inside the launcher's container, not wallpaper color, because the caution means
  something; Google's widget guidance prefers dynamic color, and that is the one place this system departs from it.

## App icons

From `kit/apps/`: one layered master (the mark on a Void tile), built in Icon Composer for iOS with all six appearances
(default, dark, clear light and dark, tinted light and dark), and an Android adaptive icon with its own monochrome layer, so
Android's automatic theming doesn't draw one. Per-tool apps add nothing to the mark; the tool's name is the app's name.

## Real screens

The reference code runs in two sample apps, `source/product/samples/apple` (Xcode, generated with XcodeGen) and
`source/product/samples/android` (Gradle), which compile the files in `product/` in place. Their simulator and emulator
captures are in [`mobile/devices/`](mobile/devices/):

![The reference code running](mobile/devices/preview.png)

The captures include the wind widget on the Home Screen in light and dark (added there the way a person would, through
Xcode 27's Device Hub), the Live Activity on the Lock Screen (locked and woken with the power button) and in the Dynamic
Island, and the Live Update on Android 17 (MetricStyle) and Android 16 (ProgressStyle, with its status-bar chip). The apps also carry the platforms' accessibility
checks as tests (Apple's audit as UI tests; on Android, the Accessibility Test Framework in instrumented tests, at 100% and
200% text), and the screens are checked by eye at xxxLarge and Accessibility XXXL (on Android at font scale 2.0): nothing
may be cut, truncated or split, and at the largest sizes the screens scroll instead. Run them after changing anything in `product/mobile/` or `product/tokens/`: compiling is not enough. On October 6, 2026
running them found layout bugs that every compile check had passed (a control taking the whole screen, text under a
button, a border cut by a rounded end, units in capitals), all fixed in the files here.

## Checklist

- [ ] System navigation, controls and gestures, unmodified except for tint and fonts.
- [ ] Every text style scales; tested at the largest size and at 200%.
- [ ] Runs in the sample app on a simulator or emulator, smallest screen included, with nothing cut by an edge or a corner.
- [ ] Colors from `FS` / `FsColors` only; static scheme on Android.
- [ ] Field theme on Increase Contrast; field-size targets on pad screens.
- [ ] Every status has a word and a shape; every value has a unit; every prediction is labeled.
- [ ] VoiceOver and TalkBack read each row as one stop, abbreviations spelled out (`CONT` is "continuity"), units as words.
- [ ] Every control's target is at least 44 pt (48 dp), including text buttons: the frame inside the button, not around it.
- [ ] Two actions for anything that arms, fires or erases; commanded vs confirmed shown.
- [ ] Works in airplane mode after the pre-trip sync.
- [ ] About screen is a title block with designation, version, build and data versions.
- [ ] Live Activity / Live Update and widgets read in every rendering mode, with units and ages, and say when they're stale.
