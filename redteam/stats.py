"""Run statistics — pure functions over results.jsonl records.

- Attack Success Rate (ASR) = fraction of flagged variations, with a
  Wilson-score 95% confidence interval (better than the naive normal
  approximation for small n and extreme rates).
- language_delta: for multilingual_jailbreak runs, compares mean judge
  score on English prompts vs non-English prompts. Positive delta means
  the model behaves worse off-English — the core claim of that module.
"""

from __future__ import annotations

import math


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Returns (low, high), clipped to [0, 1]. z=1.96 -> 95% confidence.
    """
    if n <= 0:
        return (0.0, 0.0)
    if k < 0 or k > n:
        raise ValueError(f"k={k} out of range for n={n}")
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _classify_mj_language(prompt: str) -> str:
    """Which language is a multilingual_jailbreak prompt in?

    Matches the module's own framing templates / translations, so this
    is exact for module-generated prompts (not a generic detector).
    """
    from attacks.multilingual_jailbreak import FRAMINGS, TRANSLATIONS
    for lang, framings in FRAMINGS.items():
        for template in framings:
            prefix = template.split("{req}")[0].strip()
            if prefix and prefix in prompt:
                return lang
    for lang, table in TRANSLATIONS.items():
        for req in table.values():
            if req in prompt:
                return lang
    return "en"


def language_delta(records: list[dict]) -> dict | None:
    """English vs non-English mean judge score for a multilingual run.

    Returns None when the records are not from multilingual_jailbreak
    or one side has no samples.
    """
    if not records or records[0].get("attack") != "multilingual_jailbreak":
        return None
    # Prefer the pre-mutation prompt: mutations (e.g. base64_wrap) hide
    # the language signal, so delta is only meaningful on base prompts.
    def _lang(r: dict) -> str:
        return _classify_mj_language(r.get("base_prompt") or r["prompt"])
    en = [r["judge"]["score"] for r in records if _lang(r) == "en"]
    ne = [r["judge"]["score"] for r in records if _lang(r) != "en"]
    if not en or not ne:
        return None
    en_mean, ne_mean = _mean(en), _mean(ne)
    return {
        "attack": "multilingual_jailbreak",
        "english": {"n": len(en), "mean_score": en_mean},
        "non_english": {"n": len(ne), "mean_score": ne_mean},
        # Positive delta => worse (higher flag score) off-English.
        "delta": ne_mean - en_mean,
    }


def summarize_run(records: list[dict]) -> dict:
    """Aggregate one run's records into report-ready statistics."""
    n = len(records)
    flagged = sum(1 for r in records if r["judge"]["flag"])
    low, high = wilson_ci(flagged, n)
    return {
        "n": n,
        "flagged": flagged,
        "asr": (flagged / n) if n else 0.0,
        "wilson_ci": [low, high],
        "language_delta": language_delta(records),
    }


def group_by_attack(records: list[dict]) -> dict[str, dict]:
    """summarize_run() per attack class (for multi-run aggregation)."""
    by_attack: dict[str, list[dict]] = {}
    for r in records:
        by_attack.setdefault(r.get("attack", "?"), []).append(r)
    return {name: summarize_run(rs) for name, rs in by_attack.items()}
