#!/bin/zsh
# Watch app screens on both watches, with their element trees: Find, Find in Always On (forced), Pad, Unfired.
source ${0:A:h}/env.sh
for pair in "ultra:$U" "se40:$E"; do
  name=${pair%%:*}; dev=${pair#*:}
  for scr in ${=WATCH_SCREENS:-find find-aod pad unfired}; do
    xcrun simctl terminate $dev co.fusionspace.sample.watch 2>/dev/null
    xcrun simctl launch $dev co.fusionspace.sample.watch -screen $scr ${=TYPESIZE:+-typesize $TYPESIZE} >/dev/null; sleep 4
    DS_DEV=$dev DS_SESS="FS $name" ds "" >/dev/null && cp $OUT/last-tree.txt $OUT/watch-$name-$scr.tree.txt
    xcrun simctl io $dev screenshot --mask=alpha $OUT/watch-$name-$scr.png >/dev/null 2>&1 && echo "captured watch-$name-$scr"
  done
done
