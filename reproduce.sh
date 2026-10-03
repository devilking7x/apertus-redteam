#!/usr/bin/env bash
# reproduce.sh — re-run a finding by its run ID with one command.
# Usage: bash reproduce.sh <run-id>
# Reads runs/<run-id>/config.json and re-invokes run.py with identical args.
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: bash reproduce.sh <run-id>" >&2
  exit 2
fi

RUN_ID="$1"
CFG="runs/${RUN_ID}/config.json"

if [ ! -f "$CFG" ]; then
  echo "error: no such run: $CFG" >&2
  exit 1
fi

read_cfg() {
  python3 -c "import json; print(json.load(open('$CFG'))['$1'])"
}

read_cfg_opt() {
  python3 -c "import json; v=json.load(open('$CFG')).get('$1'); print(v if v else '')"
}

ATTACK="$(read_cfg attack)"
SEED="$(read_cfg seed)"
VARIATIONS="$(read_cfg variations)"
MODEL="$(read_cfg model_id)"
BACKEND="$(read_cfg backend)"
MAXTOK="$(read_cfg max_new_tokens)"
TEMP="$(read_cfg temperature)"
API_BASE="$(read_cfg_opt api_base)"

EXTRA_ARGS=()
if [ -n "$API_BASE" ]; then
  EXTRA_ARGS+=(--api-base "$API_BASE")
fi

echo "[reproduce] re-running $RUN_ID"
echo "[reproduce] attack=$ATTACK seed=$SEED variations=$VARIATIONS model=$MODEL backend=$BACKEND"
if [ "$BACKEND" = "openai" ]; then
  echo "[reproduce] NOTE: API key is taken from \$APERTUS_API_KEY (or pass --api-key); it is never stored in run logs."
fi

python3 run.py \
  --attack "$ATTACK" \
  --seed "$SEED" \
  --variations "$VARIATIONS" \
  --model "$MODEL" \
  --backend "$BACKEND" \
  --max-tokens "$MAXTOK" \
  --temperature "$TEMP" \
  "${EXTRA_ARGS[@]}"
