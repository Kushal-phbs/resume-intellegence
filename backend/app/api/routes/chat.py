from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.llm import get_llm_provider
from app.llm.base import BaseLLMProvider
from app.llm.models import LLMRequest, LLMResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_service(
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> ChatService:
    """Resolve a ChatService instance for the current request."""
    return ChatService(provider)


@router.post("/", response_model=LLMResponse)
async def chat_endpoint(
    request: LLMRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> LLMResponse:
    """Receive an LLM request and return the generated response."""
    return await chat_service.chat(request)
