"""Persistence operations for chat messages."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:
    """Data-access operations for conversation messages."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        conversation_id: UUID,
        role: str,
        content: str,
        token_count: int,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            token_count=max(token_count, 0),
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def bulk_create(
        self,
        *,
        conversation_id: UUID,
        messages: list[dict[str, str | int]],
    ) -> list[Message]:
        rows = [
            Message(
                conversation_id=conversation_id,
                role=str(item["role"]),
                content=str(item["content"]),
                token_count=max(int(item.get("token_count", 0)), 0),
            )
            for item in messages
        ]
        self._session.add_all(rows)
        await self._session.flush()
        for row in rows:
            await self._session.refresh(row)
        return rows

    async def list_messages(
        self,
        conversation_id: UUID,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Message]:
        result = await self._session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_conversation_messages(self, conversation_id: UUID) -> int:
        result = await self._session.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )
        await self._session.flush()
        return result.rowcount or 0
