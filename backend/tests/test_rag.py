"""
Tests for the RAG layer (retrieval, prompts, embedder retries, stores, eval helpers).

Run from backend/:   PYTHONPATH=. pytest tests/test_rag.py
No network, API key or database is needed: embeddings come from a deterministic fake.
These tests check the PLUMBING (indexing, retrieval, expansion, fallbacks). They cannot
measure retrieval quality with real Gemini embeddings; use benchmarks/rag_spider_eval.py for that.
"""
import importlib.util
import json
import os
import re
import sqlite3
import tempfile
import zlib

import numpy as np

from app.services import prompt_builder
from app.services.embedding_service import Embedder, EmbeddingError, GeminiEmbedder
from app.services.llm_client import LLMError, call_gemini
from app.services.rag_service import (ExampleIndex, RagConfig, RagRuntime, SchemaIndex, build_cards,
                                      expand_tables, norm_question)
from app.services.vector_store import MemoryStore, reset_memory_stores

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Test doubles and fixtures
# ---------------------------------------------------------------------------
class FakeEmbedder(Embedder):
    """Deterministic bag-of-words + character-trigram embedder (lexical similarity only)."""
    name = "fake:test:128"
    DIM = 128

    def _vec(self, text):
        v = np.zeros(self.DIM, dtype=np.float32)
        toks = [t[:-1] if len(t) > 3 and t.endswith("s") else t for t in re.findall(r"[a-z0-9]+", text.lower())]
        feats = list(toks)
        for t in toks:
            feats += [t[i:i + 3] for i in range(max(1, len(t) - 2))]
        for f in feats:
            v[zlib.crc32(f.encode()) % self.DIM] += 1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed(self, texts, task_type="RETRIEVAL_DOCUMENT"):
        return np.vstack([self._vec(t) for t in texts]) if texts else np.zeros((0, self.DIM), np.float32)


class BrokenEmbedder(Embedder):
    name = "broken:0"

    def embed(self, texts, task_type="RETRIEVAL_DOCUMENT"):
        raise EmbeddingError("quota exceeded")


def _table(cols, pk=None, fks=None):
    return {"columns": cols, "detailed_columns": [f"{c} INTEGER" for c in cols],
            "primary_keys": pk or [], "foreign_keys_struct": fks or []}


def _fk(col, ref, ref_col):
    return {"columns": [col], "ref_table": ref, "ref_columns": [ref_col]}


def university_schema():
    return {
        "departments": _table(["department_id", "department_name", "building", "budget"], ["department_id"]),
        "students": _table(["student_id", "first_name", "last_name", "department_id", "cgpa"], ["student_id"],
                           [_fk("department_id", "departments", "department_id")]),
        "courses": _table(["course_id", "course_title", "credits", "department_id"], ["course_id"],
                          [_fk("department_id", "departments", "department_id")]),
        "enrollments": _table(["enrollment_id", "student_id", "course_id", "grade"], ["enrollment_id"],
                              [_fk("student_id", "students", "student_id"), _fk("course_id", "courses", "course_id")]),
        "products": _table(["product_id", "product_name", "unit_price"], ["product_id"]),
        "employees": _table(["emp_id", "emp_name", "salary"], ["emp_id"]),
    }


NOUNS = ["invoice", "shipment", "warehouse", "supplier", "vehicle", "driver", "route", "pallet", "carrier",
         "tariff", "customs", "depot", "container", "voyage", "harbor", "crane", "ledger", "payroll", "asset",
         "tenant", "lease", "ticket", "sensor", "reading", "battery", "turbine", "pipeline", "valve", "meter",
         "outage", "permit", "inspector", "violation", "parcel", "district", "zone", "station", "operator",
         "contract", "bidder"]


def large_schema():
    return {n: _table([f"{n}_id", f"{n}_name", "created_on"], [f"{n}_id"]) for n in NOUNS}


def runtime(embedder=None, **cfg):
    reset_memory_stores()
    emb = embedder or FakeEmbedder()
    defaults = dict(backend="memory", schema_min_tables=0, schema_top_k=3, schema_max_tables=8, examples_top_k=3)
    defaults.update(cfg)
    return RagRuntime(RagConfig(**defaults), embedder_getter=lambda: emb)


