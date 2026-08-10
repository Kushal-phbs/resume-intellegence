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


def test_tailoring_parser_parses_fenced_json_with_prose_before_and_after() -> None:
    """Regression: LLM wraps JSON in ```json fences with text before/after."""
    parser = TailoringParser()

    result = parser.parse(
        """Here is your tailored resume:

```json
{
    "professional_summary": "Experienced engineer",
    "experience_json": [{"role": "Engineer", "impact": "Improved perf"}],
    "skills_json": [{"name": "Python"}],
    "ats_score": 90,
    "recommendations_json": [{"type": "keyword", "value": "AWS"}],
    "cover_letter": {
        "title": "Application",
        "greeting": "Dear Team,",
        "introduction": "I am writing to apply.",
        "body": "I have the skills you need.",
        "closing": "Best regards"
    }
}
```

Please review and let me know if you need changes."""
    )

    assert result.resume_version.ats_score == 90
    assert result.cover_letter.title == "Application"


def test_tailoring_parser_parses_fenced_json_without_language_tag() -> None:
    """Regression: LLM uses plain ``` fences without 'json' tag."""
    parser = TailoringParser()

    result = parser.parse(
        """
        ```
        {
            "professional_summary": "Summary",
            "experience_json": [],
            "skills_json": [],
            "ats_score": 75,
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

    assert result.resume_version.ats_score == 75


def test_tailoring_parser_parses_fenced_json_with_trailing_newlines() -> None:
    """Regression: LLM output has extra blank lines after closing fence."""
    parser = TailoringParser()

    result = parser.parse(
        """```json
{
    "professional_summary": "Summary",
    "experience_json": [],
    "skills_json": [],
    "ats_score": 82,
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

    assert result.resume_version.ats_score == 82


def test_tailoring_parser_normalizes_skills_json_strings() -> None:
    """Regression: LLM returns skills_json as list of strings, not dicts."""
    parser = TailoringParser()

    result = parser.parse(
        """{
    "professional_summary": "Full stack developer.",
    "experience_json": [],
    "skills_json": ["Python", "FastAPI", "PostgreSQL"],
    "ats_score": 88,
    "recommendations_json": [],
    "cover_letter": {
        "title": "Application",
        "greeting": "Dear Team,",
        "introduction": "I am applying.",
        "body": "I have the skills.",
        "closing": "Best"
    }
}"""
    )

    assert result.resume_version.ats_score == 88
    assert result.resume_version.skills_json == [
        {"value": "Python"},
        {"value": "FastAPI"},
        {"value": "PostgreSQL"},
    ]


def test_tailoring_parser_normalizes_experience_json_strings() -> None:
    """Regression: LLM returns experience_json as list of strings, not dicts."""
    parser = TailoringParser()

    result = parser.parse(
        """{
    "professional_summary": "Senior engineer.",
    "experience_json": ["Led team of 5", "Built microservices", "Deployed to AWS"],
    "skills_json": [],
    "ats_score": 85,
    "recommendations_json": [],
    "cover_letter": {
        "title": "App",
        "greeting": "Hi,",
        "introduction": "I am interested.",
        "body": "My experience matches.",
        "closing": "Regards"
    }
}"""
    )

    assert result.resume_version.ats_score == 85
    assert result.resume_version.experience_json == [
        {"value": "Led team of 5"},
        {"value": "Built microservices"},
        {"value": "Deployed to AWS"},
    ]


def test_tailoring_parser_normalizes_recommendations_json_strings() -> None:
    """Regression: LLM returns recommendations_json as list of strings."""
    parser = TailoringParser()

    result = parser.parse(
        """{
    "professional_summary": "Developer.",
    "experience_json": [],
    "skills_json": [],
    "ats_score": 70,
    "recommendations_json": ["Add Kubernetes", "Improve test coverage"],
    "cover_letter": {
        "title": "App",
        "greeting": "Greetings,",
        "introduction": "I'd like to apply.",
        "body": "I am a good fit.",
        "closing": "Thanks"
    }
}"""
    )

    assert result.resume_version.ats_score == 70
    assert result.resume_version.recommendations_json == [
        {"value": "Add Kubernetes"},
        {"value": "Improve test coverage"},
    ]


def test_tailoring_parser_preserves_dict_arrays_when_mixed() -> None:
    """Regression: LLM returns some array items as dicts, some as strings."""
    parser = TailoringParser()

    result = parser.parse(
        """{
    "professional_summary": "Engineer.",
    "experience_json": [{"role": "Senior", "years": 5}, "Built APIs"],
    "skills_json": [{"name": "Python", "level": "advanced"}, "FastAPI"],
    "ats_score": 80,
    "recommendations_json": [],
    "cover_letter": {
        "title": "App",
        "greeting": "Hi,",
        "introduction": "Applying.",
        "body": "I fit.",
        "closing": "Best"
    }
}"""
    )

    assert result.resume_version.ats_score == 80
    assert result.resume_version.experience_json == [
        {"role": "Senior", "years": 5},
        {"value": "Built APIs"},
    ]
    assert result.resume_version.skills_json == [
        {"name": "Python", "level": "advanced"},
        {"value": "FastAPI"},
    ]


def test_tailoring_parser_parses_json_with_extra_text_after_brace() -> None:
    """Regression: LLM appends text after the closing JSON brace."""
    parser = TailoringParser()

    result = parser.parse(
        """{
    "professional_summary": "Summary",
    "experience_json": [],
    "skills_json": [],
    "ats_score": 65,
    "recommendations_json": [],
    "cover_letter": {
        "title": "T",
        "greeting": "G",
        "introduction": "I",
        "body": "B",
        "closing": "C"
    }
}
This JSON was generated for you."""
    )

    assert result.resume_version.ats_score == 65
