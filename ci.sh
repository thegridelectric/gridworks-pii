#!/bin/bash
# Run locally everything CI runs, so a push won't go red. Usage: ./ci.sh
set -euo pipefail

step() { printf '\n=== %s ===\n' "$1"; shift; "$@"; }

step "uv sync (locked)" uv sync --all-groups --locked

step "ruff check" uv run ruff check --no-fix .
step "ruff format --check" uv run ruff format --check .
step "pyright" uv run pyright

# tests need docker (testcontainers: postgres).
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: docker is not running — the test suite uses testcontainers." >&2
  exit 1
fi
step "tests" uv run pytest -q

printf '\nAll CI checks passed.\n'