def expect_raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type as exc:
        return exc
    raise AssertionError(f"{exc_type.__name__} was not raised")


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def test_legacy_prompt_contains_static_block_and_no_examples():
    p = prompt_builder.build_sql_prompt("Show students", "CREATE TABLE t (a INTEGER);")
    assert "Key Schema Mapping Guidelines:" in p and "4. Column Selection" in p
    assert p.endswith("User Question: Show students")


def test_prompt_without_static_block_and_with_examples():
    class Ex:
        question, sql, source = "How many singers?", "SELECT count(*) FROM singer", "spider"

    text = prompt_builder.format_examples([Ex()])
    assert "(other database)" in text and "SELECT count(*) FROM singer;" in text
    p = prompt_builder.build_sql_prompt("q", "SCHEMA", text, include_static_block=False, dialect="SQLite")
    assert "Key Schema Mapping Guidelines" not in p and "1. Column Selection" in p
    assert "SQLite-compatible" in p and p.index("SCHEMA") < p.index("Reference examples")


def test_schema_ddl_with_and_without_keys():
    schema = university_schema()
    rich = prompt_builder.format_schema_ddl(schema, ["enrollments"], include_keys=True)
    assert "enrollment_id INTEGER PRIMARY KEY" in rich
    assert "FOREIGN KEY (student_id) REFERENCES students(student_id)" in rich
    plain = prompt_builder.format_schema_ddl(schema, ["enrollments"], include_keys=False)
    assert "FOREIGN KEY" not in plain and "PRIMARY KEY" not in plain
    assert plain == "CREATE TABLE enrollments (enrollment_id INTEGER, student_id INTEGER, course_id INTEGER, grade INTEGER);"


# ---------------------------------------------------------------------------
# Cards and foreign-key expansion
# ---------------------------------------------------------------------------
def test_cards_include_description_columns_and_links():
    cards = build_cards(university_schema(), {"students": "Enrolled university students"})
    assert "Enrolled university students" in cards["students"]
    assert "cgpa" in cards["students"] and "departments (via department_id)" in cards["students"]


def test_expand_adds_forward_refs_and_bridge_tables():
    schema = university_schema()
    # students + courses selected -> departments (forward ref) and enrollments (bridge) are needed to join
    out = expand_tables(["students", "courses"], schema, max_tables=10)
    assert out[:2] == ["students", "courses"]
    assert "departments" in out and "enrollments" in out
    assert "products" not in out and "employees" not in out


def test_expand_respects_cap_and_keeps_retrieved_first():
    out = expand_tables(["students", "courses"], university_schema(), max_tables=3)
    assert len(out) == 3 and out[:2] == ["students", "courses"]


def test_expand_parses_legacy_string_foreign_keys():
    schema = {"a": {"columns": ["id"], "foreign_keys": []},
              "b": {"columns": ["a_id"], "foreign_keys": ["['a_id'] -> a.['id']"]}}
    assert expand_tables(["b"], schema, 5) == ["b", "a"]


# ---------------------------------------------------------------------------
# Schema retrieval
# ---------------------------------------------------------------------------
def test_schema_retrieval_finds_relevant_tables_in_large_schema():
    rt = runtime()
    schema = large_schema()
    ctx = rt.prepare("List every shipment together with its warehouse", schema, use_schema_rag=True, use_example_rag=False)
    used = ctx.meta["schema"]
    assert used["used"] and "shipment" in used["tables"] and "warehouse" in used["tables"]
    full = prompt_builder.format_schema_ddl(schema)
    assert len(ctx.schema_text) < len(full) / 3, "retrieved schema should be far smaller than the full schema"
    assert ctx.include_static_block is False


def test_schema_index_is_built_once_and_reused():
    reset_memory_stores()
    emb = FakeEmbedder()
    calls = []
    original = emb.embed
    emb.embed = lambda texts, task="RETRIEVAL_DOCUMENT": (calls.append(len(texts)), original(texts, task))[1]
    schema = large_schema()
    SchemaIndex(schema, emb, backend="memory")
    SchemaIndex(schema, emb, backend="memory")  # same schema + embedder -> same store, nothing re-embedded
    assert calls == [len(schema)]


