"""Parsing and validation for Career Insight LLM responses."""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.core.exceptions import ExternalServiceException
from app.core.logging import logger
from app.dto.career import _LlmFields


class CareerInsightParser:
    """Parse raw LLM output into the structured _LlmFields model."""

    def parse(self, content: str) -> _LlmFields:
        """Parse and validate a raw LLM JSON response string.

        Args:
            content: The raw text returned by the LLM.

        Returns:
            Validated _LlmFields instance.

        Raises:
            ExternalServiceException: If the response cannot be parsed or
                validated as valid JSON matching the expected schema.
        """
        cleaned = self._prepare_content(content)
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            candidate = self._extract_json_object(cleaned)
            if candidate is None:
                raise ExternalServiceException(
                    "Career Insight: invalid LLM response format"
                ) from exc
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError as inner_exc:
                raise ExternalServiceException(
                    "Career Insight: invalid LLM response format"
                ) from inner_exc

        if not isinstance(payload, dict):
            raise ExternalServiceException(
                "Career Insight: LLM response is not a JSON object"
            )

        try:
            return _LlmFields.model_validate(payload)
        except ValidationError as exc:
            logger.error(
                "CareerInsightParser validation failed: errors=%s keys=%s",
                exc.errors(),
                list(payload.keys()),
            )
            raise ExternalServiceException(
                "Career Insight: invalid LLM response payload"
            ) from exc

    def _prepare_content(self, content: str) -> str:
        """Strip fences and locate JSON in the response."""
        stripped = content.strip()
        # Strip code fences if present
        if stripped.startswith("```"):
            end = stripped.find("\n")
            if end == -1:
                end = 3
            stripped = stripped[end:].strip()
            if stripped.endswith("```"):
                stripped = stripped[:-3].strip()
        return stripped

    @staticmethod
    def _extract_json_object(text: str) -> str | None:
        """Extract the first complete JSON object from *text*."""
        start = text.find("{")
        if start == -1:
            return None
        try:
            import json as _json

            decoder = _json.JSONDecoder()
            obj, end = decoder.raw_decode(text, start)
            return text[start:end]
        except json.JSONDecodeError:
            return None
