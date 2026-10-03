"""Determinism: same seed -> identical prompts; correct count; seed sensitivity."""

import pytest
from attacks import REGISTRY, get_attack


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_same_seed_identical(name):
    mod = get_attack(name)
    a = mod.generate(seed=42, n=10)
    b = mod.generate(seed=42, n=10)
    assert a == b, f"{name}: same seed gave different prompts"


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_variation_count(name):
    mod = get_attack(name)
    for n in (1, 5, 13):
        assert len(mod.generate(seed=7, n=n)) == n


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_different_seed_differs(name):
    mod = get_attack(name)
    a = mod.generate(seed=1, n=20)
    b = mod.generate(seed=2, n=20)
    assert a != b, f"{name}: different seeds gave identical prompts"


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_prompts_are_nonempty_strings(name):
    for p in get_attack(name).generate(seed=3, n=8):
        assert isinstance(p, str) and p.strip(), f"{name}: empty prompt"
