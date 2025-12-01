"""
Ingestion Job Domain Model

Manages policy PDF ingestion jobs with status tracking.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class IngestionJobStatus(str, Enum):
    """Ingestion job status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionJobResults(BaseModel):
    """Results from completed ingestion job"""
    nodes_created: int = Field(default=0, description="Number of graph nodes created")
    edges_created: int = Field(default=0, description="Number of graph edges created")
    errors: list[str] = Field(default_factory=list, description="List of errors encountered")
    processing_time_seconds: Optional[float] = Field(default=None, description="Total processing time")


class IngestionJobCreate(BaseModel):
    """Schema for creating an ingestion job"""
    policy_name: str = Field(..., min_length=1, max_length=500, description="Policy name")
    insurer: str = Field(..., min_length=1, max_length=200, description="Insurance company name")
    launch_date: Optional[str] = Field(default=None, description="Product launch date (ISO 8601)")
    s3_key: str = Field(..., min_length=1, description="S3 object key for uploaded PDF")

    @field_validator('policy_name', 'insurer')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace"""
        return v.strip()


class IngestionJobUpdate(BaseModel):
    """Schema for updating an ingestion job"""
    status: Optional[IngestionJobStatus] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100, description="Progress percentage (0-100)")
    results: Optional[IngestionJobResults] = None
    error_message: Optional[str] = None

    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v: Optional[int]) -> Optional[int]:
        """Ensure progress is between 0 and 100"""
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Progress must be between 0 and 100")
        return v


class IngestionJob(BaseModel):
    """Ingestion job domain model"""
    id: UUID = Field(default_factory=uuid4, description="Internal database ID")
    job_id: UUID = Field(default_factory=uuid4, description="Public job identifier")
    policy_name: str = Field(..., description="Policy name")
    insurer: str = Field(..., description="Insurance company")
    launch_date: Optional[str] = Field(default=None, description="Product launch date")
    s3_key: str = Field(..., description="S3 object key")
    status: IngestionJobStatus = Field(default=IngestionJobStatus.PENDING, description="Current job status")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    results: Optional[IngestionJobResults] = Field(default=None, description="Job results")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")

    class Config:
        from_attributes = True

    def can_update_status(self, new_status: IngestionJobStatus) -> bool:
        """
        Validate status transitions.

        Valid transitions:
        - pending -> processing
        - processing -> completed
        - processing -> failed
        - Any status -> failed (for error recovery)
        """
        valid_transitions = {
            IngestionJobStatus.PENDING: [IngestionJobStatus.PROCESSING, IngestionJobStatus.FAILED],
            IngestionJobStatus.PROCESSING: [IngestionJobStatus.COMPLETED, IngestionJobStatus.FAILED],
            IngestionJobStatus.COMPLETED: [],  # Terminal state
            IngestionJobStatus.FAILED: [],  # Terminal state
        }

        return new_status in valid_transitions.get(self.status, [])

    def mark_as_processing(self) -> None:
        """Mark job as processing"""
        if not self.can_update_status(IngestionJobStatus.PROCESSING):
            raise ValueError(f"Cannot transition from {self.status} to processing")

        self.status = IngestionJobStatus.PROCESSING
        self.progress = 0
        self.updated_at = datetime.utcnow()

    def mark_as_completed(self, results: IngestionJobResults) -> None:
        """Mark job as completed with results"""
        if not self.can_update_status(IngestionJobStatus.COMPLETED):
            raise ValueError(f"Cannot transition from {self.status} to completed")

        self.status = IngestionJobStatus.COMPLETED
        self.progress = 100
        self.results = results
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """Mark job as failed with error message"""
        self.status = IngestionJobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_progress(self, progress: int) -> None:
        """Update job progress percentage"""
        if not (0 <= progress <= 100):
            raise ValueError("Progress must be between 0 and 100")

        if self.status != IngestionJobStatus.PROCESSING:
            raise ValueError("Can only update progress for processing jobs")

        self.progress = progress
        self.updated_at = datetime.utcnow()


class IngestionJobResponse(BaseModel):
    """Response schema for ingestion job"""
    job_id: UUID
    status: IngestionJobStatus
    policy_name: str
    insurer: str
    progress: int
    results: Optional[IngestionJobResults] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    estimated_completion_minutes: Optional[int] = Field(default=5, description="Estimated completion time in minutes")

    class Config:
        from_attributes = True
