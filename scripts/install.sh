#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
cd "$ROOT"
python3 -m pip install -e "$ROOT" >/dev/null
exec grokbots install --hermes-home "$HERMES_HOME" "$@"
