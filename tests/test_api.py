from fastapi.testclient import TestClient
from rag import api
from rag.service import RagService
from rag.store import LexicalStore


def test_upload_ask_and_validation(tmp_path, monkeypatch):
    service = RagService(LexicalStore(tmp_path))
    monkeypatch.setattr(api, "from_env", lambda: service)
    with TestClient(api.app) as client:
        assert client.get("/health").status_code == 200
        response = client.post("/documents", files={"file": ("course.md", "期末项目占40%".encode())})
        assert response.status_code == 200
        assert response.json()["chunks"] == 1
        answer = client.post("/ask", json={"question": "期末项目", "generate": False}).json()
        assert answer["mode"] == "retrieval_only"
        assert answer["sources"][0]["source"] == "course.md"
        assert client.post("/ask", json={"question": "", "k": 0}).status_code == 422
        assert client.post("/documents", files={"file": ("a.exe", b"x")}).status_code == 400
        assert client.post("/ask", json={"question": "期末项目"}).status_code == 400


def test_llm_receives_evidence_and_returns_citation(tmp_path, monkeypatch):
    service = RagService(LexicalStore(tmp_path), api_key="non-secret-test-placeholder")
    service.ingest("course.md", "期末项目占40%".encode())
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"choices": [{"message": {"content": "期末项目占40%。[1]"}}]}
    def post(url, **kwargs):
        assert url.endswith("/chat/completions")
        assert "期末项目占40%" in kwargs["json"]["messages"][1]["content"]
        assert "[1]" in kwargs["json"]["messages"][1]["content"]
        return Response()
    monkeypatch.setattr("rag.service.httpx.post", post)
    answer = service.ask("期末项目")
    assert answer["mode"] == "llm"
    assert answer["answer"].endswith("[1]")


def test_connection_retry_is_bounded(tmp_path, monkeypatch):
    import httpx
    import pytest
    service = RagService(LexicalStore(tmp_path), api_key="test-placeholder")
    service.ingest("a.txt", b"hello")
    calls = []
    def failed(*args, **kwargs):
        calls.append(1)
        raise httpx.ConnectError("offline")
    monkeypatch.setattr("rag.service.httpx.post", failed)
    monkeypatch.setattr("rag.service.time.sleep", lambda _: None)
    with pytest.raises(httpx.ConnectError):
        service.ask("hello")
    assert len(calls) == 3

