from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, UploadFile, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from .service import from_env


@asynccontextmanager
async def lifespan(app):
    app.state.rag = from_env()
    yield


app = FastAPI(title="Personal RAG", lifespan=lifespan)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    k: int = Field(default=4, ge=1, le=10)
    generate: bool = True


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents")
async def upload(request: Request, file: UploadFile):
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Maximum file size is 10 MiB")
    try:
        return await run_in_threadpool(request.app.state.rag.ingest, file.filename or "document.txt", content)
    except (ValueError, UnicodeError) as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, "Document parsing or indexing failed") from exc


@app.post("/ask")
def ask(request: Request, body: Question):
    try:
        return request.app.state.rag.ask(body.question, body.k, body.generate)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(502, "Model provider request failed; check local configuration") from exc
