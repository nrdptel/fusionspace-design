#!/bin/bash
# phone-captures.sh SERIAL [OUT]: Pad, Track and the Live Update in the shade on one phone emulator, the status bar set with
# SystemUI demo mode (9:41, full battery, Wi-Fi only), other apps' notifications snoozed, the camera cutout emulated (hole). OUT defaults to build/captures.
# Needs adb on PATH and the debug APK built (gradle :phone:assembleDebug). Names: phone-pad, phone-track, phone-live-update.
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
for s in pad track; do $A shell am start -n co.fusionspace.sample/.MainActivity --es screen $s >/dev/null; sleep 4; shot phone-$s; done
$A shell am start -n co.fusionspace.sample/.MainActivity --es screen live >/dev/null; sleep 3
demo notifications -e visible true; $A shell input keyevent KEYCODE_HOME; sleep 1
$A shell cmd statusbar expand-notifications; sleep 3; shot phone-live-update
$A shell cmd statusbar collapse; demo exit
