"""Deterministic runner: executes an attack module against a backend and
logs everything to JSONL for reproducibility (jury "validity" criterion).
"""

from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass, asdict

from redteam.backend import ModelBackend
from attacks.base import AttackModule


@dataclass
class RunConfig:
    attack: str
    seed: int
    variations: int
    model_id: str
    backend: str
    max_new_tokens: int = 256
    temperature: float = 0.0
    # Effective HTTP base URL for the openai backend (recorded so a run is
    # reproducible; the API KEY is NEVER stored — it comes from
    # $APERTUS_API_KEY / --api-key at re-run time).
    api_base: str | None = None


def _utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def run_attack(module: AttackModule, backend: ModelBackend,
               config: RunConfig, out_dir: str) -> dict:
    """Run all variations, judge each, write config.json + results.jsonl.

    Returns a summary dict. Every prompt/response/param is logged —
    re-running with the same seed reproduces the same prompts.
    """
    os.makedirs(out_dir, exist_ok=True)
    run_id = os.path.basename(os.path.normpath(out_dir))

    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump({"run_id": run_id, **asdict(config)}, f, indent=2)

    prompts = module.generate(config.seed, config.variations)
    assert len(prompts) == config.variations, \
        f"generate() returned {len(prompts)} prompts, expected {config.variations}"

    results_path = os.path.join(out_dir, "results.jsonl")
    flagged = 0
    scores: list[float] = []
    with open(results_path, "w") as f:
        for i, prompt in enumerate(prompts):
            response = backend.complete(
                prompt,
                max_new_tokens=config.max_new_tokens,
                temperature=config.temperature,
            )
            judgment = module.judge(prompt, response)
            scores.append(judgment["score"])
            flagged += 1 if judgment["flag"] else 0
            record = {
                "run_id": run_id,
                "attack": module.name,
                "seed": config.seed,
                "index": i,
                "prompt": prompt,
                "params": {"max_new_tokens": config.max_new_tokens,
                           "temperature": config.temperature},
                "response": response,
                "judge": judgment,
                "model_id": backend.model_id,
                "timestamp": _utcnow(),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "run_id": run_id,
        "attack": module.name,
        "model_id": backend.model_id,
        "variations": config.variations,
        "flagged": flagged,
        "mean_score": sum(scores) / len(scores) if scores else 0.0,
        "max_score": max(scores) if scores else 0.0,
        "results_path": results_path,
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    return summary
