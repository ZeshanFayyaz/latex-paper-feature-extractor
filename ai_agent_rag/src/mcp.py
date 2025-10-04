"""
MCP prompt-building layer for scientific paper Q&A.

Enhancements:
- Injects paper metadata into the context to help the model ground its reasoning.
- Explicitly forbids empty answers and requires detailed scientific explanations.
- Encourages partial reasoning even if the answer is indirect.
"""

from typing import List, Dict

def build_prompt(query: str, retrieved_chunks: List[Dict]) -> str:
    role = (
        "You are an advanced research assistant trained to read and interpret scientific papers written in LaTeX. "
        "You will be given text excerpts (chunks) from one or more papers. Your job is to answer the question with as much detail and scientific accuracy as possible."
    )

    # Build detailed context with metadata and source identifiers
    context_lines = []
    for c in retrieved_chunks:
        context_lines.append(
            f"---\nSOURCE: {c['reference']}\nCONTENT:\n\"{c['text']}\"\n---"
        )
    context = "\n\n".join(context_lines)

    task = (
        "Using ONLY the provided context, answer the user's question in a thorough, well-reasoned, and scientific manner. "
        "If the context does not directly answer the question, you MUST still attempt to infer the most likely conclusion based on what IS present. "
        "NEVER reply with 'Not enough information' or similar phrases. Instead, explain what the text *does* discuss and how it might relate to the question. "
        "If relevant, summarize how the paper approaches the topic even indirectly. "
        "Your response should read like a detailed explanation from a graduate-level research assistant."
    )

    schema = """{
  "answer": "A detailed explanation of the conclusion, result, or best related insight from the context, including reasoning and context references.",
  "references": ["List of chunk references or paper identifiers that support your answer."]
}"""

    return (
        f"{role}\n\n"
        f"<context>\n{context}\n</context>\n\n"
        f"<task>\n{task}\n{schema}\n</task>\n\n"
        f"<query>\n{query}\n</query>"
    )
