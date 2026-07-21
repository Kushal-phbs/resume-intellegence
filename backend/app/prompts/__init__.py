"""Prompt templates used by the application."""

from app.prompts.ats import AtsPrompt
from app.prompts.chat import ChatPrompt
from app.prompts.keywords import KeywordPrompt
from app.prompts.resume_parser import ResumeParserPrompt
from app.prompts.resume_review import ResumeReviewPrompt
from app.prompts.skills import SkillPrompt

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
]
