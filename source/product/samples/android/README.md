# FusionSpace Android sample

A small Gradle project that runs FusionSpace's Compose reference code on a phone and a Wear OS watch, so the published files
are tested on real Android, not just compiled. It compiles the files in `product/` in place (no copies), so a change to a
reference file shows up in the next build. Apache-2.0, like the code it runs.

| Module | Package | Screens | Compiles from the repo |
|---|---|---|---|
| `phone` | `co.fusionspace.sample` | Pad (field theme), Track (dark), the Live Update | `product/tokens/FusionSpaceColors.kt`, `product/mobile/compose/FsComponents.kt`, `product/mobile/compose/FsLiveUpdate.kt` |
| `wear` | `co.fusionspace.sample.wear` | Find, Pad, Unfired; the Find tile and complication | `product/watch/compose/FsWear.kt`, `product/watch/compose/FsWearTile.kt` |

The build also takes, at build time and into `build/generated/fsResources` (nothing is committed twice): Cascadia Mono from
`type/fonts/` into `res/font`, the icons from `product/icons/android/` into `res/drawable` as published (they tint with the
framework's `?android:attr/colorControlNormal`, so they work without AppCompat, which this app doesn't have), and the
adaptive app icon from `kit/apps/android/` into `res/mipmap`.

Screenshots from the emulators at the default text size, with the device and OS of each, are in
`source/product/devices/android/` (`devices.json`), the status bar set with SystemUI demo mode (9:41, full battery).

## Build

Needs JDK 21, Gradle 9.8 (or a wrapper of your own), and an Android SDK with platform `android-37.0` and build-tools 37
(AGP 9.4 also installs build-tools 36 when it needs them). From this folder:

```sh
export ANDROID_HOME=/path/to/sdk
gradle :phone:assembleDebug :wear:assembleDebug
```

compileSdk and targetSdk are 37 (Android 17); minSdk is 31 on the phone and 33 on the watch. AGP 9.4.1 with its built-in
Kotlin, the Compose compiler plugin 2.4.20, Compose BOM 2026.09.00, Wear Compose Material 3 1.7.0, Tiles 1.6.2,
ProtoLayout 1.4.2.

## Run

Phone (emulator `pixel_10`, Android 17 image):

```sh
adb install -r phone/build/outputs/apk/debug/phone-debug.apk
adb shell pm grant co.fusionspace.sample android.permission.POST_NOTIFICATIONS
adb shell am start -n co.fusionspace.sample/.MainActivity --es screen pad     # or track
adb shell am start -n co.fusionspace.sample/.MainActivity --es screen live    # posts the Live Update, opens Track
adb shell input keyevent KEYCODE_HOME                                          # the status-bar chip shows outside the app
adb shell cmd statusbar expand-notifications                                   # the card in the shade
```

`POST_PROMOTED_NOTIFICATIONS` is a normal permission (granted at install); the app logs
`canPostPromotedNotifications` under the tag `FsSample`. On Android 17 the card is MetricStyle; on Android 16 (API 36.1,
emulator image r4) it is ProgressStyle, promoted (`PROMOTED_ONGOING` in `dumpsys notification`) with the `612 ft` chip in
the status bar (`phone-live-update-android16.png`). Test large text with `adb shell settings put system font_scale 2.0`,
and a camera cutout with `adb shell cmd overlay enable com.android.internal.display.cutout.emulation.hole`.

Watch (emulators `wearos_large_round` and `wearos_small_round`, Wear OS 7 image):

```sh
adb -s <watch> install -r wear/build/outputs/apk/debug/wear-debug.apk
adb -s <watch> shell am start -n co.fusionspace.sample.wear/.MainActivity --es screen find   # or pad, unfired
adb -s <watch> shell input keyevent KEYCODE_SLEEP                                             # ambient
adb -s <watch> shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE \
    --es operation add-tile --ecn component co.fusionspace.sample.wear/.FindTileService
adb -s <watch> shell am broadcast -a com.google.android.wearable.app.DEBUG_SYSUI \
    --es operation show-tile --ei index 0
```

