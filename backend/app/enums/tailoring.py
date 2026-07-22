"""Resume tailoring domain enums."""

from enum import StrEnum


class TailoringStatus(StrEnum):
    """Lifecycle state for a resume tailoring session."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
