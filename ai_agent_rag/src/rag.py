import os
import re
import glob
import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 100


@dataclass
class PaperChunk:
    text: str
    reference: str


def _read_docs(path_glob: str) -> List[Tuple[str, str]]:
    """Read all .tex documents and return (title, cleaned_content)."""
    docs = []
    files = sorted(glob.glob(path_glob))

    if not files:
        logger.warning(f"No files found at {path_glob}. Check your Docker COPY paths.")
    else:
        logger.info(f"Found {len(files)} documents: {files}")

    for fp in files:
        title = os.path.splitext(os.path.basename(fp))[0]
        with open(fp, "r", encoding="utf-8") as f:
            raw = f.read()

            # Clean LaTeX commands and comments
            cleaned = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", raw)   # remove commands with braces
            cleaned = re.sub(r"\\[a-zA-Z]+\*?", "", cleaned)    # remove commands without braces
            cleaned = re.sub(r"%.*", "", cleaned)               # remove comments
            cleaned = re.sub(r"\s+", " ", cleaned).strip()      # collapse whitespace

        docs.append((title, cleaned))
    return docs


def _chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    if overlap >= size:
        raise ValueError("Overlap must be smaller than chunk size")

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(n, start + size)
        chunks.append(text[start:end])
        start = start + size - overlap

    return chunks


class KnowledgeBase:
    def __init__(
        self,
        docs_glob: str = "input/*.tex",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.model = SentenceTransformer(model_name)
        self.entries: List[PaperChunk] = []

        print("Reading documents from:", docs_glob)
        print("Files detected:", glob.glob(docs_glob))

        # Read and chunk papers
        for title, content in _read_docs(docs_glob):
            chunks = _chunk(content)
            for i, ch in enumerate(chunks):
                ref = f"{title}, chunk {i + 1}"
                self.entries.append(PaperChunk(text=ch, reference=ref))

        if not self.entries:
            raise RuntimeError("No text chunks were created. Check if .tex files are being copied correctly.")

        print("Total chunks created:", len(self.entries))
        print("First chunk preview:", self.entries[0].text[:400])

        # Encode chunks
        texts = [e.text for e in self.entries]
        print("Encoding chunks into embeddings...")
        embs = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        print("Embeddings generated. Shape:", embs.shape)

        # Build FAISS index
        dim = embs.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embs.astype("float32"))
        self._embs = embs
        print("FAISS index built successfully.")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve top-k most relevant text chunks for the query."""
        print("Encoding query for retrieval:", query)
        q_emb = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype("float32")

        scores, idxs = self.index.search(q_emb, top_k)
        print("Top-k scores:", scores)

        results = []
        for i in idxs[0]:
            entry = self.entries[int(i)]
            results.append({"text": entry.text, "reference": entry.reference})

        return results
