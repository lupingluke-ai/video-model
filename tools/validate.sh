#!/usr/bin/env bash
# Validate a built asset against its contract.
#   tools/validate.sh assets/xiaobo.blend contracts/xiaobo.json [--no-render]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
BLEND="$1"; CONTRACT="$2"; shift 2
exec "$BLENDER" -b --factory-startup -y "$ROOT/$BLEND" --python-exit-code 1 \
  -P "$ROOT/tools/validate_asset.py" -- --contract "$CONTRACT" "$@"
