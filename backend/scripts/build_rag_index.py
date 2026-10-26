#!/usr/bin/env python3
"""
Build the RAG example index: question -> SQL pairs embedded with Gemini and stored in ChromaDB.

Sources
  * Spider training set  (datasets/spider/train_spider.json, train_others.json; falls back to
                          datasets/huggingface_spider/train.json)
  * Project examples     (backend/app/data/rag_examples.json)

The script is RESUMABLE: every batch is saved as soon as it is embedded, and ids already in
the store are skipped, so if you hit an API quota just run it again later.

Usage (from the backend/ directory):
  PYTHONPATH=. python scripts/build_rag_index.py --check-store        # offline ChromaDB self-check
  PYTHONPATH=. python scripts/build_rag_index.py --dry-run            # show what would be indexed
  PYTHONPATH=. python scripts/build_rag_index.py --max-examples 300   # small first run
  PYTHONPATH=. python scripts/build_rag_index.py                      # default: 2000 Spider pairs
  PYTHONPATH=. python scripts/build_rag_index.py --stats              # how many examples are indexed
"""
import argparse
import hashlib
import json
import os
import random
import re
import shutil
import sys
import tempfile
from collections import defaultdict
from typing import Dict, List, Optional

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(BACKEND, ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
except ImportError:
    pass


def _read_json_any(path: str) -> List[dict]:
    """Reads a JSON array or JSON-lines file."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else []
    except ValueError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def load_spider_pairs(spider_dir: str, hf_train: str) -> List[Dict[str, str]]:
    files = [os.path.join(spider_dir, "train_spider.json"), os.path.join(spider_dir, "train_others.json")]
    rows: List[dict] = []
    for path in files:
        if os.path.exists(path):
            rows.extend(_read_json_any(path))
    if not rows and os.path.exists(hf_train):
        rows = _read_json_any(hf_train)
    pairs = []
    for r in rows:
        question = (r.get("question") or "").strip()
        q, s = r.get("query"), r.get("sql")  # Spider's "sql" key may be a parsed dict, not text
        sql = (q if isinstance(q, str) else (s if isinstance(s, str) else "")).strip()
        if question and sql:
            pairs.append({"question": question, "sql": sql, "db_id": str(r.get("db_id", ""))})
    return pairs


def select_pairs(pairs: List[Dict[str, str]], max_examples: int, seed: int) -> List[Dict[str, str]]:
    """Read-only, reasonably short SQL; de-duplicated; spread evenly across databases."""
    seen = set()
    by_db: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for p in pairs:
        sql = p["sql"]
        if not re.match(r"^\s*(select|with)\b", sql, re.I) or len(sql) > 600:
            continue
        key = re.sub(r"\W+", " ", p["question"].lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        by_db[p["db_id"]].append(p)
    rng = random.Random(seed)
    for items in by_db.values():
        rng.shuffle(items)
    db_ids = sorted(by_db)
    rng.shuffle(db_ids)
    chosen: List[Dict[str, str]] = []
    depth = 0
    while len(chosen) < max_examples and any(len(by_db[d]) > depth for d in db_ids):
        for d in db_ids:
            if len(by_db[d]) > depth and len(chosen) < max_examples:
                chosen.append(by_db[d][depth])
        depth += 1
    for p in chosen:
        p["id"] = "spider-" + hashlib.sha1((p["question"] + "|" + p["sql"]).encode()).hexdigest()[:16]
        p["source"] = "spider"
    return chosen


def load_project_examples() -> List[Dict[str, str]]:
    path = os.path.join(BACKEND, "app", "data", "rag_examples.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def check_store() -> int:
    """Offline self-check of the vector stores (no API calls, no quota used)."""
    from app.services.vector_store import ChromaStore, MemoryStore

    rng = np.random.default_rng(0)
    vecs = rng.normal(size=(5, 32)).astype(np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    ids = [f"id{i}" for i in range(5)]
    docs = [f"doc {i}" for i in range(5)]
    metas = [{"sql": f"SELECT {i}", "source": "test"} for i in range(5)]

    def run(store, label):
        store.upsert(ids, vecs, docs, metas)
        store.upsert(ids[:1], vecs[:1], docs[:1], metas[:1])  # upsert must not duplicate
        assert store.count() == 5, f"{label}: count {store.count()} != 5"
        assert store.ids() == set(ids), f"{label}: ids mismatch"
        hits = store.query(vecs[3], 3)
        assert hits and hits[0].id == "id3", f"{label}: nearest hit was {hits[0].id if hits else None}"
        assert abs(hits[0].score - 1.0) < 1e-3, f"{label}: self-similarity {hits[0].score}"
        assert hits[0].metadata.get("sql") == "SELECT 3", f"{label}: metadata not returned"
        assert len(store.query(vecs[0], 50)) == 5, f"{label}: n larger than count not handled"
        print(f"  OK  {label}")

    print("Vector store self-check")
    run(MemoryStore(), "MemoryStore (NumPy)")
    tmp = tempfile.mkdtemp(prefix="rag_check_")
    try:
        try:
            import chromadb
            print(f"  chromadb version {chromadb.__version__}")
        except ImportError:
            print("  FAIL chromadb is not installed. Run: pip install chromadb")
            return 1
        run(ChromaStore(tmp, "selfcheck", "a" * 16), "ChromaStore (persistent)")
        # reopen: data must persist
        reopened = ChromaStore(tmp, "selfcheck", "a" * 16)
        assert reopened.count() == 5, "ChromaStore did not persist data"
        print("  OK  ChromaStore persistence")
    except AssertionError as exc:
        print(f"  FAIL {exc}")
        return 1
    except Exception as exc:
        print(f"  FAIL ChromaStore raised {type(exc).__name__}: {exc}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("All checks passed.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the RAG example index.")
    ap.add_argument("--spider-dir", default=os.path.join(ROOT, "datasets", "spider"))
    ap.add_argument("--hf-train", default=os.path.join(ROOT, "datasets", "huggingface_spider", "train.json"))
    ap.add_argument("--max-examples", type=int, default=2000, help="Spider pairs to index (default 2000)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--batch-size", type=int, default=100)
    ap.add_argument("--no-project", action="store_true", help="Skip app/data/rag_examples.json")
    ap.add_argument("--dry-run", action="store_true", help="Count what would be indexed; no API calls")
    ap.add_argument("--stats", action="store_true", help="Print how many examples are in the index and exit")
    ap.add_argument("--check-store", action="store_true", help="Offline self-check of the vector stores")
    args = ap.parse_args()

    if args.check_store:
        return check_store()

    pairs = load_spider_pairs(args.spider_dir, args.hf_train)
    chosen = select_pairs(pairs, args.max_examples, args.seed)
    items = ([] if args.no_project else load_project_examples()) + chosen
    print(f"Spider pairs found: {len(pairs)}  |  selected: {len(chosen)}  |  total to index: {len(items)}")

    if args.dry_run:
        for it in items[:5]:
            print(f"  e.g. [{it['source']}] {it['question']}  ->  {it['sql'][:70]}")
        return 0
    if not items:
        print("Nothing to index: no Spider files found. Check --spider-dir / --hf-train.")
        return 1

    from app.core.config import settings
    from app.services.embedding_service import EmbeddingError, GeminiEmbedder
    from app.services.rag_service import ExampleIndex

    try:
        embedder = GeminiEmbedder(
            api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_EMBEDDING_MODEL,
            dim=settings.RAG_EMBEDDING_DIM, timeout=30, max_retries=6, base_delay=3.0)
    except EmbeddingError as exc:
        print(f"Error: {exc}")
        return 1

    index = ExampleIndex(embedder, settings.RAG_VECTOR_BACKEND, settings.RAG_STORE_PATH)
    if args.stats:
        print(f"Examples in index: {index.count()} (embedding: {embedder.name}, store: {settings.RAG_STORE_PATH})")
        return 0
    before = index.count()
    print(f"Index currently holds {before} examples (embedding: {embedder.name}).")

    def progress(done: int, total: int) -> None:
        print(f"  embedded {done}/{total}", end="\r", flush=True)

    try:
        added = index.add(items, args.batch_size, progress)
    except EmbeddingError as exc:
        print(f"\nStopped early: {exc}\nProgress so far is saved - run the same command again later to resume.")
        return 2
    print(f"\nAdded {added} new examples. Index now holds {index.count()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
