"""Job intelligence domain enums."""

from enum import StrEnum


class JobAnalysisStatus(StrEnum):
    """Lifecycle state of a job analysis job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
