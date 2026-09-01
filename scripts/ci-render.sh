#!/usr/bin/env bash
# Render exercises_solutions.qmd on a GitHub Actions Linux runner and bring the
# result back into this checkout.
#
# Why not render locally: the render EXECUTES the notebook, so the output carries
# whatever Quarto, Keras, and PyTorch versions the machine happens to have. The
# runner is the source of truth. A local macOS render swaps in a different stack
# and produces a large diff that is mostly version churn, not content.
#
# Usage:
#   scripts/ci-render.sh              dispatch on the current branch, wait, collect
#   scripts/ci-render.sh --no-wait    dispatch and return immediately
#
# On main the workflow commits the HTML, so this pulls it into the checkout.
# On any other branch the workflow only uploads an artifact, and this downloads
# it to ci-render-out/ so you can inspect it without touching the tracked file.

set -euo pipefail

WORKFLOW="render-solutions.yml"
ARTIFACT="solutions-html"
OUTDIR="ci-render-out"

cd "$(dirname "$0")/.."

command -v gh >/dev/null || { echo "gh CLI not found. brew install gh" >&2; exit 1; }

WAIT=1
[ "${1:-}" = "--no-wait" ] && WAIT=0

BRANCH="$(git branch --show-current)"
[ -n "$BRANCH" ] || { echo "Detached HEAD. Check out a branch first." >&2; exit 1; }

# CI renders what is on the remote, so warn when this checkout differs from it.
if ! git diff --quiet HEAD -- exercises_solutions.qmd requirements.txt; then
  echo "WARNING: exercises_solutions.qmd or requirements.txt has uncommitted changes."
  echo "         The runner renders the pushed version, not what is on disk."
fi
if [ -n "$(git log --oneline "origin/$BRANCH..$BRANCH" 2>/dev/null || true)" ]; then
  echo "WARNING: $BRANCH is ahead of origin/$BRANCH. Push first, or the runner"
  echo "         will render the older commit."
fi

PREV_RUN="$(gh run list --workflow="$WORKFLOW" --limit 1 --json databaseId \
            -q '.[0].databaseId' 2>/dev/null || echo 0)"

echo "Dispatching $WORKFLOW on $BRANCH ..."
gh workflow run "$WORKFLOW" --ref "$BRANCH"

# The run id is not returned by the dispatch, so poll until a newer one shows up.
RUN_ID=""
for _ in $(seq 1 30); do
  sleep 3
  RUN_ID="$(gh run list --workflow="$WORKFLOW" --limit 1 --json databaseId \
            -q '.[0].databaseId' 2>/dev/null || echo 0)"
  [ "$RUN_ID" != "$PREV_RUN" ] && [ -n "$RUN_ID" ] && break
  RUN_ID=""
done
[ -n "$RUN_ID" ] || { echo "Timed out waiting for the run to register." >&2; exit 1; }

echo "Run $RUN_ID: $(gh run view "$RUN_ID" --json url -q .url)"

if [ "$WAIT" -eq 0 ]; then
  echo "Not waiting. Collect it later with:"
  echo "  gh run download $RUN_ID -n $ARTIFACT -D $OUTDIR"
  exit 0
fi

echo "Waiting for the render (about 6 minutes) ..."
gh run watch "$RUN_ID" --exit-status || {
  echo "Run failed. Logs: gh run view $RUN_ID --log-failed" >&2
  exit 1
}

if [ "$BRANCH" = "main" ]; then
  echo "Pulling the committed render ..."
  git pull --ff-only
  echo "Updated exercises_solutions.html in the working tree."
else
  rm -rf "$OUTDIR"
  gh run download "$RUN_ID" -n "$ARTIFACT" -D "$OUTDIR"
  echo "Downloaded to $OUTDIR/exercises_solutions.html (tracked file untouched)."
fi
