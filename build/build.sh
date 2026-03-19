#!/usr/bin/env bash
# Build the submit binary for Linux x86_64.
#
# Run this on a Linux machine (Codespace, CI, Docker container).
# Output: ./submit (Linux ELF binary at repo root)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Building submit binary ==="

# Install PyInstaller if not present
pip install --quiet pyinstaller

# Build single-file binary
pyinstaller \
    --onefile \
    --name submit \
    --strip \
    --clean \
    --distpath "$REPO_ROOT" \
    --workpath "$REPO_ROOT/build/pyinstaller-work" \
    --specpath "$REPO_ROOT/build" \
    "$REPO_ROOT/src/submit.py"

# Cleanup build artifacts
rm -rf "$REPO_ROOT/build/pyinstaller-work" "$REPO_ROOT/build/submit.spec"

chmod +x "$REPO_ROOT/submit"

echo ""
echo "=== Build complete ==="
file "$REPO_ROOT/submit"
ls -lh "$REPO_ROOT/submit"
