#!/bin/bash
# wear-captures.sh SERIAL PREFIX [OUT]: Find, Find in ambient, Pad, Unfired and the Find tile on one Wear OS emulator, at
# 9:41 on the watch's clock, the fix taken at 9:41:00 (so ambient says "as of 9:41" and awake "fix 4.x s ago").
# PREFIX is "wear" (large round) or "wear-small"; OUT defaults to build/captures. Needs adb on PATH and the debug APK built
# (gradle :wear:assembleDebug). The watch's own clock is set (auto time off), not drawn: Wear OS has no status bar override.
set -e
W=$1; P=$2; OUT=${3:-$(dirname "$0")/../build/captures}
A="adb -s $W"; mkdir -p "$OUT"
$A install -r "$(dirname "$0")/../wear/build/outputs/apk/debug/wear-debug.apk" >/dev/null
$A shell settings put system screen_off_timeout 1800000
$A shell settings put global auto_time 0
T=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 09:41:00" +%s)000
at941() { $A shell cmd alarm set-time $T; }
wake() { $A shell input keyevent KEYCODE_WAKEUP; sleep 1; }
open() { at941; $A shell am start -n co.fusionspace.sample.wear/.MainActivity --es screen $1 --el fixed $T >/dev/null 2>&1; sleep 4; }
shot() { $A exec-out screencap -p > "$OUT/$P-$1.png"; echo "$OUT/$P-$1.png"; }
$A shell am force-stop co.fusionspace.sample.wear
for s in find pad unfired; do wake; open $s; shot $s; done
wake; open find; $A shell input keyevent KEYCODE_SLEEP; sleep 4; shot find-ambient
wake; at941
$A shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE --es operation add-tile --ecn component co.fusionspace.sample.wear/.FindTileService >/dev/null
$A shell am broadcast -a com.google.android.wearable.app.DEBUG_SYSUI --es operation show-tile --ei index 0 >/dev/null; sleep 4
shot tile-find
$A shell input keyevent KEYCODE_BACK; wake
$A shell settings put global auto_time 1
