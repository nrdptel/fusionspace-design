# FusionSpace Android sample

A small Gradle project that runs FusionSpace's Compose reference code on a phone and a Wear OS watch, so the published files
are tested on real Android, not just compiled. It compiles the files in `product/` in place (no copies), so a change to a
reference file shows up in the next build. Apache-2.0, like the code it runs.

| Module | Package | Screens | Compiles from the repo |
|---|---|---|---|
| `phone` | `co.fusionspace.sample` | Pad (field theme), Track (dark), the Live Update | `product/tokens/FusionSpaceColors.kt`, `product/mobile/compose/FsComponents.kt`, `product/mobile/compose/FsLiveUpdate.kt` |
| `wear` | `co.fusionspace.sample.wear` | Find, Pad, Unfired; the Find tile and complication | `product/watch/compose/FsWear.kt`, `product/watch/compose/FsWearTile.kt` |

The build also takes, at build time and into `build/generated/fsResources` (nothing is committed twice): Cascadia Mono from
`type/fonts/` into `res/font`, the icons from `product/icons/android/` into `res/drawable` (their `?attr/colorControlNormal`
tint is pointed at the framework attribute, since the sample has no AppCompat), and the adaptive app icon from
`kit/apps/android/` into `res/mipmap`.

Screenshots from the emulators, with the device and OS of each, are in `source/product/devices/android/` (`devices.json`).

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
`canPostPromotedNotifications` under the tag `FsSample`. Test large text with
`adb shell settings put system font_scale 2.0`, and a camera cutout with
`adb shell cmd overlay enable com.android.internal.display.cutout.emulation.hole`.

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

The tile's Find button opens `FindActivity`, which `FsFindTileService` launches by name (`<package>.FindActivity`).
`FindComplicationService` is registered for `SHORT_TEXT`, `LONG_TEXT` and `RANGED_VALUE`.

## What's sample and what's reference

The screens' layout (the Pad's sheets and rows, Track's phase strip and drawn map, the watch Pad's channel rows) is the
sample's own; the parts on them (`FusionSpaceTheme`, `FsStatus`, `FsSheetHeader`, `FsReadout`, `FsStateBox`,
`FsCommandedConfirmed`, `FsHoldToConfirm`, `FsArmConfirmation`, `FsLiveUpdate`, `FusionSpaceWearTheme`, `FsWearFind`,
`FsWearStateBox`, `FsWearUnfired`, `FsFindTileService`, `FsFindComplicationService`) come unchanged from `product/`.
Nothing here sends anything to hardware: "Hold to arm" and SAFE only change the sample's state.
