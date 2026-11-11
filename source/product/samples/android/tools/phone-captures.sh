#!/bin/bash
# phone-captures.sh SERIAL [OUT]: Pad, Track and the Live Update in the shade on one phone emulator, the status bar set with
# SystemUI demo mode (9:41, full battery, Wi-Fi only), other apps' notifications snoozed, the camera cutout emulated (hole). OUT defaults to build/captures.
# Needs adb on PATH and the debug APK built (gradle :phone:assembleDebug). Names: phone-pad, phone-track, phone-live-update.
# FS200=1 captures Pad and Track at font scale 2.0 instead, the largest Android offers, and Pad again scrolled to its end
# (phone-pad-fs200.png, phone-pad-fs200-end.png, phone-track-fs200.png): the build reads each back for "…".
set -e
S=$1; OUT=${2:-$(dirname "$0")/../build/captures}; A="adb -s $S"; mkdir -p "$OUT"
$A install -r "$(dirname "$0")/../phone/build/outputs/apk/debug/phone-debug.apk" >/dev/null
$A shell pm grant co.fusionspace.sample android.permission.POST_NOTIFICATIONS
$A shell cmd overlay enable com.android.internal.display.cutout.emulation.hole 2>/dev/null || true
$A shell settings put system screen_off_timeout 1800000
demo() { $A shell am broadcast -a com.android.systemui.demo -e command "$@" >/dev/null; }
$A shell settings put global sysui_demo_allowed 1
demo enter; demo clock -e hhmm 0941; demo battery -e level 100 -e plugged false
demo network -e wifi show -e level 4 -e fully true; demo network -e mobile hide; demo notifications -e visible false
# the emulator's own notifications ("Set a screen lock", "Serial console enabled") are snoozed for an hour, out of the shade
for k in $($A shell cmd notification list | tr -d '\r' | grep -v co.fusionspace); do $A shell "cmd notification snooze --for 3600000 '$k'" >/dev/null 2>&1 || true; done
shot() { $A exec-out screencap -p > "$OUT/$1.png"; echo "$OUT/$1.png"; }
$A shell input keyevent KEYCODE_WAKEUP; $A shell wm dismiss-keyguard
$A shell am force-stop co.fusionspace.sample
if [ -n "$FS200" ]; then
  $A shell settings put system font_scale 2.0; sleep 2
  for s in pad track; do $A shell am start -n co.fusionspace.sample/.MainActivity --es screen $s >/dev/null; sleep 4; shot phone-$s-fs200; done
  $A shell am force-stop co.fusionspace.sample; $A shell am start -n co.fusionspace.sample/.MainActivity --es screen pad >/dev/null; sleep 4
  for i in 1 2 3 4 5 6; do $A shell input swipe 540 1900 540 500 300; sleep 1; done; sleep 2; shot phone-pad-fs200-end
  $A shell settings put system font_scale 1.0; $A shell am force-stop co.fusionspace.sample; demo exit; exit 0
fi
for s in pad track; do $A shell am start -n co.fusionspace.sample/.MainActivity --es screen $s >/dev/null; sleep 4; shot phone-$s; done
$A shell am start -n co.fusionspace.sample/.MainActivity --es screen live >/dev/null; sleep 3
demo notifications -e visible true; $A shell input keyevent KEYCODE_HOME; sleep 1
$A shell cmd statusbar expand-notifications; sleep 3; shot phone-live-update
$A shell cmd statusbar collapse; demo exit
