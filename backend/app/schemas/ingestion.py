"""
Pydantic schemas for data ingestion endpoints
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class JobStatus(str, Enum):
    """Ingestion job status enum"""
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStageType(str, Enum):
    """Job stage types"""
    UPLOAD = "upload"
    OCR = "ocr"
    PARSE = "parse"
    EXTRACT = "extract"
    GRAPH_BUILD = "graph_build"
    VALIDATION = "validation"


class PolicyUploadRequest(BaseModel):
    """Request schema for policy upload"""
    insurer: str = Field(..., description="Insurance company name (e.g., 삼성생명)")
    product_name: str = Field(..., description="Product name (e.g., 삼성생명 무배당 건강보험)")
    product_code: Optional[str] = Field(None, description="Product code if available")
    launch_date: Optional[str] = Field(None, description="Launch date (YYYY-MM-DD)")
    description: Optional[str] = Field(None, description="Additional description")

    @field_validator("insurer", "product_name")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class PolicyUploadResponse(BaseModel):
    """Response schema for policy upload"""
    job_id: UUID = Field(..., description="Unique job ID for tracking")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Human-readable message")
    gcs_uri: Optional[str] = Field(None, description="GCS URI of uploaded file")
    created_at: datetime = Field(..., description="Job creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "uploaded",
                "message": "PDF uploaded successfully. Processing will begin shortly.",
                "gcs_uri": "gs://insuregraph-policies-dev/policies/123e4567.pdf",
                "created_at": "2025-11-25T10:30:00Z"
            }
        }


class JobStageStatus(BaseModel):
    """Job stage status"""
    stage: JobStageType = Field(..., description="Stage name")
    status: JobStatus = Field(..., description="Stage status")
    started_at: Optional[datetime] = Field(None, description="Stage start time")
    completed_at: Optional[datetime] = Field(None, description="Stage completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[dict] = Field(None, description="Additional stage metadata")


class JobStatusResponse(BaseModel):
    """Response schema for job status query"""
    job_id: UUID = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Overall job status")
    product_name: str = Field(..., description="Product name")
    insurer: str = Field(..., description="Insurer name")
    created_at: datetime = Field(..., description="Job creation time")
    updated_at: datetime = Field(..., description="Last update time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    stages: List[JobStageStatus] = Field(..., description="Pipeline stage statuses")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    progress_percentage: int = Field(..., ge=0, le=100, description="Progress percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "product_name": "삼성생명 무배당 건강보험",
                "insurer": "삼성생명",
                "created_at": "2025-11-25T10:30:00Z",
                "updated_at": "2025-11-25T10:35:00Z",
                "completed_at": None,
                "stages": [
                    {
                        "stage": "upload",
                        "status": "completed",
                        "started_at": "2025-11-25T10:30:00Z",
                        "completed_at": "2025-11-25T10:31:00Z",
                        "error_message": None,
                        "metadata": {"file_size_mb": 12.5}
                    },
                    {
                        "stage": "ocr",
                        "status": "processing",
                        "started_at": "2025-11-25T10:31:00Z",
                        "completed_at": None,
                        "error_message": None,
                        "metadata": {"pages_processed": 45, "total_pages": 120}
                    }
                ],
                "error_message": None,
                "progress_percentage": 37
            }
        }


class JobListResponse(BaseModel):
    """Response schema for job list query"""
    jobs: List[JobStatusResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Detailed error message")
    job_id: Optional[UUID] = Field(None, description="Job ID if applicable")
