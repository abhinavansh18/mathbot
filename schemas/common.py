"""
Shared Pydantic schemas used across multiple endpoints.
"""
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class HealthCheck(BaseModel):
    status: str                   # healthy | degraded | unhealthy
    database: str
    redis: str
    llm: str
