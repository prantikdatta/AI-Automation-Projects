from __future__ import annotations

import json

from job_search_automation.models.job import Job


class GeminiPrompts:
    """
    Centralized prompt builder for every Gemini capability.

    Responsibilities
    ----------------
    • Build prompts only.
    • Never call Gemini.
    • Never parse responses.
    • Never contain retry logic.

    Every prompt instructs Gemini to return STRICT JSON.
    """

    # ==========================================================
    # SYSTEM PROMPT
    # ==========================================================

    SYSTEM_PROMPT = """
You are an elite Senior Technical Recruiter, Hiring Manager,
ATS Optimization Expert and Career Coach.

Your job is to objectively evaluate jobs against the candidate.

Never hallucinate.

Never invent skills.

Never fabricate company information.

Never assume missing information.

Only use information present in the Job object.

Always produce STRICT VALID JSON.

Never wrap JSON inside markdown.

Never output explanations outside JSON.
""".strip()

    # ==========================================================
    # JSON SCHEMA
    # ==========================================================

    OUTPUT_SCHEMA = """
{
    "analysis": {
        "shortlist_score": 0,
        "shortlist_bucket": "",
        "apply_priority": 0,
        "recommendation": "",
        "blunt_reason": "",
        "strengths": [],
        "concerns": [],
        "missing_skills": [
            {
                "skill": "",
                "importance": "",
                "recommendation": ""
            }
        ],
        "resume_improvements": [
            {
                "section": "",
                "issue": "",
                "suggestion": ""
            }
        ]
    },
    "tailoring": {
        "summary": "",
        "key_changes": [],
        "rewritten_bullets": [],
        "ats_keywords": []
    },
    "cover_letter": {
        "subject": "",
        "body": ""
    },
    "interview": {
        "questions": [
            {
                "question": "",
                "answer": ""
            }
        ]
    }
}
""".strip()

    # ==========================================================
    # JOB SERIALIZATION
    # ==========================================================

    @staticmethod
    def _serialize_job(job: Job) -> dict:

        return {

            "title": job.title,

            "company": job.company,

            "location": job.location,

            "description": job.description,

            "skills": job.skills,

            "employment_type": job.employment_type,

            "seniority": job.seniority,

            "salary_min": job.salary_min,

            "salary_max": job.salary_max,

            "company_tier": job.company_tier,

            "posted_at": (
                job.posted_at.isoformat()
                if job.posted_at
                else None
            ),

            "source": job.source,

            "provider": job.provider,
        }

    # ==========================================================
    # JOB ANALYSIS PROMPT
    # ==========================================================

    @classmethod
    def build_job_analysis_prompt(
        cls,
        job: Job,
    ) -> str:

        job_json = json.dumps(
            cls._serialize_job(job),
            indent=4,
            ensure_ascii=False,
        )

        return f"""
{cls.SYSTEM_PROMPT}

-------------------------------------------------------
TASK
-------------------------------------------------------

Evaluate this job posting.

Your evaluation should focus on:

1. Recruiter attractiveness

2. Resume fit

3. Career progression

4. Missing skills

5. Resume improvements

6. ATS optimization

7. Resume tailoring

8. Cover letter generation

9. Interview preparation

-------------------------------------------------------
JOB
-------------------------------------------------------

{job_json}

-------------------------------------------------------
OUTPUT FORMAT
-------------------------------------------------------

Return ONLY valid JSON.

Use EXACTLY this schema.

{cls.OUTPUT_SCHEMA}
""".strip()

    # ==========================================================
    # RESUME TAILORING PROMPT
    # ==========================================================

    @classmethod
    def build_resume_tailoring_prompt(
        cls,
        job: Job,
        resume_text: str,
    ) -> str:

        job_json = json.dumps(
            cls._serialize_job(job),
            indent=4,
            ensure_ascii=False,
        )

        return f"""
{cls.SYSTEM_PROMPT}

Tailor the following resume for this job.

Do NOT invent experience.

Do NOT fabricate projects.

Only rewrite wording.

-------------------------------------------------------
JOB
-------------------------------------------------------

{job_json}

-------------------------------------------------------
RESUME
-------------------------------------------------------

{resume_text}

-------------------------------------------------------
OUTPUT
-------------------------------------------------------

Return ONLY the "tailoring" object from the schema.
""".strip()

    # ==========================================================
    # COVER LETTER PROMPT
    # ==========================================================

    @classmethod
    def build_cover_letter_prompt(
        cls,
        job: Job,
        resume_text: str,
    ) -> str:

        job_json = json.dumps(
            cls._serialize_job(job),
            indent=4,
            ensure_ascii=False,
        )

        return f"""
{cls.SYSTEM_PROMPT}

Write a concise professional cover letter.

Never invent achievements.

Use only information supplied.

-------------------------------------------------------
JOB
-------------------------------------------------------

{job_json}

-------------------------------------------------------
RESUME
-------------------------------------------------------

{resume_text}

-------------------------------------------------------
OUTPUT
-------------------------------------------------------

Return ONLY the "cover_letter" object.
""".strip()

    # ==========================================================
    # INTERVIEW PREPARATION PROMPT
    # ==========================================================

    @classmethod
    def build_interview_prompt(
        cls,
        job: Job,
    ) -> str:

        job_json = json.dumps(
            cls._serialize_job(job),
            indent=4,
            ensure_ascii=False,
        )

        return f"""
{cls.SYSTEM_PROMPT}

Generate likely interview questions.

Include concise model answers.

-------------------------------------------------------
JOB
-------------------------------------------------------

{job_json}

-------------------------------------------------------
OUTPUT
-------------------------------------------------------

Return ONLY the "interview" object.
""".strip()