"""Resume analysis domain enums."""

from enum import StrEnum


class AnalysisStatus(StrEnum):
    """Lifecycle state of a resume analysis job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SkillCategory(StrEnum):
    """Categories used to classify extracted skills."""

    TECHNICAL = "technical"
    SOFT = "soft"
    DOMAIN = "domain"
    TOOL = "tool"
    OTHER = "other"
