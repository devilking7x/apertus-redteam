"""Auto-generated report figures from run statistics.

Headless (Agg backend) so figures render in CI and on servers without a
display. Both functions take the plain-dict output of redteam.stats and
write PNGs, returning the output path.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)


def asr_bar_chart(per_attack: dict[str, dict], out_path: str) -> str:
    """Horizontal bar chart of ASR per attack class with Wilson CI whiskers.

    per_attack: {attack_name: {"asr": float, "wilson_ci": [low, high],
                              "n": int, "flagged": int}}
    """
    names = sorted(per_attack, key=lambda k: per_attack[k]["asr"])
    asrs = [per_attack[k]["asr"] for k in names]
    lows = [per_attack[k]["asr"] - per_attack[k]["wilson_ci"][0]
            for k in names]
    highs = [per_attack[k]["wilson_ci"][1] - per_attack[k]["asr"]
             for k in names]
    labels = [f"{k}  ({per_attack[k]['flagged']}/{per_attack[k]['n']})"
              for k in names]

    fig, ax = plt.subplots(figsize=(9, 0.7 * max(1, len(names)) + 1.2))
    ax.barh(labels, asrs, xerr=[lows, highs], capsize=4,
            color="#b91c1c", ecolor="#1f2937")
    ax.set_xlabel("Attack Success Rate (flagged / variations)")
    ax.set_title("ASR per attack class — 95% Wilson confidence intervals")
    ax.set_xlim(0, 1.02)
    for i, v in enumerate(asrs):
        ax.text(v + 0.015, i, f"{v:.0%}", va="center", fontsize=9)
    fig.tight_layout()
    _ensure_parent(out_path)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def language_delta_chart(delta: dict, out_path: str) -> str:
    """Grouped bar: mean judge score, English vs non-English prompts.

    delta: output of redteam.stats.language_delta().
    """
    en = delta["english"]
    ne = delta["non_english"]
    labels = [f"English\n(n={en['n']})", f"Non-English\n(n={ne['n']})"]
    values = [en["mean_score"], ne["mean_score"]]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(labels, values, color=["#1d4ed8", "#b91c1c"], width=0.55)
    ax.set_ylabel("Mean judge score (0 = safe, 1 = issue reproduced)")
    ax.set_title("Multilingual jailbreak: English vs low-resource languages\n"
                 f"Δ = {delta['delta']:+.2f} (positive = worse off-English)")
    ax.set_ylim(0, 1.02)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02, f"{v:.2f}",
                ha="center", fontsize=10)
    fig.tight_layout()
    _ensure_parent(out_path)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
