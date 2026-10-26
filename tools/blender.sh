#!/usr/bin/env bash
# Run a project script in headless Blender.
#   tools/blender.sh assets/build/build_xiaobo.py [-- extra args]
# Override the Blender binary with:  BLENDER=/path/to/blender tools/blender.sh ...
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
SCRIPT="$1"; shift || true
exec "$BLENDER" -b --factory-startup -y --python-exit-code 1 -P "$ROOT/$SCRIPT" -- "$@"
