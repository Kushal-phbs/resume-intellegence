// Mirrors backend/app/schemas/analysis.py and backend/app/enums/analysis.py exactly.

export type AnalysisStatus = "pending" | "processing" | "completed" | "failed";
export type SkillCategory = "technical" | "soft" | "domain" | "tool" | "other";

export interface SkillResponse {
  id: string;
  analysis_id: string;
  skill_name: string;
  category: SkillCategory;
  created_at: string;
  updated_at: string;
}

export interface KeywordResponse {
  id: string;
  analysis_id: string;
  keyword: string;
  created_at: string;
  updated_at: string;
}

export interface ResumeAnalysisSummaryResponse {
  id: string;
  resume_id: string;
  resume_version_id: string;
  analysis_status: AnalysisStatus;
  resume_score: number | null;
  ats_score: number | null;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  skill_count: number;
  keyword_count: number;
  created_at: string;
  updated_at: string;
  error_message: string | null;
}

export interface ResumeAnalysisResponse {
  id: string;
  resume_id: string;
  resume_version_id: string;
  analysis_status: AnalysisStatus;
  resume_score: number | null;
  ats_score: number | null;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  skills: SkillResponse[];
  keywords: KeywordResponse[];
  created_at: string;
  updated_at: string;
  error_message: string | null;
}
