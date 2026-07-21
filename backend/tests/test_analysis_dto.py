from __future__ import annotations

from app.dto.analysis import AnalysisResult, AnalysisSkillResult
from app.enums import SkillCategory


def test_analysis_result_validates_and_serializes() -> None:
    result = AnalysisResult.model_validate(
        {
            "ats_score": 87,
            "resume_score": 91,
            "strengths": ["Clear structure"],
            "weaknesses": ["Could add metrics"],
            "recommendations": ["Quantify impact"],
            "skills": [{"skill_name": "Python", "category": SkillCategory.TECHNICAL}],
            "keywords": ["FastAPI"],
        }
    )

    assert result.ats_score == 87
    assert result.skills[0] == AnalysisSkillResult(
        skill_name="Python",
        category=SkillCategory.TECHNICAL,
    )
    assert result.model_dump()["keywords"] == ["FastAPI"]
