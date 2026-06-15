#!/usr/bin/env bash
# AnchorPrune v1.0 one-button demo — "run the whole creature".
#
# Fully offline and deterministic: doctor, policy packs, the canonical
# deterministic benchmark, and an observational mock real-eval. No API keys.
#
# AnchorPrune does not make models smarter. It governs what reaches them.

set -euo pipefail

BENCH_OUT="${BENCH_OUT:-/tmp/anchorprune_bench}"
EVAL_OUT="${EVAL_OUT:-/tmp/anchorprune_real_eval}"

echo "==> 1/4  anchorprune doctor"
anchorprune doctor

echo
echo "==> 2/4  anchorprune packs list"
anchorprune packs list

echo
echo "==> 3/4  deterministic benchmark (canonical)"
anchorprune pack --out "${BENCH_OUT}" --window 2
echo "Wrote benchmark artifacts to ${BENCH_OUT}"

echo
echo "==> 4/4  observational real-model eval (mock provider, offline)"
anchorprune real-eval \
  --provider mock \
  --model mock-deterministic \
  --scenarios coding_agent \
  --trials 1 \
  --out "${EVAL_OUT}"
echo "Wrote observational eval (NOT the canonical benchmark) to ${EVAL_OUT}"

echo
echo "Demo complete. Optional: start the local-first API with"
echo "  anchorprune serve --log-format json"
echo "and the read-only dashboard with"
echo "  cd dashboard && npm ci && npm run dev"
echo
echo "Local-first: do not expose the API to the public internet (no auth in v1.0)."
