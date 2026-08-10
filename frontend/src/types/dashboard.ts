// Mirrors backend/app/schemas/dashboard.py exactly.
import type { UserRole } from "./auth";

export interface ActivityResponse {
  id: string | null;
  user_id: string;
  activity_type:
    | "resume_uploaded"
    | "resume_analyzed"
    | "job_analyzed"
    | "resume_tailored"
    | "cover_letter_generated"
    | "export_generated"
    | "login";
  entity_type: "resume" | "analysis" | "job" | "tailoring" | "cover_letter" | "export";
  entity_id: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string | null;
}

export interface AnalyticsResponse {
  id: string | null;
  user_id: string;
  total_ai_requests: number;
  total_tokens_used: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  average_processing_time_ms: number | null;
  last_activity_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DashboardSummaryResponse {
  total_resumes: number;
  total_resume_analyses: number;
  total_job_analyses: number;
  total_tailoring_sessions: number;
  generated_cover_letters: number;
  average_resume_score: number | null;
  average_job_match_score: number | null;
  average_tailoring_score: number | null;
}

export interface StatisticsResponse {
  total_resumes: number;
  total_analyses: number;
  total_tailoring_sessions: number;
  total_exports: number;
  average_ats_score: number | null;
  average_job_match_score: number | null;
  average_tailoring_score: number | null;
  total_ai_requests: number;
  success_rate: number;
  average_processing_time_ms: number | null;
  total_tokens_used: number;
}

export interface TrendPointResponse {
  timestamp: string;
  total_resumes: number;
  total_resume_analyses: number;
  total_job_analyses: number;
  total_tailoring_sessions: number;
  generated_cover_letters: number;
  average_resume_score: number | null;
  average_job_match_score: number | null;
  average_tailoring_score: number | null;
}

export interface DashboardResponse {
  summary: DashboardSummaryResponse;
  analytics: AnalyticsResponse;
  recent_activity: ActivityResponse[];
}

export interface DashboardTrendsResponse {
  points: TrendPointResponse[];
}

export interface DashboardUserResponse {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DashboardStatisticsOverview {
  total_resumes: number;
  average_ats_score: number | null;
  highest_ats_score: number | null;
  improvement_percentage: number;
  improvement_streak: number;
}

export interface DashboardRecentResumeResponse {
  id: string;
  title: string;
  is_primary: boolean;
  latest_ats_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardAnalyticsSummaryResponse {
  total_ai_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  total_tokens_used: number;
  average_processing_time_ms: number | null;
  last_activity_at: string | null;
}

export interface DashboardSuggestionResponse {
  source: string;
  analysis_id: string;
  resume_id: string;
  suggestion: string;
  created_at: string;
}

export interface DashboardNotificationResponse {
  id: string;
  activity_type: ActivityResponse["activity_type"];
  entity_type: ActivityResponse["entity_type"];
  entity_id: string | null;
  message: string;
  created_at: string;
  metadata_json: Record<string, unknown>;
}

export interface DashboardQuickActionResponse {
  key: string;
  title: string;
  description: string;
  route: string;
  priority: number;
}

/** GET /dashboard — the single unified payload the Dashboard page renders from. */
export interface DashboardOverviewResponse {
  user: DashboardUserResponse;
  statistics: DashboardStatisticsOverview;
  recent_resumes: DashboardRecentResumeResponse[];
  score_distribution: Record<string, number>;
  analytics_summary: DashboardAnalyticsSummaryResponse;
  latest_ai_suggestions: DashboardSuggestionResponse[];
  unread_notifications: DashboardNotificationResponse[];
  quick_actions: DashboardQuickActionResponse[];
}
