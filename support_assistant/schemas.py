from pydantic import BaseModel, Field
from typing import List


class AskRequest(BaseModel):
    """The POST /ask request body."""
    query: str


class AskResponse(BaseModel):
    """The validated response returned by /ask."""
    answer: str
    sources: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)