The tile's Find button opens the activity named by `FsFindTileService.findActivityClass` (by default
`<package>.FindActivity`); the sample's `FindTileService` overrides it with `FindActivity::class.java.name`. Large text:
`adb -s <watch> shell settings put system font_scale 1.24` (Wear OS's largest, "Largest" in Settings).
`FindComplicationService` is registered for `SHORT_TEXT`, `LONG_TEXT` and `RANGED_VALUE`.

## Accessibility checks

`AccessibilityTest` in each module runs the screens under the Accessibility Test Framework (Compose's
`enableAccessibilityChecks`, every check in the latest preset, with a screenshot so contrast is measured; warnings fail
too): Pad and Track on the phone at 100% and 200% text, Find, Pad and Unfired on the watch at 100% and 124%.

```sh
gradle :phone:connectedDebugAndroidTest      # with a phone emulator attached (ANDROID_SERIAL=... when several are)
gradle :wear:connectedDebugAndroidTest       # with a watch emulator attached
```

They pass on Android 17 (phone and Wear OS 7) and Android 16 (phone, API 36.1). Espresso is pinned to 3.7.0: the 3.5 that
Compose's test library brings can't inject input on API 37 (`InputManager.getInstance` is gone).

## Large text

Checked by hand, every screen scrolled top to bottom, at 200% on the phone (Pad, Track; also Pad at 150%) and at 124% on the
large and small round watches (Find, Pad, Unfired), then back at 100% to confirm the default screens didn't change. At
those sizes the screens scroll, so there are no large-text captures in the repo: a still frame always shows the next row
cut by the bottom edge. What the parts do as the text grows (product/mobile/compose, product/watch/compose):

- `FsStatus`: the state word is never split; the detail ("· 0.3 s") keeps its whole width on the chip's line while there's
  room, and only then wraps, the chip growing taller.
- `FsReadout`: the number never wraps. It stays beside its unit, a little smaller if that fits, else the unit goes under
  it (and only then does the number shrink further).
- `FsSheetHeader`: name and `SHEET n / N` on one line, or the number under the name.
- `FsCommandedConfirmed`: each label beside its value, or above it when both don't fit.
- `FsPhaseStrip`: the seven names in one row, or "MAIN · 6 of 7" with a tick per phase (never abbreviated).
- `FsTag`, `FsHoldToConfirm`: wrap at spaces, never truncate.
- `FsFirstThatFits` (the Compose counterpart of SwiftUI's `ViewThatFits`) does the choosing: the first layout whose texts
  all fit on one line, else the stacked one.
- Values and their units are joined by a non-breaking space (`"0.3\u00A0s ago"`, `"%,d\u00A0ft"`), in `FsFreshness.age`,
  the Live Update, the tile and the complications, so no line breaks between a number and its unit.
- Wear: `fsClearOfTime(padding)` grows the list's top padding with the time above it, which the scaffold's doesn't.

And in the sample's layouts: the Pad's rows (label, value, state) are one line or stacked; Hold to arm and SAFE stay in the
scroll at every size, side by side or, from 150% (or whenever they don't fit), SAFE below Hold to arm (SAFE is right of or
below ARM); Track's readouts go one above the other; the drawn map's labels keep their size (the map has a description);
the watch's channel rows put the state under the name, and its side margins grow with the text, since larger text puts
the rows lower on the circle.

## Findings

- Icons: `?attr/colorControlNormal` (AppCompat's) failed to link in an app without AppCompat; the generator now writes
  the framework's `?android:attr/colorControlNormal`, and the build copies the icons unchanged.
- ATF: the state box's "SAFE" and the SAFE button read the same to TalkBack (`DuplicateSpeakableTextCheck`): `FsStateBox`
  and `FsWearStateBox` now say "Device state: SAFE".
- ATF: Wear's list transformation fades rows at the screen's edge below 4.5:1 (`TextContrastCheck`), and it would dim
  ARMED; the watch Pad doesn't use it.
- Wear OS: at 124% the time ran into the first row (the scaffold's padding doesn't grow); on the small watch Unfired needs
  a scroll at 124%, and the OK edge button stays collapsed until the list reaches its end (the platform's behaviour).
- Android 16: `Build.VERSION.SDK_INT_FULL` is in the API 36 SDK, so the 36.0 branch (the `android.requestPromotedOngoing`
  extra) doesn't need a guard; 36.1 takes `setRequestPromotedOngoing`. Checked on 36.1; no 36.0 image was run.

## What's sample and what's reference

The screens' layout (the Pad's sheets and rows, Track's drawn map, the watch Pad's channel rows) is the
sample's own; the parts on them (`FusionSpaceTheme`, `FsStatus`, `FsTag`, `FsPhaseStrip`, `FsSheetHeader`, `FsReadout`, `FsStateBox`,
`FsCommandedConfirmed`, `FsHoldToConfirm`, `FsArmConfirmation`, `FsFirstThatFits`, `FsLiveUpdate`, `FusionSpaceWearTheme`,
`FsWearFind`, `FsWearStateBox`, `FsWearUnfired`, `fsClearOfTime`, `FsFindTileService`, `FsFindComplicationService`) come
unchanged from `product/`.
Nothing here sends anything to hardware: "Hold to arm" and SAFE only change the sample's state.
