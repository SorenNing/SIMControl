#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SDK="$(xcrun --sdk iphoneos --show-sdk-path)"
mkdir -p build dist
SOURCES=(src/SIMControlModule.m src/SIMControlController.m src/SIMControlService.m src/SIMControlRow.m)
for ARCH in arm64 arm64e; do
  xcrun --sdk iphoneos clang -fobjc-arc -fblocks -O2 -fvisibility=hidden \
    -Werror=implicit-function-declaration -Werror=objc-method-access \
    -isysroot "$SDK" -target "${ARCH}-apple-ios16.0" -dynamiclib -Isrc \
    -Ftools/linker -framework Foundation -framework UIKit -framework CoreGraphics -framework QuartzCore \
    -framework CoreTelephony -Wl,-needed_framework,ControlCenterUIKit \
    -Wl,-fixup_chains -Wl,-install_name,@loader_path/SIMControl \
    "${SOURCES[@]}" -o "build/SIMControl-${ARCH}"
done
xcrun lipo -create -output build/SIMControl build/SIMControl-arm64 build/SIMControl-arm64e
xcrun codesign --force --sign - --timestamp=none build/SIMControl
# The vendored helper keeps its original signature and entitlements.
python3 tools/package.py
python3 tools/verify.py
