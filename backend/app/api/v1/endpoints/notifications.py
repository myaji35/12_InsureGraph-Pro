"""
Notifications API Endpoints

In-app notification system for users.
Task D: Notification System
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.notification import (
    Notification,
    NotificationCreate,
    NotificationListResponse,
    NotificationStats,
    NotificationType,
)
from loguru import logger


router = APIRouter()


# Notification CRUD Endpoints

@router.get("/", response_model=NotificationListResponse, summary="Get user notifications")
async def list_notifications(
    unread_only: bool = QueryParam(False, description="Show only unread notifications"),
    type: Optional[NotificationType] = QueryParam(None, description="Filter by type"),
    limit: int = QueryParam(50, ge=1, le=100, description="Number of notifications to return"),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get notifications for the current user.

    Supports:
    - unread_only: Filter for unread notifications
    - type: Filter by notification type
    - limit: Limit number of results
    """
    try:
        # Build WHERE conditions
        conditions = [f"user_id = '{user.user_id}'"]

        if unread_only:
            conditions.append("is_read = FALSE")

        if type:
            conditions.append(f"type = '{type.value}'")

        where_clause = " AND ".join(conditions)

        # Get total count
        count_query = text(f"""
            SELECT COUNT(*) as total
            FROM notifications
            WHERE {where_clause}
        """)
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Get unread count
        unread_query = text(f"""
            SELECT COUNT(*) as unread
            FROM notifications
            WHERE user_id = '{user.user_id}' AND is_read = FALSE
        """)
        unread_result = await db.execute(unread_query)
        unread_count = unread_result.scalar()

        # Get notifications
        list_query = text(f"""
            SELECT *
            FROM notifications
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit}
        """)

        result = await db.execute(list_query)
        rows = result.fetchall()

        items = [Notification(**dict(row._mapping)) for row in rows]

        return NotificationListResponse(
            items=items,
            total=total,
            unread_count=unread_count,
        )

    except Exception as e:
        logger.error(f"Failed to list notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list notifications: {str(e)}")


@router.post("/", response_model=Notification, summary="Create notification")
async def create_notification(
    notification_data: NotificationCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new notification.

    Note: In production, this would typically be called by system processes,
    not directly by users. Consider adding role-based access control.
    """
    try:
        query = text("""
            INSERT INTO notifications (
                user_id, title, message, type,
                related_entity_type, related_entity_id, action_url
            )
            VALUES (
                :user_id, :title, :message, :type,
                :related_entity_type, :related_entity_id, :action_url
            )
            RETURNING *
        """)

        result = await db.execute(
            query,
            {
                "user_id": str(notification_data.user_id),
                "title": notification_data.title,
                "message": notification_data.message,
                "type": notification_data.type.value,
                "related_entity_type": notification_data.related_entity_type,
                "related_entity_id": str(notification_data.related_entity_id)
                if notification_data.related_entity_id
                else None,
                "action_url": notification_data.action_url,
            },
        )
        await db.commit()

        row = result.first()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create notification")

        logger.info(f"Created notification for user {notification_data.user_id}")
        return Notification(**dict(row._mapping))

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")


@router.put("/{notification_id}/read", response_model=Notification, summary="Mark as read")
async def mark_notification_read(
    notification_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a notification as read.
    """
    try:
        # Verify notification belongs to user
        check_query = text("""
            SELECT id FROM notifications
            WHERE id = :notification_id AND user_id = :user_id
        """)

        result = await db.execute(
            check_query,
            {"notification_id": str(notification_id), "user_id": str(user.user_id)},
        )

        if not result.first():
            raise HTTPException(status_code=404, detail="Notification not found")

        # Update notification
        update_query = text("""
            UPDATE notifications
            SET is_read = TRUE, read_at = NOW()
            WHERE id = :notification_id
            RETURNING *
        """)

        result = await db.execute(update_query, {"notification_id": str(notification_id)})
        await db.commit()

        row = result.first()
        logger.info(f"Marked notification {notification_id} as read for user {user.user_id}")
        return Notification(**dict(row._mapping))

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")


@router.put("/read-all", summary="Mark all as read")
async def mark_all_notifications_read(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark all user notifications as read.
    """
    try:
        query = text("""
            UPDATE notifications
            SET is_read = TRUE, read_at = NOW()
            WHERE user_id = :user_id AND is_read = FALSE
        """)

        result = await db.execute(query, {"user_id": str(user.user_id)})
        await db.commit()

        updated_count = result.rowcount
        logger.info(f"Marked {updated_count} notifications as read for user {user.user_id}")

        return {"message": f"Marked {updated_count} notifications as read"}

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to mark all notifications as read: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to mark all notifications as read: {str(e)}"
        )


@router.delete("/{notification_id}", summary="Delete notification")
async def delete_notification(
    notification_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a notification.
    """
    try:
        # Verify notification belongs to user
        check_query = text("""
            SELECT id FROM notifications
            WHERE id = :notification_id AND user_id = :user_id
        """)

        result = await db.execute(
            check_query,
            {"notification_id": str(notification_id), "user_id": str(user.user_id)},
        )

        if not result.first():
            raise HTTPException(status_code=404, detail="Notification not found")

        # Delete notification
        delete_query = text("""
            DELETE FROM notifications
            WHERE id = :notification_id
        """)

        await db.execute(delete_query, {"notification_id": str(notification_id)})
        await db.commit()

        logger.info(f"Deleted notification {notification_id} for user {user.user_id}")
        return {"message": "Notification deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete notification: {str(e)}")


@router.get("/stats", response_model=NotificationStats, summary="Get notification statistics")
async def get_notification_stats(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get notification statistics for the current user.
    """
    try:
        # Get counts
        stats_query = text(f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_read = FALSE) as unread
            FROM notifications
            WHERE user_id = '{user.user_id}'
        """)

        result = await db.execute(stats_query)
        row = result.first()

        # Get counts by type
        type_query = text(f"""
            SELECT type, COUNT(*) as count
            FROM notifications
            WHERE user_id = '{user.user_id}'
            GROUP BY type
        """)

        type_result = await db.execute(type_query)
        by_type = {row.type: row.count for row in type_result.fetchall()}

        return NotificationStats(
            total=row.total or 0,
            unread=row.unread or 0,
            by_type=by_type,
        )

    except Exception as e:
        logger.error(f"Failed to get notification stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get notification stats: {str(e)}")
