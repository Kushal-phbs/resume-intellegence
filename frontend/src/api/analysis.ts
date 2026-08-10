import { apiClient } from "./client";
import { API_ROUTES } from "@/constants/routes";
import type {
  ResumeAnalysisResponse,
  ResumeAnalysisSummaryResponse,
  SkillResponse,
  KeywordResponse,
} from "@/types/analysis";

export const analysisApi = {
  run: (resumeId: string) =>
    apiClient.post<ResumeAnalysisResponse>(API_ROUTES.analysisRun(resumeId)).then((r) => r.data),

  latest: (resumeId: string) =>
    apiClient.get<ResumeAnalysisResponse>(API_ROUTES.analysisLatest(resumeId)).then((r) => r.data),

  summary: (resumeId: string) =>
    apiClient.get<ResumeAnalysisSummaryResponse>(API_ROUTES.analysisSummary(resumeId)).then((r) => r.data),

  skills: (resumeId: string) =>
    apiClient.get<SkillResponse[]>(API_ROUTES.analysisSkills(resumeId)).then((r) => r.data),

  keywords: (resumeId: string) =>
    apiClient.get<KeywordResponse[]>(API_ROUTES.analysisKeywords(resumeId)).then((r) => r.data),

  history: (resumeId: string) =>
    apiClient
      .get<ResumeAnalysisSummaryResponse[]>(API_ROUTES.analysisHistory(resumeId))
      .then((r) => r.data),

  remove: (analysisId: string) =>
    apiClient.delete<void>(API_ROUTES.analysisDelete(analysisId)).then((r) => r.data),
};
