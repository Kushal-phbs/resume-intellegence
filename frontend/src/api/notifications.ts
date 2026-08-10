import { apiClient } from "./client";
import { API_ROUTES } from "@/constants/routes";
import type { NotificationListResponse, NotificationResponse, UnreadNotificationCount, NotificationPriority } from "@/types/notification";

export interface NotificationFilters extends Record<string, unknown> {
  limit?: number;
  offset?: number;
  order?: "asc" | "desc";
  only_unread?: boolean;
  priority?: NotificationPriority;
}

export const notificationsApi = {
  list: (filters: NotificationFilters = {}) =>
    apiClient
      .get<NotificationListResponse>(API_ROUTES.notifications, { params: filters })
      .then((r) => r.data),

  unreadCount: () =>
    apiClient.get<UnreadNotificationCount>(API_ROUTES.notificationsUnreadCount).then((r) => r.data),

  markAllRead: () =>
    apiClient.patch<UnreadNotificationCount>(API_ROUTES.notificationsReadAll).then((r) => r.data),

  markRead: (id: string) =>
    apiClient.patch<NotificationResponse>(API_ROUTES.notificationRead(id)).then((r) => r.data),

  remove: (id: string) =>
    apiClient.delete<void>(API_ROUTES.notificationById(id)).then((r) => r.data),
};
