import { apiClient } from "./client";
import { API_ROUTES } from "@/constants/routes";
import type {
  JobAnalysisResponse,
  JobAnalysisSummaryResponse,
  MatchedSkillResponse,
  MissingSkillResponse,
  KeywordMatchResponse,
} from "@/types/jobAnalysis";

export const jobAnalysisApi = {
  history: () =>
    apiClient.get<JobAnalysisSummaryResponse[]>(API_ROUTES.jobAnalysisHistory).then((r) => r.data),

  // job_id must be an existing JobDescription UUID — see README "Known backend gap".
  run: (resumeId: string, jobId: string) =>
    apiClient
      .post<JobAnalysisResponse>(API_ROUTES.jobAnalysisRun(resumeId, jobId))
      .then((r) => r.data),

  get: (analysisId: string) =>
    apiClient.get<JobAnalysisResponse>(API_ROUTES.jobAnalysisById(analysisId)).then((r) => r.data),

  summary: (analysisId: string) =>
    apiClient
      .get<JobAnalysisSummaryResponse>(API_ROUTES.jobAnalysisSummary(analysisId))
      .then((r) => r.data),

  matchedSkills: (analysisId: string) =>
    apiClient
      .get<MatchedSkillResponse[]>(API_ROUTES.jobAnalysisMatchedSkills(analysisId))
      .then((r) => r.data),

  missingSkills: (analysisId: string) =>
    apiClient
      .get<MissingSkillResponse[]>(API_ROUTES.jobAnalysisMissingSkills(analysisId))
      .then((r) => r.data),

  keywords: (analysisId: string) =>
    apiClient
      .get<KeywordMatchResponse[]>(API_ROUTES.jobAnalysisKeywords(analysisId))
      .then((r) => r.data),

  remove: (analysisId: string) =>
    apiClient.delete<void>(API_ROUTES.jobAnalysisById(analysisId)).then((r) => r.data),
};
