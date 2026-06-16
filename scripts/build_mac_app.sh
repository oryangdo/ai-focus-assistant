#!/bin/bash
# Stage 9.1 — Build a standalone macOS .app with PyInstaller.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP_NAME="AI Focus Assistant"
SPEC_FILE="ai_focus_assistant.spec"
DIST_APP="dist/${APP_NAME}.app"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: this script must run on macOS."
    exit 1
fi

if [[ ! -d .venv ]]; then
    echo "Error: .venv not found. Run ./scripts/setup_mac_apps.sh first."
    exit 1
fi

PYTHON="$ROOT/.venv/bin/python"
PIP="$ROOT/.venv/bin/pip"

echo "==> Installing runtime dependencies"
"$PIP" install -r requirements.txt

echo "==> Installing build dependencies (PyInstaller)"
"$PIP" install -r requirements-dev.txt

echo "==> Staging model files for bundling"
"$PYTHON" - <<'PY'
import shutil
from pathlib import Path

from src.paths import ensure_face_landmarker_model, ensure_yolo_model

root = Path.cwd()
yolo_src = ensure_yolo_model()
yolo_dest = root / "yolov8s.pt"
if yolo_src.resolve() != yolo_dest.resolve():
    shutil.copy2(yolo_src, yolo_dest)
print(f"YOLO weights: {yolo_dest}")

face_src = ensure_face_landmarker_model()
face_dest = root / "models" / "face_landmarker.task"
face_dest.parent.mkdir(parents=True, exist_ok=True)
if face_src.resolve() != face_dest.resolve():
    shutil.copy2(face_src, face_dest)
print(f"Face model: {face_dest}")
PY

echo "==> Building ${APP_NAME}.app (may take 5–15 minutes)"
"$PYTHON" -m PyInstaller --noconfirm "$SPEC_FILE"

if [[ ! -d "$DIST_APP" ]]; then
    echo "Error: expected output not found at $DIST_APP"
    exit 1
fi

echo
echo "Build complete."
echo "  App: $ROOT/$DIST_APP"
echo
echo "Run the packaged app:"
echo "  open \"$ROOT/$DIST_APP\""
echo
echo "On first launch, allow camera access when macOS prompts you."
echo
echo "Create a GitHub Release zip:"
echo "  ./scripts/release_mac.sh"
