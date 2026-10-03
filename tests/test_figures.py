"""Unit tests for redteam.figures — charts render from synthetic stats."""

import os

import pytest

mpl = pytest.importorskip("matplotlib")

from redteam.figures import asr_bar_chart, language_delta_chart  # noqa: E402

PNG_MAGIC = b"\x89PNG"


def _is_png(path: str) -> bool:
    with open(path, "rb") as f:
        return f.read(4) == PNG_MAGIC


def _per_attack():
    return {
        "prompt_injection": {"asr": 0.75, "wilson_ci": [0.5, 0.9],
                             "n": 12, "flagged": 9},
        "bias_stereotype": {"asr": 0.25, "wilson_ci": [0.1, 0.45],
                            "n": 12, "flagged": 3},
        "factual_correctness": {"asr": 0.0, "wilson_ci": [0.0, 0.22],
                                "n": 12, "flagged": 0},
    }


def test_asr_bar_chart(tmp_path):
    out = str(tmp_path / "asr.png")
    ret = asr_bar_chart(_per_attack(), out)
    assert ret == out
    assert os.path.isfile(out) and os.path.getsize(out) > 1000
    assert _is_png(out)


def test_language_delta_chart(tmp_path):
    delta = {"attack": "multilingual_jailbreak",
             "english": {"n": 8, "mean_score": 0.1},
             "non_english": {"n": 24, "mean_score": 0.6},
             "delta": 0.5}
    out = str(tmp_path / "figs" / "lang.png")  # nested dir must be created
    ret = language_delta_chart(delta, out)
    assert ret == out
    assert os.path.isfile(out) and os.path.getsize(out) > 1000
    assert _is_png(out)
