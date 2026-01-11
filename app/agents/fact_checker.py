"""Fact checking agent to prevent hallucinations."""

from anthropic import Anthropic

from .base import BaseAgent
from app.models.resume import ResumeData, TailoredResume
from app.models.analysis import (
    VerificationResult,
    VerificationStatus,
    VerificationIssue,
)


class FactCheckerAgent(BaseAgent):
    """Agent for verifying tailored resume accuracy against original."""

    @property
    def system_prompt(self) -> str:
        return """You are a meticulous fact-checker for resumes. Your job is to ensure
that a tailored resume maintains complete factual accuracy compared to the original.

You MUST flag ANY instance where:
1. Dates have been changed
2. Job titles have been modified
3. Company names have been altered
4. New metrics or achievements were added
5. Skills were claimed that weren't in the original
6. Experiences or facts were fabricated

Be extremely thorough. Even small factual changes are critical issues.
Rephrasing is acceptable; adding new facts is NOT."""

    def verify(
        self,
        original: ResumeData,
        tailored: TailoredResume,
    ) -> VerificationResult:
        """
        Verify tailored resume against original for factual accuracy.

        Args:
            original: Original parsed resume
            tailored: Tailored resume to verify

        Returns:
            Verification result with any issues found
        """
        # Build original resume text for comparison
        original_text = self._build_resume_text(original)
        tailored_text = self._build_tailored_text(tailored)

        prompt = f"""Compare the tailored resume against the original and verify factual accuracy.

<original_resume>
{original_text}
</original_resume>

<tailored_resume>
{tailored_text}
</tailored_resume>

Check for these CRITICAL issues:
1. Changed dates (employment periods, graduation dates)
2. Modified job titles
3. Altered company names
4. Added metrics/numbers not in original (e.g., "increased sales by 50%" when no number was given)
5. New achievements or accomplishments not in original
6. Skills claimed that weren't demonstrated in original
7. New experiences or projects fabricated

Check for these WARNINGS:
1. Significant rephrasing that might change meaning
2. Removed important details from original
3. Claims that stretch the original meaning too far

Return JSON:
{{
    "status": "approved" or "flagged",
    "issues": [
        {{
            "location": "Section and specific item (e.g., 'Experience 1, bullet 2')",
            "issue": "Clear description of the factual problem",
            "original_text": "What was in the original",
            "modified_text": "What it became",
            "severity": "critical" or "warning"
        }}
    ],
    "warnings": ["List of non-critical concerns"]
}}

RULES:
- If ANY critical issues exist, status MUST be "flagged"
- Rephrasing is allowed if meaning is preserved
- Reordering content is allowed
- Using synonyms is allowed if accurate
- Adding ANY new quantifiable claims is CRITICAL
- Changing dates/titles/companies is CRITICAL

Respond with ONLY the JSON object."""

        response = self._call_claude(prompt)
        data = self._extract_json_from_response(response)

        # Build issues list
        issues = []
        for issue_data in data.get("issues", []):
            issues.append(
                VerificationIssue(
                    location=issue_data.get("location", ""),
                    issue=issue_data.get("issue", ""),
                    original_text=issue_data.get("original_text", ""),
                    modified_text=issue_data.get("modified_text", ""),
                    severity=issue_data.get("severity", "warning"),
                )
            )

        # Determine status
        has_critical = any(i.severity == "critical" for i in issues)
        status = VerificationStatus.FLAGGED if has_critical else VerificationStatus.APPROVED

        return VerificationResult(
            status=status,
            issues=issues,
            warnings=data.get("warnings", []),
        )

    def _build_resume_text(self, resume: ResumeData) -> str:
        """Build text representation of original resume."""
        parts = [f"Name: {resume.contact.name}"]

        if resume.summary:
            parts.append(f"\nSummary: {resume.summary}")

        parts.append(f"\nSkills: {', '.join(resume.skills)}")

        for i, exp in enumerate(resume.experiences, 1):
            parts.append(f"\nExperience {i}:")
            parts.append(f"  Company: {exp.company}")
            parts.append(f"  Title: {exp.title}")
            parts.append(f"  Dates: {exp.start_date} - {exp.end_date or 'Present'}")
            for bullet in exp.bullets:
                parts.append(f"  - {bullet}")

        for i, edu in enumerate(resume.education, 1):
            parts.append(f"\nEducation {i}:")
            parts.append(f"  {edu.degree} from {edu.institution}")
            if edu.graduation_date:
                parts.append(f"  Graduated: {edu.graduation_date}")

        return "\n".join(parts)

    def _build_tailored_text(self, resume: TailoredResume) -> str:
        """Build text representation of tailored resume."""
        parts = [f"Name: {resume.contact.name}"]

        if resume.summary:
            parts.append(f"\nSummary: {resume.summary}")

        parts.append(f"\nSkills: {', '.join(resume.skills)}")

        for i, exp in enumerate(resume.experiences, 1):
            parts.append(f"\nExperience {i}:")
            parts.append(f"  Company: {exp.company}")
            parts.append(f"  Title: {exp.title}")
            parts.append(f"  Dates: {exp.start_date} - {exp.end_date or 'Present'}")
            for bullet in exp.bullets:
                parts.append(f"  - {bullet}")

        for i, edu in enumerate(resume.education, 1):
            parts.append(f"\nEducation {i}:")
            parts.append(f"  {edu.degree} from {edu.institution}")
            if edu.graduation_date:
                parts.append(f"  Graduated: {edu.graduation_date}")

        return "\n".join(parts)
