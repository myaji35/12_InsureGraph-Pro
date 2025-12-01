"""
Notification Models

Pydantic models for in-app notifications.
Task D: Notification System
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Notification types."""
    NEW_CUSTOMER = "new_customer"
    POLICY_EXPIRING = "policy_expiring"
    QUERY_MILESTONE = "query_milestone"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    CUSTOMER_FOLLOW_UP = "customer_follow_up"
    COMPLIANCE_ALERT = "compliance_alert"


class NotificationBase(BaseModel):
    """Base notification model."""
    title: str = Field(..., max_length=255, description="Notification title")
    message: str = Field(..., description="Notification message")
    type: NotificationType = Field(..., description="Notification type")
    related_entity_type: Optional[str] = Field(None, max_length=50, description="Related entity type")
    related_entity_id: Optional[UUID] = Field(None, description="Related entity ID")
    action_url: Optional[str] = Field(None, max_length=500, description="Action URL")


class NotificationCreate(NotificationBase):
    """Model for creating a notification."""
    user_id: UUID = Field(..., description="Target user ID")


class Notification(NotificationBase):
    """Full notification model."""
    id: UUID
    user_id: UUID
    is_read: bool = False
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    """Model for updating a notification."""
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None


class NotificationListResponse(BaseModel):
    """Response model for notification list."""
    items: list[Notification]
    total: int
    unread_count: int


class NotificationStats(BaseModel):
    """Statistics about notifications."""
    total: int
    unread: int
    by_type: dict[str, int] = Field(default_factory=dict, description="Count by type")
