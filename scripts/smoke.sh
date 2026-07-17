#!/usr/bin/env bash
# Smoke test for autoresearch-mlx.
#
# Verifies a checkout without downloading data or spending the 5-minute
# training budget: prints the resolved environment, byte-compiles every
# module, imports the full dependency chain (including MLX) via the
# prepare.py CLI, exercises config.py and all three bench.py subcommands,
# and runs the pytest suite.
#
# Usage: bash scripts/smoke.sh   (or: make smoke)
set -euo pipefail
cd "$(dirname "$0")/.."

if command -v uv >/dev/null 2>&1; then
    PY=(uv run python)
    PYTEST=(uv run pytest)
else
    PY=(python3)
    PYTEST=(python3 -m pytest)
fi

echo "== environment =="
"${PY[@]}" - <<'EOF'
import importlib.metadata as im
import platform

print("python", platform.python_version())
for pkg in ("mlx", "numpy", "polars", "pyarrow", "tiktoken", "rustbpe"):
    print(pkg, im.version(pkg))
EOF

echo "== byte-compile all modules =="
"${PY[@]}" -m py_compile train.py prepare.py bench.py config.py tests/test_smoke.py

echo "== import chain incl. mlx (prepare.py --help) =="
"${PY[@]}" prepare.py --help >/dev/null

echo "== config extraction (config.py) =="
"${PY[@]}" config.py >/dev/null

echo "== bench.py subcommands =="
for cmd in summary latest best; do
    "${PY[@]}" bench.py "$cmd" >/dev/null
done

echo "== pytest =="
"${PYTEST[@]}" tests/ -q

echo "smoke: all checks passed"
