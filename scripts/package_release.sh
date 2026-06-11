#!/bin/bash
# Create a shareable macOS release zip (focus app + dashboard launcher).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FOCUS_APP="dist/AI Focus Assistant.app"
DASHBOARD_APP="macos/Open Dashboard.app"
RELEASE_DIR="release/AI-Focus-Assistant-mac"
ZIP_PATH="release/AI-Focus-Assistant-mac.zip"

if [[ ! -d "$FOCUS_APP" ]]; then
    echo "Error: $FOCUS_APP not found. Run ./scripts/build_mac_app.sh first."
    exit 1
fi

if [[ ! -d "$DASHBOARD_APP" ]]; then
    echo "Error: $DASHBOARD_APP not found."
    exit 1
fi

echo "==> Assembling release bundle"
rm -rf "$RELEASE_DIR" "$ZIP_PATH"
mkdir -p "$RELEASE_DIR"

cp -R "$FOCUS_APP" "$RELEASE_DIR/"
cp -R "$DASHBOARD_APP" "$RELEASE_DIR/"

cat > "$RELEASE_DIR/README.txt" <<'EOF'
AI Focus Assistant — macOS Release

1. Unzip this folder
2. Double-click "AI Focus Assistant.app" to start a focus session
   - Press SPACE on the home screen to begin
   - Allow camera access when macOS prompts you
3. Double-click "Open Dashboard.app" to view session history in your browser
   - Requires one-time Python setup (see GitHub repo) unless you received
     a full installer bundle with dependencies included

Session data is stored at:
  ~/Library/Application Support/AI Focus Assistant/data/sessions.csv

The focus app and dashboard are separate apps:
  - Focus app: live webcam session (standalone, no Python needed)
  - Dashboard: opens Safari/Chrome with charts (needs Python + Streamlit)
EOF

echo "==> Creating zip"
mkdir -p release
ditto -c -k --sequesterRsrc --keepParent "$RELEASE_DIR" "$ZIP_PATH"

echo
echo "Release ready: $ROOT/$ZIP_PATH"
du -sh "$FOCUS_APP" "$ZIP_PATH"
