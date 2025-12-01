'use client'

/**
 * Notification Bell Component
 *
 * Task D: Notification System Frontend
 * Displays notification icon with badge and dropdown
 */

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import {
  listNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
} from '@/lib/notification-api'
import { Notification, NotificationListResponse } from '@/types/notification'
import { useToast } from '@/components/Toast'

export default function NotificationBell() {
  const router = useRouter()
  const toast = useToast()
  const dropdownRef = useRef<HTMLDivElement>(null)

  const [notifications, setNotifications] = useState<NotificationListResponse | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)
  const [loading, setLoading] = useState(false)

  // Auto-refresh every 30 seconds
  useEffect(() => {
    loadNotifications()

    const interval = setInterval(() => {
      loadNotifications(true) // Silent refresh
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showDropdown])

  const loadNotifications = async (silent: boolean = false) => {
    try {
      if (!silent) setLoading(true)
      const data = await listNotifications(false, undefined, 10) // Get latest 10
      setNotifications(data)
    } catch (err) {
      console.error('Failed to load notifications:', err)
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const handleNotificationClick = async (notification: Notification) => {
    try {
      if (!notification.is_read) {
        await markNotificationRead(notification.id)
      }

      if (notification.action_url) {
        router.push(notification.action_url)
      }

      setShowDropdown(false)
      loadNotifications(true)
    } catch (err) {
      toast.error('알림 처리에 실패했습니다')
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead()
      toast.success('모든 알림을 읽음 처리했습니다')
      loadNotifications(true)
    } catch (err) {
      toast.error('알림 읽음 처리에 실패했습니다')
    }
  }

  const handleDelete = async (e: React.MouseEvent, notificationId: string) => {
    e.stopPropagation()
    try {
      await deleteNotification(notificationId)
      toast.success('알림이 삭제되었습니다')
      loadNotifications(true)
    } catch (err) {
      toast.error('알림 삭제에 실패했습니다')
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'new_customer':
        return '👤'
      case 'policy_expiring':
        return '⚠️'
      case 'query_milestone':
        return '🎯'
      case 'system_announcement':
        return '📢'
      case 'customer_follow_up':
        return '📞'
      case 'compliance_alert':
        return '🚨'
      default:
        return '🔔'
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return '방금 전'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}분 전`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}시간 전`
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}일 전`
    return date.toLocaleDateString('ko-KR')
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>

        {/* Unread Badge */}
        {notifications && notifications.unread_count > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
            {notifications.unread_count > 9 ? '9+' : notifications.unread_count}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              알림
            </h3>
            {notifications && notifications.unread_count > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
              >
                모두 읽음
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              </div>
            ) : notifications && notifications.items.length > 0 ? (
              notifications.items.map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  className={`p-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                    !notification.is_read ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl flex-shrink-0">
                      {getNotificationIcon(notification.type)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {notification.title}
                        </p>
                        <button
                          onClick={(e) => handleDelete(e, notification.id)}
                          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 flex-shrink-0"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                        {formatTimeAgo(notification.created_at)}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  알림이 없습니다
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications && notifications.items.length > 0 && (
            <div className="p-3 border-t border-gray-200 dark:border-gray-700 text-center">
              <button
                onClick={() => {
                  router.push('/notifications')
                  setShowDropdown(false)
                }}
                className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
              >
                모든 알림 보기
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
