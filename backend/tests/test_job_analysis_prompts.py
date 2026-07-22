from __future__ import annotations

from app.prompts.job_match import JobMatchPrompt
from app.prompts.keyword_match import KeywordMatchPrompt
from app.prompts.missing_skills import MissingSkillsPrompt
from app.prompts.recommendations import JobRecommendationsPrompt


def test_job_match_prompt_mentions_scoring() -> None:
    prompt = JobMatchPrompt().build()

    assert "overall match percentage" in prompt
    assert "ATS match percentage" in prompt


def test_missing_skills_prompt_mentions_missing_capabilities() -> None:
    prompt = MissingSkillsPrompt().build()

    assert "missing" in prompt.lower()
    assert "skill" in prompt.lower()


def test_keyword_match_prompt_mentions_keywords() -> None:
    prompt = KeywordMatchPrompt().build()

    assert "keyword" in prompt.lower()
    assert "job description" in prompt


def test_job_recommendations_prompt_mentions_improvement() -> None:
    prompt = JobRecommendationsPrompt().build()

    assert "strengths" in prompt
    assert "recommendations" in prompt
