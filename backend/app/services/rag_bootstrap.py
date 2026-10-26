"""
First-run setup for retrieval: embed the project's own question->SQL examples when the
vector store is empty, so a fresh clone works without running scripts/build_rag_index.py.

Runs in a background thread at startup. It never raises: without an API key, or when the
embedding service is unavailable, the app simply keeps using the built-in prompt examples.
"""
from __future__ import annotations

import json
import logging
import os
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)

EXAMPLES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rag_examples.json")


def _index_project_examples() -> None:
    try:
        from app.services.rag_service import get_runtime

        index = get_runtime().example_index()
        if index.count() > 0:
            return
        with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
            items = json.load(f)
        added = index.add(items)
        logger.info("RAG bootstrap: embedded %d project examples.", added)
    except Exception as exc:  # startup must never fail because of retrieval
        logger.warning("RAG bootstrap skipped: %s", exc)


def start_background_bootstrap() -> None:
    if not (settings.GEMINI_API_KEY and settings.RAG_EXAMPLES_ENABLED):
        return
    threading.Thread(target=_index_project_examples, name="rag-bootstrap", daemon=True).start()
