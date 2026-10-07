#!/bin/zsh
# A watch face with Find the rocket on it, awake and in Always On: face.sh ultra|se40. Set the face up once through Device
# Hub (long-press the face, add one with complication slots, Edit, pick FusionSpace in each slot; see README). Device Hub
# has no wrist-down, so UITestsWatch/WatchFaceTests presses the lock button to dim the watch, then again to raise it.
# The fix is fresh for 60 s after the app is installed: run it right after build.sh or reinstall the app.
source ${0:A:h}/env.sh; name=$1; dev=$U; [[ $name == se40 ]] && dev=$E
DS_DEV=$dev DS_SESS="FS $name" ds "b c" >/dev/null; grep -q com.apple.clockface $OUT/last-tree.txt || DS_DEV=$dev DS_SESS="FS $name" ds "b c" >/dev/null
[[ -n $AT_SECOND ]] && while [[ $(date +%S) != $AT_SECOND ]]; do sleep 0.3; done   # an analog face: keep the second hand clear
xcrun simctl io $dev screenshot --mask=alpha $OUT/watch-$name-face.png >/dev/null 2>&1 && echo "captured watch-$name-face"
cd $APPLE
t() { xcodebuild test -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleWatchUITests -destination "id=$dev" \
        -derivedDataPath $DD-test -only-testing:FusionSpaceSampleWatchUITests/WatchFaceTests/$1 > $OUT/face-$name-$1.log 2>&1; }
TEST_RUNNER_FS_HOLD=45 t testAlwaysOn &
until grep -q "testAlwaysOn\]' started" $OUT/face-$name-testAlwaysOn.log 2>/dev/null; do sleep 2; done
sleep 12; xcrun simctl io $dev screenshot --mask=alpha $OUT/watch-$name-face-aod.png >/dev/null 2>&1 && echo "captured watch-$name-face-aod"
wait; t testWake; echo "woke $name"
