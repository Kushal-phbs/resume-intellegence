"""Regression test: reproduce the exact 2558->900 truncation bug.

Evidence:
- has_fences=False, has_json_prefix=True
- raw_len=2558, cleaned_len=900
- Preview shows valid JSON with professional_summary + experience_json
- 6 top-level fields expected: professional_summary, experience_json, skills_json,
  ats_score, recommendations_json, cover_letter
- HTTP 502 from ExternalServiceException (not json.JSONDecodeError)

Hypothesis:
_extract_json_object() incorrectly terminates at a } that is NOT the
top-level closing brace, due to in_string being toggled by unescaped "
inside a string value.
"""

from __future__ import annotations

import json

import pytest

from app.core.exceptions import ExternalServiceException
from app.parsers.tailoring_parser import TailoringParser

# ---------------------------------------------------------------------------
# Helper: build a realistic payload similar to what Groq LLM returns
# ---------------------------------------------------------------------------


def _build_full_payload() -> str:
    """Return a ~2500+ char JSON string with ALL 6 required top-level keys."""
    payload = {
        "professional_summary": (
            "Senior full-stack engineer with 10+ years of experience building "
            "scalable distributed systems using Python, FastAPI, PostgreSQL, "
            "and React. Proven track record of leading cross-functional teams "
            "to deliver high-impact products in fast-paced environments. "
            "Expert in cloud-native architecture on AWS with Kubernetes."
        ),
        "experience_json": [
            {
                "role": "Senior Backend Engineer",
                "company": "TechCorp Inc.",
                "duration": "2020-Present",
                "impact": (
                    "Designed and implemented microservices architecture "
                    "handling 50K+ RPM with 99.99% uptime using Python, "
                    "FastAPI, and PostgreSQL. Reduced p95 latency by 40%."
                ),
            },
            {
                "role": "Backend Engineer",
                "company": "StartupXYZ",
                "duration": "2017-2020",
                "impact": (
                    "Built real-time data processing pipeline handling "
                    "10M+ events/day using Apache Kafka and Python."
                ),
            },
        ],
        "skills_json": [
            {"name": "Python", "level": "expert"},
            {"name": "FastAPI", "level": "expert"},
            {"name": "PostgreSQL", "level": "advanced"},
            {"name": "AWS", "level": "advanced"},
            {"name": "Kubernetes", "level": "intermediate"},
            {"name": "React", "level": "advanced"},
        ],
        "ats_score": 85,
        "recommendations_json": [
            {"category": "keywords", "text": "Add more cloud-native terms"},
            {"category": "format", "text": "Use standard section headings"},
        ],
        "cover_letter": {
            "title": "Application for Senior Backend Engineer",
            "greeting": "Dear Hiring Manager,",
            "introduction": (
                "I am writing to express my strong interest in the Senior "
                "Backend Engineer position at TechCorp Inc."
            ),
            "body": (
                "With over 10 years of experience in backend engineering "
                "and a proven track record of delivering scalable solutions, "
                "I am confident in my ability to drive impact at TechCorp. "
                "At my current role, I reduced p95 latency by 40% through "
                "architectural improvements."
            ),
            "closing": (
                "Thank you for considering my application. I look forward "
                "to discussing how I can contribute to your team."
            ),
        },
    }
    return json.dumps(payload, indent=2)


