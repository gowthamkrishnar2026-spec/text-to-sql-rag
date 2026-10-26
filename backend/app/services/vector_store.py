"""
Minimal vector-store layer for the RAG code.

Two interchangeable backends:
  * ChromaStore  - persistent ChromaDB collection (default in the app)
  * MemoryStore  - NumPy brute-force cosine search (tests, Spider evaluation,
                   and automatic fallback if ChromaDB is not installed)

All vectors must be L2-normalised, so similarity == cosine similarity == dot product.
`score` is always "higher is better" (cosine similarity).
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Hit:
    id: str
    document: str
    metadata: Dict[str, Any]
    score: float


class VectorStore:
    backend = "base"

    def count(self) -> int:
        raise NotImplementedError

    def ids(self) -> Set[str]:
        raise NotImplementedError

    def upsert(self, ids: Sequence[str], vectors: np.ndarray,
               documents: Sequence[str], metadatas: Sequence[Dict[str, Any]]) -> None:
        raise NotImplementedError

    def query(self, vector: np.ndarray, n: int) -> List[Hit]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------
class MemoryStore(VectorStore):
    backend = "memory"

    def __init__(self) -> None:
        self._ids: List[str] = []
        self._pos: Dict[str, int] = {}
        self._vecs: List[np.ndarray] = []
        self._docs: List[str] = []
        self._meta: List[Dict[str, Any]] = []
        self._mat: Optional[np.ndarray] = None
        self._lock = threading.Lock()

    def count(self) -> int:
        return len(self._ids)

    def ids(self) -> Set[str]:
        return set(self._ids)

    def upsert(self, ids, vectors, documents, metadatas) -> None:
        with self._lock:
            for i, id_ in enumerate(ids):
                vec = np.asarray(vectors[i], dtype=np.float32)
                if id_ in self._pos:
                    p = self._pos[id_]
                    self._vecs[p], self._docs[p], self._meta[p] = vec, documents[i], dict(metadatas[i])
                else:
                    self._pos[id_] = len(self._ids)
                    self._ids.append(id_)
                    self._vecs.append(vec)
                    self._docs.append(documents[i])
                    self._meta.append(dict(metadatas[i]))
            self._mat = None

    def query(self, vector, n) -> List[Hit]:
        with self._lock:
            if not self._ids or n <= 0:
                return []
            if self._mat is None:
                self._mat = np.vstack(self._vecs)
            sims = self._mat @ np.asarray(vector, dtype=np.float32)
            order = np.argsort(-sims)[: min(n, len(self._ids))]
            return [Hit(self._ids[i], self._docs[i], dict(self._meta[i]), float(sims[i])) for i in order]


# ---------------------------------------------------------------------------
# ChromaDB adapter
# ---------------------------------------------------------------------------
_chroma_clients: Dict[str, Any] = {}
_chroma_lock = threading.Lock()
_UPSERT_CHUNK = 1000


def _get_chroma_client(path: Optional[str]):
    import chromadb
    from chromadb.config import Settings

    key = path or ":memory:"
    with _chroma_lock:
        client = _chroma_clients.get(key)
        if client is None:
            settings = Settings(anonymized_telemetry=False)
            if path:
                os.makedirs(path, exist_ok=True)
                client = chromadb.PersistentClient(path=path, settings=settings)
            else:
                client = chromadb.EphemeralClient(settings=settings)
            _chroma_clients[key] = client
        return client


class ChromaStore(VectorStore):
    backend = "chroma"

    def __init__(self, path: Optional[str], logical_name: str, signature: str) -> None:
        client = _get_chroma_client(path)
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", logical_name)
        self.collection_name = f"{safe}_{signature[:12]}"
        self._col = client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=None,  # we always pass our own vectors
        )
        if path:
            self._drop_stale_collection(client, path, safe)

    def _drop_stale_collection(self, client, path: str, logical: str) -> None:
        """Remember which collection is current per logical name; delete the old one."""
        manifest_path = os.path.join(path, "rag_manifest.json")
        manifest: Dict[str, str] = {}
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        except (OSError, ValueError):
            manifest = {}
        old = manifest.get(logical)
        if old and old != self.collection_name:
            try:
                client.delete_collection(old)
                logger.info("Removed stale RAG collection %s", old)
            except Exception as exc:  # best effort only
                logger.debug("Could not delete stale collection %s: %s", old, exc)
        if old != self.collection_name:
            manifest[logical] = self.collection_name
            try:
                with open(manifest_path, "w") as f:
                    json.dump(manifest, f, indent=2)
            except OSError as exc:
                logger.debug("Could not write RAG manifest: %s", exc)

    def count(self) -> int:
        return int(self._col.count())

    def ids(self) -> Set[str]:
        return set(self._col.get(include=[])["ids"])

    def upsert(self, ids, vectors, documents, metadatas) -> None:
        for start in range(0, len(ids), _UPSERT_CHUNK):
            end = start + _UPSERT_CHUNK
            self._col.upsert(
                ids=list(ids[start:end]),
                embeddings=[np.asarray(v, dtype=np.float32).tolist() for v in vectors[start:end]],
                documents=list(documents[start:end]),
                metadatas=[dict(m) for m in metadatas[start:end]],
            )

    def query(self, vector, n) -> List[Hit]:
        total = self.count()
        n = min(n, total)
        if n <= 0:
            return []
        res = self._col.query(
            query_embeddings=[np.asarray(vector, dtype=np.float32).tolist()],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        hits: List[Hit] = []
        for id_, doc, meta, dist in zip(res["ids"][0], res["documents"][0],
                                        res["metadatas"][0], res["distances"][0]):
            hits.append(Hit(id_, doc, dict(meta or {}), 1.0 - float(dist)))  # cosine distance -> similarity
        return hits


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
_memory_stores: Dict[Tuple[str, str], MemoryStore] = {}
_memory_lock = threading.Lock()


def open_store(backend: str, logical_name: str, signature: str, path: Optional[str] = None) -> VectorStore:
    """Open (or create) the store for `logical_name`. A new `signature` means a new, empty store."""
    if backend == "chroma":
        try:
            return ChromaStore(path, logical_name, signature)
        except ImportError:
            logger.warning("chromadb is not installed - using an in-memory vector store "
                           "(index will not persist). Run: pip install chromadb")
        except Exception as exc:
            logger.warning("ChromaDB unavailable (%s) - using an in-memory vector store.", exc)
    with _memory_lock:
        key = (logical_name, signature)
        store = _memory_stores.get(key)
        if store is None:
            store = _memory_stores[key] = MemoryStore()
        return store


def reset_memory_stores() -> None:
    with _memory_lock:
        _memory_stores.clear()
