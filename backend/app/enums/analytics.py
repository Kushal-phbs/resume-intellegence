"""Analytics domain enums."""

from __future__ import annotations

from enum import Enum


class ActivityType(str, Enum):
    """Allowed activity event types used in activity logs."""

    RESUME_UPLOADED = "resume_uploaded"
    RESUME_ANALYZED = "resume_analyzed"
    JOB_ANALYZED = "job_analyzed"
    RESUME_TAILORED = "resume_tailored"
    COVER_LETTER_GENERATED = "cover_letter_generated"
    EXPORT_GENERATED = "export_generated"
    LOGIN = "login"


class EntityType(str, Enum):
    """Allowed entity categories referenced by activity events."""

    RESUME = "resume"
    ANALYSIS = "analysis"
    JOB = "job"
    TAILORING = "tailoring"
    COVER_LETTER = "cover_letter"
    EXPORT = "export"
