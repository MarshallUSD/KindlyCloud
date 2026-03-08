"""Base schemas and responses."""
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationQuery(BaseModel):
    """Pagination query parameters."""
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    skip: int
    limit: int
    pages: int


class APIResponse(BaseModel, Generic[T]):
    """Generic API response."""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[dict] = None
