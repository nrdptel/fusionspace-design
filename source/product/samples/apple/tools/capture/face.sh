#!/bin/zsh
# Both watch faces with Find the rocket on them, awake and in Always On, inside one minute: AT_TIME=10:09 ./face.sh.
# Set each face up once through Device Hub (long-press the face, add one with complication slots, Edit, pick FusionSpace
# in each slot; see README). The published faces are taken at 10:09 AM, the watch convention: the hands frame the top of
# the dial and keep out of the lower subdials, and the SE's Earth subdial shows the day side.
# AT_TIME is the Mac's clock in 24-hour time (the watch shows it; watchOS has no clock override): 22:09 is 10:09 PM.
# Start it at least two minutes before; it builds the test bundle first.
#
# The complication's fix is fresh for 60 s after the watch app is installed (the extension starts again and dates its
# example fix 4 s back), so each watch reinstalls the app shortly before its awake capture, and its Always On capture
# follows inside the same minute from a pre-built test bundle (WatchFaceTests: Device Hub has no wrist-down, so the test
# presses the lock button to dim the watch, then again to raise it).
#   Ultra: installed 20 s before the minute, awake at :00, then Always On.
#   SE:    installed at :05, awake at :27 (the second hand clear of the hands and the subdials), then Always On.
source ${0:A:h}/env.sh
[[ -z $AT_TIME ]] && { echo "usage: AT_TIME=HH:MM ./face.sh"; exit 1; }
APP=$DD/Build/Products/Debug-watchsimulator/FusionSpaceSampleWatch.app
M=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) $AT_TIME:00" +%s)
cd $APPLE
xcodebuild build-for-testing -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleWatchUITests -destination "id=$U" \
  -derivedDataPath $DD-test > $OUT/face-build.log 2>&1 || { echo "the test bundle didn't build: $OUT/face-build.log"; exit 1; }
(( M - $(date +%s) < 75 )) && { echo "too close to $AT_TIME: start at least two minutes before"; exit 1; }

at() { while (( $(date +%s) < $1 )); do sleep 0.1; done; }
face() {      # bring a watch to its face: the crown goes from an app to the face, and from the face to the app grid
  DS_DEV=$1 DS_SESS="FS $2" ds "b c" >/dev/null
  grep -q com.apple.clockface $OUT/last-tree.txt || DS_DEV=$1 DS_SESS="FS $2" ds "b c" >/dev/null
  grep -q com.apple.clockface $OUT/last-tree.txt || echo "$2: not on its face"
}
t() { xcodebuild test-without-building -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleWatchUITests -destination "id=$1" \
        -derivedDataPath $DD-test -only-testing:FusionSpaceSampleWatchUITests/WatchFaceTests/$3 > $OUT/face-$2-$3.log 2>&1; }
shoot() { xcrun simctl io $1 screenshot --mask=alpha $OUT/watch-$2.png >/dev/null 2>&1 && echo "captured watch-$2 at $(date +%T)"; }
aod() {       # dim the watch, capture it, raise it again
  rm -f $OUT/face-$2-testAlwaysOn.log
  TEST_RUNNER_FS_HOLD=20 t $1 $2 testAlwaysOn &
  until grep -q "testAlwaysOn\]' started" $OUT/face-$2-testAlwaysOn.log 2>/dev/null; do sleep 0.5; done
  sleep 10; shoot $1 $2-face-aod
  (( $(date +%s) < M + 60 )) || echo "$2: Always On was captured after the minute: run it again"
  wait; t $1 $2 testWake; echo "woke $2"
}

at $(( M - 70 )); face $U ultra; face $E se40
( at $(( M - 20 )); xcrun simctl install $U $APP; at $M; shoot $U ultra-face; aod $U ultra ) &
( at $(( M + 5 )); xcrun simctl install $E $APP; at $(( M + 27 )); shoot $E se40-face; aod $E se40 ) &
wait
