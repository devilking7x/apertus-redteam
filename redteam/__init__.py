"""Apertus red-teaming harness — Track 1A, Hack Apertus.

Authorized security research: systematically probe the Apertus open LLM for
safety failures (jailbreaks, bias, privacy leakage, copyright regurgitation,
prompt injection) and document findings for the organizers.

Heuristic judges are triage signals only — a human researcher must confirm
every finding before it goes into the report.
"""

__version__ = "0.2.0"

from .backend import ModelBackend, HFBackend, OpenAIBackend, StubBackend
from .runner import run_attack, RunConfig

__all__ = [
    "ModelBackend",
    "HFBackend",
    "OpenAIBackend",
    "StubBackend",
    "run_attack",
    "RunConfig",
]
