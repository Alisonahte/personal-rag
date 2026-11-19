"""Real vector retrieval and an explicitly labelled offline lexical test backend."""
import json
import re
from pathlib import Path


def terms(text):
    return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower()))


class LexicalStore:
    """Offline demonstration only: NOT semantic vector retrieval."""
    def __init__(self, directory):
        self.path = Path(directory) / "lexical.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rows = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []

    def replace(self, source, rows):
        self.rows = [r for r in self.rows if r["source"] != source] + rows
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.rows, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.path)

    def search(self, question, k=4):
        q = terms(question)
        ranked = [{**r, "score": len(q & terms(r["text"])) / max(len(q | terms(r["text"])), 1)} for r in self.rows]
        return sorted((r for r in ranked if r["score"] > 0), key=lambda r: r["score"], reverse=True)[:k]


class ChromaStore:
    def __init__(self, directory, model_name):
        import chromadb
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, device="cpu")
        self.collection = chromadb.PersistentClient(path=str(directory)).get_or_create_collection("knowledge", metadata={"hnsw:space": "cosine", "embedding_model": model_name})
        if self.collection.metadata.get("embedding_model") != model_name:
            raise ValueError("Embedding model changed: use a new data directory and rebuild the index")

    def replace(self, source, rows):
        # Compute before deleting so embedding failures do not erase the old document.
        vectors = self.model.encode([r["text"] for r in rows], normalize_embeddings=True).tolist()
        self.collection.delete(where={"source": source})
        self.collection.upsert(ids=[r["id"] for r in rows], documents=[r["text"] for r in rows], embeddings=vectors, metadatas=[{k: r[k] for k in ("source", "page", "chunk")} for r in rows])

    def search(self, question, k=4):
        count = self.collection.count()
        if not count:
            return []
        query = self.model.encode([question], normalize_embeddings=True).tolist()
        result = self.collection.query(query_embeddings=query, n_results=min(k, count), include=["documents", "metadatas", "distances"])
        return [{"id": id_, "text": text, **meta, "score": 1 - distance} for id_, text, meta, distance in zip(result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0])]
