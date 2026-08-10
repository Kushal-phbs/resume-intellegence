import { apiClient } from "./client";
import { API_ROUTES } from "@/constants/routes";
import type {
  DashboardOverviewResponse,
  DashboardResponse,
  DashboardTrendsResponse,
  StatisticsResponse,
  AnalyticsResponse,
  ActivityResponse,
} from "@/types/dashboard";

export const dashboardApi = {
  overview: () =>
    apiClient.get<DashboardOverviewResponse>(API_ROUTES.dashboard).then((r) => r.data),

  activity: (limit = 20) =>
    apiClient
      .get<ActivityResponse[]>(API_ROUTES.dashboardActivity, { params: { limit } })
      .then((r) => r.data),

  statistics: () =>
    apiClient.get<StatisticsResponse>(API_ROUTES.dashboardStatistics).then((r) => r.data),

  trends: (points = 12) =>
    apiClient
      .get<DashboardTrendsResponse>(API_ROUTES.dashboardTrends, { params: { points } })
      .then((r) => r.data),

  performance: () =>
    apiClient.get<AnalyticsResponse>(API_ROUTES.dashboardPerformance).then((r) => r.data),

  refresh: () =>
    apiClient.post<DashboardResponse>(API_ROUTES.dashboardRefresh).then((r) => r.data),
};
