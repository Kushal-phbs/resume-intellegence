"""Parsing and validation for resume tailoring LLM responses."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.exceptions import ExternalServiceException
from app.dto.tailoring import CoverLetterDTO, ResumeTailoringDTO, ResumeVersionDTO


class _ParsedCoverLetter(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    greeting: str = Field(min_length=1)
    introduction: str = Field(min_length=1)
    body: str = Field(min_length=1)
    closing: str = Field(min_length=1)

    @field_validator("title", "greeting", "introduction", "body", "closing")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Cover letter fields must not be blank")
        return cleaned


class _ParsedTailoringPayload(BaseModel):
    professional_summary: str = Field(min_length=1)
    experience_json: list[dict[str, object]] = Field(default_factory=list)
    skills_json: list[dict[str, object]] = Field(default_factory=list)
    ats_score: int = Field(ge=0, le=100)
    recommendations_json: list[dict[str, object]] = Field(default_factory=list)
    cover_letter: _ParsedCoverLetter

    @field_validator("professional_summary")
    @classmethod
    def _strip_summary(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("professional_summary must not be blank")
        return cleaned


class TailoringParser:
    """Parse raw LLM output into validated tailoring DTOs."""

    _FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.DOTALL)
    _FENCED_BLOCK_RE = re.compile(
        r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL
    )

    def parse(self, content: str) -> ResumeTailoringDTO:
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
            parsed = _ParsedTailoringPayload.model_validate(payload)
        except ValidationError as exc:
            raise ExternalServiceException("Invalid LLM response payload") from exc

        resume_version = ResumeVersionDTO(
            professional_summary=parsed.professional_summary,
            experience_json=parsed.experience_json,
            skills_json=parsed.skills_json,
            ats_score=parsed.ats_score,
            recommendations_json=parsed.recommendations_json,
        )
        cover_letter = CoverLetterDTO(
            title=parsed.cover_letter.title,
            greeting=parsed.cover_letter.greeting,
            introduction=parsed.cover_letter.introduction,
            body=parsed.cover_letter.body,
            closing=parsed.cover_letter.closing,
        )
        return ResumeTailoringDTO(
            session=None,
            resume_version=resume_version,
            cover_letter=cover_letter,
        )

    def _strip_code_fences(self, content: str) -> str:
        return self._FENCE_RE.sub("", content).strip()

    def _prepare_content(self, content: str) -> str:
        stripped = content.strip()
        fenced = self._FENCED_BLOCK_RE.search(stripped)
        if fenced is not None:
            return fenced.group(1).strip()
        return self._strip_code_fences(stripped)

    def _extract_json_object(self, text: str) -> str | None:
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
