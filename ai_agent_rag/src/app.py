"""
FastAPI application for paper Q&A.

Endpoints:
- POST /ask-paper: Ask a question about a LaTeX paper
- GET /ping: Health check
"""

from fastapi import FastAPI
from .models import QueryRequest, QueryResponse
from .rag import KnowledgeBase
from .mcp import build_prompt
from .llm import call_llm

app = FastAPI(title="Paper Q&A Assistant", version="1.0.0")

kb = None

@app.post("/ask-paper", response_model=QueryResponse)
def ask_paper(query: QueryRequest) -> QueryResponse:
    global kb
    if kb is None:
        kb = KnowledgeBase()

    retrieved = kb.retrieve(query.query, top_k=10)
    prompt = build_prompt(query.query, retrieved)
    return call_llm(prompt)

@app.get("/ping")
def ping():
    return {"status": "ok"}
