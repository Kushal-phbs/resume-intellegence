// Mirrors backend/app/schemas/resume_tailoring.py and backend/app/enums/tailoring.py.
// NOTE: creating a session requires an existing job_description_id — see README.

export type TailoringStatus = "pending" | "processing" | "completed" | "failed";

export interface TailoringResumeVersionResponse {
  id: string;
  resume_id: string;
  tailoring_session_id: string;
  professional_summary: string;
  experience_json: Array<Record<string, unknown>>;
  skills_json: Array<Record<string, unknown>>;
  ats_score: number;
  recommendations_json: Array<Record<string, unknown>>;
  created_at: string;
  updated_at: string;
}

export interface CoverLetterResponse {
  id: string | null;
  tailoring_session_id: string | null;
  title: string;
  greeting: string;
  introduction: string;
  body: string;
  closing: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface TailoringSessionResponse {
  id: string;
  resume_id: string;
  job_description_id: string;
  status: TailoringStatus;
  created_at: string;
  updated_at: string;
}

export interface TailoringSummaryResponse {
  session: TailoringSessionResponse;
  resume_version: TailoringResumeVersionResponse;
  cover_letter: CoverLetterResponse;
}

export type ExportFormat = "md" | "docx" | "pdf";
