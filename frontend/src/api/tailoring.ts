import { apiClient } from "./client";
import { API_ROUTES } from "@/constants/routes";
import type { TailoringSessionResponse, TailoringSummaryResponse, TailoringResumeVersionResponse, CoverLetterResponse, ExportFormat } from "@/types/tailoring";

export const tailoringApi = {
  // job_id must be an existing JobDescription UUID — see README "Known backend gap".
  create: (resumeId: string, jobId: string) =>
    apiClient
      .post<TailoringSummaryResponse>(API_ROUTES.tailoringCreate(resumeId, jobId))
      .then((r) => r.data),

  history: () =>
    apiClient.get<TailoringSessionResponse[]>(API_ROUTES.tailoringHistory).then((r) => r.data),

  session: (sessionId: string) =>
    apiClient.get<TailoringSessionResponse>(API_ROUTES.tailoringSession(sessionId)).then((r) => r.data),

  resumeVersion: (sessionId: string) =>
    apiClient
      .get<TailoringResumeVersionResponse>(API_ROUTES.tailoringResume(sessionId))
      .then((r) => r.data),

  coverLetter: (sessionId: string) =>
    apiClient.get<CoverLetterResponse>(API_ROUTES.tailoringCoverLetter(sessionId)).then((r) => r.data),

  remove: (sessionId: string) =>
    apiClient.delete<void>(API_ROUTES.tailoringSession(sessionId)).then((r) => r.data),

  exportResumeUrl: (versionId: string, format: ExportFormat) =>
    `${apiClient.defaults.baseURL}${API_ROUTES.exportResume(versionId, format)}`,

  exportCoverLetterUrl: (coverLetterId: string, format: ExportFormat) =>
    `${apiClient.defaults.baseURL}${API_ROUTES.exportCoverLetter(coverLetterId, format)}`,
};
