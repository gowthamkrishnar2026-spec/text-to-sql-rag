"""Tests for the past-queries RAG evaluation (pure logic; Gemini and the database are replaced by fakes)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.rag_eval_service import RagEvalService, collect_prompts, summarise  # noqa: E402

HISTORY = [  # newest first: (prompt, sql, status)
    ("Show all students", "SELECT 2", "success"),
    ("show all   students!", "SELECT 1", "success"),       # same prompt, older -> deduplicated
    ("Delete all students", "[RESTRICTED OPERATION BLOCKED]", "blocked"),
    ("Broken one", "SELECT bad", "error"),                  # never succeeded -> no reference -> skipped
    ("Top products", "SELECT p", "success"),
]


def test_collect_prompts_dedups_keeps_blocked_and_skips_unreferenced():
    items = collect_prompts(HISTORY)
    prompts = [i["prompt"] for i in items]
    assert prompts == ["Show all students", "Delete all students", "Top products"]
    assert items[0]["reference_sql"] == "SELECT 2"        # newest successful SQL wins
    assert items[1]["blocked"] is True
    assert len(collect_prompts(HISTORY, limit=1)) == 1


def _fakes(off_ok=True, on_ok=True):
    def generate(prompt, opts):
        if "delete" in prompt.lower():
            return {"blocked": True, "generated_sql": "", "rag": {}}
        on = bool(opts.get("use_example_rag"))
        good = on_ok if on else off_ok
        return {"blocked": False, "generated_sql": "GOOD" if good else "BAD",
                "rag": {"examples": {"count": 4 if on else 0}}}

    def execute(sql):
        if sql == "BAD":
            return {"success": True, "rows": [{"x": 2}]}
        if sql == "ERR":
            return {"success": False, "error": "boom"}
        return {"success": True, "rows": [{"x": 1}]}

    match = lambda ref, got: ref == got
    return generate, execute, match


def test_run_one_scores_each_configuration_independently():
    svc = RagEvalService()
    g, e, m = _fakes(off_ok=False, on_ok=True)
    rec = svc._run_one({"prompt": "Top products", "reference_sql": "REF", "blocked": False}, g, e, m)
    assert rec["reference_ok"] and rec["off"]["executed"] and not rec["off"]["match"]
    assert rec["on"]["match"] and rec["on"]["examples"] == 4 and rec["off"]["examples"] == 0


def test_blocked_prompts_count_as_guardrail_checks():
    svc = RagEvalService()
    g, e, m = _fakes()
    rec = svc._run_one({"prompt": "Delete all students", "reference_sql": None, "blocked": True}, g, e, m)
    s = summarise([rec], "on")
    assert s["guardrail_total"] == 1 and s["guardrail_held"] == 1 and s["prompts"] == 0


def test_one_failing_generation_does_not_stop_the_run():
    svc = RagEvalService()
    _, e, m = _fakes()

    def explode(prompt, opts):
        raise RuntimeError("quota")
    rec = svc._run_one({"prompt": "Top products", "reference_sql": "REF", "blocked": False}, explode, e, m)
    assert rec["off"]["error"].startswith("RuntimeError") and not rec["off"]["executed"]


def test_summary_rates():
    svc = RagEvalService()
    g, e, m = _fakes(off_ok=False, on_ok=True)
    recs = [svc._run_one({"prompt": f"p{i}", "reference_sql": "REF", "blocked": False}, g, e, m) for i in range(4)]
    off, on = summarise(recs, "off"), summarise(recs, "on")
    assert off["executed_ok_rate"] == 1.0 and off["match_previous_rate"] == 0.0
    assert on["match_previous_rate"] == 1.0 and on["with_reference"] == 4
