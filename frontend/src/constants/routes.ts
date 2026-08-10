/** Frontend route paths. Keep in sync with src/routes/index.tsx. */
export const ROUTES = {
  login: "/login",
  register: "/register",
  dashboard: "/",
  resumes: "/resumes",
  resumeDetail: (id: string) => `/resumes/${id}`,
  resumeAnalysis: (id: string) => `/resumes/${id}/analysis`,
  jobAnalysis: "/job-analysis",
  jobAnalysisDetail: (id: string) => `/job-analysis/${id}`,
  tailoring: "/tailoring",
  tailoringDetail: (id: string) => `/tailoring/${id}`,
  chat: "/chat",
  chatConversation: (id: string) => `/chat/${id}`,
  settings: "/settings",
  profile: "/profile",
};

/**
 * Backend API paths. These are mounted at the API root with NO version
 * prefix (see backend/app/main.py — app.include_router(api_router) with
 * no prefix, and each router sets its own e.g. "/auth", "/resumes").
 */
export const API_ROUTES = {
  authRegister: "/auth/register",
  authLogin: "/auth/login",
  authRefresh: "/auth/refresh",
  usersMe: "/users/me",

  resumes: "/resumes",
  resumeUpload: "/resumes/upload",
  resumeById: (id: string) => `/resumes/${id}`,
  resumeDownload: (id: string) => `/resumes/${id}/download`,

  analysisRun: (resumeId: string) => `/analysis/${resumeId}`,
  analysisLatest: (resumeId: string) => `/analysis/${resumeId}`,
  analysisSummary: (resumeId: string) => `/analysis/${resumeId}/summary`,
  analysisSkills: (resumeId: string) => `/analysis/${resumeId}/skills`,
  analysisKeywords: (resumeId: string) => `/analysis/${resumeId}/keywords`,
  analysisHistory: (resumeId: string) => `/analysis/${resumeId}/history`,
  analysisDelete: (analysisId: string) => `/analysis/${analysisId}`,

  jobAnalysisHistory: "/job-analysis/history",
  jobAnalysisRun: (resumeId: string, jobId: string) => `/job-analysis/${resumeId}/${jobId}`,
  jobAnalysisById: (analysisId: string) => `/job-analysis/${analysisId}`,
  jobAnalysisSummary: (analysisId: string) => `/job-analysis/${analysisId}/summary`,
  jobAnalysisMatchedSkills: (analysisId: string) => `/job-analysis/${analysisId}/matched-skills`,
  jobAnalysisMissingSkills: (analysisId: string) => `/job-analysis/${analysisId}/missing-skills`,
  jobAnalysisKeywords: (analysisId: string) => `/job-analysis/${analysisId}/keywords`,

  tailoringCreate: (resumeId: string, jobId: string) => `/resume-tailoring/${resumeId}/${jobId}`,
  tailoringHistory: "/resume-tailoring/history",
  tailoringSession: (sessionId: string) => `/resume-tailoring/${sessionId}`,
  tailoringResume: (sessionId: string) => `/resume-tailoring/${sessionId}/resume`,
  tailoringCoverLetter: (sessionId: string) => `/resume-tailoring/${sessionId}/cover-letter`,

  exportResume: (versionId: string, format: string) => `/export/resume/${versionId}?format=${format}`,
  exportCoverLetter: (coverLetterId: string, format: string) => `/export/cover-letter/${coverLetterId}?format=${format}`,

  chatOnce: "/chat/",
  conversations: "/chat/conversations",
  conversationById: (id: string) => `/chat/conversations/${id}`,
  messages: (conversationId: string) => `/chat/conversations/${conversationId}/messages`,

  dashboard: "/dashboard",
  dashboardSummary: "/dashboard/summary",
  dashboardActivity: "/dashboard/activity",
  dashboardStatistics: "/dashboard/statistics",
  dashboardTrends: "/dashboard/trends",
  dashboardPerformance: "/dashboard/performance",
  dashboardRefresh: "/dashboard/refresh",

  notifications: "/notifications",
  notificationsUnreadCount: "/notifications/unread-count",
  notificationsReadAll: "/notifications/read-all",
  notificationRead: (id: string) => `/notifications/${id}/read`,
  notificationById: (id: string) => `/notifications/${id}`,

  health: "/health",
};
