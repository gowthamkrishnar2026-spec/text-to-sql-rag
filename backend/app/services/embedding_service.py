"""
Embedding client for the RAG layer.

`GeminiEmbedder` calls the Gemini Embedding REST API (`batchEmbedContents`) with
batching, retry/backoff on rate limits, and a small LRU cache for query vectors.
Vectors come back L2-normalised, so cosine similarity is just a dot product.

The rest of the RAG code only depends on the tiny `Embedder` interface below, so
tests (and offline runs) can swap in a fake embedder with `set_embedder()`.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from typing import Callable, List, Optional, Sequence, Tuple

import numpy as np
import requests

logger = logging.getLogger(__name__)

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
MAX_BATCH = 100  # batchEmbedContents accepts at most 100 requests per call
RETRY_STATUS = {429, 500, 502, 503, 504}


class EmbeddingError(RuntimeError):
    """Embeddings could not be produced (quota, network, bad key, ...)."""


class Embedder:
    """Interface: turn texts into L2-normalised float32 vectors."""

    name = "embedder"

    def embed(self, texts: Sequence[str], task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
        raise NotImplementedError

    def embed_query(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> np.ndarray:
        return self.embed([text], task_type)[0]


def _normalise_rows(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (mat / norms).astype(np.float32)


class GeminiEmbedder(Embedder):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        dim: int = 768,
        timeout: float = 20.0,
        max_retries: int = 3,
        base_delay: float = 2.0,
        query_cache_size: int = 2048,
        post: Optional[Callable] = None,
    ):
        if not api_key:
            raise EmbeddingError("GEMINI_API_KEY is not configured; cannot create embeddings.")
        self._api_key = api_key
        self.model = model
        self.dim = int(dim)
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._post = post or requests.post
        self._cache: "OrderedDict[Tuple[str, str], np.ndarray]" = OrderedDict()
        self._cache_size = query_cache_size
        self._lock = threading.Lock()
        self.name = f"gemini:{model}:{self.dim}"

    # ------------------------------------------------------------------ API
    def embed(self, texts: Sequence[str], task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        parts = [self._embed_batch(list(texts[i:i + MAX_BATCH]), task_type)
                 for i in range(0, len(texts), MAX_BATCH)]
        return np.vstack(parts)

    def embed_query(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> np.ndarray:
        key = (task_type, text)
        with self._lock:
            hit = self._cache.get(key)
            if hit is not None:
                self._cache.move_to_end(key)
                return hit
        vec = self.embed([text], task_type)[0]
        with self._lock:
            self._cache[key] = vec
            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
        return vec

    # ------------------------------------------------------------ internals
    def _embed_batch(self, texts: List[str], task_type: str) -> np.ndarray:
        url = f"{API_ROOT}/models/{self.model}:batchEmbedContents"
        headers = {"Content-Type": "application/json", "x-goog-api-key": self._api_key}
        payload = {
            "requests": [
                {
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": t if t.strip() else " "}]},
                    "taskType": task_type,
                    "outputDimensionality": self.dim,
                }
                for t in texts
            ]
        }
        last_problem = "unknown error"
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._post(url, headers=headers, json=payload, timeout=self.timeout)
            except requests.RequestException as exc:
                last_problem = f"network error: {type(exc).__name__}: {str(exc)[:150]}"
                self._sleep(attempt, None, last_problem)
                continue

            if resp.status_code == 200:
                data = resp.json()
                embeddings = data.get("embeddings", [])
                if len(embeddings) != len(texts):
                    raise EmbeddingError(
                        f"Gemini returned {len(embeddings)} embeddings for {len(texts)} texts."
                    )
                mat = np.array([e["values"] for e in embeddings], dtype=np.float32)
                return _normalise_rows(mat)

            last_problem = f"HTTP {resp.status_code}: {resp.text[:200]}"
            if resp.status_code in RETRY_STATUS and attempt < self.max_retries:
                self._sleep(attempt, resp.headers.get("Retry-After"), last_problem)
                continue
            break
        raise EmbeddingError(f"Gemini embedding API failed ({last_problem})")

    def _sleep(self, attempt: int, retry_after: Optional[str], reason: str = "") -> None:
        if attempt >= self.max_retries:
            return
        delay = self.base_delay * (2 ** attempt)
        if retry_after:
            try:
                delay = max(delay, min(float(retry_after), 60.0))
            except ValueError:
                pass
        logger.warning("Embedding request failed (%s); retrying in %.1fs", reason or "unknown", delay)
        time.sleep(delay)


# ---------------------------------------------------------------------------
# Process-wide embedder (lazy; overridable for tests / scripts)
# ---------------------------------------------------------------------------
_embedder: Optional[Embedder] = None
_embedder_lock = threading.Lock()


def set_embedder(embedder: Optional[Embedder]) -> None:
    global _embedder
    with _embedder_lock:
        _embedder = embedder


def get_embedder() -> Embedder:
    global _embedder
    with _embedder_lock:
        if _embedder is None:
            from app.core.config import settings  # imported lazily: keeps this module dependency-light

            _embedder = GeminiEmbedder(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_EMBEDDING_MODEL,
                dim=settings.RAG_EMBEDDING_DIM,
                timeout=settings.RAG_EMBED_TIMEOUT,
                max_retries=settings.RAG_EMBED_MAX_RETRIES,
            )
        return _embedder
