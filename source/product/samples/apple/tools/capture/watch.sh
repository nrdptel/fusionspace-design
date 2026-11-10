#!/bin/zsh
# Watch app screens on both watches, with their element trees: Find, Find in Always On (forced), Pad, Unfired.
# LARGEST=1 captures them at the largest text size each watch reaches instead (Accessibility 3 on the 49 mm Ultra,
# Accessibility 1 on the 40 mm SE; see the README), as watch-ultra-pad-ax3.png and so on: the build reads each back for "…".
source ${0:A:h}/env.sh
for pair in "ultra:${U}:ax3" "se40:${E}:ax1"; do
  name=${pair%%:*}; rest=${pair#*:}; dev=${rest%%:*}; largest=${rest#*:}
  ts=${TYPESIZE:-}; sfx=""; [[ -n $LARGEST ]] && { ts=$largest; sfx="-$largest"; }
  for scr in ${=WATCH_SCREENS:-find find-aod pad unfired}; do
    xcrun simctl terminate $dev co.fusionspace.sample.watch 2>/dev/null
    xcrun simctl launch $dev co.fusionspace.sample.watch -screen $scr ${=ts:+-typesize $ts} >/dev/null; sleep 4
    DS_DEV=$dev DS_SESS="FS $name" ds "" >/dev/null && cp $OUT/last-tree.txt $OUT/watch-$name-$scr$sfx.tree.txt
    xcrun simctl io $dev screenshot --mask=alpha $OUT/watch-$name-$scr$sfx.png >/dev/null 2>&1 && echo "captured watch-$name-$scr$sfx"
  done
done
