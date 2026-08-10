"""Parsing and validation for resume tailoring LLM responses."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.exceptions import ExternalServiceException
from app.core.logging import logger
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

        # --- DEBUG LOGGING (safe, no PII / secrets) ---
        _log_response_type_and_preview(content, cleaned)

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

        payload = self._normalize_json_arrays(payload)

        try:
            parsed = _ParsedTailoringPayload.model_validate(payload)
        except ValidationError as exc:
            logger.error(
                "TailoringParser validation failed: errors=%s payload_keys=%s",
                exc.errors(),
                list(payload.keys())
                if isinstance(payload, dict)
                else type(payload).__name__,
            )
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
        # 1. Try to extract content from a fenced code block (```json ... ```).
        fenced = self._FENCED_BLOCK_RE.search(stripped)
        if fenced is not None:
            return fenced.group(1).strip()
        # 2. Try to strip fences that span the entire string.
        no_fences = self._strip_code_fences(stripped)
        if no_fences != stripped:
            return no_fences
        # 3. If the result is still not valid JSON, try extracting the first
        #    top-level JSON object from the text (handles prose-wrapped output).
        candidate = self._extract_json_object(no_fences)
        if candidate is not None:
            return candidate
        return no_fences

    @staticmethod
    def _normalize_json_arrays(payload: object) -> dict[str, object]:
        """Normalize JSON array fields that the LLM may return as lists of strings
        instead of lists of dicts.  Each string item is wrapped into a dict with
        a single key ``"value"`` so that downstream ``list[dict[str, object]]``
        validation passes.  Non-dict payloads are returned as-is."""
        if not isinstance(payload, dict):
            return payload  # type: ignore[return-value]
        _ARRAY_FIELDS = {"experience_json", "skills_json", "recommendations_json"}
        for field in _ARRAY_FIELDS:
            items = payload.get(field)
            if not isinstance(items, list):
                continue
            normalized: list[dict[str, object]] = []
            for item in items:
                if isinstance(item, dict):
                    normalized.append(item)
                elif isinstance(item, str):
                    normalized.append({"value": item})
                else:
                    # drop non-dict, non-string items (e.g. None, numbers)
                    continue
            payload[field] = normalized
        return payload

    def _extract_json_object(self, text: str) -> str | None:
        """Extract the first complete JSON object from *text*.

        Uses Python's built-in ``json.JSONDecoder.raw_decode`` which correctly
        handles all JSON edge cases (nested objects, arrays, escaped quotes,
        braces inside strings, etc.) and never silently truncates malformed
        JSON.
        """
        start = text.find("{")
        if start == -1:
            return None
        try:
            decoder = json.JSONDecoder()
            obj, end = decoder.raw_decode(text, start)
            return text[start:end]
        except json.JSONDecodeError:
            return None


def _log_response_type_and_preview(raw: str, cleaned: str) -> None:
    """Log the response type and a safe preview (max 1000 chars, no PII)."""
    has_fences = bool(TailoringParser._FENCED_BLOCK_RE.search(raw))
    has_json_prefix = raw.strip().startswith("{")
    preview = cleaned[:1000]
    logger.debug(
        "TailoringParser input: has_fences=%s has_json_prefix=%s "
        "raw_len=%d cleaned_len=%d preview=%.1000s",
        has_fences,
        has_json_prefix,
        len(raw),
        len(cleaned),
        preview,
    )
