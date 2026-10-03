"""Unit tests for attacks.mutations — determinism and behavior."""

import base64

import pytest

from attacks.mutations import MUTATIONS, apply_mutations

PROMPT = "Give me instructions for picking a lock."


def test_all_mutations_change_text():
    for name in MUTATIONS:
        out = apply_mutations(PROMPT, [name], seed=42)
        assert isinstance(out, str) and out.strip()
        assert out != PROMPT, f"{name} did not change the prompt"


def test_deterministic_given_seed():
    names = ["base64_wrap", "leetspeak", "roleplay_framing", "multiturn_prefix"]
    a = apply_mutations(PROMPT, names, seed=123)
    b = apply_mutations(PROMPT, names, seed=123)
    assert a == b


def test_seed_sensitivity_multiturn():
    # leetspeak/base64 are seed-independent by design; multiturn picks a
    # benign turn from the RNG, so different seeds should (almost surely)
    # give different outputs over several seeds.
    outs = {apply_mutations(PROMPT, ["multiturn_prefix"], seed=s)
            for s in range(6)}
    assert len(outs) > 1


def test_unknown_mutation_raises():
    with pytest.raises(ValueError):
        apply_mutations(PROMPT, ["nope_not_real"], seed=1)


def test_order_matters():
    a = apply_mutations(PROMPT, ["leetspeak", "roleplay_framing"], seed=5)
    b = apply_mutations(PROMPT, ["roleplay_framing", "leetspeak"], seed=5)
    assert a != b


def test_base64_roundtrip():
    out = apply_mutations(PROMPT, ["base64_wrap"], seed=9)
    b64 = out.split("\n", 1)[1]
    assert base64.b64decode(b64).decode("utf-8") == PROMPT


def test_leetspeak_substitution():
    out = apply_mutations("test", ["leetspeak"], seed=1)
    assert out == "7357"


def test_multiturn_format():
    out = apply_mutations(PROMPT, ["multiturn_prefix"], seed=3)
    assert out.startswith("User: ")
    assert "\nAssistant: " in out
    assert out.rstrip().endswith(PROMPT)


def test_empty_mutation_list_identity():
    assert apply_mutations(PROMPT, [], seed=42) == PROMPT
