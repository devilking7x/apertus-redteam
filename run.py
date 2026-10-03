#!/usr/bin/env python3
"""Apertus red-teaming harness — deterministic attack runner.

Usage:
    python run.py --attack multilingual_jailbreak --seed 42 --variations 12
    python run.py --attack prompt_injection --seed 7 --variations 8 \\
        --backend openai --model apertus-70b-instruct
    python run.py --attack bias_stereotype --seed 1 --variations 5 \\
        --backend stub        # CI/tests only — never for real findings

Every run writes runs/<run-id>/{config.json,results.jsonl,summary.json}.
Re-run any finding with: bash reproduce.sh <run-id>
"""

import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from attacks import get_attack, REGISTRY
from attacks.mutations import MUTATIONS
from redteam.backend import HFBackend, OpenAIBackend, StubBackend
from redteam.runner import run_attack, RunConfig

DEFAULT_MODEL = "swiss-ai/Apertus-8B-Instruct-2509"


def build_backend(kind: str, model: str, api_base: str | None = None,
                   api_key: str | None = None):
    if kind == "hf":
        return HFBackend(model_id=model)
    if kind == "openai":
        # api_base/api_key fall back to APERTUS_BASE_URL / APERTUS_API_KEY
        # env vars inside OpenAIBackend when None.
        return OpenAIBackend(model_id=model, base_url=api_base,
                             api_key=api_key)
    if kind == "stub":
        print("WARNING: stub backend — for tests/CI only, not real findings.",
              file=sys.stderr)
        return StubBackend()
    raise ValueError(f"unknown backend {kind!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--attack", required=True, choices=sorted(REGISTRY),
                    help="attack class to run")
    ap.add_argument("--seed", type=int, required=True,
                    help="RNG seed — same seed reproduces the same prompts")
    ap.add_argument("--variations", type=int, required=True,
                    help="number of prompt variations")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help=f"model id (default: {DEFAULT_MODEL})")
    ap.add_argument("--backend", default="hf", choices=["hf", "openai", "stub"],
                    help="model backend (default: hf)")
    ap.add_argument("--api-base", default=None,
                    help="base URL for --backend openai "
                         "(default: $APERTUS_BASE_URL or http://localhost:8000/v1)")
    ap.add_argument("--api-key", default=None,
                    help="API key for --backend openai "
                         "(default: $APERTUS_API_KEY; prefer env over CLI "
                         "so the key never lands in shell history)")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="0.0 = greedy/deterministic (default)")
    ap.add_argument("--mutations", default="",
                    help="comma-separated prompt mutations applied to every "
                         f"prompt, in order (choices: {', '.join(sorted(MUTATIONS))})")
    ap.add_argument("--out-root", default="runs",
                    help="directory for run logs (default: runs/)")
    args = ap.parse_args()

    if args.variations < 1:
        ap.error("--variations must be >= 1")
    mutations = [m.strip() for m in args.mutations.split(",") if m.strip()]
    unknown = [m for m in mutations if m not in MUTATIONS]
    if unknown:
        ap.error(f"unknown mutation(s): {unknown}. "
                 f"Choose from: {sorted(MUTATIONS)}")

    module = get_attack(args.attack)
    backend = build_backend(args.backend, args.model,
                            api_base=args.api_base, api_key=args.api_key)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{module.name}-seed{args.seed}-{ts}"
    out_dir = os.path.join(args.out_root, run_id)

    config = RunConfig(attack=args.attack, seed=args.seed,
                       variations=args.variations, model_id=backend.model_id,
                       backend=args.backend, max_new_tokens=args.max_tokens,
                       temperature=args.temperature,
                       # Record the effective base URL so re-runs hit the
                       # same endpoint. The key is never stored — it comes
                       # from $APERTUS_API_KEY / --api-key at re-run time.
                       api_base=getattr(backend, "base_url", None),
                       mutations=mutations)
    print(f"[redteam] attack={module.name} seed={args.seed} "
          f"variations={args.variations} model={backend.model_id} "
          f"mutations={mutations or 'none'}")
    summary = run_attack(module, backend, config, out_dir)
    print(f"[redteam] done: {summary['flagged']}/{summary['variations']} flagged, "
          f"mean_score={summary['mean_score']:.2f}")
    print(f"[redteam] asr={summary['asr']:.2f} "
          f"95% CI=[{summary['wilson_ci'][0]:.2f}, {summary['wilson_ci'][1]:.2f}]")
    print(f"[redteam] logs: {out_dir}")
    print(f"[redteam] reproduce: bash reproduce.sh {run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
