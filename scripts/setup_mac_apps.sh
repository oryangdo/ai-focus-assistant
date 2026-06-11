#!/bin/bash
# One-time setup for double-click macOS apps in macos/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Setting up AI Focus Assistant for desktop use"

if [[ ! -d .venv ]]; then
    echo "==> Creating virtual environment"
    python3 -m venv .venv
fi

echo "==> Installing dependencies"
.venv/bin/pip install -r requirements.txt

chmod +x "macos/AI Focus Assistant.app/Contents/MacOS/launcher"
chmod +x "macos/Open Dashboard.app/Contents/MacOS/launcher"

echo
echo "Setup complete."
echo
echo "Double-click these apps (no Terminal needed for normal use):"
echo "  $ROOT/macos/AI Focus Assistant.app"
echo "  $ROOT/macos/Open Dashboard.app"
echo
echo "Tip: drag both apps to your Dock or Desktop for quick access."
echo "Session data is saved to:"
echo "  ~/Library/Application Support/AI Focus Assistant/data/sessions.csv"
