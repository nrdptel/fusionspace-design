#!/bin/zsh
# iPhone Home Screen with the wind widgets, in dark and light. Put them there once, as a person would: long-press the Home
# Screen, Edit, Add Widget, FusionSpace, then the medium and the small size, on page 2 (see README). Build with CLOCK=9:41.
source ${0:A:h}/env.sh; export DS_DEV=$P DS_SESS="FS iPhone"
xcrun simctl status_bar $P override --time 9:41 --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3
xcrun simctl uninstall $P co.fusionspace.sample.uitests.xctrunner 2>/dev/null   # a test run installs it; iOS cuts its name
pkill -f FusionSpaceWidgets.appex; xcrun simctl terminate $P co.fusionspace.sample 2>/dev/null
xcrun simctl launch $P co.fusionspace.sample -activity end >/dev/null; sleep 4   # no Live Activity in the island; the extension restarts at 9:41
for ap in ${=APPEARANCES:-dark light}; do
  xcrun simctl ui $P appearance $ap; sleep 6
  ds "b h" >/dev/null; sleep 1; ds "b h" >/dev/null; sleep 1             # Home twice lands on page 1 from anywhere
  ds "t 340 600 f 60 600 0.25" >/dev/null; sleep 4; ds "" >/dev/null
  grep -q "identifier: 'FusionSpace', label: 'FusionSpace', value: Widget" $OUT/last-tree.txt || { echo "no widgets on page 2 ($ap)"; continue; }
  xcrun simctl io $P screenshot --mask=alpha $OUT/ios-home-widgets-$ap.png >/dev/null 2>&1 && echo "captured ios-home-widgets-$ap"
  cp $OUT/last-tree.txt $OUT/ios-home-widgets-$ap.tree.txt
done
