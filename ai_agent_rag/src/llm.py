"""
Handles interaction with Ollama LLM backend.

- Sends MCP prompt
- Ensures JSON-only output
- Handles malformed responses gracefully
"""

import os, json, re
from typing import Any, Dict
from pydantic import ValidationError
from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError
from .models import QueryResponse

def get_client() -> OpenAI:
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY", "EMPTY")
    return OpenAI(base_url=base_url, api_key=api_key) if base_url else OpenAI(api_key=api_key)

def _strip_to_json(text: str) -> str:
    if "```" in text:
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.DOTALL)
    start, end = text.find("{"), text.rfind("}")
    return text[start:end+1] if start != -1 and end > start else text

def call_llm(prompt: str, model: str = None) -> QueryResponse:
    client = get_client()
    model = model or os.getenv("OPENAI_MODEL", "llama3.1")


    messages = [
        {"role": "system", "content": "You are a careful assistant. Return ONLY valid JSON."},
        {"role": "user", "content": prompt},
    ]

    try:
        resp = client.chat.completions.create(
            model=model, messages=messages,
            response_format={"type": "json_object"},
            temperature=0, timeout=120
        )
        text = resp.choices[0].message.content.strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            text = _strip_to_json(text)
            data = json.loads(text)
        return QueryResponse(**data)

    except (APIConnectionError, RateLimitError, APIStatusError) as e:
        return QueryResponse(answer=f"LLM error: {e}", references=[])
    except (ValidationError, Exception) as e:
        return QueryResponse(answer=f"Parsing error: {e}", references=[])
