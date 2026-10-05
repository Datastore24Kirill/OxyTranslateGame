#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Native architecture by default; pass --arch arm64 or --arch x86_64 to SwiftPM.
swift build -c release "$@"
bin_dir=$(swift build -c release --show-bin-path "$@")
app="$PWD/dist/OxyTranslateGame.app"
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
cp "$bin_dir/OxyTranslateGame" "$app/Contents/MacOS/OxyTranslateGame"
cp Resources/Info.plist "$app/Contents/Info.plist"
if [ -f Resources/AppIcon.icns ]; then cp Resources/AppIcon.icns "$app/Contents/Resources/"; fi
codesign --force --sign "${CODESIGN_IDENTITY:--}" "$app"
codesign --verify --strict "$app"
ditto -c -k --sequesterRsrc --keepParent "$app" dist/OxyTranslateGame-macOS.zip
printf 'Built: %s\n' "$app"
