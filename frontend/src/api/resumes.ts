import { apiClient } from "./client";
import { API_ROUTES } from "@/constants/routes";
import type { ResumeListResponse, ResumeResponse, ResumeUploadResponse } from "@/types/resume";

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
};
