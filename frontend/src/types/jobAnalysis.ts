// Mirrors backend/app/schemas/job_analysis.py and backend/app/enums/job_analysis.py.
// NOTE: there is no backend endpoint to CREATE a JobDescription record — see README.
// job_id below must be an existing JobDescription UUID.

export type JobAnalysisStatus = "pending" | "processing" | "completed" | "failed";

export interface MatchedSkillResponse {
  id: string;
  job_analysis_id: string;
  skill_name: string;
  created_at: string;
  updated_at: string;
}

export interface MissingSkillResponse {
  id: string;
  job_analysis_id: string;
  skill_name: string;
  created_at: string;
  updated_at: string;
}

export interface KeywordMatchResponse {
  id: string;
  job_analysis_id: string;
  keyword: string;
  created_at: string;
  updated_at: string;
}

export interface JobAnalysisSummaryResponse {
  id: string;
  resume_id: string;
  job_description_id: string;
  analysis_status: JobAnalysisStatus;
  match_score: number | null;
  ats_match_score: number | null;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  created_at: string;
  updated_at: string;
  error_message: string | null;
}

export interface JobAnalysisResponse extends JobAnalysisSummaryResponse {
  summary: string | null;
  matched_skills: MatchedSkillResponse[];
  missing_skills: MissingSkillResponse[];
  keyword_matches: KeywordMatchResponse[];
}
