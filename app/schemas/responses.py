from typing import Any

from pydantic import BaseModel


class ChatResponse(BaseModel):
    user_id: int
    answer: str
    analysis: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str


class GenericDataResponse(BaseModel):
    data: list[dict[str, Any]]
