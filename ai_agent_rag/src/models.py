"""
Defines the core Pydantic schemas used by the API.

- QueryRequest: input model for user queries/questions.
- QueryResponse: output model enforcing structured JSON with
  'answer' and 'references'.
"""

from pydantic import BaseModel, Field
from typing import List

class QueryRequest(BaseModel):
    query: str = Field(..., description="User's question about the scientific paper")

class QueryResponse(BaseModel):
    answer: str
    references: List[str]
