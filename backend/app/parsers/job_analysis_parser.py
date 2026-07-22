"""Parsing and validation for LLM job analysis responses."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.exceptions import ExternalServiceException
from app.dto.job_analysis import JobAnalysisResult


class _ParsedJobAnalysisPayload(BaseModel):
    overall_match: int = Field(ge=0, le=100)
    ats_match: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    keyword_matches: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    @field_validator(
        "matched_skills",
        "missing_skills",
        "keyword_matches",
        "strengths",
        "weaknesses",
        "recommendations",
    )
    @classmethod
    def _normalize_lists(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]

    @field_validator("summary")
    @classmethod
    def _normalize_summary(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Summary must not be blank")
        return cleaned


class JobAnalysisParser:
    """Parse raw LLM output into a typed ``JobAnalysisResult``."""

    _FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.DOTALL)
    _FENCED_BLOCK_RE = re.compile(
        r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL
    )

    def parse(self, content: str) -> JobAnalysisResult:
        """Parse and validate a raw LLM response string."""
        cleaned = self._prepare_content(content)

        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            candidate = self._extract_json_object(cleaned)
            if candidate is None:
                raise ExternalServiceException("Invalid LLM response format") from exc
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError as inner_exc:
                raise ExternalServiceException(
                    "Invalid LLM response format"
                ) from inner_exc

        try:
            parsed = _ParsedJobAnalysisPayload.model_validate(payload)
        except ValidationError as exc:
            raise ExternalServiceException("Invalid LLM response payload") from exc

        return JobAnalysisResult(
            overall_match=parsed.overall_match,
            ats_match=parsed.ats_match,
            summary=parsed.summary,
            matched_skills=parsed.matched_skills,
            missing_skills=parsed.missing_skills,
            keyword_matches=parsed.keyword_matches,
            strengths=parsed.strengths,
            weaknesses=parsed.weaknesses,
            recommendations=parsed.recommendations,
        )

    def _strip_code_fences(self, content: str) -> str:
        """Remove markdown code fences commonly returned by LLMs."""
        return self._FENCE_RE.sub("", content).strip()

    def _prepare_content(self, content: str) -> str:
        """Normalize wrapper formats and preserve the most likely JSON payload."""
        stripped = content.strip()
        fenced = self._FENCED_BLOCK_RE.search(stripped)
        if fenced is not None:
            return fenced.group(1).strip()
        return self._strip_code_fences(stripped)

    def _extract_json_object(self, text: str) -> str | None:
        """Extract the first balanced JSON object from wrapper prose."""
        start = text.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False

        for index in range(start, len(text)):
            char = text[index]

            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]

        return None
