"""ORM model registry.

Importing this module registers every mapped class with ``Base.metadata``,
which is required for Alembic autogenerate to detect the full schema.
"""

from app.models.activity_log import ActivityLog
from app.models.conversation import Conversation
from app.models.cover_letter import CoverLetter
from app.models.dashboard_snapshot import DashboardSnapshot
from app.models.job_analysis import JobAnalysis
from app.models.job_description import JobDescription
from app.models.keyword_match import KeywordMatch
from app.models.matched_skill import MatchedSkill
from app.models.message import Message
from app.models.missing_skill import MissingSkill
from app.models.notification import Notification
from app.models.profile import Profile
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.resume_keyword import ResumeKeyword
from app.models.resume_skill import ResumeSkill
from app.models.resume_tailoring_version import ResumeTailoringVersion
from app.models.resume_version import ResumeVersion
from app.models.tailoring_session import TailoringSession
from app.models.user import User
from app.models.user_analytics import UserAnalytics

__all__ = [
    "User",
    "Profile",
    "Resume",
    "ResumeVersion",
    "JobDescription",
    "JobAnalysis",
    "MatchedSkill",
    "MissingSkill",
    "KeywordMatch",
    "ResumeAnalysis",
    "ResumeSkill",
    "ResumeKeyword",
    "TailoringSession",
    "ResumeTailoringVersion",
    "CoverLetter",
    "DashboardSnapshot",
    "UserAnalytics",
    "ActivityLog",
    "Notification",
    "Conversation",
    "Message",
]
