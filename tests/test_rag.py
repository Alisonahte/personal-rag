import pytest
from rag.documents import parse, chunks
from rag.store import LexicalStore
from rag.service import RagService


def test_ingestion_is_idempotent_and_replaces_old_document(tmp_path):
    service = RagService(LexicalStore(tmp_path))
    service.ingest("a.md", "项目截止日期为12月20日".encode())
    service.ingest("a.md", "项目截止日期为12月21日".encode())
    restored = LexicalStore(tmp_path)
    assert len(restored.rows) == 1
    assert "21" in restored.rows[0]["text"]


def test_answer_provenance_and_offline_label(tmp_path):
    service = RagService(LexicalStore(tmp_path))
    service.ingest("a.md", "项目截止日期为12月20日".encode())
    answer = service.ask("项目截止日期", generate=False)
    assert answer["mode"] == "retrieval_only"
    assert answer["sources"][0]["source"] == "a.md"
    assert answer["sources"][0]["page"] == 1


def test_empty_index_refuses(tmp_path):
    assert RagService(LexicalStore(tmp_path)).ask("hello")["mode"] == "no_evidence"


def test_missing_key_is_not_fake_llm(tmp_path):
    service = RagService(LexicalStore(tmp_path))
    service.ingest("a.txt", b"hello world")
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        service.ask("hello")


def test_chunk_boundaries():
    result = chunks(parse("a.txt", ("word " * 200).encode()), size=100, overlap=20)
    assert len(result) > 1
    assert all(len(r["text"]) <= 100 for r in result)
    assert len({r["id"] for r in result}) == len(result)


@pytest.mark.parametrize("name,content", [("a.exe", b"x"), ("a.md", b" ")])
def test_bad_documents(name, content):
    with pytest.raises(ValueError):
        parse(name, content)
