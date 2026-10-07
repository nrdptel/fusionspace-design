#!/bin/sh
# Run by XcodeGen before it writes the project (options.preGenCommand): puts the kit's app icon (kit/apps/ios/AppIcon-1024.png)
# in an asset catalog under build-info/ (generated, not committed), for the iPhone and the watch app.
set -e
cd "$(dirname "$0")/.."
set_dir=build-info/AppIcon.xcassets/AppIcon.appiconset
mkdir -p "$set_dir"
cp ../../../../kit/apps/ios/AppIcon-1024.png "$set_dir/AppIcon-1024.png"
printf '{ "info": { "author": "xcode", "version": 1 } }\n' > build-info/AppIcon.xcassets/Contents.json
cat > "$set_dir/Contents.json" <<'JSON'
{
  "images": [
    { "filename": "AppIcon-1024.png", "idiom": "universal", "platform": "ios", "size": "1024x1024" },
    { "filename": "AppIcon-1024.png", "idiom": "universal", "platform": "watchos", "size": "1024x1024" }
  ],
  "info": { "author": "xcode", "version": 1 }
}
JSON
