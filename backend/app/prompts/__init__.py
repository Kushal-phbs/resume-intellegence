"""Prompt templates used by the application."""

from app.prompts.ats import AtsPrompt
from app.prompts.chat import ChatPrompt
from app.prompts.cover_letter_builder import CoverLetterPrompt
from app.prompts.job_match import JobMatchPrompt
from app.prompts.keyword_match import KeywordMatchPrompt
from app.prompts.keywords import KeywordPrompt
from app.prompts.missing_skills import MissingSkillsPrompt
from app.prompts.recommendations import JobRecommendationsPrompt
from app.prompts.resume_parser import ResumeParserPrompt
from app.prompts.resume_review import ResumeReviewPrompt
from app.prompts.resume_rewrite import ResumeRewritePrompt
from app.prompts.skills import SkillPrompt
from app.prompts.tailoring_ats import TailoringAtsPrompt

AtsAnalysisPrompt = AtsPrompt
KeywordExtractionPrompt = KeywordPrompt
ResumeParsingPrompt = ResumeParserPrompt
SkillExtractionPrompt = SkillPrompt

__all__ = [
    "ChatPrompt",
    "ResumeParsingPrompt",
    "AtsAnalysisPrompt",
    "SkillExtractionPrompt",
    "KeywordExtractionPrompt",
    "ResumeReviewPrompt",
    "JobMatchPrompt",
    "MissingSkillsPrompt",
    "KeywordMatchPrompt",
    "JobRecommendationsPrompt",
    "ResumeRewritePrompt",
    "CoverLetterPrompt",
    "TailoringAtsPrompt",
]
