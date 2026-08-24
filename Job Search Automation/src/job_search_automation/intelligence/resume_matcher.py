from __future__ import annotations

import json
from typing import Any

from job_search_automation.intelligence.matchers.career_progression import (
    CareerProgressionMatcher,
)
from job_search_automation.intelligence.matchers.experience_matcher import (
    ExperienceMatcher,
)
from job_search_automation.intelligence.matchers.location_matcher import (
    LocationMatcher,
)
from job_search_automation.intelligence.matchers.skill_matcher import (
    SkillMatcher,
)
from job_search_automation.intelligence.models import (
    ResumeMatchResult,
)
from job_search_automation.intelligence.scorers.company_scorer import (
    CompanyScorer,
)
from job_search_automation.intelligence.scorers.final_score_calculator import (
    FinalScoreCalculator,
)
from job_search_automation.intelligence.scorers.freshness_scorer import (
    FreshnessScorer,
)
from job_search_automation.models.job import Job
from job_search_automation.services import logger
from job_search_automation.services.gemini.client import (
    GeminiClient,
)


class ResumeMatcher:
    """
    Central deterministic intelligence engine.

    Responsibilities
    ----------------
    • Skill matching
    • Experience matching
    • Career progression scoring
    • Location scoring
    • Company scoring
    • Freshness scoring
    • Final weighted score calculation

    After deterministic scoring,
    Gemini enriches only the highest quality jobs.

    Deterministic scoring always remains the source of truth.
    """

    def __init__(self) -> None:
        self.skill_matcher = SkillMatcher()

        self.experience_matcher = (
            ExperienceMatcher()
        )

        self.location_matcher = (
            LocationMatcher()
        )

        self.career_matcher = (
            CareerProgressionMatcher()
        )

        self.company_scorer = (
            CompanyScorer()
        )

        self.freshness_scorer = (
            FreshnessScorer()
        )

        self.final_score = (
            FinalScoreCalculator()
        )

        self.gemini = GeminiClient()

    # ==========================================================
    # PUBLIC ENTRYPOINT
    # ==========================================================

    def match(
        self,
        job: Job,
    ) -> ResumeMatchResult:
        """
        Production-facing resume matching entrypoint.
        """

        return self.evaluate(job)

    def evaluate(
        self,
        job: Job,
    ) -> ResumeMatchResult:
        logger.info(
            "Evaluating job '%s' at '%s'.",
            job.title,
            job.company,
        )

        # ------------------------------------------------------
        # Deterministic evaluation
        # ------------------------------------------------------

        skill_result = self.skill_matcher.match(
            job.skills,
        )

        experience_result = (
            self.experience_matcher.match(
                job.description,
            )
        )

        location_result = (
            self.location_matcher.match(
                location=job.location,
                remote=job.remote,
                work_mode=job.work_mode,
            )
        )

        career_result = (
            self.career_matcher.match(
                job.title,
            )
        )

        company_result = (
            self.company_scorer.score(
                job.company,
            )
        )

        freshness_result = (
            self.freshness_scorer.score(
                job.posted_at,
            )
        )

        # ------------------------------------------------------
        # Final deterministic score
        # ------------------------------------------------------

        final_result = (
            self.final_score.calculate(
                skill_result,
                experience_result,
                career_result,
                location_result,
                company_result,
                freshness_result,
            )
        )

        # ------------------------------------------------------
        # Build deterministic result
        # ------------------------------------------------------

        resume_match = ResumeMatchResult(
            overall_score=final_result.overall_score,
            shortlist_bucket=final_result.shortlist_bucket,
            apply_priority=final_result.apply_priority,
            recommendation=final_result.recommendation,
            overall_explanation=final_result.explanation,
            skill_result=skill_result,
            experience_result=experience_result,
            career_result=career_result,
            location_result=location_result,
            company_result=company_result,
            freshness_result=freshness_result,
        )

        # ------------------------------------------------------
        # Persist deterministic results onto Job
        # ------------------------------------------------------

        job.matched_skills = (
            skill_result.matched_skills
        )

        job.missing_skills = (
            skill_result.missing_skills
        )

        job.company_tier = (
            company_result.company_tier
        )

        # Canonical deterministic score used by
        # downstream ranking and final selection.
        job.overall_score = (
            resume_match.overall_score
        )

        # Preserve the existing shortlist score field
        # for backward compatibility with downstream
        # consumers such as Google Sheets.
        job.shortlist_likelihood_score = (
            resume_match.overall_score
        )

        job.shortlist_bucket = (
            resume_match.shortlist_bucket
        )

        job.apply_priority = (
            resume_match.apply_priority
        )

        job.recommendation = (
            resume_match.recommendation
        )

        job.overall_explanation = (
            resume_match.overall_explanation
        )

        job.blunt_reason = (
            resume_match.overall_explanation
        )

        job.resume_match_result = (
            resume_match.model_dump()
        )

        # ------------------------------------------------------
        # AI enrichment
        # ------------------------------------------------------

        try:
            self._enrich_with_gemini(
                job=job,
                resume_match=resume_match,
            )

        except Exception:
            logger.exception(
                "Gemini enrichment failed for '%s' at '%s'.",
                job.title,
                job.company,
            )

        logger.info(
            "Finished evaluating '%s' (Score %.2f).",
            job.title,
            resume_match.overall_score,
        )

        self.enrich_job(
            job,
            resume_match,
        )

        return resume_match

    # ==========================================================
    # GEMINI ENRICHMENT
    # ==========================================================

    def _enrich_with_gemini(
        self,
        job: Job,
        resume_match: ResumeMatchResult,
    ) -> None:
        """
        Enrich an already scored job using Gemini.

        Gemini never changes the deterministic score.

        GeminiClient returns raw strings. Structured JSON
        responses are parsed and persisted onto Job.
        """

        if resume_match.overall_score < 60:
            logger.info(
                "Skipping Gemini enrichment for '%s' "
                "because score %.2f is below threshold.",
                job.title,
                resume_match.overall_score,
            )

            return

        logger.info(
            "Running Gemini enrichment for '%s'.",
            job.title,
        )

        # ------------------------------------------------------
        # Job analysis
        # ------------------------------------------------------

        try:
            analysis_prompt = self._build_analysis_prompt(
                job,
                resume_match,
            )

            analysis_text = self.gemini.analyze_job(
                analysis_prompt,
            )

            analysis = self._parse_json(
                analysis_text,
            )

            blunt_reason = analysis.get(
                "blunt_reason",
            )

            if isinstance(
                blunt_reason,
                str,
            ) and blunt_reason:
                job.blunt_reason = blunt_reason

            job_bucket = analysis.get(
                "job_bucket",
            )

            if isinstance(
                job_bucket,
                str,
            ) and job_bucket:
                job.job_bucket = job_bucket

        except Exception:
            logger.exception(
                "Gemini job analysis failed.",
            )

        # ------------------------------------------------------
        # Resume tailoring
        # ------------------------------------------------------

        try:
            resume_prompt = self._build_resume_prompt(
                job,
                resume_match,
            )

            resume_text = self.gemini.tailor_resume(
                resume_prompt,
            )

            resume_response = self._parse_json(
                resume_text,
            )

            tailored_reason = resume_response.get(
                "tailored_resume_reason",
            )

            if isinstance(
                tailored_reason,
                str,
            ):
                job.tailored_resume_reason = tailored_reason

            tailored_text = resume_response.get(
                "tailored_resume_text",
            )

            if isinstance(
                tailored_text,
                str,
            ):
                job.tailored_resume_text = tailored_text

        except Exception:
            logger.exception(
                "Resume tailoring failed.",
            )

        # ------------------------------------------------------
        # Cover letter
        # ------------------------------------------------------

        try:
            cover_letter_prompt = (
                self._build_cover_letter_prompt(
                    job,
                    resume_match,
                )
            )

            cover_letter = (
                self.gemini.generate_cover_letter(
                    cover_letter_prompt,
                )
            )

            job.cover_letter = cover_letter

        except Exception:
            logger.exception(
                "Cover letter generation failed.",
            )

        # ------------------------------------------------------
        # Interview questions
        # ------------------------------------------------------

        try:
            interview_prompt = (
                self._build_interview_prompt(
                    job,
                    resume_match,
                )
            )

            interview_text = (
                self.gemini.generate_interview_questions(
                    interview_prompt,
                )
            )

            interview_response = self._parse_json(
                interview_text,
            )

            questions = interview_response.get(
                "questions",
                [],
            )

            if isinstance(
                questions,
                list,
            ):
                job.interview_questions = [
                    question
                    for question in questions
                    if isinstance(question, str)
                ]

        except Exception:
            logger.exception(
                "Interview question generation failed.",
            )

        logger.info(
            "Gemini enrichment completed for '%s'.",
            job.title,
        )

    # ==========================================================
    # GEMINI PROMPTS
    # ==========================================================

    @staticmethod
    def _build_analysis_prompt(
        job: Job,
        result: ResumeMatchResult,
    ) -> str:
        return f"""
Analyze this job against the candidate's deterministic match result.

Job title:
{job.title}

Company:
{job.company}

Location:
{job.location}

Description:
{job.description}

Deterministic score:
{result.overall_score}

Shortlist bucket:
{result.shortlist_bucket}

Recommendation:
{result.recommendation}

Return ONLY valid JSON:

{{
    "blunt_reason": "concise explanation of the fit",
    "job_bucket": "best-fit job category"
}}
""".strip()

    @staticmethod
    def _build_resume_prompt(
        job: Job,
        result: ResumeMatchResult,
    ) -> str:
        return f"""
Tailor the candidate resume for this job.

Job title:
{job.title}

Company:
{job.company}

Location:
{job.location}

Job description:
{job.description}

Deterministic match score:
{result.overall_score}

Matched skills:
{", ".join(result.skill_result.matched_skills)}

Missing skills:
{", ".join(result.skill_result.missing_skills)}

Return ONLY valid JSON:

{{
    "tailored_resume_reason": "brief explanation of tailoring strategy",
    "tailored_resume_text": "tailored resume content"
}}
""".strip()

    @staticmethod
    def _build_cover_letter_prompt(
        job: Job,
        result: ResumeMatchResult,
    ) -> str:
        return f"""
Generate a concise professional cover letter for this job.

Job title:
{job.title}

Company:
{job.company}

Location:
{job.location}

Job description:
{job.description}

Deterministic match score:
{result.overall_score}

Matched skills:
{", ".join(result.skill_result.matched_skills)}

Return only the cover letter text.
""".strip()

    @staticmethod
    def _build_interview_prompt(
        job: Job,
        result: ResumeMatchResult,
    ) -> str:
        return f"""
Generate interview questions for this job.

Job title:
{job.title}

Company:
{job.company}

Job description:
{job.description}

Deterministic match score:
{result.overall_score}

Return ONLY valid JSON:

{{
    "questions": [
        "question 1",
        "question 2",
        "question 3"
    ]
}}
""".strip()

    # ==========================================================
    # JSON HELPER
    # ==========================================================

    @staticmethod
    def _parse_json(
        text: str,
    ) -> dict[str, Any]:
        """
        Safely parse a Gemini JSON response.

        If Gemini returns fenced JSON, remove the
        markdown fence before parsing.
        """

        cleaned = text.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        parsed = json.loads(cleaned)

        if not isinstance(parsed, dict):
            raise ValueError(
                "Gemini response must contain a JSON object.",
            )

        return parsed

    # ==========================================================
    # HELPER METHODS
    # ==========================================================

    def build_summary(
        self,
        result: ResumeMatchResult,
    ) -> str:
        """
        Creates a concise summary describing why the
        job received its deterministic score.
        """

        return (
            f"Overall Score: {result.overall_score:.2f} | "
            f"Bucket: {result.shortlist_bucket} | "
            f"Recommendation: {result.recommendation}"
        )

    def log_result(
        self,
        job: Job,
        result: ResumeMatchResult,
    ) -> None:
        """
        Writes a structured log entry useful during
        debugging and monitoring.
        """

        logger.info(
            "Job='%s' Company='%s' Score=%.2f "
            "Bucket='%s' Priority=%s",
            job.title,
            job.company,
            result.overall_score,
            result.shortlist_bucket,
            result.apply_priority,
        )

    def attach_metadata(
        self,
        job: Job,
        result: ResumeMatchResult,
    ) -> None:
        """
        Stores useful deterministic metadata inside Job.
        """

        metadata = {
            "skill_score": result.skill_result.score,
            "experience_score": result.experience_result.score,
            "career_score": result.career_result.score,
            "location_score": result.location_result.score,
            "company_score": result.company_result.score,
            "freshness_score": result.freshness_result.score,
            "overall_score": result.overall_score,
            "bucket": result.shortlist_bucket,
            "recommendation": result.recommendation,
        }

        if hasattr(
            job,
            "metadata",
        ):
            if job.metadata is None:
                job.metadata = {}

            job.metadata.update(metadata)

    def enrich_job(
        self,
        job: Job,
        result: ResumeMatchResult,
    ) -> None:
        """
        Final post-processing after deterministic evaluation
        and Gemini enrichment.
        """

        self.attach_metadata(
            job,
            result,
        )

        self.log_result(
            job,
            result,
        )