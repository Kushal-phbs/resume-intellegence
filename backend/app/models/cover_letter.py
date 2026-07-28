"""CoverLetter ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.tailoring_session import TailoringSession


class CoverLetter(UUIDMixin, TimestampMixin, Base):
    """A generated cover letter tied to one tailoring session."""

    __tablename__ = "cover_letters"
    __table_args__ = (
        UniqueConstraint("tailoring_session_id", name="uq_cover_letters_session_id"),
    )

    tailoring_session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tailoring_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    greeting: Mapped[str] = mapped_column(Text, nullable=False)
    introduction: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    closing: Mapped[str] = mapped_column(Text, nullable=False)

    tailoring_session: Mapped["TailoringSession"] = relationship(
        back_populates="cover_letter"
    )
