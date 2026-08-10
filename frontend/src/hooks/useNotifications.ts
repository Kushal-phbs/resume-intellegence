import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notificationsApi, type NotificationFilters } from "@/api/notifications";
import { queryKeys } from "@/constants/queryKeys";

export function useNotifications(filters: NotificationFilters = {}) {
  return useQuery({
    queryKey: queryKeys.notifications(filters),
    queryFn: () => notificationsApi.list(filters),
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: queryKeys.unreadCount,
    queryFn: notificationsApi.unreadCount,
    refetchInterval: 60_000,
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useMarkRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });
}
