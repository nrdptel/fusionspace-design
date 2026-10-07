# FusionSpace sample apps: iPhone and Apple Watch

Small apps that run the published SwiftUI parts on real simulators, so the code in `product/` is proven, not only compiled.
They compile the files in `product/` directly (nothing is copied), so a change there is tested here on the next build.

| Target | What | Compiles |
|---|---|---|
| `FusionSpaceSample` (iOS 26+) | Pad and Track screens inside the system's tab bar and navigation | `product/tokens/FusionSpaceColors.swift`, `product/mobile/swiftui/FSComponents.swift`, `FSFlightActivity.swift` |
| `FusionSpaceWidgets` (iOS widget extension) | The flight's Live Activity and Window's wind widget | the above plus `FSWindWidget.swift` |
| `FusionSpaceSampleWatch` (watchOS 26+, watch only) | Find, Find in Always On, Pad and Unfired | the above plus `product/watch/swiftui/FSWatch.swift` |
| `FusionSpaceWatchWidgets` (watchOS widget extension) | Find on every complication family | the above plus `FSWatchComplications.swift` |
| `FusionSpaceSampleUITests`, `FusionSpaceSampleWatchUITests` | Apple's accessibility audit (`performAccessibilityAudit`) on Pad and Track, and on Find, Pad and Unfired at the default size, xxxLarge, Accessibility 1 and 3; `LockScreenTests` locks the iPhone (the fallback for the Lock Screen capture); `WatchFaceTests` dims a watch to Always On and raises it again | |

The apps also use the FusionSpace SF Symbols (`product/icons/sf-symbols/`) in the tab bar and the status chips, and the kit's
app icon (`kit/apps/ios/AppIcon-1024.png`, put in an asset catalog under `build-info/` by `tools/app-icon.sh` when XcodeGen
runs).

Fonts come from `type/fonts/` (SIL OFL).

## Build and run

```
brew install xcodegen          # or the release binary from github.com/yonaskolb/XcodeGen
cd source/product/samples/apple
xcodegen generate              # writes FusionSpaceSample.xcodeproj (not committed)
open FusionSpaceSample.xcodeproj
```

The audits (they fail on any issue Apple's audit reports, except the ones explained in the test files):

```
xcodebuild test -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleUITests -destination 'platform=iOS Simulator,name=iPhone 17 Pro'
xcodebuild test -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleWatchUITests -destination 'platform=watchOS Simulator,name=Apple Watch SE 3 (40mm)'
```

Large text: `xcrun simctl ui <iphone> content_size accessibility-extra-extra-extra-large` (and `extra-extra-extra-large`), then
launch as below. simctl can't set a watch's text size; the watch's own setting is in its Settings app (Display & Brightness ›
Text Size, reachable through Device Hub), and the watch app takes `-typesize` with any size: `xs` … `xxxl`, `ax1` … `ax5`.
Measured with the watch's own setting (October 7, 2026): the default is Large on the 40 mm SE and xLarge on the 49 mm Ultra;
the largest setting is Accessibility 1 on the 40 mm and Accessibility 3 on the Ultra, each pixel for pixel the same as the
app's `-typesize`; Accessibility 4 and 5 draw as 3. Accessibility (Larger Text) is greyed out on a watch simulator with no
paired iPhone.

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

The Lock Screen (only a locked iPhone shows the Live Activity there): Device Hub's power button locks and wakes it
(`tools/capture/lock.sh`, below). Without Device Hub, `LockScreenTests` does it: it starts the activity, presses the lock
button through `XCUIDevice`, wakes the screen, allows Live Activities if iOS asks, and holds the Lock Screen for
`TEST_RUNNER_FS_HOLD` seconds, while `simctl io screenshot` captures it:

```
TEST_RUNNER_FS_HOLD=40 xcodebuild test -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleUITests \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -only-testing:FusionSpaceSampleUITests/LockScreenTests/testFlight &
sleep 75; xcrun simctl io <iphone> screenshot --mask=alpha lock.png    # once the test has started and locked
```

