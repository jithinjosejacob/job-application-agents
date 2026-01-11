"""Orchestrator service that coordinates the resume tailoring pipeline."""

from typing import Callable
from dataclasses import dataclass

from anthropic import Anthropic
from loguru import logger

from app.config.settings import get_settings
from app.models.resume import ResumeData, TailoredResume
from app.models.job_ad import JobAd
from app.models.analysis import SkillMatchResult, VerificationResult, ChangeReport
from app.agents.job_analyzer import JobAnalyzerAgent
from app.agents.resume_parser import ResumeParserAgent
from app.agents.skill_matcher import SkillMatcherAgent
from app.agents.resume_tailor import ResumeTailorAgent
from app.agents.fact_checker import FactCheckerAgent


@dataclass
class ProcessingResult:
    """Result of the resume tailoring process."""

    success: bool
    original_resume: ResumeData | None = None
    job_analysis: JobAd | None = None
    skill_matches: SkillMatchResult | None = None
    tailored_resume: TailoredResume | None = None
    verification: VerificationResult | None = None
    change_report: ChangeReport | None = None
    error: str | None = None


class ResumeOrchestrator:
    """Orchestrates the full resume tailoring pipeline."""

    def __init__(self, client: Anthropic | None = None):
        """
        Initialize the orchestrator with all agents.

        Args:
            client: Anthropic client. If None, creates a new one.
        """
        settings = get_settings()
        self.client = client or Anthropic(api_key=settings.anthropic_api_key)

        # Initialize all agents with shared client
        self.job_analyzer = JobAnalyzerAgent(self.client)
        self.resume_parser = ResumeParserAgent(self.client)
        self.skill_matcher = SkillMatcherAgent(self.client)
        self.tailor = ResumeTailorAgent(self.client)
        self.fact_checker = FactCheckerAgent(self.client)

    def process(
        self,
        resume_text: str,
        job_text: str,
        on_progress: Callable[[str, float], None] | None = None,
    ) -> ProcessingResult:
        """
        Run the full resume tailoring pipeline.

        Args:
            resume_text: Raw text extracted from resume
            job_text: Raw text of job posting
            on_progress: Optional callback for progress updates (message, percentage)

        Returns:
            ProcessingResult with tailored resume and analysis
        """

        def update_progress(message: str, pct: float):
            logger.info(f"[{pct:.0%}] {message}")
            if on_progress:
                on_progress(message, pct)

        try:
            # Step 1: Parse the resume
            update_progress("Parsing your resume...", 0.1)
            original_resume = self.resume_parser.parse(resume_text)
            logger.info(f"Parsed resume for: {original_resume.contact.name}")

            # Step 2: Analyze the job posting
            update_progress("Analyzing job requirements...", 0.25)
            job_analysis = self.job_analyzer.analyze(job_text)
            logger.info(f"Analyzed job: {job_analysis.title}")

            # Step 3: Match skills
            update_progress("Matching your skills to requirements...", 0.4)
            skill_matches = self.skill_matcher.match(original_resume, job_analysis)
            logger.info(f"Match score: {skill_matches.match_score:.0f}%")

            # Step 4: Tailor the resume
            update_progress("Tailoring your resume...", 0.6)
            job_keywords = (
                job_analysis.requirements.required_skills
                + job_analysis.requirements.keywords
            )
            tailored_resume = self.tailor.tailor(
                original_resume, skill_matches, job_keywords
            )
            logger.info(f"Made {len(tailored_resume.changes)} changes")

            # Step 5: Fact-check the result
            update_progress("Verifying accuracy...", 0.8)
            verification = self.fact_checker.verify(original_resume, tailored_resume)
            logger.info(f"Verification status: {verification.status.value}")

            # Step 6: Generate change report
            update_progress("Generating report...", 0.9)
            change_report = self._generate_change_report(
                skill_matches, tailored_resume, verification
            )

            update_progress("Complete!", 1.0)

            return ProcessingResult(
                success=True,
                original_resume=original_resume,
                job_analysis=job_analysis,
                skill_matches=skill_matches,
                tailored_resume=tailored_resume,
                verification=verification,
                change_report=change_report,
            )

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return ProcessingResult(
                success=False,
                error=str(e),
            )

    def _generate_change_report(
        self,
        skill_matches: SkillMatchResult,
        tailored: TailoredResume,
        verification: VerificationResult,
    ) -> ChangeReport:
        """
        Generate a comprehensive change report.

        Args:
            skill_matches: Skill matching results
            tailored: Tailored resume
            verification: Verification results

        Returns:
            ChangeReport with all changes documented
        """
        # Count changes by section
        changes_by_section: dict[str, int] = {}
        for change in tailored.changes:
            section = change.section
            changes_by_section[section] = changes_by_section.get(section, 0) + 1

        # Generate key improvements list
        key_improvements = []
        for match in skill_matches.matched_skills[:5]:
            if match.suggestion:
                key_improvements.append(
                    f"Highlighted {match.skill}: {match.suggestion}"
                )

        # Collect warnings
        warnings = verification.warnings.copy()
        for issue in verification.issues:
            if issue.severity == "warning":
                warnings.append(f"{issue.location}: {issue.issue}")

        # Estimate improved score (original + boost from changes)
        improvement_boost = min(len(tailored.changes) * 2, 15)  # Cap at 15%
        improved_score = min(
            skill_matches.match_score + improvement_boost, 100
        )

        return ChangeReport(
            original_match_score=skill_matches.match_score,
            improved_match_score=improved_score,
            total_changes=len(tailored.changes),
            changes_by_section=changes_by_section,
            key_improvements=key_improvements,
            warnings=warnings,
            verification=verification,
        )
