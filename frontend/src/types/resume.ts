// Mirrors backend/app/schemas/resume.py and backend/app/enums/resume.py exactly.

export type ResumeStatus = "active" | "archived" | "deleted";
export type ResumeFileType = "pdf" | "doc" | "docx" | "txt";

export interface ResumeResponse {
  id: string;
  user_id: string;
  title: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResumeListResponse {
  items: ResumeResponse[];
  total: number;
}

export interface ResumeVersionResponse {
  id: string;
  resume_id: string;
  version_number: number;
  content: string;
  file_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResumeUploadResponse {
  resume: ResumeResponse;
  version: ResumeVersionResponse;
  status: ResumeStatus;
  file_type: ResumeFileType;
}
