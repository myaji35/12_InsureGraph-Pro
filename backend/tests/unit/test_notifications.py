"""
Unit Tests for Notifications API

Task E: Backend Unit Tests
"""
import pytest
from uuid import uuid4
from datetime import datetime


class TestNotificationModels:
    """Test Notification Pydantic models."""

    def test_notification_type_enum(self):
        """Test NotificationType enum."""
        from app.models.notification import NotificationType

        assert NotificationType.NEW_CUSTOMER == "new_customer"
        assert NotificationType.POLICY_EXPIRING == "policy_expiring"
        assert NotificationType.QUERY_MILESTONE == "query_milestone"
        assert NotificationType.SYSTEM_ANNOUNCEMENT == "system_announcement"
        assert NotificationType.CUSTOMER_FOLLOW_UP == "customer_follow_up"
        assert NotificationType.COMPLIANCE_ALERT == "compliance_alert"

    def test_notification_create_valid(self):
        """Test creating valid NotificationCreate model."""
        from app.models.notification import NotificationCreate, NotificationType

        user_id = uuid4()
        customer_id = uuid4()

        data = NotificationCreate(
            user_id=user_id,
            title="신규 고객 등록",
            message="김철수님이 고객으로 추가되었습니다",
            type=NotificationType.NEW_CUSTOMER,
            related_entity_type="customer",
            related_entity_id=customer_id,
            action_url=f"/customers/{customer_id}",
        )

        assert data.user_id == user_id
        assert data.title == "신규 고객 등록"
        assert data.type == NotificationType.NEW_CUSTOMER
        assert data.related_entity_id == customer_id

    def test_notification_create_minimal(self):
        """Test creating minimal NotificationCreate model."""
        from app.models.notification import NotificationCreate, NotificationType

        user_id = uuid4()

        data = NotificationCreate(
            user_id=user_id,
            title="시스템 공지",
            message="시스템 점검 안내",
            type=NotificationType.SYSTEM_ANNOUNCEMENT,
        )

        assert data.user_id == user_id
        assert data.related_entity_type is None
        assert data.related_entity_id is None
        assert data.action_url is None


class TestNotificationStats:
    """Test Notification Statistics."""

    def test_stats_model(self):
        """Test NotificationStats model."""
        from app.models.notification import NotificationStats

        stats = NotificationStats(
            total=50,
            unread=10,
            by_type={
                "new_customer": 20,
                "policy_expiring": 15,
                "system_announcement": 15,
            },
        )

        assert stats.total == 50
        assert stats.unread == 10
        assert stats.by_type["new_customer"] == 20
        assert len(stats.by_type) == 3


class TestNotificationResponse:
    """Test Notification Response models."""

    def test_notification_list_response(self):
        """Test NotificationListResponse model."""
        from app.models.notification import (
            NotificationListResponse,
            Notification,
            NotificationType,
        )

        notifications = [
            Notification(
                id=uuid4(),
                user_id=uuid4(),
                title="Test 1",
                message="Message 1",
                type=NotificationType.NEW_CUSTOMER,
                is_read=False,
                created_at=datetime.utcnow(),
            ),
            Notification(
                id=uuid4(),
                user_id=uuid4(),
                title="Test 2",
                message="Message 2",
                type=NotificationType.SYSTEM_ANNOUNCEMENT,
                is_read=True,
                created_at=datetime.utcnow(),
                read_at=datetime.utcnow(),
            ),
        ]

        response = NotificationListResponse(
            items=notifications, total=2, unread_count=1
        )

        assert len(response.items) == 2
        assert response.total == 2
        assert response.unread_count == 1
        assert response.items[0].is_read is False
        assert response.items[1].is_read is True


@pytest.mark.asyncio
class TestNotificationAPI:
    """Test Notification API endpoints (integration-style)."""

    async def test_create_notification_schema(self):
        """Test notification creation data schema."""
        from app.models.notification import NotificationCreate, NotificationType

        data = NotificationCreate(
            user_id=uuid4(),
            title="Test Notification",
            message="Test Message",
            type=NotificationType.NEW_CUSTOMER,
        )

        assert data.title == "Test Notification"
        assert data.type == NotificationType.NEW_CUSTOMER

    async def test_notification_update_schema(self):
        """Test notification update schema."""
        from app.models.notification import NotificationUpdate

        update = NotificationUpdate(is_read=True, read_at=datetime.utcnow())

        assert update.is_read is True
        assert update.read_at is not None


# Fixtures
@pytest.fixture
def sample_notification_data():
    """Sample notification data."""
    return {
        "user_id": str(uuid4()),
        "title": "보험 만기 임박",
        "message": "김철수님의 암보험이 3개월 후 만기됩니다.",
        "type": "policy_expiring",
        "related_entity_type": "policy",
        "related_entity_id": str(uuid4()),
        "action_url": "/customers/12345",
    }


@pytest.fixture
def sample_notification_list():
    """Sample notification list."""
    user_id = uuid4()
    return [
        {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "title": "신규 고객 등록",
            "message": "김철수님이 등록되었습니다",
            "type": "new_customer",
            "is_read": False,
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "title": "시스템 공지",
            "message": "시스템 업데이트 안내",
            "type": "system_announcement",
            "is_read": True,
            "created_at": datetime.utcnow().isoformat(),
            "read_at": datetime.utcnow().isoformat(),
        },
    ]


@pytest.fixture
def sample_notification_stats():
    """Sample notification statistics."""
    return {
        "total": 100,
        "unread": 25,
        "by_type": {
            "new_customer": 40,
            "policy_expiring": 20,
            "query_milestone": 15,
            "system_announcement": 15,
            "customer_follow_up": 8,
            "compliance_alert": 2,
        },
    }
