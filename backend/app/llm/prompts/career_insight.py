"""LLM prompt for generating Career Insight analysis."""

from __future__ import annotations

SYSTEM_PROMPT = """
You are a career progression analyst. Your task is to analyze the user's
resume history and generate evidence-based career insights.

RULES:
1. You may ONLY reference skills, versions, analyses, and job data that are
   provided in the evidence payload below.
2. Do NOT invent skills, version IDs, analysis IDs, job analysis IDs, or
   tailoring session IDs.
3. Every claim about experience_growth, career_fields, strengths, and
   next_opportunities must be supported by evidence supplied in the context.
4. If the evidence is insufficient to make a claim, leave that field empty
   — do not fabricate.
5. Return ONLY valid JSON that matches the exact schema specified.
6. The "confidence" field for career_fields must be between 0.0 and 1.0 and
   reflect how many of the user's skills support that field.
7. priority for next_opportunities must be one of: "high", "medium", "low".
8. Keep descriptions concise and actionable — aim for 1-3 sentences per
   claim.
""".strip()


USER_PROMPT_TEMPLATE = """
Analyze this user's career progression data and return structured insights.

## Resumes Overview
Total resumes: {total_resumes}
Total versions analyzed: {total_versions}
Total version pairs compared: {total_pairs}
Longest analysis span: {longest_span_days} days

## Latest ATS Scores
Latest: {latest_ats}
Previous: {previous_ats}
Delta: {ats_delta}

## Skill Changes Across Version Pairs
{skill_changes_text}

## Per-Version Analysis Strengths & Weaknesses
{version_analyses_text}

## Job Analysis History
{job_analyses_text}

## Tailoring Session History
{tailoring_sessions_text}

## Latest Resume Excerpt (first 2000 chars)
{resume_excerpt}

Return ONLY valid JSON matching this exact schema:
{{
  "experience_growth": [
    {{
      "area": "string — e.g. Backend Engineering",
      "description": "string — what improved",
      "evidence_resume_version_id": "string | null",
      "evidence_analysis_id": "string | null",
      "source_snippet": "string | null — short excerpt from newer version",
      "related_skills": ["string"]
    }}
  ],
  "career_fields": [
    {{
      "field_name": "string",
      "confidence": 0.0,
      "evidence_summary": "string — why you believe this",
      "matching_skills": ["string"],
      "job_analysis_ids": ["string"],
      "tailoring_session_ids": ["string"],
      "resume_version_ids": ["string"]
    }}
  ],
  "strengths": [
    {{
      "title": "string",
      "description": "string",
      "evidence_analysis_ids": ["string"],
      "evidence_job_analysis_ids": ["string"],
      "source_snippets": ["string"]
    }}
  ],
  "next_opportunities": [
    {{
      "opportunity": "string",
      "reason": "string",
      "priority": "high|medium|low",
      "evidence_job_analysis_ids": ["string"],
      "evidence_missing_skills": ["string"],
      "related_field": "string | null"
    }}
  ]
}}
""".strip()


def build_prompt(
    *,
    total_resumes: int,
    total_versions: int,
    total_pairs: int,
    longest_span_days: int | None,
    latest_ats: int | None,
    previous_ats: int | None,
    ats_delta: int | None,
    skill_changes_text: str,
    version_analyses_text: str,
    job_analyses_text: str,
    tailoring_sessions_text: str,
    resume_excerpt: str,
) -> str:
    """Build the user prompt for the Career Insight LLM call."""
    return USER_PROMPT_TEMPLATE.format(
        total_resumes=total_resumes,
        total_versions=total_versions,
        total_pairs=total_pairs,
        longest_span_days=longest_span_days or 0,
        latest_ats=latest_ats or "N/A",
        previous_ats=previous_ats or "N/A",
        ats_delta=ats_delta or 0,
        skill_changes_text=skill_changes_text,
        version_analyses_text=version_analyses_text,
        job_analyses_text=job_analyses_text,
        tailoring_sessions_text=tailoring_sessions_text,
        resume_excerpt=resume_excerpt,
    )
