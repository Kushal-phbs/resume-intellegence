from __future__ import annotations

from app.dto.job_analysis import JobAnalysisResult


def test_job_analysis_result_validates_and_serializes() -> None:
    result = JobAnalysisResult.model_validate(
        {
            "overall_match": 82,
            "ats_match": 78,
            "summary": "Strong alignment with backend role requirements.",
            "matched_skills": ["Python", "FastAPI"],
            "missing_skills": ["Kubernetes"],
            "keyword_matches": ["REST APIs", "SQLAlchemy"],
            "strengths": ["Clear backend experience"],
            "weaknesses": ["Limited cloud depth"],
            "recommendations": ["Add cloud project outcomes"],
        }
    )

    assert result.overall_match == 82
    assert result.ats_match == 78
    assert result.model_dump()["matched_skills"] == ["Python", "FastAPI"]
