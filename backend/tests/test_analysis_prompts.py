from __future__ import annotations

from app.prompts.ats import AtsPrompt
from app.prompts.keywords import KeywordPrompt
from app.prompts.resume_parser import ResumeParserPrompt
from app.prompts.resume_review import ResumeReviewPrompt
from app.prompts.skills import SkillPrompt


def test_resume_parser_prompt_mentions_normalization() -> None:
    prompt = ResumeParserPrompt().build()

    assert "Normalize" in prompt
    assert "resume text" in prompt


def test_ats_prompt_mentions_ats_score() -> None:
    prompt = AtsPrompt().build()

    assert "ATS" in prompt
    assert "0 to 100" in prompt


def test_skill_prompt_mentions_categories() -> None:
    prompt = SkillPrompt().build()

    assert "technical, soft, domain, tool, or other" in prompt


def test_keyword_prompt_mentions_ats_matching() -> None:
    prompt = KeywordPrompt().build()

    assert "ATS" in prompt
    assert "keywords" in prompt


def test_resume_review_prompt_mentions_recommendations() -> None:
    prompt = ResumeReviewPrompt().build()

    assert "strengths" in prompt
    assert "recommendations" in prompt
