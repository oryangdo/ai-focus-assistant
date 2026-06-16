#!/bin/bash
# Full macOS release pipeline: build → package → verify.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SKIP_BUILD=0
SKIP_VERIFY=0

usage() {
    cat <<'EOF'
Usage: ./scripts/release_mac.sh [options]

Build AI Focus Assistant.app, package AI-Focus-Assistant-mac.zip,
and run automated verification.

Options:
  --skip-build   Package and verify an existing dist/AI Focus Assistant.app
  --skip-verify  Build and package only
  -h, --help     Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-build) SKIP_BUILD=1 ;;
        --skip-verify) SKIP_VERIFY=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
    esac
    shift
done

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: macOS release workflow must run on macOS."
    exit 1
fi

if [[ "$SKIP_BUILD" -eq 0 ]]; then
    echo "==> Step 1/3: Build"
    ./scripts/build_mac_app.sh
else
    echo "==> Step 1/3: Build (skipped)"
fi

echo "==> Step 2/3: Package"
./scripts/package_release.sh

if [[ "$SKIP_VERIFY" -eq 0 ]]; then
    echo "==> Step 3/3: Verify"
    ./scripts/verify_release.sh
else
    echo "==> Step 3/3: Verify (skipped)"
fi

echo
echo "Release workflow complete."
echo "  Zip: release/AI-Focus-Assistant-mac.zip"
echo "  Next: upload the zip to GitHub Releases (not committed to git)."