def test_changed_schema_gets_a_fresh_index():
    reset_memory_stores()
    emb = FakeEmbedder()
    a = SchemaIndex(university_schema(), emb, backend="memory")
    changed = university_schema()
    changed["students"]["columns"].append("scholarship")
    b = SchemaIndex(changed, emb, backend="memory")
    assert a.signature != b.signature and a.store is not b.store


def test_auto_mode_skips_retrieval_for_small_schemas():
    rt = runtime(schema_min_tables=15)
    ctx = rt.prepare("students with high cgpa", university_schema(), use_example_rag=False)
    assert ctx.meta["schema"]["used"] is False and "full schema" in ctx.meta["schema"]["reason"]
    assert ctx.schema_text is None and ctx.include_static_block is True  # exactly the old behaviour


def test_explicit_request_forces_retrieval_even_for_small_schemas():
    rt = runtime(schema_min_tables=15)
    ctx = rt.prepare("students with high cgpa", university_schema(), use_schema_rag=True, use_example_rag=False)
    assert ctx.meta["schema"]["used"] and "students" in ctx.meta["schema"]["tables"]


# ---------------------------------------------------------------------------
# Example retrieval
# ---------------------------------------------------------------------------
def _items():
    return [
        {"id": "p1", "question": "Show all students with CGPA greater than 8", "sql": "SELECT * FROM students WHERE cgpa > 8",
         "db_id": "project", "source": "project"},
        {"id": "s1", "question": "How many singers are from each country?",
         "sql": "SELECT country, count(*) FROM singer GROUP BY country", "db_id": "concert_singer", "source": "spider"},
        {"id": "s2", "question": "List the names of all stadiums", "sql": "SELECT name FROM stadium",
         "db_id": "concert_singer", "source": "spider"},
        {"id": "s3", "question": "What is the average salary of employees per department?",
         "sql": "SELECT dept, avg(salary) FROM employee GROUP BY dept", "db_id": "company", "source": "spider"},
    ]


def test_example_retrieval_returns_most_similar_first():
    reset_memory_stores()
    idx = ExampleIndex(FakeEmbedder(), backend="memory")
    assert idx.add(_items()) == 4 and idx.count() == 4
    hits = idx.retrieve("How many singers are there in each country", k=2)
    assert hits[0].id if hasattr(hits[0], "id") else True
    assert hits[0].question.startswith("How many singers") and hits[0].source == "spider"


def test_example_add_is_resumable_and_idempotent():
    reset_memory_stores()
    idx = ExampleIndex(FakeEmbedder(), backend="memory")
    assert idx.add(_items()[:2]) == 2
    assert idx.add(_items()) == 2  # only the two new ones
    assert idx.add(_items()) == 0 and idx.count() == 4


def test_holdout_excludes_identical_question():
    reset_memory_stores()
    idx = ExampleIndex(FakeEmbedder(), backend="memory")
    idx.add(_items())
    q = "Show all students with CGPA greater than 8."
    with_leak = idx.retrieve(q, k=2)
    held_out = idx.retrieve(q, k=2, exclude_questions={norm_question(q)})
    assert with_leak[0].question.startswith("Show all students")
    assert all(norm_question(h.question) != norm_question(q) for h in held_out) and len(held_out) == 2


def test_example_source_filter_keeps_only_requested_sources():
    reset_memory_stores()
    idx = ExampleIndex(FakeEmbedder(), backend="memory")
    items = _items() + [{"id": "sp-1", "question": "Show all students with CGPA greater than 8 in the dorm",
                         "sql": "SELECT 1", "db_id": "dorm_1", "source": "spider"}]
    idx.add(items)
    q = "Show all students with CGPA greater than 8"
    everything = idx.retrieve(q, k=5)
    only_spider = idx.retrieve(q, k=5, sources={"spider"})
    assert any(h.source == "spider" for h in everything)
    assert only_spider and all(h.source == "spider" for h in only_spider)
    assert not any(h.source == "spider" for h in idx.retrieve(q, k=5, sources={"project"}))


