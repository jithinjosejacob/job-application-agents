"""Resume tailoring agent."""

from anthropic import Anthropic

from .base import BaseAgent
from app.models.resume import (
    ResumeData,
    TailoredResume,
    ResumeChange,
    Experience,
    ContactInfo,
)
from app.models.analysis import SkillMatchResult


class ResumeTailorAgent(BaseAgent):
    """Agent for tailoring resumes to job requirements while preserving facts."""

    @property
    def system_prompt(self) -> str:
        return """You are an expert resume writer who optimizes resumes for specific job applications.

CRITICAL CONSTRAINTS - YOU MUST FOLLOW THESE:
1. You may ONLY rephrase or reorder existing content
2. You may NOT add new experiences, skills, achievements, or facts
3. You may NOT change dates, job titles, company names, or metrics
4. You may NOT invent quantifiable results not in the original
5. Every modification must be traceable to original resume content

Your goal is to:
- Emphasize relevant skills by using similar terminology to the job posting
- Reorder bullet points to put most relevant ones first
- Rephrase descriptions to highlight applicable experience
- Adjust the summary to target the specific role

Always maintain complete factual accuracy."""

    def tailor(
        self,
        resume: ResumeData,
        skill_matches: SkillMatchResult,
        job_keywords: list[str],
    ) -> TailoredResume:
        """
        Tailor a resume based on skill matching analysis.

        Args:
            resume: Original parsed resume
            skill_matches: Results from skill matching
            job_keywords: Important keywords from job posting

        Returns:
            Tailored resume with change tracking
        """
        # Build context about what to emphasize
        matched_skills = [m.skill for m in skill_matches.matched_skills]
        suggestions = [
            f"- {m.skill}: {m.suggestion}"
            for m in skill_matches.matched_skills + skill_matches.transferable_skills
            if m.suggestion
        ]

        # Build experience section for prompt
        experiences_text = ""
        for i, exp in enumerate(resume.experiences):
            experiences_text += f"""
Experience {i + 1}:
Company: {exp.company}
Title: {exp.title}
Dates: {exp.start_date} - {exp.end_date or 'Present'}
Bullets:
{chr(10).join(f'  - {b}' for b in exp.bullets)}
"""

        prompt = f"""Tailor this resume for the target job.

<original_resume>
Name: {resume.contact.name}
Summary: {resume.summary or 'None'}

Skills: {', '.join(resume.skills)}

{experiences_text}

Education: {', '.join(f'{e.degree} from {e.institution}' for e in resume.education)}
</original_resume>

<matched_skills_to_emphasize>
{', '.join(matched_skills)}
</matched_skills_to_emphasize>

<job_keywords>
{', '.join(job_keywords)}
</job_keywords>

<optimization_suggestions>
{chr(10).join(suggestions)}
</optimization_suggestions>

Return a tailored resume as JSON:
{{
    "summary": "Optimized summary targeting the role (or null if no changes)",
    "experiences": [
        {{
            "company": "UNCHANGED - exact company name",
            "title": "UNCHANGED - exact job title",
            "start_date": "UNCHANGED",
            "end_date": "UNCHANGED or null",
            "location": "UNCHANGED or null",
            "bullets": [
                "Rephrased/reordered bullet points",
                "Using job-relevant keywords where applicable"
            ],
            "original_text": "Copy the original_text from input"
        }}
    ],
    "skills": ["Reordered to put most relevant first"],
    "changes": [
        {{
            "section": "summary|experience|skills",
            "original": "Exact original text",
            "modified": "New version",
            "reason": "Why this change helps match the job"
        }}
    ]
}}

CRITICAL RULES:
1. NEVER change company names, job titles, or dates
2. NEVER add achievements or metrics not in the original
3. NEVER add skills not demonstrated in the resume
4. Only rephrase to use relevant keywords where truthful
5. Reorder bullets to put most relevant experience first
6. Track ALL changes in the changes array

Respond with ONLY the JSON object."""

        response = self._call_claude(prompt, max_tokens=8192)
        data = self._extract_json_from_response(response)

        # Build tailored experiences
        tailored_experiences = []
        for i, exp_data in enumerate(data.get("experiences", [])):
            # Use original data for immutable fields
            original_exp = resume.experiences[i] if i < len(resume.experiences) else None

            tailored_experiences.append(
                Experience(
                    company=original_exp.company if original_exp else exp_data.get("company", ""),
                    title=original_exp.title if original_exp else exp_data.get("title", ""),
                    start_date=original_exp.start_date if original_exp else exp_data.get("start_date", ""),
                    end_date=original_exp.end_date if original_exp else exp_data.get("end_date"),
                    location=original_exp.location if original_exp else exp_data.get("location"),
                    bullets=exp_data.get("bullets", original_exp.bullets if original_exp else []),
                    original_text=original_exp.original_text if original_exp else "",
                )
            )

        # Build changes list
        changes = []
        for change_data in data.get("changes", []):
            changes.append(
                ResumeChange(
                    section=change_data.get("section", ""),
                    original=change_data.get("original", ""),
                    modified=change_data.get("modified", ""),
                    reason=change_data.get("reason", ""),
                )
            )

        return TailoredResume(
            contact=resume.contact,
            summary=data.get("summary") or resume.summary,
            experiences=tailored_experiences,
            education=resume.education,
            skills=data.get("skills", resume.skills),
            projects=resume.projects,
            certifications=resume.certifications,
            changes=changes,
        )
