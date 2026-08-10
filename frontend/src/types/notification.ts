// Mirrors backend/app/schemas/notification.py exactly.

export type NotificationPriority = "low" | "medium" | "high" | "critical";

export interface NotificationResponse {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: string;
  priority: NotificationPriority;
  is_read: boolean;
  action_url: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  items: NotificationResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface UnreadNotificationCount {
  unread_count: number;
}
