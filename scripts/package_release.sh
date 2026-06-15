#!/bin/bash
# Create a shareable macOS release zip for GitHub Releases (focus app only).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP_NAME="AI Focus Assistant"
FOCUS_APP="dist/${APP_NAME}.app"
RELEASE_DIR="release/AI-Focus-Assistant-mac"
ZIP_PATH="release/AI-Focus-Assistant-mac.zip"
README_TEMPLATE="scripts/release_README.txt"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: this script must run on macOS."
    exit 1
fi

if [[ ! -d "$FOCUS_APP" ]]; then
    echo "Error: $FOCUS_APP not found. Run ./scripts/build_mac_app.sh first."
    exit 1
fi

if [[ ! -f "$README_TEMPLATE" ]]; then
    echo "Error: $README_TEMPLATE not found."
    exit 1
fi

echo "==> Assembling release bundle (focus app only)"
rm -rf "$RELEASE_DIR" "$ZIP_PATH"
mkdir -p "$RELEASE_DIR"

# Avoid AppleDouble (__MACOSX) metadata in the release zip.
export COPYFILE_DISABLE=1
cp -R "$FOCUS_APP" "$RELEASE_DIR/"
cp "$README_TEMPLATE" "$RELEASE_DIR/README.txt"

echo "==> Creating zip"
mkdir -p release
ditto -c -k --sequesterRsrc --keepParent "$RELEASE_DIR" "$ZIP_PATH"

echo
echo "Release ready: $ROOT/$ZIP_PATH"
echo "Contents:"
echo "  AI-Focus-Assistant-mac/README.txt"
echo "  AI-Focus-Assistant-mac/${APP_NAME}.app"
echo
du -sh "$FOCUS_APP" "$ZIP_PATH"
echo
echo "Upload $ZIP_PATH to GitHub Releases."
echo "Run ./scripts/verify_release.sh to smoke-test the bundle."
