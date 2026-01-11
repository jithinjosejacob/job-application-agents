"""Skill matching agent."""

from anthropic import Anthropic

from .base import BaseAgent
from app.models.resume import ResumeData
from app.models.job_ad import JobAd
from app.models.analysis import SkillMatch, SkillMatchResult, MatchStrength


class SkillMatcherAgent(BaseAgent):
    """Agent for matching resume skills against job requirements."""

    @property
    def system_prompt(self) -> str:
        return """You are an expert at analyzing skill matches between resumes and job requirements.

You MUST:
- Identify direct matches between resume skills and job requirements
- Recognize transferable/related skills that demonstrate capability
- Provide specific evidence from the resume for each match
- Calculate an accurate match score based on coverage of requirements

Be thorough but honest - only claim matches where there is real evidence."""

    def match(self, resume: ResumeData, job: JobAd) -> SkillMatchResult:
        """
        Match resume skills against job requirements.

        Args:
            resume: Parsed resume data
            job: Analyzed job posting

        Returns:
            Skill matching analysis
        """
        # Build resume context
        resume_skills = ", ".join(resume.skills)
        resume_experiences = "\n".join(
            f"- {exp.title} at {exp.company}: {'; '.join(exp.bullets[:3])}"
            for exp in resume.experiences[:5]
        )

        # Build job requirements context
        required = ", ".join(job.requirements.required_skills)
        preferred = ", ".join(job.requirements.preferred_skills)
        keywords = ", ".join(job.requirements.keywords)

        prompt = f"""Analyze how well this resume matches the job requirements.

<resume_skills>
{resume_skills}
</resume_skills>

<resume_experience>
{resume_experiences}
</resume_experience>

<job_required_skills>
{required}
</job_required_skills>

<job_preferred_skills>
{preferred}
</job_preferred_skills>

<job_keywords>
{keywords}
</job_keywords>

Analyze the match and return JSON:
{{
    "matched_skills": [
        {{
            "skill": "Skill name from job requirements",
            "strength": "strong" or "partial",
            "resume_evidence": ["Specific quotes/references from resume showing this skill"],
            "suggestion": "How to better highlight this skill"
        }}
    ],
    "missing_skills": [
        {{
            "skill": "Required skill not found in resume",
            "strength": "missing",
            "resume_evidence": [],
            "suggestion": "Note if there's any related experience that could partially address this"
        }}
    ],
    "transferable_skills": [
        {{
            "skill": "Resume skill that relates to a job requirement",
            "strength": "partial",
            "resume_evidence": ["Evidence of this skill"],
            "suggestion": "How to frame this as relevant"
        }}
    ],
    "match_score": 0-100,
    "summary": "Brief assessment of overall match quality and key strengths/gaps"
}}

INSTRUCTIONS:
- "strong" = direct match with clear evidence
- "partial" = related skill or indirect evidence
- "missing" = no evidence found
- match_score should reflect: (matched + 0.5*partial) / total_required * 100
- Be specific with resume_evidence - quote actual text
- Provide actionable suggestions for improvement

Respond with ONLY the JSON object."""

        response = self._call_claude(prompt)
        data = self._extract_json_from_response(response)

        # Build matched skills
        matched = []
        for m in data.get("matched_skills", []):
            matched.append(
                SkillMatch(
                    skill=m["skill"],
                    strength=MatchStrength.STRONG if m.get("strength") == "strong" else MatchStrength.PARTIAL,
                    resume_evidence=m.get("resume_evidence", []),
                    suggestion=m.get("suggestion", ""),
                )
            )

        # Build missing skills
        missing = []
        for m in data.get("missing_skills", []):
            missing.append(
                SkillMatch(
                    skill=m["skill"],
                    strength=MatchStrength.MISSING,
                    resume_evidence=[],
                    suggestion=m.get("suggestion", ""),
                )
            )

        # Build transferable skills
        transferable = []
        for m in data.get("transferable_skills", []):
            transferable.append(
                SkillMatch(
                    skill=m["skill"],
                    strength=MatchStrength.PARTIAL,
                    resume_evidence=m.get("resume_evidence", []),
                    suggestion=m.get("suggestion", ""),
                )
            )

        return SkillMatchResult(
            matched_skills=matched,
            missing_skills=missing,
            transferable_skills=transferable,
            match_score=float(data.get("match_score", 0)),
            summary=data.get("summary", ""),
        )
