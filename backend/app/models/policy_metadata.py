"""
Policy Metadata Domain Model

Represents insurance policy metadata for Human-in-the-Loop curation workflow.
This model tracks policies discovered by the metadata crawler through their
entire lifecycle from discovery to completion.

Epic: Epic 1, Story 1.0
Created: 2025-11-28
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class PolicyMetadataStatus(str, Enum):
    """Policy metadata lifecycle status"""
    DISCOVERED = "DISCOVERED"      # Crawler discovered this policy
    QUEUED = "QUEUED"              # Admin queued for learning
    DOWNLOADING = "DOWNLOADING"    # Worker is downloading file
    PROCESSING = "PROCESSING"      # Ingestion pipeline is running
    COMPLETED = "COMPLETED"        # Successfully ingested
    FAILED = "FAILED"              # Ingestion failed
    IGNORED = "IGNORED"            # Admin marked as ignore


class PolicyCategory(str, Enum):
    """Insurance policy categories"""
    CANCER = "cancer"
    LIFE = "life"
    ANNUITY = "annuity"
    DISABILITY = "disability"
    CARDIOVASCULAR = "cardiovascular"
    HEALTH = "health"
    ACCIDENT = "accident"
    DENTAL = "dental"
    LONG_TERM_CARE = "long_term_care"
    SAVINGS = "savings"
    OTHER = "other"


class PolicyMetadata(BaseModel):
    """
    Domain model for policy metadata

    This represents a discovered insurance policy that can be queued
    for learning through the Human-in-the-Loop curation workflow.
    """

    id: UUID = Field(default_factory=uuid4)

    # Source Information
    insurer: str = Field(..., min_length=1, max_length=255, description="Insurance company name")
    category: Optional[PolicyCategory] = Field(None, description="Policy category")
    policy_name: str = Field(..., min_length=1, max_length=500, description="Full policy name")
    file_name: Optional[str] = Field(None, max_length=500, description="PDF file name")
    publication_date: Optional[datetime] = Field(None, description="Policy publication date")
    download_url: HttpUrl = Field(..., description="Original download URL from insurer website")

    # Lifecycle Status
    status: PolicyMetadataStatus = Field(default=PolicyMetadataStatus.DISCOVERED)

    # Curation Information
    queued_by: Optional[UUID] = Field(None, description="Admin user ID who queued this policy")
    queued_at: Optional[datetime] = Field(None, description="When this was queued for learning")

    # Timestamps
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # Manual Review
    notes: Optional[str] = Field(None, description="Manual review notes")

    # Additional flexible metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }

    @field_validator('insurer')
    @classmethod
    def validate_insurer(cls, v: str) -> str:
        """Validate and normalize insurer name"""
        if not v or not v.strip():
            raise ValueError("Insurer name cannot be empty")
        return v.strip()

    @field_validator('policy_name')
    @classmethod
    def validate_policy_name(cls, v: str) -> str:
        """Validate and normalize policy name"""
        if not v or not v.strip():
            raise ValueError("Policy name cannot be empty")
        return v.strip()

    def can_be_queued(self) -> bool:
        """Check if this policy can be queued for learning"""
        return self.status in [
            PolicyMetadataStatus.DISCOVERED,
            PolicyMetadataStatus.FAILED,
        ]

    def can_be_ignored(self) -> bool:
        """Check if this policy can be marked as ignored"""
        return self.status not in [
            PolicyMetadataStatus.PROCESSING,
            PolicyMetadataStatus.DOWNLOADING,
            PolicyMetadataStatus.COMPLETED,
        ]

    def mark_as_queued(self, user_id: UUID) -> None:
        """Mark this policy as queued for learning"""
        if not self.can_be_queued():
            raise ValueError(f"Cannot queue policy with status {self.status}")

        self.status = PolicyMetadataStatus.QUEUED
        self.queued_by = user_id
        self.queued_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()

    def mark_as_ignored(self, reason: Optional[str] = None) -> None:
        """Mark this policy as ignored"""
        if not self.can_be_ignored():
            raise ValueError(f"Cannot ignore policy with status {self.status}")

        self.status = PolicyMetadataStatus.IGNORED
        if reason:
            self.notes = f"{self.notes}\n{reason}" if self.notes else reason
        self.last_updated = datetime.utcnow()

    def update_status(self, new_status: PolicyMetadataStatus) -> None:
        """Update status with validation"""
        # Define valid status transitions
        valid_transitions = {
            PolicyMetadataStatus.DISCOVERED: [
                PolicyMetadataStatus.QUEUED,
                PolicyMetadataStatus.IGNORED,
            ],
            PolicyMetadataStatus.QUEUED: [
                PolicyMetadataStatus.DOWNLOADING,
                PolicyMetadataStatus.FAILED,
                PolicyMetadataStatus.IGNORED,
            ],
            PolicyMetadataStatus.DOWNLOADING: [
                PolicyMetadataStatus.PROCESSING,
                PolicyMetadataStatus.FAILED,
            ],
            PolicyMetadataStatus.PROCESSING: [
                PolicyMetadataStatus.COMPLETED,
                PolicyMetadataStatus.FAILED,
            ],
            PolicyMetadataStatus.FAILED: [
                PolicyMetadataStatus.QUEUED,  # Retry
                PolicyMetadataStatus.IGNORED,
            ],
            PolicyMetadataStatus.COMPLETED: [],  # Terminal state
            PolicyMetadataStatus.IGNORED: [
                PolicyMetadataStatus.DISCOVERED,  # Re-enable
            ],
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(
                f"Invalid status transition: {self.status} -> {new_status}"
            )

        self.status = new_status
        self.last_updated = datetime.utcnow()


class PolicyMetadataCreate(BaseModel):
    """Schema for creating new policy metadata (used by crawler)"""

    insurer: str = Field(..., min_length=1, max_length=255)
    category: Optional[PolicyCategory] = None
    policy_name: str = Field(..., min_length=1, max_length=500)
    file_name: Optional[str] = Field(None, max_length=500)
    publication_date: Optional[datetime] = None
    download_url: HttpUrl
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyMetadataUpdate(BaseModel):
    """Schema for updating policy metadata (used by admin)"""

    status: Optional[PolicyMetadataStatus] = None
    notes: Optional[str] = None
    category: Optional[PolicyCategory] = None


class PolicyMetadataFilter(BaseModel):
    """Schema for filtering policy metadata list"""

    status: Optional[PolicyMetadataStatus] = None
    insurer: Optional[str] = None
    category: Optional[PolicyCategory] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = Field(None, description="Full-text search on policy_name and file_name")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")


class PolicyMetadataStats(BaseModel):
    """Statistics for policy metadata"""

    total_count: int = Field(..., description="Total number of policies")
    status_counts: Dict[str, int] = Field(..., description="Count by status")
    insurer_counts: Dict[str, int] = Field(..., description="Count by insurer")
    category_counts: Dict[str, int] = Field(..., description="Count by category")
    recent_discoveries: int = Field(..., description="Policies discovered in last 7 days")
