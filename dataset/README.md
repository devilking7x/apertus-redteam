# Public dataset (sanitized)

This directory contains **sanitized** run records for the five findings in
the technical report. Sanitization:

- `config.json`: exact reproduction parameters (safe to share).
- `summary.json`: aggregate statistics only.
- `results.jsonl`: prompts, judgments, and metadata are intact; **model
  responses are redacted or truncated** where they were flagged as
  disallowed or may contain copyrighted text. See report §4 for summaries.

To reproduce any run from scratch (fresh model outputs):

```bash
bash reproduce.sh <run-id>
# e.g. bash reproduce.sh prompt_injection-seed42-20261003T195509Z
```

`reproduce.sh` reads `dataset/<run-id>/config.json` (falls back to
`runs/<run-id>/config.json` for local runs). You need an API key:
`export APERTUS_API_KEY=...` — the key is never logged or stored.
