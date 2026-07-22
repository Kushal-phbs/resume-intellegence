from __future__ import annotations

from app.prompts.cover_letter_builder import CoverLetterPrompt
from app.prompts.resume_rewrite import ResumeRewritePrompt
from app.prompts.tailoring_ats import TailoringAtsPrompt


def test_resume_rewrite_prompt_requires_json_only_output() -> None:
    prompt = ResumeRewritePrompt().build()

    assert "Return ONLY valid JSON" in prompt
    assert "Do not include markdown" in prompt


def test_cover_letter_prompt_mentions_required_sections() -> None:
    prompt = CoverLetterPrompt().build()

    assert "greeting" in prompt
    assert "introduction" in prompt
    assert "closing" in prompt


def test_tailoring_ats_prompt_mentions_keywords_and_optimization() -> None:
    prompt = TailoringAtsPrompt().build()

    assert "missing keywords" in prompt
    assert "optimization" in prompt
