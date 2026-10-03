"""Attack registry — maps CLI names to modules."""

from .base import AttackModule
from .multilingual_jailbreak import MultilingualJailbreak
from .pii_extraction import PIIExtraction
from .copyright_regurgitation import CopyrightRegurgitation
from .bias_stereotype import BiasStereotype
from .prompt_injection import PromptInjection
from .factual_correctness import FactualCorrectness
from .swiss_culture_values import SwissCultureValues

REGISTRY: dict[str, type[AttackModule]] = {
    "multilingual_jailbreak": MultilingualJailbreak,
    "pii_extraction": PIIExtraction,
    "copyright_regurgitation": CopyrightRegurgitation,
    "bias_stereotype": BiasStereotype,
    "prompt_injection": PromptInjection,
    "factual_correctness": FactualCorrectness,
    "swiss_culture_values": SwissCultureValues,
}


def get_attack(name: str) -> AttackModule:
    try:
        return REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown attack {name!r}. Choose from: {sorted(REGISTRY)}")
