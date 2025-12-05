"""
Query History Models

Pydantic models for query history tracking and analytics.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QueryHistoryBase(BaseModel):
    """Base model for query history."""

    query_text: str = Field(..., description="Original natural language query")
    intent: Optional[str] = Field(None, max_length=100, description="Parsed query intent")
    customer_id: Optional[UUID] = Field(None, description="Optional customer context")


class QueryHistoryCreate(QueryHistoryBase):
    """Model for creating a new query history entry."""

    answer: Optional[str] = Field(None, description="Generated answer text")
    confidence: Optional[Decimal] = Field(None, ge=0, le=1, description="Confidence score (0-1)")
    source_documents: Optional[List[Dict[str, Any]]] = Field(None, description="Source document references")
    reasoning_path: Optional[Dict[str, Any]] = Field(None, description="Graph reasoning path")
    execution_time_ms: Optional[int] = Field(None, ge=0, description="Execution time in milliseconds")


class QueryHistory(QueryHistoryBase):
    """Full query history model with all fields."""

    id: UUID
    user_id: UUID
    answer: Optional[str] = None
    confidence: Optional[Decimal] = None
    source_documents: Optional[List[Dict[str, Any]]] = None
    reasoning_path: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QueryHistoryResponse(BaseModel):
    """Response model for query history with summary info."""

    id: UUID
    query_text: str
    intent: Optional[str]
    answer_preview: Optional[str] = Field(None, description="First 200 chars of answer")
    confidence: Optional[Decimal]
    customer_id: Optional[UUID]
    customer_name: Optional[str] = Field(None, description="Customer name if available")
    execution_time_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class QueryHistoryListResponse(BaseModel):
    """Paginated response for query history list."""

    items: List[QueryHistoryResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class QueryHistoryStats(BaseModel):
    """Statistics about query history."""

    total_queries: int
    queries_today: int
    queries_this_week: int
    queries_this_month: int
    avg_confidence: Optional[Decimal]
    avg_execution_time_ms: Optional[int]
    top_intents: List[Dict[str, Any]] = Field(default_factory=list, description="Most common intents")
    queries_by_customer: List[Dict[str, Any]] = Field(
        default_factory=list, description="Query count by customer"
    )
