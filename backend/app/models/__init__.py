"""ORM model registry.

Importing this module registers every mapped class with ``Base.metadata``,
which is required for Alembic autogenerate to detect the full schema.
"""

from app.models.job_description import JobDescription
from app.models.profile import Profile
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.resume_keyword import ResumeKeyword
from app.models.resume_skill import ResumeSkill
from app.models.resume_version import ResumeVersion
from app.models.user import User

__all__ = [
    "User",
    "Profile",
    "Resume",
    "ResumeVersion",
    "JobDescription",
    "ResumeAnalysis",
    "ResumeSkill",
    "ResumeKeyword",
]
