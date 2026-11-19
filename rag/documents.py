"""Parse documents, preserve page provenance, split with overlap."""
import hashlib
import io
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def parse(name: str, content: bytes) -> list[dict]:
    suffix = Path(name).suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise ValueError("Only PDF, TXT and Markdown are supported")
    if suffix == ".pdf":
        pages = [(i + 1, p.extract_text() or "") for i, p in enumerate(PdfReader(io.BytesIO(content)).pages)]
    else:
        pages = [(1, content.decode("utf-8-sig"))]
    result = [{"source": Path(name).name, "page": page, "text": text.replace("\x00", "").strip()} for page, text in pages if text.strip()]
    if not result:
        raise ValueError("No extractable text; scanned PDFs require OCR (not implemented)")
    return result


def chunks(pages: list[dict], size: int = 600, overlap: int = 100) -> list[dict]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Require size > overlap >= 0")
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap, separators=["\n\n", "\n", "。", "；", " ", ""])
    result = []
    for page in pages:
        for i, text in enumerate(splitter.split_text(page["text"])):
            identity = f'{page["source"]}\0{page["page"]}\0{i}\0{text}'
            result.append({**page, "text": text, "chunk": i, "id": hashlib.sha256(identity.encode()).hexdigest()})
    return result
