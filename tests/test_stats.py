"""Unit tests for redteam.stats — Wilson CIs, ASR, language deltas."""

import pytest

from attacks import get_attack
from redteam.stats import wilson_ci, summarize_run, group_by_attack


def test_wilson_known_value():
    # Hand-computed: 5/10 @ z=1.96 -> center 0.5, margin ~0.2634
    low, high = wilson_ci(5, 10)
    assert low == pytest.approx(0.2366, abs=1e-3)
    assert high == pytest.approx(0.7634, abs=1e-3)


def test_wilson_empty():
    assert wilson_ci(0, 0) == (0.0, 0.0)


def test_wilson_extremes_clipped():
    low, _ = wilson_ci(0, 20)
    _, high = wilson_ci(20, 20)
    assert low == 0.0
    assert high == 1.0


def test_wilson_contains_estimate():
    for k, n in [(1, 10), (7, 10), (3, 50), (0, 5)]:
        low, high = wilson_ci(k, n)
        assert low <= k / n <= high
        assert 0.0 <= low <= high <= 1.0


def test_wilson_invalid():
    with pytest.raises(ValueError):
        wilson_ci(11, 10)


def _rec(attack, score, flag, prompt="p"):
    return {"attack": attack, "prompt": prompt, "base_prompt": prompt,
            "judge": {"score": score, "flag": flag, "reason": "t"}}


def test_summarize_run_basic():
    recs = [_rec("prompt_injection", 1.0, True) for _ in range(3)]
    recs += [_rec("prompt_injection", 0.0, False) for _ in range(7)]
    s = summarize_run(recs)
    assert s["n"] == 10 and s["flagged"] == 3
    assert s["asr"] == pytest.approx(0.3)
    low, high = s["wilson_ci"]
    assert low <= 0.3 <= high
    assert s["language_delta"] is None  # not a multilingual run


def test_summarize_run_empty():
    s = summarize_run([])
    assert s["n"] == 0 and s["asr"] == 0.0
    assert s["wilson_ci"] == [0.0, 0.0]
    assert s["language_delta"] is None


def test_group_by_attack():
    recs = [_rec("a", 1.0, True), _rec("a", 0.0, False),
            _rec("b", 1.0, True)]
    g = group_by_attack(recs)
    assert set(g) == {"a", "b"}
    assert g["a"]["asr"] == pytest.approx(0.5)
    assert g["b"]["asr"] == pytest.approx(1.0)


def test_language_delta_synthetic():
    # English prompts score 0, non-English score 1 -> delta == 1.0
    mod = get_attack("multilingual_jailbreak")
    prompts = mod.generate(seed=7, n=60)
    recs = []
    for p in prompts:
        from redteam.stats import _classify_mj_language
        lang = _classify_mj_language(p)
        score = 0.0 if lang == "en" else 1.0
        recs.append({"attack": "multilingual_jailbreak", "prompt": p,
                     "base_prompt": p,
                     "judge": {"score": score, "flag": score > 0.5,
                               "reason": "synthetic"}})
    d = summarize_run(recs)["language_delta"]
    assert d is not None
    assert d["english"]["n"] > 0 and d["non_english"]["n"] > 0
    assert d["english"]["mean_score"] == pytest.approx(0.0)
    assert d["non_english"]["mean_score"] == pytest.approx(1.0)
    assert d["delta"] == pytest.approx(1.0)


def test_language_delta_wrong_attack():
    recs = [_rec("prompt_injection", 0.5, False)]
    assert summarize_run(recs)["language_delta"] is None
