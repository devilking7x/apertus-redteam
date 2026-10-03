"""End-to-end: runner writes valid config.json + results.jsonl + summary.json."""

import json
import os

from attacks import get_attack
from redteam.backend import StubBackend
from redteam.runner import run_attack, RunConfig

REQUIRED_RECORD_KEYS = {"run_id", "attack", "seed", "index", "prompt",
                        "params", "response", "judge", "model_id", "timestamp"}
REQUIRED_JUDGE_KEYS = {"score", "flag", "reason"}


def test_runner_schema(tmp_path):
    module = get_attack("prompt_injection")
    backend = StubBackend(rules=[("CANARY-", "BLUEBIRD")])
    out = str(tmp_path / "run123")
    cfg = RunConfig(attack="prompt_injection", seed=5, variations=4,
                    model_id=backend.model_id, backend="stub")
    summary = run_attack(module, backend, cfg, out)

    assert os.path.isfile(os.path.join(out, "config.json"))
    assert os.path.isfile(os.path.join(out, "results.jsonl"))
    with open(os.path.join(out, "config.json")) as f:
        saved = json.load(f)
    assert saved["attack"] == "prompt_injection" and saved["seed"] == 5

    lines = open(os.path.join(out, "results.jsonl")).read().strip().split("\n")
    assert len(lines) == 4
    for i, line in enumerate(lines):
        rec = json.loads(line)
        assert REQUIRED_RECORD_KEYS <= set(rec), f"missing keys in record {i}"
        assert REQUIRED_JUDGE_KEYS <= set(rec["judge"])
        assert rec["index"] == i and rec["seed"] == 5
        assert rec["model_id"] == "stub-test-model"
        assert 0.0 <= rec["judge"]["score"] <= 1.0

    assert summary["variations"] == 4
    assert summary["attack"] == "prompt_injection"


def test_runner_mutations_and_stats(tmp_path):
    """Mutations apply deterministically; summary carries ASR + Wilson CI."""
    module = get_attack("prompt_injection")
    backend = StubBackend()  # default: canned refusal -> nothing flagged
    out = str(tmp_path / "runm")
    cfg = RunConfig(attack="prompt_injection", seed=5, variations=4,
                    model_id=backend.model_id, backend="stub",
                    mutations=["leetspeak"])
    summary = run_attack(module, backend, cfg, out)

    assert summary["mutations"] == ["leetspeak"]
    assert summary["asr"] == 0.0 and summary["flagged"] == 0
    low, high = summary["wilson_ci"]
    assert low <= summary["asr"] <= high
    assert summary["language_delta"] is None

    with open(os.path.join(out, "config.json")) as f:
        assert json.load(f)["mutations"] == ["leetspeak"]

    lines = open(os.path.join(out, "results.jsonl")).read().strip().split("\n")
    assert len(lines) == 4
    for line in lines:
        rec = json.loads(line)
        assert rec["prompt"] != rec["base_prompt"]  # leetspeak changed it
        assert rec["mutations"] == ["leetspeak"]

    # Same seed + same mutations -> identical mutated prompts (reproducible).
    out2 = str(tmp_path / "runm2")
    run_attack(module, backend, cfg, out2)
    ps1 = [json.loads(l)["prompt"] for l in
           open(os.path.join(out, "results.jsonl"))]
    ps2 = [json.loads(l)["prompt"] for l in
           open(os.path.join(out2, "results.jsonl"))]
    assert ps1 == ps2


def test_runner_reproducible_prompts(tmp_path):
    """Same seed through the runner -> same prompts logged."""
    module = get_attack("bias_stereotype")
    backend = StubBackend()
    outs = []
    for k in range(2):
        out = str(tmp_path / f"r{k}")
        cfg = RunConfig(attack="bias_stereotype", seed=99, variations=6,
                        model_id=backend.model_id, backend="stub")
        run_attack(module, backend, cfg, out)
        outs.append(out)
    ps = []
    for out in outs:
        lines = open(os.path.join(out, "results.jsonl")).read().strip().split("\n")
        ps.append([json.loads(l)["prompt"] for l in lines])
    assert ps[0] == ps[1]
