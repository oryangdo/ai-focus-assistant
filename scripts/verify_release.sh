#!/bin/bash
# Verify the macOS release zip: structure, launch, and session CSV write.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP_NAME="AI Focus Assistant"
ZIP_PATH="release/AI-Focus-Assistant-mac.zip"
FOCUS_APP_NAME="${APP_NAME}.app"
EXEC_NAME="$APP_NAME"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: this script must run on macOS."
    exit 1
fi

if [[ ! -f "$ZIP_PATH" ]]; then
    echo "Error: $ZIP_PATH not found. Run ./scripts/package_release.sh first."
    exit 1
fi

VERIFY_DIR="$(mktemp -d /tmp/ai-focus-assistant-verify.XXXXXX)"
cleanup() {
    if pgrep -f "$EXEC_NAME" >/dev/null 2>&1; then
        pkill -f "$EXEC_NAME" >/dev/null 2>&1 || true
        sleep 1
    fi
    rm -rf "$VERIFY_DIR"
}
trap cleanup EXIT

pass() { echo "  ✓ $1"; }
fail() { echo "  ✗ $1" >&2; exit 1; }

echo "==> Verifying $ZIP_PATH"
echo "    Temp dir: $VERIFY_DIR"

echo "==> Checking zip contents"
ZIP_LIST="$(unzip -Z1 "$ZIP_PATH")"
[[ "$ZIP_LIST" == *"AI-Focus-Assistant-mac/README.txt"* ]] || fail "README.txt missing from zip"
[[ "$ZIP_LIST" == *"AI-Focus-Assistant-mac/${FOCUS_APP_NAME}/"* ]] || fail "${FOCUS_APP_NAME} missing from zip"
if [[ "$ZIP_LIST" == *"Open Dashboard.app"* ]]; then
    fail "zip must not include Open Dashboard.app (not self-contained)"
fi
pass "zip contains README.txt and ${FOCUS_APP_NAME} only"

echo "==> Extracting zip"
unzip -q "$ZIP_PATH" -d "$VERIFY_DIR"

APP_PATH="$(find "$VERIFY_DIR" -name "$FOCUS_APP_NAME" -maxdepth 3 -type d | head -n 1)"
[[ -n "$APP_PATH" ]] || fail "could not locate ${FOCUS_APP_NAME} after unzip"

BIN_PATH="$APP_PATH/Contents/MacOS/$EXEC_NAME"
[[ -x "$BIN_PATH" ]] || fail "executable not found at $BIN_PATH"
pass "app bundle structure looks valid"

echo "==> Verifying session save (packaged smoke test)"
if ! "$BIN_PATH" --packaged-smoke-test; then
    fail "packaged smoke test failed (session CSV write)"
fi
pass "session data saves from packaged binary"

echo "==> Verifying app launch"
open -n "$APP_PATH"
LAUNCHED=0
for _ in $(seq 1 20); do
    if pgrep -f "$EXEC_NAME" >/dev/null 2>&1; then
        LAUNCHED=1
        break
    fi
    sleep 0.5
done

if [[ "$LAUNCHED" -ne 1 ]]; then
    fail "app did not start after open (check Gatekeeper or camera permissions)"
fi
pass "app launched successfully from unzipped bundle"

pkill -f "$EXEC_NAME" >/dev/null 2>&1 || true
sleep 1

echo
echo "All release checks passed."
echo "Manual check recommended: unzip on a clean Mac, right-click → Open if"
echo "Gatekeeper blocks the app, press SPACE to start a real focus session."
