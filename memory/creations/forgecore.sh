#!/bin/bash
# ForgeCore Quick Wrapper
# Drop this in your project root for quick access

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGECORE_PY="${SCRIPT_DIR}/forgecore_cli.py"

# Check if Python script exists
if [[ ! -f "$FORGECORE_PY" ]]; then
    echo "❌ forgecore_cli.py not found at $FORGECORE_PY"
    exit 1
fi

# Run the Python script with all arguments
exec python3 "$FORGECORE_PY" "$@"