Now and then the card is missing from the Lock Screen (SpringBoard logs `sceneNotReady` for the activity's snapshot):
run it again.

## Captures, through Device Hub

Xcode 27 has no Simulator.app: its simulators run in **Device Hub**, which Xcode's MCP tools drive (taps, long presses,
swipes, the power and Home buttons, the watch's crown, and the element tree of what's on screen). `tools/capture/` holds
the scripts that made the captures in `source/product/devices/apple/` (Xcode 27.0, iOS 27.0 and watchOS 27.0 simulators
named "FS iPhone 17 Pro", "FS Ultra 4" and "FS SE 3 40", or Apple's default names); `devices.json` there says which is which.

```
cd tools/capture
python3 devicehub.py &          # one lasting connection to Xcode's MCP tools (xcrun mcpbridge), for ds and xc.py
CLOCK=9:41 ./build.sh           # XcodeGen, build both apps with the capture clock, install on the three simulators
./app.sh                        # Pad and Track, opened from the Home Screen icon (no "◂ Calendar" back-link)
./home.sh                       # the wind widgets on the Home Screen, dark and light
./lock.sh                       # the Live Activity on the Lock Screen, locked and woken with the power button
./watch.sh                      # Find, Find in Always On, Pad, Unfired on both watches, with their element trees
./face.sh ultra; AT_SECOND=27 ./face.sh se40      # a watch face with our complications, awake and in Always On
python3 keep.py ios-pad.png app # copy one into source/product/devices/apple, with its row and its element frames
```

Captures land in `build/captures/` (not committed) with the element tree Device Hub returned (`*.tree.txt`); `keep.py`
records our elements' frames in `elements.json`, and the build tests each one against the screen's outline and reads every
capture back with text recognition for "…" (`tools/build/kit_clip.py`, `check_captures`). One-time setup by hand through
`ds` (or Device Hub's window): the widgets on page 2 of the Home Screen (long-press, Edit, Add Widget, FusionSpace, the
medium size, then the small one), and a face with complication slots on each watch (long-press the face, swipe to New,
Modular Ultra on the Ultra and Infograph on the SE, Edit, the complications page, FusionSpace › Find the rocket in each
slot, the crown to scroll the list).

- **The capture clock.** simctl draws 9:41 in the iPhone's status bar and on its Lock Screen, but the widget and the Live
  Activity format times from the real clock ("measured 6:03 AM", "your pad time, 11:15 PM"). Built with `CLOCK=9:41`
  (`FS_CAPTURE_CLOCK`, `Shared/CaptureClock.swift`), the iPhone app and its widget extension move their own time zone so
  that now reads 9:41 when they start: the widget says "9:37 AM · 4 min ago" and the pad time 9:45 AM with 3:48 to go,
  in agreement. Ages and countdowns are untouched. Not on the watch: watchOS has no status bar override, so the watch
  keeps its real clock and the app and complications agree with it.
- **No back-link.** iOS puts "◂ Settings" or "◂ Calendar" in the status bar when an app is opened from another app, which
  `simctl launch` does; `app.sh` sets the screen in the app's defaults and taps the icon instead.
- **Always On.** Device Hub has no wrist-down. `WatchFaceTests/testAlwaysOn` presses the lock button through `XCUIDevice`,
  which dims the watch; `testWake` raises it again (until then every app on that watch draws in Always On).
- **Sessions.** A UI test run ends Device Hub's sessions; `ds` opens a new one when that happens.

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

## What Device Hub found (October 7, 2026, later)

Putting the parts where a person meets them, and reading the element tree, found what the earlier runs couldn't:

- **On a real watch face:** the bearing arrow, drawn with fixed offsets for the app's 48 to 104 pt sizes, put its tip past
  the centre at a complication's 22 pt and drew a blob at the corner's 36 pt (every length is now a share of the radius,
  and below 44 pt the ticks go); the complication's age was a string made once per timeline entry, so it would still say
  "4 s" a minute later and in Always On (now a relative date that counts up, plus an entry at the stale limit); the circle
  and the corner showed no sign of a stale fix (now an outlined arrow, a muted number, "Stale ·"); the corner label with
  "Stale ·" was cut by the face to "STALE · 1,352 F…", and a 5-digit distance to "12,3…" in the circle (the label drops the
  bearing when stale, and the circle shows the first of 12,345 / 12345 / 12.3k that fits).
- **At the watch's own largest text size:** Unfired's title was cut to "UNFIRED 2 ·…" on the 40 mm (the tight layout put
  the channel on the title's line without checking its width). Apple's audit passed it; the build's text recognition is
  what catches it now.
- **The medium widget** left its right half empty: the mock-up's ceiling and winds aloft were never written in SwiftUI. They
  are now, the winds aloft marked stale with `FSHatch`, whose Canvas drew past its frame across the widget until clipped.
- **The element tree:** the Pad's "Arm with a confirmation instead" had a 20 pt tall target (its 44 pt frame sat outside
  the button) and did nothing (now a 44 pt row that opens a confirmation); each Pad and watch channel row was three stops
  for VoiceOver ("SWITCH", "ON", "On") and is one now; `CONT` was spoken "Cont" (`FSStatus` takes `spoken:`); the state box
  read "SAFE" like the SAFE button beside it ("Device state, safe"); the watch's Find hid its arrow from VoiceOver without
  saying which way to turn (now "42 degrees to your right"); Unfired read its message twice; the Live Activity read "ft AGL"
  and "062° T" as letters.

## What large text and the audits found (October 7, 2026)

- At Accessibility XXXL the Pad's fixed arming panel left no room for anything else, "COMMANDED" broke mid-word, chips
  truncated to "…", the phase strip abbreviated to "BOO…", and "612" broke across two lines. The components now adapt
  (chips wrap between words, numbers never break, labels go above values, the phase strip says "MAIN · 6 of 7"), and from
  xxxLarge the Pad's controls scroll with the content, SAFE under Hold to arm.
- A number and its unit wrapped apart ("0.3 / s ago"): ages and the sample's strings use a non-breaking space.
- The audit: upcoming phases in the faint ink failed contrast (now muted); a synthesized semibold on Cascadia Mono
  (`.weight(.semibold)` on a custom font) was replaced by the real SemiBold face (`FS.labelStrong()`); a lone "0.3 s" on the
  watch wasn't a readable label (now "FS-VEGA-004, link 0.3 s").
- On watchOS, "CONT" broke into "CO / NT" at large text: a state word is never split now, and channel rows stack.
- SF Symbols: Xcode ignored the transform on the symbol group (icons came out tiny), the icons were drawn at half an SF
  Symbol's size, and with only the medium scale a symbol asked for small drew nothing. `tools/build/kit_symbols.py` fixes
  all three.
- The Lock Screen (October 7): the Live Activity runs clean at the edges, but its two readouts' labels sat at different
  heights (ALTITUDE under FROM YOU, aligned by their last lines); they are top-aligned now. "T+62 s", "612 ft", "062° T"
  and the wind widget's "mph" now keep their number and unit together with a non-breaking space.
