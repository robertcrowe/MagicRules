from datetime import datetime

from pydantic import BaseModel, Field


class Rule(BaseModel):
    model_config = {"from_attributes": True}

    id: int | None = None
    rule_number: str
    section_title: str
    rule_text: str
    full_text: str
    embedding: list[float] | None = None
    created_at: datetime | None = None


class Citation(BaseModel):
    rule_number: str
    quoted_text: str


class Answer(BaseModel):
    answer_text: str
    citations: list[Citation]
    has_exact_match: bool
    disclaimer: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    question: str
    answer_text: str
    citations: list[Citation]
    has_exact_match: bool
    disclaimer: str | None = None
    latency_ms: float
