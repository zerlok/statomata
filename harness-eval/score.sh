#!/usr/bin/env bash
# Score a harness run: objective gates + diff stats.
# Usage: ./harness-eval/score.sh <worktree-path> <run-id>
# Writes harness-eval/results/<run-id>.md (appends objective results to the rubric template).
set -u

WORKTREE="${1:?usage: score.sh <worktree-path> <run-id>}"
RUN_ID="${2:?usage: score.sh <worktree-path> <run-id>}"
EVAL_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$EVAL_DIR/results/$RUN_ID.md"

cd "$WORKTREE" || exit 1

BASE=$(git merge-base HEAD main 2>/dev/null || git merge-base HEAD origin/main 2>/dev/null || true)
if [ -z "$BASE" ]; then
  echo "score.sh: could not determine merge-base with main/origin-main in $WORKTREE" >&2
  exit 1
fi

run_check() { # name, command...
  local name="$1"; shift
  local log
  log=$("$@" 2>&1)
  local code=$?
  if [ $code -eq 0 ]; then
    echo "| $name | PASS |" >>"$OUT"
  else
    echo "| $name | **FAIL** (exit $code) |" >>"$OUT"
    {
      echo "<details><summary>$name output</summary>"
      echo
      echo '```'
      echo "$log" | tail -40
      echo '```'
      echo "</details>"
      echo
    } >>"$FAIL_DETAILS"
  fi
}

FAIL_DETAILS=$(mktemp)

cp "$EVAL_DIR/results/TEMPLATE.md" "$OUT"
{
  echo
  echo "## Objective results — $RUN_ID"
  echo
  echo "- scored: $(date -Iseconds)"
  echo "- worktree: \`$WORKTREE\`"
  echo "- HEAD: \`$(git rev-parse --short HEAD)\` (base \`$(git rev-parse --short "$BASE")\`)"
  echo "- uncommitted changes at scoring time: $(git status --porcelain | wc -l) files"
  echo
  echo "### Diff stats vs base"
  echo
  echo '```'
  git diff --stat "$BASE" HEAD | tail -5
  echo '```'
  echo
  echo "- tests added: $(git diff "$BASE" HEAD -- tests | grep -c '^+.*def test_') (removed: $(git diff "$BASE" HEAD -- tests | grep -c '^-.*def test_'))"
  # NOTE: count only added Poetry dependency declarations (`pkg = "..."` / `pkg = {...}`);
  # a bare `grep -c '^+.*='` over-counts (extras lists, ruff/mypy config keys, the `+++` header).
  echo "- new deps in pyproject: $(git diff "$BASE" HEAD -- pyproject.toml | grep -cE '^\+[[:space:]]*[A-Za-z0-9_.-]+ = [{\"]')"
  echo
  echo "### Gates"
  echo
  echo "| check | result |"
  echo "|-------|--------|"
} >>"$OUT"

# NOTE: `--all-extras` (not `-E anyio`) so a Task B solution's Postgres extra is installed —
# mypy must type-check the Postgres storage module, which needs its driver present. No DB is
# started, so opt-in integration tests still skip. Surface install failure so a blanket gate
# FAIL isn't misread as a solution defect.
if ! poetry install --all-extras --quiet >/dev/null 2>&1; then
  echo "| poetry install --all-extras | **FAIL** (deps did not install — gate results below are unreliable) |" >>"$OUT"
fi

run_check "ruff format --check" poetry run ruff format --check
run_check "ruff check" poetry run ruff check
run_check "mypy" poetry run mypy
run_check "pytest" poetry run pytest

{
  echo
  cat "$FAIL_DETAILS"
} >>"$OUT"
rm -f "$FAIL_DETAILS"

echo "Scored -> $OUT"
