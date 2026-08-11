import { API_ROUTES } from "@/constants/routes";
import { toast } from "@/lib/toastBus";
import type { ResumeListResponse, ResumeResponse, ResumeUploadResponse } from "@/types/resume";
import { apiClient } from "./client";

export const resumesApi = {
  list: () => apiClient.get<ResumeListResponse>(API_ROUTES.resumes).then((r) => r.data),

  get: (id: string) => apiClient.get<ResumeResponse>(API_ROUTES.resumeById(id)).then((r) => r.data),

  upload: (title: string, file: File) => {
    const form = new FormData();
    form.append("title", title);
    form.append("file", file);
    return apiClient
      .post<ResumeUploadResponse>(API_ROUTES.resumeUpload, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },

  remove: (id: string) => apiClient.delete<void>(API_ROUTES.resumeById(id)).then((r) => r.data),

  /** Triggers a browser download of the latest stored file for this resume. */
  downloadUrl: (id: string) => `${apiClient.defaults.baseURL}${API_ROUTES.resumeDownload(id)}`,

  /** Download a resume file through the authenticated API client. */
  download: async (id: string) => {
    try {
      const { data, headers } = await apiClient.get<Blob>(API_ROUTES.resumeDownload(id), {
        responseType: "blob",
      });
      const disposition = headers["content-disposition"];
      let filename = `resume-${id}`;
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
    } catch {
      toast.error("Failed to download resume. Please try again.");
    }
  },
};
