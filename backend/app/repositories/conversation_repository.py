"""Persistence operations for chat conversations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationRepository:
    """Data-access operations for conversations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: UUID, title: str) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self._session.add(conversation)
        await self._session.flush()
        await self._session.refresh(conversation)
        return conversation

    async def get(self, conversation_id: UUID) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def rename(self, conversation_id: UUID, *, title: str) -> Conversation | None:
        conversation = await self.get(conversation_id)
        if conversation is None:
            return None
        conversation.title = title
        await self._session.flush()
        return conversation

    async def delete(self, conversation_id: UUID) -> bool:
        conversation = await self.get(conversation_id)
        if conversation is None:
            return False
        await self._session.delete(conversation)
        await self._session.flush()
        return True

    async def get_latest(self, user_id: UUID) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc(), Conversation.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
