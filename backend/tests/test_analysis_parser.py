from __future__ import annotations

import pytest

from app.core.exceptions import ExternalServiceException
from app.enums import SkillCategory
from app.parsers.analysis_parser import AnalysisParser


def test_analysis_parser_parses_valid_payload() -> None:
    parser = AnalysisParser()

    result = parser.parse(
        """
        {
            "resume_score": 93,
            "ats_score": 101,
            "strengths": ["Clear structure"],
            "weaknesses": ["Could add metrics"],
            "recommendations": ["Quantify results"],
            "skills": [{"skill_name": "Python", "category": "technical"}],
            "keywords": ["FastAPI"]
        }
        """
    )

    assert result.resume_score == 93
    assert result.ats_score == 100
    assert result.skills[0].category == SkillCategory.TECHNICAL


def test_analysis_parser_rejects_malformed_payload() -> None:
    parser = AnalysisParser()

    with pytest.raises(ExternalServiceException, match="Invalid LLM response format"):
        parser.parse("not-json")


def test_analysis_parser_rejects_missing_fields() -> None:
    parser = AnalysisParser()

    with pytest.raises(ExternalServiceException, match="Invalid LLM response format"):
        parser.parse("{ats_score: 10}")


def test_analysis_parser_clamps_invalid_ats_score() -> None:
    parser = AnalysisParser()

    result = parser.parse(
        """
        {
            "resume_score": 80,
            "ats_score": -25,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "skills": [],
            "keywords": []
        }
        """
    )

    assert result.ats_score == 0


def test_analysis_parser_rejects_invalid_skill_structure() -> None:
    parser = AnalysisParser()

    with pytest.raises(ExternalServiceException, match="Invalid LLM response payload"):
        parser.parse(
            """
            {
                "resume_score": 80,
                "ats_score": 75,
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "skills": [{"skill_name": ""}],
                "keywords": []
            }
            """
        )
