#!/usr/bin/env sh
set -eu

REPO_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-}

python_ok() {
  "$1" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
}

if [ -n "$PYTHON" ]; then
  if ! command -v "$PYTHON" >/dev/null 2>&1 || ! python_ok "$PYTHON"; then
    echo "PYTHON must point to Python 3.10 or newer: $PYTHON" >&2
    exit 1
  fi
else
  for candidate in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && python_ok "$candidate"; then
      PYTHON=$candidate
      break
    fi
  done
fi

if [ -z "$PYTHON" ]; then
  echo "Python 3.10+ is required. Install Python 3.10 or newer, then rerun this script." >&2
  exit 1
fi

cd "$REPO_DIR"

if [ -x .venv/bin/python ] && ! python_ok .venv/bin/python; then
  echo "Removing incompatible .venv because it was created with Python older than 3.10." >&2
  rm -rf .venv
fi

"$PYTHON" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

asl --version

SMOKE_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/asl-deploy-smoke.XXXXXX")
asl init \
  --root "$SMOKE_ROOT" \
  --slug deploy-smoke \
  --title "Deploy Smoke Test" \
  --topic "a policy question that still needs verified evidence" \
  --brief-file examples/topic_brief.md >/dev/null
asl run "$SMOKE_ROOT/papers/deploy-smoke" --cycles 1 --offline >/dev/null
test -f "$SMOKE_ROOT/papers/deploy-smoke/v1/html/index.html"

cat <<'EOF'

Academic Sludge Line is installed in .venv and passed an offline smoke test.

Next commands:
  . .venv/bin/activate
  asl init --slug demo-policy-paper --title "Demo Policy Paper" --topic "a policy question that still needs verified evidence" --brief-file examples/topic_brief.md
  asl run papers/demo-policy-paper --cycles 1 --offline
  asl ui --open
EOF