def test_runtime_example_sources_config():
    rt = runtime(example_sources={"project"})
    rt.example_index().add(_items() + [{"id": "sp-1", "question": "Show all students with CGPA greater than 8 now",
                                         "sql": "SELECT 1", "db_id": "dorm_1", "source": "spider"}])
    ctx = rt.prepare("Show all students with CGPA greater than 8", university_schema(),
                     use_schema_rag=False, use_example_rag=True)
    assert ctx.meta["examples"]["used"]
    assert all(i["source"] == "project" for i in ctx.meta["examples"]["items"])


def test_runtime_uses_examples_and_turns_static_block_off():
    rt = runtime()
    rt.example_index().add(_items())
    ctx = rt.prepare("How many singers per country?", university_schema(), use_schema_rag=False, use_example_rag=True)
    assert ctx.meta["examples"]["used"] and ctx.meta["examples"]["count"] == 3
    assert "Reference examples" in ctx.examples_text and ctx.include_static_block is False


def test_runtime_holdout_flag():
    rt = runtime()
    rt.example_index().add(_items())
    q = "Show all students with CGPA greater than 8"
    leaked = rt.prepare(q, university_schema(), use_schema_rag=False, use_example_rag=True)
    clean = rt.prepare(q, university_schema(), use_schema_rag=False, use_example_rag=True, holdout=True)
    assert any(i["question"] == q for i in leaked.meta["examples"]["items"])
    assert not any(norm_question(i["question"]) == norm_question(q) for i in clean.meta["examples"]["items"])


# ---------------------------------------------------------------------------
# Fallbacks: RAG problems must never break a query
# ---------------------------------------------------------------------------
def test_empty_example_index_falls_back_to_builtin_examples():
    rt = runtime()
    ctx = rt.prepare("anything", university_schema(), use_schema_rag=False, use_example_rag=True)
    assert ctx.meta["examples"]["used"] is False and "empty" in ctx.meta["examples"]["reason"]
    assert ctx.include_static_block is True and ctx.examples_text is None


def test_embedding_failure_falls_back_to_full_schema_and_builtin_examples():
    rt = runtime(embedder=BrokenEmbedder())
    ctx = rt.prepare("anything", large_schema(), use_schema_rag=True, use_example_rag=True)
    assert ctx.schema_text is None and ctx.examples_text is None and ctx.include_static_block is True
    assert "fallback" in ctx.meta["schema"]["reason"] and "quota" in ctx.meta["schema"]["reason"]
    # the example index is empty here, so no embedding call is attempted: either reason is a safe fallback
    assert ctx.meta["examples"]["used"] is False and ctx.meta["examples"]["reason"]


def test_explicit_static_override():
    rt = runtime()
    ctx = rt.prepare("q", university_schema(), use_schema_rag=False, use_example_rag=False, static_examples=False)
    assert ctx.include_static_block is False
    ctx = rt.prepare("q", university_schema(), use_schema_rag=False, use_example_rag=False, static_examples=True)
    assert ctx.include_static_block is True


# ---------------------------------------------------------------------------
# Vector store
# ---------------------------------------------------------------------------
def test_memory_store_upsert_replaces_and_query_orders_by_similarity():
    s = MemoryStore()
    vecs = np.eye(3, dtype=np.float32)
    s.upsert(["a", "b", "c"], vecs, ["A", "B", "C"], [{}, {}, {}])
    s.upsert(["b"], vecs[1:2], ["B2"], [{"x": 1}])
    assert s.count() == 3
    hits = s.query(np.array([0, 1, 0], dtype=np.float32), 5)
    assert hits[0].id == "b" and hits[0].document == "B2" and hits[0].metadata == {"x": 1}
    assert len(hits) == 3


# ---------------------------------------------------------------------------
# Gemini embedder (HTTP mocked)
# ---------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, status, payload=None, text="", headers=None):
        self.status_code, self._payload, self.text, self.headers = status, payload or {}, text, headers or {}

    def json(self):
        return self._payload


