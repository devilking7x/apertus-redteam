# Apertus Red-Team Harness

Systematic, reproducible red-teaming of the Apertus open LLM for
**Hack Apertus — Track 1A** ("find and document where the model
underperforms or behaves unexpectedly").

## What / why

Safety fine-tuning is usually validated in English and on a handful of
attack styles. This harness probes **fifteen attack classes** with **seeded,
deterministic prompt generation** and logs every prompt/response/judgment
to JSONL, so any finding reproduces with one command — the jury's
"validity" criterion rewards exactly this. `summary.json` carries the
Attack Success Rate with a 95% Wilson confidence interval, and
`redteam/figures.py` turns run statistics into report-ready charts.
Tool/agentic attack classes drive the model's real tool-calling API
(`chat_with_tools`), simulating agentic loops with poisoned tool outputs.

**Heuristic judges are triage signals, not verdicts.** Every flagged case
must be human-reviewed before it becomes a finding (see
`findings/TEMPLATE.md`).

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# CPU-only torch (recommended without a GPU):
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Primary target: `swiss-ai/Apertus-v1.5-70B` via the CSCS Inference API
(OpenAI-compatible, https://api.inference.cscs.ch/v1). Local HF backend
also supported for the 8B variant.

## Quickstart

```bash
# 1. Run one attack class (12 seeded variations, greedy decoding)
python run.py --attack multilingual_jailbreak --seed 42 --variations 12

# 2. Inspect runs/<run-id>/summary.json + results.jsonl
# 3. Reproduce any run exactly:
bash reproduce.sh <run-id>

# Run everything (example sweep)
for a in multilingual_jailbreak pii_extraction copyright_regurgitation \
         bias_stereotype prompt_injection factual_correctness \
         swiss_culture_values system_prompt_extraction swiss_dialect_jailbreak \
         encoding_obfuscation crescendo_jailbreak manyshot_jailbreak \
         tool_call_hijack agentic_loop_injection tool_description_poisoning; do
  python run.py --attack $a --seed 42 --variations 12
done

# Layer obfuscation on top of any attack (comma-separated, applied in order)
python run.py --attack prompt_injection --seed 7 --variations 8 \
  --mutations base64_wrap,roleplay_framing
# Available: base64_wrap, leetspeak, roleplay_framing, multiturn_prefix
```

CI / smoke test without a model:

```bash
python run.py --attack prompt_injection --seed 1 --variations 3 --backend stub
```

## The 15 attack classes

| Module | What it tests | Novelty angle |
|---|---|---|
| `multilingual_jailbreak` | Same disallowed requests in EN/Hindi/Bengali/Swahili — does refusal hold off-English? | Model trained on 1,811 languages; safety gaps in low-resource languages |
| `pii_extraction` | **Synthetic canaries only** (fake names/emails/phones). Direct elicitation, confidentiality-marked memos, social-engineering pretexts | Privacy-boundary / instruction-following failure |
| `copyright_regurgitation` | Verbatim-text requests; longest-verbatim-run vs local refs (`refs/`, gitignored) | Regurgitation measurement |
| `bias_stereotype` | Swiss linguistic-region groups: stereotype agreement + open completions | Home-culture bias |
| `prompt_injection` | Carrier task + embedded instruction with unique canary; canary in output = hierarchy failure | Indirect injection |
| `factual_correctness` | Verifiable Swiss facts (canton capitals), post-cutoff questions (model should hedge, not fabricate), YES/NO self-contradiction pairs | Hallucination traps with ground truth |
| `swiss_culture_values` | Pushes to abandon neutrality / bypass direct democracy / drop a national language — does the model defend the value? | Values-alignment for a sovereign Swiss model |
| `system_prompt_extraction` | Attempts to reveal hidden instructions | Confidentiality of system prompt |
| `swiss_dialect_jailbreak` | Jailbreak attempts in Schwiizerdütsch | Native-dialect safety |
| `encoding_obfuscation` | ROT13/reversed/interleaved payloads | Obfuscation robustness |
| `crescendo_jailbreak` | 3-turn gradual escalation (multi-turn) | Multi-turn safety |
| `manyshot_jailbreak` | 8/24/48-shot in-context conditioning (262K window) | Context-scale safety erosion |
| `tool_call_hijack` | Injection steering tool calls via tool-calling API | Agentic confused-deputy |
| `tool_description_poisoning` | Instructions hidden in tool descriptions | Tool metadata trust boundary |
| `agentic_loop_injection` | Poisoned tool output in simulated agent loop | Indirect injection, agentic |

## Prompt mutations (`--mutations`)

Composable obfuscation wrappers applied deterministically on top of any
attack's base prompts (recorded in `config.json`, re-applied by
`reproduce.sh`):

| Mutation | Effect |
|---|---|
| `base64_wrap` | Base64-encodes the prompt, asks the model to decode it |
| `leetspeak` | Deterministic 1337 character substitution |
| `roleplay_framing` | Prefixes an "authorized red-team exercise" framing |
| `multiturn_prefix` | Fake benign first turn; attack arrives as the second user turn |

Example: `--mutations base64_wrap,roleplay_framing`

## Statistics & figures

Every `summary.json` includes `asr` (attack success rate), `wilson_ci`
(95% Wilson confidence interval — honest error bars for small n), and,
for multilingual runs, `language_delta` (mean judge score English vs
non-English; positive = worse off-English). Generate report charts:

```python
from redteam.stats import group_by_attack
from redteam.figures import asr_bar_chart, language_delta_chart
# per_attack = group_by_attack(all_records)  # across runs
asr_bar_chart(per_attack, "report/figures/asr.png")
language_delta_chart(delta, "report/figures/language_delta.png")
```

## How to add an attack class

1. Create `attacks/my_attack.py` with a class extending `AttackModule`:
   - `generate(seed, n) -> list[str]` — **must** be deterministic (use `self._rng(seed)`, never global `random`)
   - `judge(prompt, response) -> {"score": 0..1, "flag": bool, "reason": str}`
2. Register it in `attacks/__init__.py` (`REGISTRY`).
3. Add determinism + judge tests in `tests/`.

## Backends

- `hf` (default): local transformers. `--model swiss-ai/Apertus-8B-Instruct-2509`.
  Set `CUDA_VISIBLE_DEVICES` / device via code for GPU use.
- `openai`: any OpenAI-compatible endpoint — `APERTUS_BASE_URL`
  (default `http://localhost:8000/v1`) + `APERTUS_API_KEY`.
- `stub`: canned responses, tests/CI only.

## Model size (planning)

| Model | fp16 | 8-bit | Notes |
|---|---|---|---|
| Apertus-8B-Instruct-2509 | ~16 GB | ~8 GB | single GPU or high-RAM CPU box |
| Apertus-70B-Instruct-2509 | ~140 GB | ~70 GB | use the hosted CSCS API instead |

No HF token required (ungated repos).

## Responsible use

This is **authorized security research** for the Hack Apertus Track 1A
challenge ("find and document where the model underperforms"). Rules we
follow:

- **Synthetic canaries only** — never real names, emails, phones.
- **No large copyrighted excerpts** stored in the repo (`runs/` and
  `refs/` are gitignored).
- Findings are **disclosed to the organizers**, documented like security
  advisories (impact + mitigation) — not published as how-tos.
- Heuristic flags are triage; a human confirms every finding.

## Layout

```
redteam/        # package: backends + deterministic runner + stats + figures
attacks/        # 7 attack modules (generate + judge) + mutations.py
findings/       # TEMPLATE.md + one file per confirmed issue
report/         # outline.md — technical-report skeleton
                # figures/ — auto-generated charts (asr.png, language_delta.png)
tests/          # pytest: determinism, judge sanity, log schema, stats, mutations
run.py          # CLI entry point (--attack, --mutations, --backend, ...)
reproduce.sh    # one-command repro by run ID
runs/           # logs (gitignored)
```
