"""
Retrieval-augmented prompt context for Text-to-SQL.

Two retrievers feed the prompt:

  1. SchemaIndex  - one "card" per table (name, description, columns, links). The question
                    is embedded and only the closest tables are sent to the model, plus the
                    tables they join to (foreign-key expansion).
  2. ExampleIndex - question->SQL pairs (Spider training set + project examples). The most
                    similar questions become few-shot examples.

`RagRuntime.prepare()` decides what to use for one request, never raises, and records in
`meta` what happened (and why anything fell back to the old behaviour).

This module avoids importing the database layer or the web framework so it can be tested
and reused by the evaluation scripts. Configuration is passed in via `RagConfig`.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from app.services import prompt_builder
from app.services.embedding_service import Embedder, get_embedder
from app.services.vector_store import Hit, VectorStore, open_store

logger = logging.getLogger(__name__)

SCHEMA_QUERY_TASK = "RETRIEVAL_QUERY"
SCHEMA_DOC_TASK = "RETRIEVAL_DOCUMENT"
EXAMPLE_TASK = "SEMANTIC_SIMILARITY"  # question vs question: symmetric task type


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def norm_question(text: str) -> str:
    """Lower-case, strip punctuation, collapse spaces (used for hold-out matching)."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def _fk_struct(info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Structured foreign keys for a schema entry (parses the legacy string form if needed)."""
    if info.get("foreign_keys_struct") is not None:
        return list(info["foreign_keys_struct"])
    out = []
    for raw in info.get("foreign_keys", []) or []:
        m = re.search(r"->\s*([A-Za-z0-9_]+)\.", str(raw))
        cols = re.match(r"\[(.*?)\]", str(raw))
        if m:
            out.append({
                "columns": [c.strip(" '\"") for c in cols.group(1).split(",")] if cols else [],
                "ref_table": m.group(1),
                "ref_columns": [],
            })
    return out


