/**
 * Notification Types
 *
 * Task D: Notification System Frontend
 */

export enum NotificationType {
  NEW_CUSTOMER = 'new_customer',
  POLICY_EXPIRING = 'policy_expiring',
  QUERY_MILESTONE = 'query_milestone',
  SYSTEM_ANNOUNCEMENT = 'system_announcement',
  CUSTOMER_FOLLOW_UP = 'customer_follow_up',
  COMPLIANCE_ALERT = 'compliance_alert',
}

export interface NotificationBase {
  title: string
  message: string
  type: NotificationType
  related_entity_type?: string
  related_entity_id?: string
  action_url?: string
}

export interface NotificationCreate extends NotificationBase {
  user_id: string
}

export interface Notification extends NotificationBase {
  id: string
  user_id: string
  is_read: boolean
  created_at: string
  read_at?: string
}

export interface NotificationListResponse {
  items: Notification[]
  total: number
  unread_count: number
}

export interface NotificationStats {
  total: number
  unread: number
  by_type: Record<string, number>
}
