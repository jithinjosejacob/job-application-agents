"""Analysis and matching data models."""

from pydantic import BaseModel
from enum import Enum


class MatchStrength(str, Enum):
    """Strength of a skill match."""

    STRONG = "strong"  # Direct match
    PARTIAL = "partial"  # Related/transferable
    MISSING = "missing"  # Not found in resume


class SkillMatch(BaseModel):
    """A single skill match result."""

    skill: str
    strength: MatchStrength
    resume_evidence: list[str] = []  # Where in resume this skill appears
    suggestion: str = ""  # How to highlight this skill


class SkillMatchResult(BaseModel):
    """Complete skill matching analysis."""

    matched_skills: list[SkillMatch] = []
    missing_skills: list[SkillMatch] = []
    transferable_skills: list[SkillMatch] = []
    match_score: float = 0.0  # 0-100 percentage
    summary: str = ""


class VerificationStatus(str, Enum):
    """Status of fact verification."""

    APPROVED = "approved"
    FLAGGED = "flagged"


class VerificationIssue(BaseModel):
    """A single verification issue."""

    location: str  # Section/bullet where issue found
    issue: str  # Description of the problem
    original_text: str
    modified_text: str
    severity: str  # "critical" or "warning"


class VerificationResult(BaseModel):
    """Result of fact-checking the tailored resume."""

    status: VerificationStatus
    issues: list[VerificationIssue] = []
    warnings: list[str] = []


class ChangeReport(BaseModel):
    """Complete change report for user review."""

    original_match_score: float
    improved_match_score: float
    total_changes: int
    changes_by_section: dict[str, int] = {}
    key_improvements: list[str] = []
    warnings: list[str] = []
    verification: VerificationResult
