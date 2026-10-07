#!/bin/zsh
# Generates the project (XcodeGen), builds the iPhone and watch apps for the simulator, installs them on the three simulators.
# CLOCK=9:41 builds the capture clock in (Shared/CaptureClock.swift): the iPhone's clock times agree with simctl's 9:41.
# Build the reference outputs first (python tools/build/build.py, or kit_mobile/kit_watch.build_code), since the apps
# compile product/ in place.
source ${0:A:h}/env.sh
cd $APPLE && ${XCODEGEN:-xcodegen} generate -q || exit 1
for scheme in FusionSpaceSample FusionSpaceSampleWatch; do
  dest='generic/platform=iOS Simulator'; [[ $scheme == *Watch ]] && dest='generic/platform=watchOS Simulator'
  xcodebuild -project FusionSpaceSample.xcodeproj -scheme $scheme -destination "$dest" -derivedDataPath $DD \
    FS_CAPTURE_CLOCK=${CLOCK:-} build 2>&1 | grep -E "error:|BUILD (SUCCEEDED|FAILED)" | sort -u
done
xcrun simctl install $P $DD/Build/Products/Debug-iphonesimulator/FusionSpaceSample.app
for d in $U $E; do xcrun simctl install $d $DD/Build/Products/Debug-watchsimulator/FusionSpaceSampleWatch.app; done
echo installed
