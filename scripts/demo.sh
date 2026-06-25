#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DESTINATION=${SIGNOFF_DEMO_DIR:-}
if [ -n "$DESTINATION" ]; then
  PROJECT=$(python3 "$ROOT/scripts/create_demo.py" --destination "$DESTINATION" | python3 -c 'import json,sys; print(json.load(sys.stdin)["project"])')
else
  PROJECT=$(python3 "$ROOT/scripts/create_demo.py" | python3 -c 'import json,sys; print(json.load(sys.stdin)["project"])')
fi
printf 'Demo project: %s\n' "$PROJECT"
printf 'The active slice is ready. Ask a coding agent to read AGENTS.md and run ./signoff next.\n'
printf 'Opening the local UI. Press Ctrl-C to stop it.\n\n'
exec "$PROJECT/signoff" ui "$@"
