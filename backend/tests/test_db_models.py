"""Structural tests for the persistence layer (models + db package).

These tests validate ORM metadata, columns, constraints and relationships
without requiring a live PostgreSQL connection.
"""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import configure_mappers

from app.db.base import Base
from app.models import JobDescription, Profile, Resume, ResumeVersion, User


def test_all_models_are_registered_on_base_metadata() -> None:
    """Importing app.models must register every table on Base.metadata."""
    expected_tables = {
        "users",
        "profiles",
        "resumes",
        "resume_versions",
        "job_descriptions",
    }
    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_primary_keys_are_uuid_columns() -> None:
    """Every model must use a UUID primary key."""
    for model in (User, Profile, Resume, ResumeVersion, JobDescription):
        table = model.__table__
        pk_columns = list(table.primary_key.columns)
        assert len(pk_columns) == 1
        assert isinstance(pk_columns[0].type, PGUUID)
        assert pk_columns[0].default.arg.__qualname__ == uuid.uuid4.__qualname__


def test_models_have_created_at_and_updated_at_columns() -> None:
    """Every model must carry created_at/updated_at timestamp columns."""
    for model in (User, Profile, Resume, ResumeVersion, JobDescription):
        table = model.__table__
        assert "created_at" in table.columns
        assert "updated_at" in table.columns
        assert table.columns["created_at"].nullable is False
        assert table.columns["updated_at"].nullable is False


def test_profile_has_unique_foreign_key_to_user() -> None:
    """Profile <-> User is a one-to-one relationship enforced by a unique FK."""
    user_id_column = Profile.__table__.columns["user_id"]
    assert user_id_column.unique is True

    foreign_keys = list(user_id_column.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].column.table.name == "users"


def test_resume_and_resume_version_foreign_keys() -> None:
    resume_user_fk = list(Resume.__table__.columns["user_id"].foreign_keys)
    assert resume_user_fk[0].column.table.name == "users"

    version_resume_fk = list(ResumeVersion.__table__.columns["resume_id"].foreign_keys)
    assert version_resume_fk[0].column.table.name == "resumes"


def test_resume_version_unique_constraint_per_resume() -> None:
    """A resume cannot have two versions with the same version number."""
    constraint_columns = {
        tuple(col.name for col in constraint.columns)
        for constraint in ResumeVersion.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("resume_id", "version_number") in constraint_columns


def test_job_description_foreign_key_to_user() -> None:
    foreign_keys = list(JobDescription.__table__.columns["user_id"].foreign_keys)
    assert foreign_keys[0].column.table.name == "users"


def test_relationships_are_configured_both_ways() -> None:
    """Relationships must be mapped and bidirectional via back_populates."""
    configure_mappers()

    user_rels = {rel.key for rel in User.__mapper__.relationships}
    assert {"profile", "resumes", "job_descriptions"}.issubset(user_rels)

    assert "user" in {rel.key for rel in Profile.__mapper__.relationships}
    assert "user" in {rel.key for rel in Resume.__mapper__.relationships}
    assert "versions" in {rel.key for rel in Resume.__mapper__.relationships}
    assert "resume" in {rel.key for rel in ResumeVersion.__mapper__.relationships}
    assert "user" in {rel.key for rel in JobDescription.__mapper__.relationships}
