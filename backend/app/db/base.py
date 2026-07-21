"""Declarative base class and shared ORM mixins.

All persistence models should inherit from ``Base`` (directly or through the
mixins defined here) so that Alembic autogenerate and the async engine share a
single source of truth for table metadata.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = ["Base", "UUIDMixin", "TimestampMixin"]


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class UUIDMixin:
    """Adds a UUID primary key column generated client-side."""

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` columns maintained by the database."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
