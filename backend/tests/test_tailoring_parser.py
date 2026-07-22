from __future__ import annotations

import pytest

from app.core.exceptions import ExternalServiceException
from app.parsers.tailoring_parser import TailoringParser


def test_tailoring_parser_parses_valid_payload() -> None:
    parser = TailoringParser()

    result = parser.parse(
        """
        {
            "professional_summary": "Senior backend engineer with cloud experience.",
            "experience_json": [
                {"role": "Backend Engineer", "impact": "Reduced p95 by 40%"}
            ],
            "skills_json": [{"name": "Python"}],
            "ats_score": 86,
            "recommendations_json": [{"type": "keyword", "value": "Kubernetes"}],
            "cover_letter": {
                "title": "Application for Backend Engineer",
                "greeting": "Dear Hiring Team,",
                "introduction": "I am excited to apply.",
                "body": "I have delivered scalable APIs.",
                "closing": "Sincerely, Candidate"
            }
        }
        """
    )

    assert result.resume_version.ats_score == 86
    assert result.cover_letter.title == "Application for Backend Engineer"


def test_tailoring_parser_parses_fenced_json() -> None:
    parser = TailoringParser()

    result = parser.parse(
        """
        ```json
        {
            "professional_summary": "Summary",
            "experience_json": [],
            "skills_json": [],
            "ats_score": 80,
            "recommendations_json": [],
            "cover_letter": {
                "title": "T",
                "greeting": "G",
                "introduction": "I",
                "body": "B",
                "closing": "C"
            }
        }
        ```
        """
    )

    assert result.resume_version.ats_score == 80


def test_tailoring_parser_parses_json_inside_wrapper_prose() -> None:
    parser = TailoringParser()

    result = parser.parse(
        """
        Here is the requested output:
        {
            "professional_summary": "Summary",
            "experience_json": [],
            "skills_json": [],
            "ats_score": 77,
            "recommendations_json": [],
            "cover_letter": {
                "title": "T",
                "greeting": "G",
                "introduction": "I",
                "body": "B",
                "closing": "C"
            }
        }
        End.
        """
    )

    assert result.resume_version.ats_score == 77


def test_tailoring_parser_rejects_malformed_payload() -> None:
    parser = TailoringParser()

    with pytest.raises(ExternalServiceException, match="Invalid LLM response format"):
        parser.parse("not-json")


def test_tailoring_parser_rejects_invalid_payload_shape() -> None:
    parser = TailoringParser()

    with pytest.raises(ExternalServiceException, match="Invalid LLM response payload"):
        parser.parse(
            """
            {
                "professional_summary": "Summary",
                "experience_json": [],
                "skills_json": [],
                "ats_score": 77,
                "recommendations_json": []
            }
            """
        )
