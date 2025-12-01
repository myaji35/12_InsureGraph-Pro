/**
 * Notification API Client
 *
 * Task D: Notification System Frontend
 */

import type {
  Notification,
  NotificationCreate,
  NotificationListResponse,
  NotificationStats,
  NotificationType,
} from '@/types/notification'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Get auth headers with JWT token
 */
async function getAuthHeaders(): Promise<HeadersInit> {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  }
}

/**
 * Get user notifications
 */
export async function listNotifications(
  unreadOnly: boolean = false,
  type?: NotificationType,
  limit: number = 50
): Promise<NotificationListResponse> {
  const params = new URLSearchParams()
  if (unreadOnly) params.append('unread_only', 'true')
  if (type) params.append('type', type)
  if (limit) params.append('limit', limit.toString())

  const response = await fetch(`${API_BASE}/api/v1/notifications/?${params.toString()}`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to fetch notifications')
  }

  return response.json()
}

/**
 * Create a notification
 */
export async function createNotification(data: NotificationCreate): Promise<Notification> {
  const response = await fetch(`${API_BASE}/api/v1/notifications/`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to create notification')
  }

  return response.json()
}

/**
 * Mark notification as read
 */
export async function markNotificationRead(notificationId: string): Promise<Notification> {
  const response = await fetch(`${API_BASE}/api/v1/notifications/${notificationId}/read`, {
    method: 'PUT',
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to mark notification as read')
  }

  return response.json()
}

/**
 * Mark all notifications as read
 */
export async function markAllNotificationsRead(): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/notifications/read-all`, {
    method: 'PUT',
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to mark all notifications as read')
  }
}

/**
 * Delete notification
 */
export async function deleteNotification(notificationId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/notifications/${notificationId}`, {
    method: 'DELETE',
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to delete notification')
  }
}

/**
 * Get notification statistics
 */
export async function getNotificationStats(): Promise<NotificationStats> {
  const response = await fetch(`${API_BASE}/api/v1/notifications/stats`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to fetch notification stats')
  }

  return response.json()
}