def _ok(n, dim=4):
    return FakeResponse(200, {"embeddings": [{"values": [3.0] + [0.0] * (dim - 1)} for _ in range(n)]})


def test_embedder_batches_normalises_and_sends_key_in_header():
    seen = []

    def post(url, headers=None, json=None, timeout=None):
        seen.append((url, headers, len(json["requests"]), json["requests"][0]["taskType"]))
        return _ok(len(json["requests"]))

    emb = GeminiEmbedder("SECRET-KEY", dim=4, post=post)
    out = emb.embed([f"text {i}" for i in range(250)], "RETRIEVAL_DOCUMENT")
    assert out.shape == (250, 4) and np.allclose(np.linalg.norm(out, axis=1), 1.0)
    assert [s[2] for s in seen] == [100, 100, 50]
    assert all("SECRET-KEY" not in s[0] and s[1]["x-goog-api-key"] == "SECRET-KEY" for s in seen)


def test_embedder_retries_on_rate_limit_then_succeeds():
    calls = {"n": 0}

    def post(url, headers=None, json=None, timeout=None):
        calls["n"] += 1
        return FakeResponse(429, text="rate limited") if calls["n"] < 3 else _ok(len(json["requests"]))

    emb = GeminiEmbedder("k", dim=4, post=post, base_delay=0.0, max_retries=3)
    assert emb.embed(["x"]).shape == (1, 4) and calls["n"] == 3


def test_embedder_raises_after_retries_without_leaking_key():
    def post(url, headers=None, json=None, timeout=None):
        return FakeResponse(429, text="Quota exceeded")

    emb = GeminiEmbedder("TOPSECRET", dim=4, post=post, base_delay=0.0, max_retries=2)
    exc = expect_raises(EmbeddingError, emb.embed, ["x"])
    assert "429" in str(exc) and "TOPSECRET" not in str(exc)


def test_embedder_query_cache():
    calls = {"n": 0}

    def post(url, headers=None, json=None, timeout=None):
        calls["n"] += 1
        return _ok(len(json["requests"]))

    emb = GeminiEmbedder("k", dim=4, post=post)
    emb.embed_query("same question")
    emb.embed_query("same question")
    assert calls["n"] == 1


def test_embedder_requires_api_key():
    expect_raises(EmbeddingError, GeminiEmbedder, "")


# ---------------------------------------------------------------------------
# LLM client (HTTP mocked)
# ---------------------------------------------------------------------------
def _gemini_ok(text="SQL:\n```sql\nSELECT 1;\n```", tokens=321):
    return FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": text}]}}],
                              "usageMetadata": {"promptTokenCount": tokens}})


def test_llm_client_falls_through_models_and_reports_usage():
    tried = []

    def post(url, headers=None, json=None, timeout=None):
        tried.append(url)
        return FakeResponse(503, text="overloaded") if len(tried) == 1 else _gemini_ok()

    res = call_gemini("prompt", "k", ["m1", "m2"], post=post)
    assert res.model == "m2" and res.prompt_tokens == 321 and "SELECT 1" in res.text and len(tried) == 2


def test_llm_client_maps_total_failure_to_429_or_503():
    exc = expect_raises(LLMError, call_gemini, "p", "k", ["m1"], post=lambda *a, **k: FakeResponse(429, text="Quota exceeded"))
    assert exc.status_code == 429
    exc = expect_raises(LLMError, call_gemini, "p", "k", ["m1"], post=lambda *a, **k: FakeResponse(500, text="boom"))
    assert exc.status_code == 503 and "500" in exc.detail


