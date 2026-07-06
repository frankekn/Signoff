#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET=${1:-}

fail() {
  printf '%s\n' "Traction install: $*" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "Git is required."
command -v python3 >/dev/null 2>&1 || fail "Python 3.10+ is required."

python3 - <<'PY' || exit 1
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Traction requires Python 3.10 or newer")
print(f"Python {sys.version_info.major}.{sys.version_info.minor}: OK")
PY

chmod +x "$ROOT/traction"

if [ -n "$TARGET" ]; then
  TARGET=$(CDPATH= cd -- "$TARGET" && pwd)
  "$ROOT/traction" --project "$TARGET" install
  printf '\nInstalled into %s\n' "$TARGET"
  printf 'Next: cd %s && ./traction ui\n' "$TARGET"
  exit 0
fi

[ -f "$ROOT/src/traction/web_dist/index.html" ] || fail "Prebuilt UI assets are missing. Run npm ci && npm run build:web."
"$ROOT/traction" --version
python3 "$ROOT/scripts/check_repo.py"
printf '\nTraction is ready.\n'
printf 'Run: ./traction ui\n'
printf 'Demo: ./scripts/demo.sh\n'
printf 'Install into another repository: ./install.sh /path/to/repository\n'
