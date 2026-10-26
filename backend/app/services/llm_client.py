"""
Gemini text-generation client (no database or web-framework imports).

Extracted from ai_service.py so that the evaluation scripts can call the model
directly. Behaviour is unchanged: try each candidate model in order, fall through
on 429/5xx/other errors, and map a total failure to a 429 or 503 style error.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import requests

logger = logging.getLogger(__name__)

DEFAULT_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-flash-latest",
]


@dataclass
class LLMResult:
    text: str
    model: str
    prompt_tokens: Optional[int]
    latency_ms: float


class LLMError(Exception):
    """All candidate models failed. `status_code` is 429 (rate limit) or 503."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def call_gemini(
    prompt: str,
    api_key: str,
    models: Sequence[str] = tuple(DEFAULT_MODELS),
    timeout: float = 25,
    temperature: float = 0.0,
    max_output_tokens: int = 2048,
    post: Callable = requests.post,
) -> LLMResult:
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_output_tokens},
    }

    last_error_msg = ""
    last_status: Optional[int] = None
    start = time.perf_counter()

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            res = post(url, headers=headers, json=payload, timeout=timeout)
        except Exception as exc:
            logger.warning("Gemini connection error for model %s: %s. Falling back...", model, exc)
            last_error_msg = str(exc)
            continue

        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Google Gemini API returned an empty response.")
            text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            usage = data.get("usageMetadata") or {}
            logger.info("Gemini model %s responded successfully.", model)
            return LLMResult(
                text=text_out,
                model=model,
                prompt_tokens=usage.get("promptTokenCount"),
                latency_ms=round((time.perf_counter() - start) * 1000, 1),
            )

        err_text = res.text[:300]
        last_status = res.status_code
        last_error_msg = f"Model {model}: {err_text}"
        logger.warning("Gemini model %s returned status %s: %s. Falling back...", model, res.status_code, err_text)

    if last_status == 429 or "429" in last_error_msg or "Quota exceeded" in last_error_msg:
        raise LLMError(429, "Google Gemini API free tier rate limit reached. Please wait 10-15 seconds and try again.")
    raise LLMError(503, f"Google Gemini API error ({last_status or 500}): {last_error_msg[:250]}")
