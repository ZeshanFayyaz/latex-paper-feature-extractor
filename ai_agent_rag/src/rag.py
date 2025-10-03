"""
Implements the Retrieval Augmented Generation (RAG) layer.

- Reads LaTeX papers from disk and splits them into overlapping chunks.
- Embeds chunks with SentenceTransformers and indexes them in FAISS.
- Provides a 'PaperKnowledgeBase' class to retrieve the top-k most relevant
  chunks for a given user query.
"""

import os, glob, logging, re
from dataclasses import dataclass
from typing import List, Dict, Tuple
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

def _read_tex(path_glob: str) -> List[Tuple[str, str]]:
    """Read all LaTeX files and return (title, content)."""
    docs = []
    for fp in sorted(glob.glob(path_glob)):
        title = os.path.splitext(os.path.basename(fp))[0]
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        # Clean LaTeX commands
        content = re.sub(r"(?m)^%.*$", " ", content)
        content = re.sub(r"\\begin\{.*?\}.*?\\end\{.*?\}", " ", content, flags=re.DOTALL)
        content = re.sub(r"\\[A-Za-z]+(\[[^\]]*\])?(\{[^\}]*\})?", " ", content)
        docs.append((title, content))
    return docs

def _chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    if overlap >= size:
        raise ValueError("Overlap must be smaller than chunk size")

    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        start += size - overlap
    return chunks

@dataclass
class PaperChunk:
    text: str
    reference: str

class PaperKnowledgeBase:
    def __init__(self, docs_glob: str = "input/*.tex", model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.entries: List[PaperChunk] = []

        logger.info("Reading LaTeX papers…")
        for title, content in _read_tex(docs_glob):
            for i, ch in enumerate(_chunk(content)):
                ref = f"{title}, chunk {i+1}"
                self.entries.append(PaperChunk(text=ch, reference=ref))
        logger.info(f"Total chunks: {len(self.entries)}")

        texts = [e.text for e in self.entries]
        embs = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True)
        dim = embs.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embs.astype("float32"))
        self._embs = embs

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        q_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        scores, idxs = self.index.search(q_emb, top_k)
        return [{"text": self.entries[int(i)].text, "reference": self.entries[int(i)].reference} for i in idxs[0]]
