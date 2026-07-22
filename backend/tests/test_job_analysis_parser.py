from __future__ import annotations

import pytest

from app.core.exceptions import ExternalServiceException
from app.parsers.job_analysis_parser import JobAnalysisParser


def test_job_analysis_parser_parses_valid_payload() -> None:
    parser = JobAnalysisParser()

    result = parser.parse(
        """
        {
            "overall_match": 84,
            "ats_match": 80,
            "summary": "Good fit with minor gaps.",
            "matched_skills": ["Python"],
            "missing_skills": ["Kubernetes"],
            "keyword_matches": ["FastAPI"],
            "strengths": ["Strong API background"],
            "weaknesses": ["Limited cloud examples"],
            "recommendations": ["Add cloud deployment impact"]
        }
        """
    )

    assert result.overall_match == 84
    assert result.ats_match == 80
    assert result.summary == "Good fit with minor gaps."


def test_job_analysis_parser_rejects_malformed_payload() -> None:
    parser = JobAnalysisParser()

    with pytest.raises(ExternalServiceException, match="Invalid LLM response format"):
        parser.parse("not-json")


def test_job_analysis_parser_rejects_invalid_percentages() -> None:
    parser = JobAnalysisParser()

    with pytest.raises(ExternalServiceException, match="Invalid LLM response payload"):
        parser.parse(
            """
            {
                "overall_match": 140,
                "ats_match": 80,
                "summary": "Bad percentage",
                "matched_skills": [],
                "missing_skills": [],
                "keyword_matches": [],
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }
            """
        )


def test_job_analysis_parser_rejects_missing_required_fields() -> None:
    parser = JobAnalysisParser()

    with pytest.raises(ExternalServiceException, match="Invalid LLM response payload"):
        parser.parse(
            """
            {
                "overall_match": 80,
                "ats_match": 70,
                "matched_skills": [],
                "missing_skills": [],
                "keyword_matches": [],
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }
            """
        )


def test_job_analysis_parser_parses_fenced_json_with_wrapper_text() -> None:
    parser = JobAnalysisParser()

    result = parser.parse(
        """
        Here is your requested analysis.

        ```json
        {
            "overall_match": 79,
            "ats_match": 74,
            "summary": "Solid fit with moderate gaps.",
            "matched_skills": ["Python"],
            "missing_skills": ["Terraform"],
            "keyword_matches": ["FastAPI"],
            "strengths": ["API experience"],
            "weaknesses": ["Limited infra depth"],
            "recommendations": ["Add IaC project details"]
        }
        ```

        End of response.
        """
    )

    assert result.overall_match == 79
    assert result.ats_match == 74


def test_job_analysis_parser_parses_json_object_inside_prose() -> None:
    parser = JobAnalysisParser()

    result = parser.parse(
        """
        Analysis result below:
        {
            "overall_match": 82,
            "ats_match": 77,
            "summary": "Good fit.",
            "matched_skills": ["Python"],
            "missing_skills": ["Kubernetes"],
            "keyword_matches": ["REST APIs"],
            "strengths": ["Backend ownership"],
            "weaknesses": ["Cloud depth"],
            "recommendations": ["Add production deployment outcomes"]
        }
        Thanks.
        """
    )

    assert result.overall_match == 82
    assert result.summary == "Good fit."
