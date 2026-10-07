#!/bin/zsh
# iPhone Lock Screen with the Live Activity, locked and woken with the power button through Device Hub (UITests/
# LockScreenTests is the scripted fallback). Build with CLOCK=9:41: the widget extension restarts here so the pad time
# agrees with the 9:41 clock. ACTS="pad flight".
source ${0:A:h}/env.sh; export DS_DEV=$P DS_SESS="FS iPhone"
xcrun simctl ui $P appearance ${APPEAR:-dark}; sleep 4
xcrun simctl status_bar $P override --time 9:41 --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3
for act in ${=ACTS:-pad flight}; do
  ds "b h" >/dev/null
  pkill -f FusionSpaceWidgets.appex; xcrun simctl terminate $P co.fusionspace.sample 2>/dev/null
  # start at the top of a minute: the extension's clock reads 9:41 for the next 60 s, which the 40 s wait below fits in, so
  # the countdown, the pad time and the 9:41 clock agree
  while [[ $(date +%S) != 01 ]]; do sleep 0.3; done
  xcrun simctl launch $P co.fusionspace.sample -screen pad -activity $act >/dev/null; sleep 5
  ds "b p" >/dev/null; sleep 2; ds "b p" >/dev/null                       # lock, then wake: the Lock Screen
  hp=$(grep "label: 'Allow'" $OUT/last-tree.txt | sed -E 's/.*hitPoint: \{([0-9.]+), ([0-9.]+)\}.*/\1 \2/' | head -1)
  [[ -n $hp ]] && ds "t $hp" >/dev/null                                   # "Allow Live Activities from FusionSpace?"
  sleep 40; ds "" >/dev/null                                              # the Control Center hint at the top fades
  grep -q "FLIGHT 04" $OUT/last-tree.txt || { echo "no card for $act (run it again)"; continue; }
  xcrun simctl io $P screenshot --mask=alpha $OUT/ios-lock-$act.png >/dev/null 2>&1 && echo "captured ios-lock-$act"
  cp $OUT/last-tree.txt $OUT/ios-lock-$act.tree.txt
done
ds "b p" >/dev/null; ds "b h w 0.5 b h" >/dev/null                       # unlock
xcrun simctl launch $P co.fusionspace.sample -activity end >/dev/null     # and end the activity