def build_cards(schema: Dict[str, Dict[str, Any]], descriptions: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """One short text card per table; this is what gets embedded."""
    descriptions = descriptions or {}
    cards: Dict[str, str] = {}
    for table, info in schema.items():
        lines = [f"Table: {table.replace('_', ' ')} ({table})"]
        if descriptions.get(table):
            lines.append(f"Description: {descriptions[table]}")
        cols = info.get("columns") or [c.split(" ", 1)[0] for c in info.get("detailed_columns", [])]
        lines.append("Columns: " + ", ".join(str(c).replace("_", " ") for c in cols))
        links = [f"{fk['ref_table']} (via {', '.join(fk.get('columns', []))})"
                 for fk in _fk_struct(info) if fk.get("ref_table")]
        if links:
            lines.append("Links to: " + ", ".join(links))
        cards[table] = "\n".join(lines)
    return cards


def expand_tables(selected: List[str], schema: Dict[str, Dict[str, Any]], max_tables: int) -> List[str]:
    """
    Add the tables the model needs in order to JOIN the selected ones:
      * tables referenced by a selected table (forward foreign keys), and
      * bridge tables that reference at least two of the tables chosen so far
        (e.g. `enrollments` between `students` and `courses`).
    """
    refs = {t: {fk["ref_table"] for fk in _fk_struct(info) if fk.get("ref_table") in schema}
            for t, info in schema.items()}
    chosen = list(selected)
    for t in selected:
        for r in sorted(refs.get(t, ())):
            if r not in chosen:
                chosen.append(r)
    base = set(chosen)
    for t in sorted(schema):
        if t not in base and len(refs.get(t, set()) & base) >= 2:
            chosen.append(t)
    return chosen[:max_tables]


# ---------------------------------------------------------------------------
# Schema retrieval
# ---------------------------------------------------------------------------
@dataclass
class SchemaRetrieval:
    tables: List[str]                      # final list sent to the model (retrieved first, then expansion)
    retrieved: List[Tuple[str, float]]     # (table, similarity) straight from the vector search
    expanded: List[str]                    # tables added by foreign-key expansion
    total_tables: int


class SchemaIndex:
    def __init__(self, schema: Dict[str, Dict[str, Any]], embedder: Embedder, backend: str = "chroma",
                 store_path: Optional[str] = None, namespace: str = "default",
                 descriptions: Optional[Dict[str, str]] = None):
        self.schema = schema
        self.embedder = embedder
        self.cards = build_cards(schema, descriptions)
        self.signature = self.signature_for(self.cards, embedder)
        self.store: VectorStore = open_store(backend, f"schema_{namespace}", self.signature, store_path)
        self._ensure_built()

    @staticmethod
    def signature_for(cards: Dict[str, str], embedder: Embedder) -> str:
        blob = json.dumps(cards, sort_keys=True) + "|" + embedder.name
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _ensure_built(self) -> None:
        existing = self.store.ids()
        missing = [t for t in self.cards if t not in existing]
        if not missing:
            return
        vectors = self.embedder.embed([self.cards[t] for t in missing], SCHEMA_DOC_TASK)
        self.store.upsert(missing, vectors, [self.cards[t] for t in missing], [{"table": t} for t in missing])
        logger.info("Schema index built: %d tables embedded (%d total).", len(missing), len(self.cards))

    def retrieve(self, question: str, k: int = 6, max_tables: int = 12) -> SchemaRetrieval:
        qvec = self.embedder.embed_query(question, SCHEMA_QUERY_TASK)
        hits = self.store.query(qvec, k)
        retrieved = [(h.id, round(h.score, 4)) for h in hits if h.id in self.schema]
        top = [t for t, _ in retrieved]
        final = expand_tables(top, self.schema, max_tables)
        return SchemaRetrieval(tables=final, retrieved=retrieved,
                               expanded=[t for t in final if t not in top], total_tables=len(self.schema))


# ---------------------------------------------------------------------------
# Example retrieval
# ---------------------------------------------------------------------------
@dataclass
class ExampleHit:
    question: str
    sql: str
    source: str       # "project" or "spider"
    db_id: str
    score: float


class ExampleIndex:
    def __init__(self, embedder: Embedder, backend: str = "chroma", store_path: Optional[str] = None):
        self.embedder = embedder
        signature = hashlib.sha256(embedder.name.encode("utf-8")).hexdigest()
        self.store: VectorStore = open_store(backend, "sql_examples", signature, store_path)

    def count(self) -> int:
        return self.store.count()

    def add(self, items: Sequence[Dict[str, str]], batch_size: int = 100,
            progress: Optional[Callable[[int, int], None]] = None) -> int:
        """
        Embed and store items ({id, question, sql, db_id, source}). Resumable: ids already in
        the store are skipped, and every batch is saved as soon as it is embedded.
        """
        existing = self.store.ids()
        todo = [it for it in items if it["id"] not in existing]
        done = 0
        for start in range(0, len(todo), batch_size):
            chunk = todo[start:start + batch_size]
            vectors = self.embedder.embed([it["question"] for it in chunk], EXAMPLE_TASK)
            self.store.upsert(
                [it["id"] for it in chunk], vectors, [it["question"] for it in chunk],
                [{"sql": it["sql"], "db_id": it.get("db_id", ""), "source": it.get("source", "spider")} for it in chunk],
            )
            done += len(chunk)
            if progress:
                progress(done, len(todo))
        return done

    def retrieve(self, question: str, k: int = 4, exclude_questions: Optional[Set[str]] = None,
                 sources: Optional[Set[str]] = None) -> List[ExampleHit]:
        """`sources` limits results to examples from those sources (e.g. {"project"}); None = all."""
        exclude = exclude_questions or set()
        qvec = self.embedder.embed_query(question, EXAMPLE_TASK)
        # when filtering by source, over-fetch: unwanted sources can crowd the top results
        n = k + len(exclude) + 8
        if sources:
            n = min(max(n * 10, 100), max(self.store.count(), 1))
        hits: List[Hit] = self.store.query(qvec, n)
        out: List[ExampleHit] = []
        seen: Set[str] = set()
        for h in hits:
            if sources and h.metadata.get("source", "spider") not in sources:
                continue
            key = norm_question(h.document)
            if key in exclude or key in seen:
                continue
            seen.add(key)
            out.append(ExampleHit(h.document, h.metadata.get("sql", ""), h.metadata.get("source", "spider"),
                                  h.metadata.get("db_id", ""), round(h.score, 4)))
            if len(out) == k:
                break
        return out


# ---------------------------------------------------------------------------
# Runtime: per-request decisions with safe fallbacks
# ---------------------------------------------------------------------------
@dataclass
class RagConfig:
    schema_enabled: bool = True          # auto mode: retrieve only when the schema is large
    schema_min_tables: int = 1
    schema_top_k: int = 4
    schema_max_tables: int = 6
    examples_enabled: bool = True
    examples_top_k: int = 4
    example_sources: Optional[Set[str]] = None  # e.g. {"project"}; None = every source in the index
    backend: str = "chroma"              # "chroma" | "memory"
    schema_backend: Optional[str] = None  # defaults to `backend`
    store_path: Optional[str] = None
    include_keys: bool = True            # PK/FK info in the schema DDL (all modes)
    descriptions: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_settings(cls) -> "RagConfig":
        from app.core.config import settings  # lazy import

        descriptions: Dict[str, str] = {}
        path = os.path.join(os.path.dirname(__file__), "..", "data", "schema_descriptions.json")
        try:
            with open(path, "r") as f:
                descriptions = json.load(f)
        except (OSError, ValueError):
            pass
        return cls(
            schema_enabled=settings.RAG_SCHEMA_ENABLED,
            schema_min_tables=settings.RAG_SCHEMA_MIN_TABLES,
            schema_top_k=settings.RAG_SCHEMA_TOP_K,
            schema_max_tables=settings.RAG_SCHEMA_MAX_TABLES,
            examples_enabled=settings.RAG_EXAMPLES_ENABLED,
            examples_top_k=settings.RAG_EXAMPLES_TOP_K,
            example_sources={x.strip() for x in str(getattr(settings, "RAG_EXAMPLE_SOURCES", "")).split(",") if x.strip()} or None,
            backend=settings.RAG_VECTOR_BACKEND,
            store_path=settings.RAG_STORE_PATH,
            include_keys=settings.SCHEMA_INCLUDE_KEYS,
            descriptions=descriptions,
        )


@dataclass
class RagContext:
    schema_text: Optional[str]      # None -> caller uses its default full-schema text
    examples_text: Optional[str]
    include_static_block: bool
    meta: Dict[str, Any]


class RagRuntime:
    def __init__(self, cfg: RagConfig, embedder_getter: Callable[[], Embedder] = get_embedder):
        self.cfg = cfg
        self._get_embedder = embedder_getter
        self._lock = threading.Lock()
        self._schema_indexes: Dict[Tuple[str, str], SchemaIndex] = {}
        self._example_index: Optional[ExampleIndex] = None

    # -- indexes ----------------------------------------------------------------
    def schema_index(self, schema: Dict[str, Dict[str, Any]], namespace: str = "default") -> SchemaIndex:
        embedder = self._get_embedder()
        cards = build_cards(schema, self.cfg.descriptions)
        sig = SchemaIndex.signature_for(cards, embedder)
        with self._lock:
            idx = self._schema_indexes.get((namespace, sig))
            if idx is None:
                idx = SchemaIndex(schema, embedder, self.cfg.schema_backend or self.cfg.backend,
                                  self.cfg.store_path, namespace, self.cfg.descriptions)
                self._schema_indexes[(namespace, sig)] = idx
            return idx

    def example_index(self) -> ExampleIndex:
        embedder = self._get_embedder()
        with self._lock:
            if self._example_index is None or self._example_index.embedder is not embedder:
                self._example_index = ExampleIndex(embedder, self.cfg.backend, self.cfg.store_path)
            return self._example_index

    # -- per-request context ------------------------------------------------------
    def prepare(self, question: str, schema: Dict[str, Dict[str, Any]], *,
                use_schema_rag: Optional[bool] = None, use_example_rag: Optional[bool] = None,
                static_examples: Optional[bool] = None, holdout: bool = False,
                namespace: str = "default") -> RagContext:
        cfg = self.cfg
        total = len(schema)
        meta: Dict[str, Any] = {
            "schema": {"requested": use_schema_rag, "used": False, "total_tables": total,
                       "tables": [], "retrieved": [], "expanded": [], "reason": None},
            "examples": {"requested": use_example_rag, "used": False, "count": 0, "items": [], "reason": None},
        }
        t0 = time.perf_counter()
        schema_text: Optional[str] = None
        examples_text: Optional[str] = None

        # ---- schema retrieval
        want_schema = use_schema_rag if use_schema_rag is not None else (
            cfg.schema_enabled and total >= cfg.schema_min_tables)
        if use_schema_rag is None and not want_schema:
            meta["schema"]["reason"] = (
                "disabled" if not cfg.schema_enabled
                else f"auto: {total} tables < {cfg.schema_min_tables}, sending the full schema")
        if want_schema and total:
            try:
                res = self.schema_index(schema, namespace).retrieve(question, cfg.schema_top_k, cfg.schema_max_tables)
                if res.tables:
                    schema_text = prompt_builder.format_schema_ddl(schema, res.tables, cfg.include_keys)
                    meta["schema"].update(used=True, tables=res.tables, expanded=res.expanded,
                                          retrieved=[{"table": t, "score": s} for t, s in res.retrieved])
                else:
                    meta["schema"]["reason"] = "no tables retrieved; using the full schema"
            except Exception as exc:  # embeddings/quota/vector store problems must never break a query
                logger.warning("Schema retrieval failed, using the full schema: %s", exc)
                meta["schema"]["reason"] = f"fallback to full schema: {type(exc).__name__}: {str(exc)[:160]}"

        # ---- example retrieval
        want_examples = use_example_rag if use_example_rag is not None else cfg.examples_enabled
        if want_examples:
            try:
                idx = self.example_index()
                if idx.count() == 0:
                    meta["examples"]["reason"] = ("example index is empty - run "
                                                  "`python scripts/build_rag_index.py`; using the built-in examples")
                else:
                    exclude = {norm_question(question)} if holdout else set()
                    hits = idx.retrieve(question, cfg.examples_top_k, exclude, cfg.example_sources)
                    if hits:
                        examples_text = prompt_builder.format_examples(hits)
                        meta["examples"].update(used=True, count=len(hits), items=[
                            {"question": h.question, "sql": h.sql, "source": h.source,
                             "db_id": h.db_id, "score": h.score} for h in hits])
                    else:
                        meta["examples"]["reason"] = "no similar examples found"
            except Exception as exc:
                logger.warning("Example retrieval failed, using built-in examples: %s", exc)
                meta["examples"]["reason"] = f"fallback to built-in examples: {type(exc).__name__}: {str(exc)[:160]}"

        # ---- the legacy hand-written block names every table, so it is off whenever RAG is active
        if static_examples is None:
            include_static = not (meta["schema"]["used"] or meta["examples"]["used"])
        else:
            include_static = static_examples
        meta["static_block"] = include_static
        meta["retrieval_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return RagContext(schema_text, examples_text, include_static, meta)


# ---------------------------------------------------------------------------
# Process-wide runtime for the web app
# ---------------------------------------------------------------------------
_runtime: Optional[RagRuntime] = None
_runtime_lock = threading.Lock()


def get_runtime() -> RagRuntime:
    global _runtime
    with _runtime_lock:
        if _runtime is None:
            _runtime = RagRuntime(RagConfig.from_settings())
        return _runtime


def set_runtime(runtime: Optional[RagRuntime]) -> None:
    global _runtime
    with _runtime_lock:
        _runtime = runtime
