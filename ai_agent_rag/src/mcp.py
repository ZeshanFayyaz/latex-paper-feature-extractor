"""
This module defines the MCP prompt-building layer for scientific paper Q&A.

Responsibilities:
- Define allowed response structure
- Build structured prompts with context chunks
- Enforce grounding and schema
"""

from typing import List, Dict

def build_prompt(query: str, retrieved_chunks: List[Dict]) -> str:
    role = "You are a research assistant helping users understand scientific papers."
    context_lines = [f"Source: {c['reference']}\n\"{c['text']}\"" for c in retrieved_chunks]
    context = "\n\n".join(context_lines)

    task = (
        "Using ONLY the provided context, answer the user's query. "
        "If information is missing, say so explicitly. "
        "Always reply in strict JSON with the following schema:"
    )
    schema = """{
  "answer": "string",
  "references": ["list of strings"]
}"""

    return (
        f"{role}\n\n"
        f"<context>\n{context}\n</context>\n\n"
        f"<task>\n{task}\n{schema}\n</task>\n\n"
        f"<query>\n{query}\n</query>"
    )