def _build_payload_with_unescaped_quotes() -> str:
    """Return a payload where string values contain unescaped " chars.

    This produces INVALID JSON where unescaped " characters appear inside
    string values. The _extract_json_object algorithm must handle this
    gracefully (either extracting correctly or failing with a clear error).
    """
    # Build as a raw template string to embed unescaped quotes
    return """{
    "professional_summary": "A "proven" engineer with 10+ years building "
        ""scalable" systems",
    "experience_json": [
        {
            "role": "Senior Engineer",
            "impact": "Reduced "p95" latency by 40% and "cost" by 30%"
        }
    ],
    "skills_json": [],
    "ats_score": 85,
    "recommendations_json": [
        {"text": "Add "cloud" keywords"}
    ],
    "cover_letter": {
        "title": "App",
        "greeting": "Hi,",
        "introduction": "I am applying.",
        "body": "I have relevant "experience".",
        "closing": "Best regards"
    }
}"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTailoringParserRegression:
    """Reproduce exact bugs from production."""

    def test_parses_full_payload_with_all_six_keys(self) -> None:
        """The parser must handle a complete JSON object with all six fields."""
        parser = TailoringParser()
        raw = _build_full_payload()
        assert len(raw) > 2000, "Test payload too small"

        result = parser.parse(raw)

        assert result.resume_version.ats_score == 85
        assert result.resume_version.professional_summary
        assert len(result.resume_version.experience_json) == 2
        assert len(result.resume_version.skills_json) == 6
        assert len(result.resume_version.recommendations_json) == 2
        assert result.cover_letter.title
        assert result.cover_letter.greeting
        assert result.cover_letter.introduction
        assert result.cover_letter.body
        assert result.cover_letter.closing

    def test_unescaped_quotes_in_strings(self) -> None:
        """Reproduce: LLM returns invalid JSON with unescaped " inside strings.

        _extract_json_object() must NOT truncate when " characters inside
        string values toggle in_string incorrectly.
        """
        parser = TailoringParser()
        raw = _build_payload_with_unescaped_quotes()

        # This should either parse successfully or raise a clear error,
        # but it must NOT silently truncate to a partial object.
        try:
            result = parser.parse(raw)
            # If it parses, all 6 keys must be present
            fields = [
                "professional_summary",
                "experience_json",
                "skills_json",
                "ats_score",
                "recommendations_json",
            ]
            for field in fields:
                assert getattr(result.resume_version, field) is not None
            assert result.cover_letter is not None
        except ExternalServiceException:
            # Acceptable — invalid JSON should fail, but not truncate
            pass

    def test_prepare_content_does_not_truncate_valid_json(self) -> None:
        """_prepare_content must preserve the complete JSON object."""
        parser = TailoringParser()
        raw = _build_full_payload()
        raw_len = len(raw)

        cleaned = parser._prepare_content(raw)
        cleaned_len = len(cleaned)

        # The cleaned content should be CLOSE to the original length
        # (some whitespace normalization may occur)
        assert cleaned_len >= raw_len * 0.9, (
            f"_prepare_content truncated from {raw_len} to {cleaned_len} chars"
        )

        # The cleaned content must parse as complete valid JSON
        parsed = json.loads(cleaned)
        assert "cover_letter" in parsed, "Missing cover_letter key"
        assert "ats_score" in parsed, "Missing ats_score key"

    def test_extract_json_object_with_nested_objects(self) -> None:
        """_extract_json_object must handle deeply nested structures."""
        parser = TailoringParser()
        raw = _build_full_payload()

        # Directly test _extract_json_object
        start = raw.find("{")
        assert start == 0

        # Call the internal method
        result = parser._extract_json_object(raw)

        assert result is not None
        # The extracted object should contain the cover_letter key
        assert '"cover_letter"' in result, (
            f"_extract_json_object truncated: result length={len(result)}"
        )

    def test_prepare_content_trailing_text_after_json(self) -> None:
        """_prepare_content handles JSON followed by prose/text."""
        parser = TailoringParser()
        raw = _build_full_payload() + "\n\nThis response was generated for you."

        cleaned = parser._prepare_content(raw)
        parsed = json.loads(cleaned)

        assert "cover_letter" in parsed
        assert parsed["ats_score"] == 85

    def test_prepare_content_prose_before_json(self) -> None:
        """_prepare_content handles prose before JSON."""
        parser = TailoringParser()
        raw = "Here is your tailored resume:\n\n" + _build_full_payload()

        cleaned = parser._prepare_content(raw)
        parsed = json.loads(cleaned)

        assert "cover_letter" in parsed

    def test_extract_json_object_with_braces_in_strings(self) -> None:
        """String values containing { or } must not confuse depth counting."""
        parser = TailoringParser()

        payload = {
            "professional_summary": "Experienced in {Python, Java, C++} and {AWS, GCP}",
            "experience_json": [
                {"role": "Engineer", "impact": "Reduced bugs from {100} to {50}"},
            ],
            "skills_json": [],
            "ats_score": 80,
            "recommendations_json": [],
            "cover_letter": {
                "title": "App",
                "greeting": "Hi,",
                "introduction": "Applying.",
                "body": "Experience: {5 years} at {company}.",
                "closing": "Best",
            },
        }
        raw = json.dumps(payload, indent=2)

        result = parser.parse(raw)
        assert result.resume_version.ats_score == 80
        assert result.cover_letter.body == "Experience: {5 years} at {company}."


# ---------------------------------------------------------------------------
# Diagnostic: inspect _prepare_content behavior on realistic edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "description, raw, expected_has_fences, expected_has_prefix",
    [
        (
            "plain JSON",
            '{"a": 1}',
            False,
            True,
        ),
        (
            "JSON with backtick fence",
            '```json\n{"a": 1}\n```',
            True,
            False,
        ),
        (
            "JSON without lang tag",
            '```\n{"a": 1}\n```',
            True,
            False,
        ),
        (
            "JSON with prose prefix",
            'Here: {"a": 1}',
            False,
            False,
        ),
        (
            "JSON with prose and single brace in string",
            'Here: {"a": "text with } in it"}',
            False,
            False,
        ),
    ],
)
def test_prepare_content_variants(
    description: str,
    raw: str,
    expected_has_fences: bool,
    expected_has_prefix: bool,
) -> None:
    """Verify prepare_content handles various input formats."""
    parser = TailoringParser()
    cleaned = parser._prepare_content(raw)

    # Verify prepare_content worked
    assert len(cleaned) > 0
    # Parse the result to confirm it's valid JSON
    parsed = json.loads(cleaned)
    assert "a" in parsed
    if description == "JSON with prose and single brace in string":
        assert parsed["a"] == "text with } in it"
    else:
        assert parsed["a"] == 1
