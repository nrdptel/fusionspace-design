#!/bin/bash
# setup.sh: the Android SDK packages and emulators the sample was run on, into $ANDROID_HOME (and $ANDROID_AVD_HOME, or
# ~/.android/avd). Needs the command-line tools in $ANDROID_HOME/cmdline-tools/latest and JDK 21. About 12 GB.
#   fs_pixel10       Pixel 10 profile, Android 17 (API 37.0, Google APIs)      the phone captures and tests
#   fs_pixel10_a16   Pixel 10 profile, Android 16 QPR2 (API 36.1, Google APIs) ProgressStyle Live Update, promoted
#   fs_pixel10_a36   Pixel 10 profile, Android 16 (API 36.0, AOSP default)    the 36.0 branch; not promoted there
#   fs_wear_large    Wear OS large round, Wear OS 7 (API 37.0)                 the watch captures and tests
#   fs_wear_small    Wear OS small round, Wear OS 7 (API 37.0)                 the small-watch checks
set -e
: "${ANDROID_HOME:?set ANDROID_HOME}"
SM=$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager; AM=$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager
P37="system-images;android-37.0;google_apis;arm64-v8a"; P361="system-images;android-36.1;google_apis;arm64-v8a"
P36="system-images;android-36;default;arm64-v8a"; W37="system-images;android-37.0;android-wear-signed;arm64-v8a"
[ "$(uname -m)" = arm64 ] || { P37=${P37/arm64-v8a/x86_64}; P361=${P361/arm64-v8a/x86_64}; P36=${P36/arm64-v8a/x86_64}; W37=${W37/arm64-v8a/x86_64}; }
yes | $SM --licenses >/dev/null || true
$SM "platform-tools" "emulator" "platforms;android-37.0" "build-tools;37.0.0" "$P37" "$P361" "$P36" "$W37"
avd() { [ -n "$($AM list avd -c | grep -x "$1")" ] || echo no | $AM create avd -n "$1" -k "$2" -d "$3"; }
avd fs_pixel10 "$P37" pixel_10
avd fs_pixel10_a16 "$P361" pixel_10
avd fs_pixel10_a36 "$P36" pixel_10
avd fs_wear_large "$W37" wearos_large_round
avd fs_wear_small "$W37" wearos_small_round
echo "emulators: $($AM list avd -c | tr '\n' ' ')"
echo "run one: emulator -avd fs_pixel10 -no-snapshot   (add -no-window to run headless)"
