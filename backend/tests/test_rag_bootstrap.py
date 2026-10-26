"""The startup bootstrap must index project examples once and never raise."""
from app.services import rag_bootstrap


class FakeIndex:
    def __init__(self, count=0):
        self._count = count
        self.added = None

    def count(self):
        return self._count

    def add(self, items):
        self.added = items
        return len(items)


class FakeRuntime:
    def __init__(self, index):
        self._index = index

    def example_index(self):
        return self._index


def _patch(monkeypatch, index):
    import app.services.rag_service as rag_service
    monkeypatch.setattr(rag_service, "get_runtime", lambda: FakeRuntime(index))


def test_indexes_project_examples_when_store_is_empty(monkeypatch):
    index = FakeIndex(count=0)
    _patch(monkeypatch, index)
    rag_bootstrap._index_project_examples()
    assert index.added and all(it["source"] == "project" for it in index.added)


def test_skips_when_store_already_populated(monkeypatch):
    index = FakeIndex(count=52)
    _patch(monkeypatch, index)
    rag_bootstrap._index_project_examples()
    assert index.added is None


def test_never_raises_when_embedding_fails(monkeypatch):
    class Broken(FakeIndex):
        def add(self, items):
            raise RuntimeError("quota exceeded")

    _patch(monkeypatch, Broken())
    rag_bootstrap._index_project_examples()  # must not raise


def test_no_thread_without_api_key(monkeypatch):
    monkeypatch.setattr(rag_bootstrap.settings, "GEMINI_API_KEY", "")
    started = []
    monkeypatch.setattr(rag_bootstrap.threading, "Thread", lambda *a, **k: started.append(1))
    rag_bootstrap.start_background_bootstrap()
    assert not started
