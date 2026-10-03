"""Attack registry — maps CLI names to modules."""

from .base import AttackModule
from .multilingual_jailbreak import MultilingualJailbreak
from .pii_extraction import PIIExtraction
from .copyright_regurgitation import CopyrightRegurgitation
from .bias_stereotype import BiasStereotype
from .prompt_injection import PromptInjection
from .factual_correctness import FactualCorrectness
from .swiss_culture_values import SwissCultureValues
from .system_prompt_extraction import SystemPromptExtraction
from .swiss_dialect_jailbreak import SwissDialectJailbreak
from .encoding_obfuscation import EncodingObfuscation
from .crescendo_jailbreak import CrescendoJailbreak
from .manyshot_jailbreak import ManyShotJailbreak
from .tool_call_hijack import ToolCallHijack
from .agentic_loop_injection import AgenticLoopInjection
from .tool_description_poisoning import ToolDescriptionPoisoning

REGISTRY: dict[str, type[AttackModule]] = {
    "multilingual_jailbreak": MultilingualJailbreak,
    "pii_extraction": PIIExtraction,
    "copyright_regurgitation": CopyrightRegurgitation,
    "bias_stereotype": BiasStereotype,
    "prompt_injection": PromptInjection,
    "factual_correctness": FactualCorrectness,
    "swiss_culture_values": SwissCultureValues,
    "system_prompt_extraction": SystemPromptExtraction,
    "swiss_dialect_jailbreak": SwissDialectJailbreak,
    "encoding_obfuscation": EncodingObfuscation,
    "crescendo_jailbreak": CrescendoJailbreak,
    "manyshot_jailbreak": ManyShotJailbreak,
    "tool_call_hijack": ToolCallHijack,
    "agentic_loop_injection": AgenticLoopInjection,
    "tool_description_poisoning": ToolDescriptionPoisoning,
}


def get_attack(name: str) -> AttackModule:
    try:
        return REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown attack {name!r}. Choose from: {sorted(REGISTRY)}")
