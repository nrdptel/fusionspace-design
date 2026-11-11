#!/bin/zsh
# SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
# iPhone: the Live Activity in the Dynamic Island (compact), over Settings, opened from its Home Screen icon so the status
# bar has no back-link. Build with CLOCK=9:41: the countdown and the 9:41 clock agree. ACTS="pad flight".
source ${0:A:h}/env.sh; export DS_DEV=$P DS_SESS="FS iPhone"
xcrun simctl ui $P appearance light; sleep 3
xcrun simctl status_bar $P override --time 9:41 --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3
for act in ${=ACTS:-pad flight}; do
  ds "b h" >/dev/null
  pkill -f FusionSpaceWidgets.appex; xcrun simctl terminate $P co.fusionspace.sample 2>/dev/null; xcrun simctl terminate $P com.apple.Preferences 2>/dev/null
  while [[ $(date +%S) != 01 ]]; do sleep 0.3; done                   # the extension's clock reads 9:41 for the next minute
  xcrun simctl launch $P co.fusionspace.sample -screen pad -activity $act >/dev/null; sleep 5
  ds "b h" >/dev/null; sleep 1; ds "b h" >/dev/null; sleep 1           # page 1, where Settings is
  hp=$(grep "identifier: 'Settings', label: 'Settings'," $OUT/last-tree.txt | sed -E 's/.*hitPoint: \{([0-9.]+), ([0-9.]+)\}.*/\1 \2/' | head -1)
  [[ -z $hp ]] && { echo "no Settings icon"; continue; }
  ds "t $hp" >/dev/null; sleep 4; ds "" >/dev/null
  xcrun simctl io $P screenshot --mask=alpha $OUT/ios-island-$act.png >/dev/null 2>&1 && echo "captured ios-island-$act"
  cp $OUT/last-tree.txt $OUT/ios-island-$act.tree.txt
done
ds "b h" >/dev/null
xcrun simctl launch $P co.fusionspace.sample -activity end >/dev/null     # end the activity
