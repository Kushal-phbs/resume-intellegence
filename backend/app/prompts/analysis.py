"""Compatibility exports for resume analysis prompt builders."""

from app.prompts.ats import AtsPrompt as AtsAnalysisPrompt
from app.prompts.keywords import KeywordPrompt as KeywordExtractionPrompt
from app.prompts.resume_parser import ResumeParserPrompt as ResumeParsingPrompt
from app.prompts.resume_review import ResumeReviewPrompt
from app.prompts.skills import SkillPrompt as SkillExtractionPrompt

__all__ = [
    "ResumeParsingPrompt",
    "AtsAnalysisPrompt",
    "SkillExtractionPrompt",
    "KeywordExtractionPrompt",
    "ResumeReviewPrompt",
]
