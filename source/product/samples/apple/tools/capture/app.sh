#!/bin/zsh
# iPhone: Pad (light) and Track (dark), opened from the Home Screen icon so iOS draws no "◂ <app>" back-link in the status
# bar (a launch from simctl after another app does). The screen comes from the app's defaults instead of launch arguments.
# AX5=1 captures them at the largest accessibility text size instead (ios-pad-ax5.png, ...), and the pad screen again
# scrolled to its end, where the arming controls are (ios-pad-ax5-end.png): the build reads each back for "…".
source ${0:A:h}/env.sh; export DS_DEV=$P DS_SESS="FS iPhone"
xcrun simctl status_bar $P override --time 9:41 --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3
sfx=""; [[ -n $AX5 ]] && { sfx="-ax5"; xcrun simctl ui $P content_size accessibility-extra-extra-extra-large; }
for scr in ${=IOS_SCREENS:-pad track}; do
  ap=light; [[ $scr == track ]] && ap=dark
  xcrun simctl terminate $P co.fusionspace.sample 2>/dev/null
  xcrun simctl ui $P appearance $ap; sleep 5
  xcrun simctl spawn $P defaults write co.fusionspace.sample screen $scr
  ds "b h" >/dev/null; sleep 1; ds "b h" >/dev/null; sleep 1           # page 1, then the app's page
  ds "t 340 600 f 60 600 0.25" >/dev/null; sleep 2
  hp=$(grep "identifier: 'FusionSpace', label: 'FusionSpace'," $OUT/last-tree.txt | grep -v Widget | sed -E 's/.*hitPoint: \{([0-9.]+), ([0-9.]+)\}.*/\1 \2/' | head -1)
  [[ -z $hp ]] && { echo "no icon for $scr"; continue; }
  ds "t $hp" >/dev/null; sleep 4; ds "" >/dev/null
  xcrun simctl io $P screenshot --mask=alpha $OUT/ios-$scr$sfx.png >/dev/null 2>&1 && echo "captured ios-$scr$sfx"
  cp $OUT/last-tree.txt $OUT/ios-$scr$sfx.tree.txt
  if [[ -n $AX5 && $scr == pad ]]; then
    for i in 1 2 3 4 5 6; do ds "t 200 760 f 200 160 0.3" >/dev/null; sleep 1; done; sleep 2; ds "" >/dev/null
    xcrun simctl io $P screenshot --mask=alpha $OUT/ios-$scr$sfx-end.png >/dev/null 2>&1 && echo "captured ios-$scr$sfx-end"
    cp $OUT/last-tree.txt $OUT/ios-$scr$sfx-end.tree.txt
  fi
done
xcrun simctl spawn $P defaults delete co.fusionspace.sample screen
[[ -n $AX5 ]] && xcrun simctl ui $P content_size large
