"""
Metadata API Request/Response Models

API models for Human-in-the-Loop metadata curation endpoints.
These models define the contract between frontend and backend.

Epic: Epic 1, Story 1.0
Created: 2025-11-28
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.models.policy_metadata import (
    PolicyMetadataStatus,
    PolicyCategory,
)


# ============================================
# Request Models
# ============================================

class PolicyMetadataQueueRequest(BaseModel):
    """Request to queue policies for learning"""

    policy_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of policy metadata IDs to queue (max 100)"
    )
    priority: Optional[str] = Field(
        None,
        pattern="^(low|medium|high|urgent)$",
        description="Priority level for processing"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional notes for this batch"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "policy_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "223e4567-e89b-12d3-a456-426614174001"
                ],
                "priority": "high",
                "notes": "New cancer insurance products - urgent for sales team"
            }
        }


class PolicyMetadataUpdateRequest(BaseModel):
    """Request to update policy metadata"""

    status: Optional[PolicyMetadataStatus] = Field(
        None,
        description="New status (if changing)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=5000,
        description="Additional notes"
    )
    category: Optional[PolicyCategory] = Field(
        None,
        description="Policy category"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "IGNORED",
                "notes": "Duplicate of existing policy - filed under different name"
            }
        }


# ============================================
# Response Models
# ============================================

class PolicyMetadataResponse(BaseModel):
    """Response model for a single policy metadata"""

    id: UUID
    insurer: str
    category: Optional[str]
    policy_name: str
    file_name: Optional[str]
    publication_date: Optional[datetime]
    download_url: str
    status: str
    queued_by: Optional[UUID]
    queued_at: Optional[datetime]
    discovered_at: datetime
    last_updated: datetime
    notes: Optional[str]
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "insurer": "Samsung Life",
                "category": "cancer",
                "policy_name": "종합암보험 2.0 약관",
                "file_name": "cancer_insurance_v2_2025.pdf",
                "publication_date": "2025-11-01T00:00:00Z",
                "download_url": "https://www.samsunglife.com/download?id=12345",
                "status": "DISCOVERED",
                "queued_by": None,
                "queued_at": None,
                "discovered_at": "2025-11-25T09:00:00Z",
                "last_updated": "2025-11-25T09:00:00Z",
                "notes": None,
                "metadata": {}
            }
        }


class PolicyMetadataListResponse(BaseModel):
    """Response model for paginated list of policy metadata"""

    policies: List[PolicyMetadataResponse]
    pagination: Dict[str, Any] = Field(
        ...,
        description="Pagination information"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "policies": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "insurer": "Samsung Life",
                        "policy_name": "종합암보험 2.0",
                        "status": "DISCOVERED",
                        "discovered_at": "2025-11-25T09:00:00Z"
                    }
                ],
                "pagination": {
                    "total": 247,
                    "page": 1,
                    "page_size": 50,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }


class PolicyQueueJobResponse(BaseModel):
    """Response for a single queued job"""

    job_id: UUID = Field(..., description="Ingestion job ID")
    policy_id: UUID = Field(..., description="Policy metadata ID")
    status: str = Field(..., description="Job status")


class PolicyMetadataQueueResponse(BaseModel):
    """Response after queuing policies for learning"""

    queued_count: int = Field(..., description="Number of policies successfully queued")
    jobs_created: List[PolicyQueueJobResponse] = Field(
        ...,
        description="List of created ingestion jobs"
    )
    skipped_count: int = Field(
        default=0,
        description="Number of policies skipped (invalid status)"
    )
    skipped_policies: List[UUID] = Field(
        default_factory=list,
        description="IDs of skipped policies"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "queued_count": 2,
                "jobs_created": [
                    {
                        "job_id": "456e7890-e89b-12d3-a456-426614174000",
                        "policy_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "QUEUED"
                    }
                ],
                "skipped_count": 0,
                "skipped_policies": []
            }
        }


class PolicyMetadataStatsResponse(BaseModel):
    """Response model for policy metadata statistics"""

    total_count: int
    status_counts: Dict[str, int]
    insurer_counts: Dict[str, int]
    category_counts: Dict[str, int]
    recent_discoveries: int = Field(
        ...,
        description="Policies discovered in last 7 days"
    )
    last_crawl: Optional[datetime] = Field(
        None,
        description="Last successful crawler run"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 247,
                "status_counts": {
                    "DISCOVERED": 180,
                    "QUEUED": 15,
                    "PROCESSING": 3,
                    "COMPLETED": 45,
                    "FAILED": 2,
                    "IGNORED": 2
                },
                "insurer_counts": {
                    "Samsung Life": 82,
                    "Hanwha Life": 75,
                    "KB Insurance": 90
                },
                "category_counts": {
                    "cancer": 120,
                    "life": 80,
                    "annuity": 47
                },
                "recent_discoveries": 25,
                "last_crawl": "2025-11-28T02:00:00Z"
            }
        }


# ============================================
# Error Response Models
# ============================================

class PolicyMetadataErrorResponse(BaseModel):
    """Error response for metadata API"""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "INVALID_STATUS",
                "message": "Cannot queue policy with status COMPLETED",
                "details": {
                    "policy_id": "123e4567-e89b-12d3-a456-426614174000",
                    "current_status": "COMPLETED"
                }
            }
        }
