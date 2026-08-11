import { API_ROUTES } from "@/constants/routes";
import { toast } from "@/lib/toastBus";
import type { CoverLetterResponse, ExportFormat, TailoringResumeVersionResponse, TailoringSessionResponse, TailoringSummaryResponse } from "@/types/tailoring";
import { apiClient } from "./client";

function triggerDownload(data: Blob, disposition: string | null, fallbackName: string) {
  let filename = fallbackName;
  if (disposition) {
    const match = disposition.match(/filename\*?=(?:UTF-8'')?["']?([^"'\s;]+)/i);
    if (match) filename = decodeURIComponent(match[1]);
  }
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

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

  exportResume: async (versionId: string, format: ExportFormat) => {
    try {
      const { data, headers } = await apiClient.get<Blob>(API_ROUTES.exportResume(versionId, format), {
        responseType: "blob",
      });
      const disposition = headers["content-disposition"] as string | null;
      triggerDownload(data, disposition, `resume-${versionId}.${format}`);
    } catch {
      toast.error("Failed to export resume. Please try again.");
    }
  },

  exportCoverLetter: async (coverLetterId: string, format: ExportFormat) => {
    try {
      const { data, headers } = await apiClient.get<Blob>(API_ROUTES.exportCoverLetter(coverLetterId, format), {
        responseType: "blob",
      });
      const disposition = headers["content-disposition"] as string | null;
      triggerDownload(data, disposition, `cover-letter-${coverLetterId}.${format}`);
    } catch {
      toast.error("Failed to export cover letter. Please try again.");
    }
  },
};
