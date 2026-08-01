"""Production chat provider backed by Groq API via GroqClient."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from app.config.settings import settings
from app.core.exceptions import ExternalServiceException
from app.core.logging import logger
from app.llm.groq_client import GroqClient
from app.llm.providers.base_provider import BaseProvider

_ALLOWED_ROLES = {"system", "user", "assistant"}
_STREAM_CHUNK_SIZE = 120


class GroqProvider(BaseProvider):
    """Generate chat replies using Groq's OpenAI-compatible API."""

    def __init__(
        self,
        *,
        client: GroqClient | None = None,
        model: str | None = None,
    ) -> None:
        self._client = client or GroqClient(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            timeout_seconds=float(settings.groq_http_timeout),
            max_retries=settings.groq_max_retries,
        )
        self._model = model or settings.groq_model

    async def generate_reply(
        self,
        *,
        user_message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, dict[str, int]]:
        """Generate assistant content and usage metadata for chat workflows."""
        messages = self._build_messages(
            user_message=user_message,
            context=context,
            history=history,
        )

        try:
            payload = await self._client.chat_completion(
                model=self._model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            return self._parse_response(payload)
        except ExternalServiceException as exc:
            raise self._map_service_error(exc) from exc

    async def stream_reply(
        self,
        *,
        user_message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        """Yield assistant response chunks for streaming chat workflows."""
        reply, _ = await self.generate_reply(
            user_message=user_message,
            context=context,
            history=history,
        )

        for chunk in self._chunk_text(reply):
            yield chunk

    async def health_check(self) -> bool:
        """Return provider readiness by issuing a minimal completion request."""
        try:
            await self._client.chat_completion(
                model=self._model,
                messages=[{"role": "user", "content": "health check"}],
                temperature=0.0,
                max_tokens=1,
            )
            return True
        except ExternalServiceException:
            return False

    async def close(self) -> None:
        """Close underlying HTTP resources."""
        await self._client.close()

    def _build_messages(
        self,
        *,
        user_message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []

        context_prompt = self._context_prompt(context)
        if context_prompt:
            messages.append({"role": "system", "content": context_prompt})

        for item in history:
            role = str(item.get("role", "user")).lower()
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            if role not in _ALLOWED_ROLES:
                role = "user"
            messages.append({"role": role, "content": content})

        trimmed_user = user_message.strip()
        if trimmed_user and (
            not messages
            or messages[-1].get("role") != "user"
            or messages[-1].get("content") != trimmed_user
        ):
            messages.append({"role": "user", "content": trimmed_user})

        return messages

    def _context_prompt(self, context: dict[str, Any]) -> str:
        if not context:
            return ""
        try:
            serialized = json.dumps(context, ensure_ascii=True, separators=(",", ":"))
        except (TypeError, ValueError):
            logger.warning(
                "Failed to serialize chat context, using empty context prompt"
            )
            return ""
        return f"User context: {serialized}"

    def _parse_response(self, payload: dict[str, Any]) -> tuple[str, dict[str, int]]:
        try:
            choices = payload["choices"]
            first_choice = choices[0]
            message = first_choice["message"]
            content = str(message["content"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ExternalServiceException(
                "Groq API returned malformed response",
                status_code=502,
            ) from exc

        usage = payload.get("usage") if isinstance(payload, dict) else None
        usage_dict = usage if isinstance(usage, dict) else {}
        input_tokens = self._as_int(usage_dict.get("prompt_tokens"))
        output_tokens = self._as_int(usage_dict.get("completion_tokens"))
        total_tokens = self._as_int(usage_dict.get("total_tokens"))

        return content, {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

    def _map_service_error(
        self,
        exc: ExternalServiceException,
    ) -> ExternalServiceException:
        message = str(exc)
        lowered = message.lower()

        if "timed out" in lowered:
            return ExternalServiceException(
                "Groq API request timed out",
                status_code=504,
            )
        if "http 401" in lowered or "http 403" in lowered:
            return ExternalServiceException("Invalid Groq API key", status_code=401)
        if "http 429" in lowered:
            return ExternalServiceException(
                "Groq API rate limit exceeded",
                status_code=429,
            )
        if "http 404" in lowered or "http 400" in lowered:
            return ExternalServiceException("Groq model unavailable", status_code=503)
        return ExternalServiceException(message, status_code=exc.status_code)

    def _as_int(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _chunk_text(self, text: str) -> list[str]:
        if not text:
            return []
        return [
            text[i : i + _STREAM_CHUNK_SIZE]
            for i in range(0, len(text), _STREAM_CHUNK_SIZE)
        ]
