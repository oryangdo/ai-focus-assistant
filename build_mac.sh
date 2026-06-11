#!/bin/bash
# Convenience wrapper — see scripts/build_mac_app.sh
exec "$(cd "$(dirname "$0")" && pwd)/scripts/build_mac_app.sh" "$@"
