# SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
# Sourced by the capture scripts: the three simulators by name, where builds and captures go, Device Hub's client.
export DEVELOPER_DIR=${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}
CAP=${0:A:h}                                             # this folder
APPLE=${CAP:h:h}                                         # source/product/samples/apple
REPO=${APPLE:h:h:h:h}
OUT=${FS_OUT:-$APPLE/build/captures}; DD=${FS_DD:-$APPLE/build/dd}; mkdir -p $OUT
udid() { for n in "$@"; do u=$(xcrun simctl list devices available | grep -F "    $n (" | head -1 | sed -E 's/.*\(([0-9A-F-]{36})\).*/\1/'); [[ -n $u ]] && { echo $u; return; }; done; }
P=$(udid "${FS_IPHONE:-FS iPhone 17 Pro}" "iPhone 17 Pro")
U=$(udid "${FS_ULTRA:-FS Ultra 4}" "Apple Watch Ultra 4 (49mm)")
E=$(udid "${FS_SE:-FS SE 3 40}" "Apple Watch SE 3 (40mm)")
ds() { $CAP/ds "$@"; }                                   # one Device Hub interaction (needs devicehub.py running)
treepoint() { grep "$1" $OUT/last-tree.txt | sed -E 's/.*hitPoint: \{([0-9.]+), ([0-9.]+)\}.*/\1 \2/' | head -1; }
