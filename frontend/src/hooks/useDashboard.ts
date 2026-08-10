import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { dashboardApi } from "@/api/dashboard";
import { queryKeys } from "@/constants/queryKeys";

export function useDashboardOverview() {
  return useQuery({ queryKey: queryKeys.dashboard, queryFn: dashboardApi.overview });
}

export function useDashboardTrends(points = 12) {
  return useQuery({
    queryKey: queryKeys.dashboardTrends(points),
    queryFn: () => dashboardApi.trends(points),
  });
}

export function useRefreshDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dashboardApi.refresh,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.dashboard }),
  });
}
