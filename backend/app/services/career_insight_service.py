"""Business logic for generating evidence-backed Career Insight data."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from app.core.exceptions import ExternalServiceException
from app.core.logging import logger
from app.dto.career import (
    CareerInsightResponse,
    CareerOverviewDTO,
    SkillChangeDTO,
    SkillChangesDTO,
)
from app.llm.models import LLMRequest
from app.llm.prompts.career_insight import SYSTEM_PROMPT, build_prompt
from app.parsers.career_insight_parser import CareerInsightParser
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.tailoring_session_repository import TailoringSessionRepository
from app.services.chat_service import ChatService

if TYPE_CHECKING:
    from app.dto.career import _LlmFields
    from app.models.resume_analysis import ResumeAnalysis


class CareerInsightService:
    """Generates evidence-backed Career Insight by comparing resume versions.

    Deterministic server-side logic computes skill changes (added/removed/
    mention-count changes). The LLM is asked to generate the narrative
    insights (experience_growth, career_fields, strengths, next_opportunities)
    based on the supplied evidence.
    """

    def __init__(
        self,
        resume_repository: ResumeRepository,
        resume_analysis_repository: ResumeAnalysisRepository,
        job_analysis_repository: JobAnalysisRepository,
        tailoring_session_repository: TailoringSessionRepository,
        chat_service: ChatService,
        parser: CareerInsightParser | None = None,
    ) -> None:
        self._resumes = resume_repository
        self._resume_analyses = resume_analysis_repository
        self._job_analyses = job_analysis_repository
        self._tailoring_sessions = tailoring_session_repository
        self._chat_service = chat_service
        self._parser = parser or CareerInsightParser()

    async def generate_insight(self, *, user_id: UUID) -> CareerInsightResponse:
        """Generate a full Career Insight for the given user.

        Args:
            user_id: The user's primary key.

        Returns:
            A validated CareerInsightResponse with deterministic skill changes
            merged with LLM-generated narrative insights.
        """
        # ── 1. Load all user data ────────────────────────────────────────
        resumes = await self._resumes.list_by_user(user_id)
        if not resumes:
            return CareerInsightResponse(
                overview=CareerOverviewDTO(total_resumes_analyzed=0),
                data_version_pairs=0,
            )

        resume_ids = [r.id for r in resumes]
        all_analyses = await self._resume_analyses.list_by_user(user_id)
        all_job_analyses = await self._job_analyses.list_by_user(user_id)
        all_tailoring = await self._tailoring_sessions.list_by_user(user_id)

        # ── 2. Group analyses by resume_id ──────────────────────────────
        analyses_by_resume: dict[UUID, list] = {}
        for a in all_analyses:
            analyses_by_resume.setdefault(a.resume_id, []).append(a)

        # ── 3. Load versions for each resume (via resume.get()) ──────────
        versions_by_resume: dict[UUID, list] = {}
        for r in resumes:
            full = await self._resumes.get(r.id)
            if full is not None:
                versions_by_resume[r.id] = list(full.versions)

        # ── 4. Compute deterministic skill changes ───────────────────────
        all_skill_changes = SkillChangesDTO()
        total_pairs = 0
        total_versions = 0
        latest_ats: int | None = None
        previous_ats: int | None = None
        longest_span_days: int | None = None
        all_analysis_timestamps: list[datetime] = []

        # Build a map of analysis_id -> version_number for cross-referencing
        analysis_version_map: dict[UUID, int] = {}
        version_analysis_map: dict[UUID, "ResumeAnalysis"] = {}

        for resume_id in resume_ids:
            versions = sorted(
                versions_by_resume.get(resume_id, []),
                key=lambda v: v.version_number,
            )
            analyses = sorted(
                analyses_by_resume.get(resume_id, []),
                key=lambda a: a.created_at or datetime.min.replace(tzinfo=timezone.utc),
            )
            if not versions:
                continue

            total_versions += len(versions)

            # Map each analysis to its version
            for a in analyses:
                version_analysis_map[a.resume_version_id] = a
                analysis_version_map[a.id] = a.resume_version_id

            # Track timestamps for span calculation
            for a in analyses:
                if a.created_at:
                    all_analysis_timestamps.append(a.created_at)

            # Compare adjacent version pairs
            for i in range(len(versions) - 1):
                v_old = versions[i]
                v_new = versions[i + 1]
                a_old = version_analysis_map.get(v_old.id)
                a_new = version_analysis_map.get(v_new.id)

                if a_old is None or a_new is None:
                    continue  # need both analyses to compare
                if (
                    a_old.analysis_status != "completed"
                    or a_new.analysis_status != "completed"
                ):
                    continue

                total_pairs += 1

                # Update ATS scores
                if a_new.ats_score is not None:
                    latest_ats = a_new.ats_score
                if a_old.ats_score is not None:
                    previous_ats = a_old.ats_score

                # Extract skill names from analyses
                old_skills = Counter(s.skill_name for s in (a_old.skills or []))
                new_skills = Counter(s.skill_name for s in (a_new.skills or []))

                old_names = set(old_skills.keys())
                new_names = set(new_skills.keys())

                # Added skills
                added_names = new_names - old_names
                added_skills = []
                for name in sorted(added_names):
                    snippet = _find_skill_snippet(name, v_new.content or "")
                    added_skills.append(
                        SkillChangeDTO(
                            skill_name=name,
                            category=_get_skill_category(name, a_new),
                            evidence_resume_version_id=str(v_new.id),
                            evidence_analysis_id=str(a_new.id),
                            previous_analysis_id=str(a_old.id),
                            previous_skill_count=0,
                            current_skill_count=new_skills[name],
                            source_snippet=snippet,
                        )
                    )
                all_skill_changes.added.extend(added_skills)

                # Removed skills
                removed_names = old_names - new_names
                removed_skills = []
                for name in sorted(removed_names):
                    removed_skills.append(
                        SkillChangeDTO(
                            skill_name=name,
                            category=_get_skill_category(name, a_old),
                            evidence_resume_version_id=str(v_new.id),
                            evidence_analysis_id=str(a_new.id),
                            previous_analysis_id=str(a_old.id),
                            previous_skill_count=old_skills[name],
                            current_skill_count=0,
                            source_snippet=None,
                        )
                    )
                all_skill_changes.removed.extend(removed_skills)

                # Strengthened skills (same name, higher count)
                common_names = old_names & new_names
                strengthened = []
                for name in sorted(common_names):
                    old_count = old_skills[name]
                    new_count = new_skills[name]
                    if new_count > old_count:
                        snippet = _find_skill_snippet(name, v_new.content or "")
                        strengthened.append(
                            SkillChangeDTO(
                                skill_name=name,
                                category=_get_skill_category(name, a_new),
                                evidence_resume_version_id=str(v_new.id),
                                evidence_analysis_id=str(a_new.id),
                                previous_analysis_id=str(a_old.id),
                                previous_skill_count=old_count,
                                current_skill_count=new_count,
                                source_snippet=snippet,
                            )
                        )
                all_skill_changes.strengthened.extend(strengthened)

        # Compute span
        if len(all_analysis_timestamps) >= 2:
            sorted_ts = sorted(all_analysis_timestamps)
            span = (sorted_ts[-1] - sorted_ts[0]).days
            longest_span_days = max(1, span)

        ats_delta = None
        if latest_ats is not None and previous_ats is not None:
            ats_delta = latest_ats - previous_ats

        # ── 5. Build LLM prompt ─────────────────────────────────────────
        skill_changes_text = _format_skill_changes(all_skill_changes)
        version_analyses_text = _format_version_analyses(version_analysis_map)
        job_analyses_text = _format_job_analyses(all_job_analyses)
        tailoring_text = _format_tailoring(all_tailoring)

        # Get the latest resume content excerpt
        resume_excerpt = ""
        for resume_id in resume_ids:
            versions = sorted(
                versions_by_resume.get(resume_id, []),
                key=lambda v: v.version_number,
                reverse=True,
            )
            if versions:
                content = versions[0].content or ""
                resume_excerpt = content[:2000]
                break

        prompt = build_prompt(
            total_resumes=len(resumes),
            total_versions=total_versions,
            total_pairs=total_pairs,
            longest_span_days=longest_span_days,
            latest_ats=latest_ats,
            previous_ats=previous_ats,
            ats_delta=ats_delta,
            skill_changes_text=skill_changes_text,
            version_analyses_text=version_analyses_text,
            job_analyses_text=job_analyses_text,
            tailoring_sessions_text=tailoring_text,
            resume_excerpt=resume_excerpt,
        )

        # ── 6. Call LLM ─────────────────────────────────────────────────
        if total_pairs == 0 and not all_job_analyses:
            # No comparison data at all; return deterministic-only response
            return CareerInsightResponse(
                overview=CareerOverviewDTO(
                    latest_ats_score=latest_ats,
                    previous_ats_score=previous_ats,
                    ats_delta=ats_delta,
                    total_resumes_analyzed=len(resumes),
                    total_versions_compared=total_versions,
                    longest_analysis_span_days=longest_span_days,
                ),
                skill_changes=all_skill_changes,
                data_version_pairs=total_pairs,
            )

        try:
            llm_response = await self._chat_service.chat(
                LLMRequest(
                    system_prompt=SYSTEM_PROMPT,
                    prompt=prompt,
                    temperature=0.3,
                    max_tokens=2048,
                )
            )
            llm_fields = self._parser.parse(llm_response.content)
        except ExternalServiceException:
            logger.warning(
                "Career Insight LLM call failed; returning deterministic-only response"
            )
            return CareerInsightResponse(
                overview=CareerOverviewDTO(
                    latest_ats_score=latest_ats,
                    previous_ats_score=previous_ats,
                    ats_delta=ats_delta,
                    total_resumes_analyzed=len(resumes),
                    total_versions_compared=total_versions,
                    longest_analysis_span_days=longest_span_days,
                ),
                skill_changes=all_skill_changes,
                data_version_pairs=total_pairs,
            )

        # ── 7. Validate LLM references ───────────────────────────────────
        known_version_ids = set()
        for vl in versions_by_resume.values():
            for v in vl:
                known_version_ids.add(str(v.id))
        known_analysis_ids = set()
        for a in all_analyses:
            known_analysis_ids.add(str(a.id))
        known_job_analysis_ids = set()
        for ja in all_job_analyses:
            known_job_analysis_ids.add(str(ja.id))
        known_tailoring_ids = set()
        for t in all_tailoring:
            known_tailoring_ids.add(str(t.id))

        llm_fields = _filter_unknown_references(
            llm_fields,
            known_version_ids=known_version_ids,
            known_analysis_ids=known_analysis_ids,
            known_job_analysis_ids=known_job_analysis_ids,
            known_tailoring_ids=known_tailoring_ids,
        )

        # ── 8. Merge deterministic + AI results ──────────────────────────
        return CareerInsightResponse(
            overview=CareerOverviewDTO(
                latest_ats_score=latest_ats,
                previous_ats_score=previous_ats,
                ats_delta=ats_delta,
                total_resumes_analyzed=len(resumes),
                total_versions_compared=total_versions,
                longest_analysis_span_days=longest_span_days,
            ),
            skill_changes=all_skill_changes,
            experience_growth=llm_fields.experience_growth,
            career_fields=llm_fields.career_fields,
            strengths=llm_fields.strengths,
            next_opportunities=llm_fields.next_opportunities,
            data_version_pairs=total_pairs,
        )


def _find_skill_snippet(
    skill_name: str, content: str, max_len: int = 200
) -> str | None:
    """Find a short excerpt in *content* that mentions *skill_name*."""
    if not content:
        return None
    lower = content.lower()
    idx = lower.find(skill_name.lower())
    if idx == -1:
        return None
    start = max(0, idx - 40)
    end = min(len(content), idx + len(skill_name) + 60)
    snippet = content[start:end].strip()
    if len(snippet) > max_len:
        snippet = snippet[:max_len] + "..."
    return snippet


def _get_skill_category(
    skill_name: str, analysis: "ResumeAnalysis | None"
) -> str | None:
    """Get the category for a skill from an analysis."""
    if analysis is None or not analysis.skills:
        return None
    for s in analysis.skills:
        if s.skill_name.lower() == skill_name.lower():
            return s.category
    return None


def _format_skill_changes(changes: SkillChangesDTO) -> str:
    """Format skill changes as a compact text block."""
    parts = []
    if changes.added:
        parts.append("### Added Skills")
        for s in changes.added:
            parts.append(
                f"- {s.skill_name} (cat={s.category}, count={s.current_skill_count}, "
                f"analysis={s.evidence_analysis_id})"
            )
    if changes.strengthened:
        parts.append("### Strengthened Skills")
        for s in changes.strengthened:
            parts.append(
                f"- {s.skill_name} (cat={s.category}, "
                f"{s.previous_skill_count}→{s.current_skill_count}, "
                f"analysis={s.evidence_analysis_id})"
            )
    if changes.removed:
        parts.append("### Removed Skills")
        for s in changes.removed:
            parts.append(
                f"- {s.skill_name} (cat={s.category}, "
                f"was count={s.previous_skill_count}, "
                f"analysis={s.previous_analysis_id})"
            )
    if not parts:
        return "No skill changes detected."
    return "\n".join(parts)


def _format_version_analyses(
    version_analysis_map: dict[UUID, "ResumeAnalysis"],
) -> str:
    """Format per-version analysis data as a compact text block."""
    parts = []
    for version_id, analysis in sorted(
        version_analysis_map.items(),
        key=lambda x: x[1].created_at or datetime.min.replace(tzinfo=timezone.utc),
    ):
        strengths = ", ".join(analysis.strengths or []) or "None"
        weaknesses = ", ".join(analysis.weaknesses or []) or "None"
        recommendations = ", ".join(analysis.recommendations or []) or "None"
        skills = ", ".join(s.skill_name for s in (analysis.skills or [])) or "None"
        parts.append(
            f"Version {version_id} (analysis_id={analysis.id}, "
            f"ats={analysis.ats_score}):\n"
            f"  Skills: [{skills}]\n"
            f"  Strengths: [{strengths}]\n"
            f"  Weaknesses: [{weaknesses}]\n"
            f"  Recommendations: [{recommendations}]"
        )
    if not parts:
        return "No analysis data available."
    return "\n\n".join(parts)


def _format_job_analyses(analyses: list) -> str:
    """Format job analysis data as a compact text block."""
    parts = []
    for ja in analyses:
        matched = ", ".join(s.skill_name for s in (ja.matched_skills or [])) or "None"
        missing = ", ".join(s.skill_name for s in (ja.missing_skills or [])) or "None"
        title = getattr(ja, "job_description", None)
        job_title = getattr(title, "title", "N/A") if title else "N/A"
        parts.append(
            f"Job '{job_title}' (id={ja.id}, "
            f"match={ja.match_score}, ats={ja.ats_match_score}):\n"
            f"  Matched skills: [{matched}]\n"
            f"  Missing skills: [{missing}]"
        )
    if not parts:
        return "No job analysis data available."
    return "\n\n".join(parts)


def _format_tailoring(sessions: list) -> str:
    """Format tailoring session data as a compact text block."""
    parts = []
    for s in sessions:
        job_title = getattr(s, "job_description", None)
        title = getattr(job_title, "title", "N/A") if job_title else "N/A"
        parts.append(
            f"Tailoring session (id={s.id}, job='{title}', resume={s.resume_id})"
        )
    if not parts:
        return "No tailoring sessions."
    return "\n".join(parts)


def _filter_unknown_references(
    fields: "_LlmFields",
    *,
    known_version_ids: set[str],
    known_analysis_ids: set[str],
    known_job_analysis_ids: set[str],
    known_tailoring_ids: set[str],
) -> "_LlmFields":
    """Remove claims that reference IDs not in the known sets.

    Returns a new _LlmFields instance with invalid references filtered out.
    The original instance is not modified (DTOs are frozen).
    """
    from app.dto.career import (
        CareerFieldDTO,
        NextOpportunityDTO,
        StrengthDTO,
        _LlmFields,
    )

    # Experience growth — rebuild with filtered list
    filtered_experience_growth = [
        eg
        for eg in fields.experience_growth
        if (
            eg.evidence_resume_version_id is None
            or eg.evidence_resume_version_id in known_version_ids
        )
        and (
            eg.evidence_analysis_id is None
            or eg.evidence_analysis_id in known_analysis_ids
        )
    ]

    # Career fields — rebuild each with filtered ID lists
    filtered_career_fields = []
    for cf in fields.career_fields:
        filtered_career_fields.append(
            CareerFieldDTO(
                field_name=cf.field_name,
                confidence=cf.confidence,
                evidence_summary=cf.evidence_summary,
                matching_skills=list(set(cf.matching_skills)),
                job_analysis_ids=[
                    jid for jid in cf.job_analysis_ids if jid in known_job_analysis_ids
                ],
                tailoring_session_ids=[
                    tid
                    for tid in cf.tailoring_session_ids
                    if tid in known_tailoring_ids
                ],
                resume_version_ids=[
                    rid for rid in cf.resume_version_ids if rid in known_version_ids
                ],
            )
        )

    # Strengths — rebuild each with filtered ID lists
    filtered_strengths = []
    for st in fields.strengths:
        filtered_strengths.append(
            StrengthDTO(
                title=st.title,
                description=st.description,
                evidence_analysis_ids=[
                    aid for aid in st.evidence_analysis_ids if aid in known_analysis_ids
                ],
                evidence_job_analysis_ids=[
                    jaid
                    for jaid in st.evidence_job_analysis_ids
                    if jaid in known_job_analysis_ids
                ],
                source_snippets=st.source_snippets,
            )
        )

    # Next opportunities — rebuild each with filtered ID lists
    filtered_next_ops = []
    for no in fields.next_opportunities:
        filtered_next_ops.append(
            NextOpportunityDTO(
                opportunity=no.opportunity,
                reason=no.reason,
                priority=no.priority,
                evidence_job_analysis_ids=[
                    jaid
                    for jaid in no.evidence_job_analysis_ids
                    if jaid in known_job_analysis_ids
                ],
                evidence_missing_skills=no.evidence_missing_skills,
                related_field=no.related_field,
            )
        )

    return _LlmFields(
        experience_growth=filtered_experience_growth,
        career_fields=filtered_career_fields,
        strengths=filtered_strengths,
        next_opportunities=filtered_next_ops,
    )