# ---------------------------------------------------------------------------
# Script helpers
# ---------------------------------------------------------------------------
def _load_module(rel_path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BACKEND, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_index_select_pairs_filters_dedupes_and_spreads_databases():
    mod = _load_module("scripts/build_rag_index.py", "build_rag_index")
    pairs = [{"question": f"Question {i} about thing", "sql": "SELECT a FROM t", "db_id": f"db{i % 3}"} for i in range(30)]
    pairs += [{"question": "Drop it", "sql": "DROP TABLE t", "db_id": "db0"},       # not read-only
              {"question": "Question 1 about thing!", "sql": "SELECT a FROM t", "db_id": "db1"},  # duplicate
              {"question": "Long", "sql": "SELECT " + "x," * 400 + "y FROM t", "db_id": "db0"}]  # too long
    chosen = mod.select_pairs(pairs, 9, seed=1)
    assert len(chosen) == 9 and all(p["sql"].startswith("SELECT") for p in chosen)
    assert {p["db_id"] for p in chosen} == {"db0", "db1", "db2"} and all(p["id"].startswith("spider-") for p in chosen)


def test_build_index_loads_spider_and_json_lines_formats():
    mod = _load_module("scripts/build_rag_index.py", "build_rag_index2")
    with tempfile.TemporaryDirectory() as d:
        spider = os.path.join(d, "spider")
        os.makedirs(spider)
        with open(os.path.join(spider, "train_spider.json"), "w") as f:
            json.dump([{"db_id": "a", "question": "Q1", "query": "SELECT 1", "sql": {"select": []}}], f)
        assert mod.load_spider_pairs(spider, "nope.json") == [{"question": "Q1", "sql": "SELECT 1", "db_id": "a"}]
        hf = os.path.join(d, "train.json")
        with open(hf, "w") as f:
            f.write('{"db_id": "b", "question": "Q2", "query": "SELECT 2"}\n{"db_id": "c", "question": "Q3", "query": "SELECT 3"}\n')
        assert [p["question"] for p in mod.load_spider_pairs(os.path.join(d, "missing"), hf)] == ["Q2", "Q3"]


def test_spider_eval_schema_conversion_and_comparison_helpers():
    ev = _load_module("benchmarks/rag_spider_eval.py", "rag_spider_eval")
    entry = {"db_id": "demo", "table_names_original": ["singer", "concert"],
             "column_names_original": [[-1, "*"], [0, "id"], [0, "name"], [1, "cid"], [1, "singer_id"]],
             "column_types": ["text", "number", "text", "number", "number"],
             "primary_keys": [1, 3], "foreign_keys": [[4, 1]]}
    schema = ev.spider_schema(entry)
    assert schema["singer"]["columns"] == ["id", "name"] and schema["concert"]["primary_keys"] == ["cid"]
    assert schema["concert"]["foreign_keys_struct"] == [{"columns": ["singer_id"], "ref_table": "singer", "ref_columns": ["id"]}]
    assert ev.gold_tables(schema, "SELECT name FROM singer JOIN concert ON 1=1") == ["singer", "concert"]
    # result comparison
    assert ev.results_match([(1, "a"), (2, "b")], [(2, "b"), (1, "a")], ordered=False)
    assert not ev.results_match([(1, "a"), (2, "b")], [(2, "b"), (1, "a")], ordered=True)
    assert ev.results_match([(1, "a")], [("a", 1)], ordered=False)          # column order ignored
    assert ev.results_match([(1.0,)], [(1,)], ordered=False)                # 1 == 1.0
    assert not ev.results_match([(1,)], [(1,), (1,)], ordered=False)
    assert ev.extract_sql("SQL:\n```sql\nSELECT 1;\n```\nEXPLANATION: x") == "SELECT 1"


def test_spider_eval_sqlite_runner_is_read_only():
    ev = _load_module("benchmarks/rag_spider_eval.py", "rag_spider_eval2")
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "t.sqlite")
        con = sqlite3.connect(path)
        con.execute("CREATE TABLE t (a INTEGER)")
        con.execute("INSERT INTO t VALUES (1),(2)")
        con.commit()
        con.close()
        rows, err = ev.run_sqlite(path, "SELECT a FROM t ORDER BY a")
        assert rows == [(1,), (2,)] and err is None
        rows, err = ev.run_sqlite(path, "DELETE FROM t")
        assert rows is None and err
        rows, err = ev.run_sqlite(path, "SELECT * FROM missing_table")
        assert rows is None and "OperationalError" in err
