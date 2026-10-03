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

ATTACK="$(read_cfg attack)"
SEED="$(read_cfg seed)"
VARIATIONS="$(read_cfg variations)"
MODEL="$(read_cfg model_id)"
BACKEND="$(read_cfg backend)"
MAXTOK="$(read_cfg max_new_tokens)"
TEMP="$(read_cfg temperature)"

echo "[reproduce] re-running $RUN_ID"
echo "[reproduce] attack=$ATTACK seed=$SEED variations=$VARIATIONS model=$MODEL backend=$BACKEND"

python3 run.py \
  --attack "$ATTACK" \
  --seed "$SEED" \
  --variations "$VARIATIONS" \
  --model "$MODEL" \
  --backend "$BACKEND" \
  --max-tokens "$MAXTOK" \
  --temperature "$TEMP"
