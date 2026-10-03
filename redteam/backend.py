"""Model backends — one interface, multiple ways to reach the target model.

Design goals:
  * Model-agnostic: attacks never talk to a model directly, only to a
    ModelBackend. Swap backends without touching attack code.
  * Lazy heavy imports: `transformers`/`torch` are imported only inside
    HFBackend, so the rest of the harness (and CI) works without them.
  * Deterministic by default: greedy decoding (temperature=0.0) unless the
    caller explicitly asks for sampling.
"""

from __future__ import annotations

import json
import os
import urllib.request
from abc import ABC, abstractmethod
from typing import Any


class ModelBackend(ABC):
    """Minimal interface every backend must implement."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Human-readable model identifier, recorded in every run log."""

    @abstractmethod
    def complete(self, prompt: str, max_new_tokens: int = 256,
                 temperature: float = 0.0) -> str:
        """Return the model's continuation for `prompt` (no prompt echo)."""


class HFBackend(ModelBackend):
    """Local Hugging Face transformers backend (default).

    Loads e.g. ``swiss-ai/Apertus-8B-Instruct-2509``. Works on CPU
    (slow) or CUDA (set device="cuda"). Uses the tokenizer's chat template
    when available so instruct models get proper formatting.
    """

    def __init__(self, model_id: str = "swiss-ai/Apertus-8B-Instruct-2509",
                 device: str | None = None, load_in_8bit: bool = False):
        self._model_id = model_id
        self._device = device
        self._load_in_8bit = load_in_8bit
        self._pipe = None

    @property
    def model_id(self) -> str:
        return self._model_id

    def _ensure_loaded(self):
        if self._pipe is not None:
            return
        try:
            from transformers import pipeline
            import torch
        except ImportError as e:  # pragma: no cover - needs heavy deps
            raise RuntimeError(
                "HFBackend needs `transformers` and `torch`. "
                "Install with: pip install transformers torch "
                "(CPU-only torch: pip install torch --index-url "
                "https://download.pytorch.org/whl/cpu)"
            ) from e
        device = self._device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        kwargs: dict[str, Any] = {"device": device}
        if self._load_in_8bit:
            kwargs["model_kwargs"] = {"load_in_8bit": True}
        self._pipe = pipeline("text-generation", model=self._model_id, **kwargs)
        self._tokenizer = self._pipe.tokenizer

    def _format(self, prompt: str) -> str:
        tok = self._tokenizer
        try:
            if hasattr(tok, "apply_chat_template"):
                return tok.apply_chat_template(
                    [{"role": "user", "content": prompt}],
                    tokenize=False, add_generation_prompt=True,
                )
        except Exception:
            pass
        return prompt

    def complete(self, prompt: str, max_new_tokens: int = 256,
                 temperature: float = 0.0) -> str:
        self._ensure_loaded()
        out = self._pipe(
            self._format(prompt),
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0.0,
            temperature=max(temperature, 1e-6),
            return_full_text=False,
            pad_token_id=self._tokenizer.eos_token_id,
        )
        text = out[0]["generated_text"]
        return text.strip()


class OpenAIBackend(ModelBackend):
    """OpenAI-compatible HTTP backend (for a hosted Apertus endpoint).

    Reads base URL from ``APERTUS_BASE_URL`` (default
    http://localhost:8000/v1) and key from ``APERTUS_API_KEY`` (may be
    empty for local servers). Pure stdlib — no extra dependency.
    """

    def __init__(self, model_id: str = "apertus-8b-instruct",
                 base_url: str | None = None, api_key: str | None = None):
        self._model_id = model_id
        self._base_url = (base_url or os.environ.get(
            "APERTUS_BASE_URL", "http://localhost:8000/v1")).rstrip("/")
        self._api_key = api_key if api_key is not None else os.environ.get(
            "APERTUS_API_KEY", "")

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def base_url(self) -> str:
        """Effective base URL (after env fallback) — safe to log."""
        return self._base_url

    def complete(self, prompt: str, max_new_tokens: int = 256,
                 temperature: float = 0.0) -> str:
        body = json.dumps({
            "model": self._model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_new_tokens,
            "temperature": temperature,
        }).encode()
        req = urllib.request.Request(
            self._base_url + "/chat/completions", data=body,
            headers={"Content-Type": "application/json"},
        )
        if self._api_key:
            req.add_header("Authorization", f"Bearer {self._api_key}")
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"].strip()


class StubBackend(ModelBackend):
    """Deterministic canned backend — for tests and CI only.

    NEVER use for real findings. Maps prompt substrings to canned
    responses; unmatched prompts get a neutral refusal.
    """

    def __init__(self, model_id: str = "stub-test-model",
                 rules: list[tuple[str, str]] | None = None):
        self._model_id = model_id
        self._rules = rules or []

    @property
    def model_id(self) -> str:
        return self._model_id

    def complete(self, prompt: str, max_new_tokens: int = 256,
                 temperature: float = 0.0) -> str:
        for needle, response in self._rules:
            if needle.lower() in prompt.lower():
                return response
        return "I'm sorry, but I can't help with that."
