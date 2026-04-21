from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from pipelore.rag_service import RAGService

_rag_service: RAGService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _rag_service
    _rag_service = RAGService()
    yield


app = FastAPI(title="Pipelore API", lifespan=lifespan)


class QueryRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query(body: QueryRequest):
    result = _rag_service.query(body.question)
    return {"response": result["response"], "sources": result["sources"]}


@app.get("/sources")
def sources():
    return _rag_service.sources()
