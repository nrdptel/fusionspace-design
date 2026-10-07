# FusionSpace sample apps: iPhone and Apple Watch

Small apps that run the published SwiftUI parts on real simulators, so the code in `product/` is proven, not only compiled.
They compile the files in `product/` directly (nothing is copied), so a change there is tested here on the next build.

| Target | What | Compiles |
|---|---|---|
| `FusionSpaceSample` (iOS 26+) | Pad and Track screens inside the system's tab bar and navigation | `product/tokens/FusionSpaceColors.swift`, `product/mobile/swiftui/FSComponents.swift`, `FSFlightActivity.swift` |
| `FusionSpaceWidgets` (iOS widget extension) | The flight's Live Activity and Window's wind widget | the above plus `FSWindWidget.swift` |
| `FusionSpaceSampleWatch` (watchOS 26+, watch only) | Find, Find in Always On, Pad and Unfired | the above plus `product/watch/swiftui/FSWatch.swift` |
| `FusionSpaceWatchWidgets` (watchOS widget extension) | Find on every complication family | the above plus `FSWatchComplications.swift` |

Fonts come from `type/fonts/` (SIL OFL).

## Build and run

```
brew install xcodegen          # or the release binary from github.com/yonaskolb/XcodeGen
cd source/product/samples/apple
xcodegen generate              # writes FusionSpaceSample.xcodeproj (not committed)
open FusionSpaceSample.xcodeproj
```

From the command line (simulators; no signing needed):

```
xcodebuild -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSample -destination 'generic/platform=iOS Simulator' -derivedDataPath build build
xcodebuild -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleWatch -destination 'generic/platform=watchOS Simulator' -derivedDataPath build build
xcrun simctl install <iphone> build/Build/Products/Debug-iphonesimulator/FusionSpaceSample.app
xcrun simctl launch <iphone> co.fusionspace.sample -screen pad          # or -screen track
xcrun simctl launch <iphone> co.fusionspace.sample -activity flight     # or -activity pad: starts the Live Activity
xcrun simctl install <watch> build/Build/Products/Debug-watchsimulator/FusionSpaceSampleWatch.app
xcrun simctl launch <watch> co.fusionspace.sample.watch -screen find    # find, find-aod, pad, unfired
xcrun simctl io <device> screenshot --mask=alpha shot.png
```

The captures in `source/product/devices/apple/` were made this way on Xcode 27.0 with the iOS 27.0 and watchOS 27.0
simulators (iPhone 17 Pro, Apple Watch Ultra 4 49 mm, Apple Watch SE 3 40 mm); `devices.json` there says which is which.

## What running them found (October 6, 2026)

Everything below compiled before; it broke or looked wrong only when it ran:

- `FusionSpaceColors.swift` didn't build for watchOS (UIKit's dynamic colors don't exist there): a watch now gets the dark
  roles directly.
- `FSHoldToConfirm` filled the whole screen (a `GeometryReader` in its stack took every point offered): the progress now
  lives in the background.
- `fsKeepsScreenOn()` broke every widget extension (`UIApplication.shared` isn't allowed there): it's marked unavailable in
  extensions.
- Status chips upper-cased their units (`0.3 S`): `FSStatus` takes a `detail:` that keeps its case.
- On the watch: the bottom-bar "Found it" drew as an empty capsule over the text above it, the Unfired message truncated,
  the Pad rows touched the screen edge, and the SE 40 mm cut the bottom of Pad and Unfired. The watch screens now pick the
  first of a few layouts that fits (then scroll for very large text), with scene padding, and "Found it" is a full-width
  button in the content.
- In the Dynamic Island the SAFE box's border was cut by the island's rounded end, and the countdown pushed the island over
  the clock: the box is inset and the countdown fits the compact width.
- `UINavigationBarAppearance` fonts aren't applied to large titles on iOS 27: the sample sets the Cascadia Mono large title
  with `ToolbarItem(placement: .largeTitle)`.
