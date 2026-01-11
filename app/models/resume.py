"""Resume data models."""

from pydantic import BaseModel
from typing import Optional


class ContactInfo(BaseModel):
    """Contact information from resume."""

    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None


class Experience(BaseModel):
    """Work experience entry."""

    company: str
    title: str
    start_date: str
    end_date: Optional[str] = None  # None means "Present"
    location: Optional[str] = None
    bullets: list[str]
    original_text: str  # Preserve original for fact-checking


class Education(BaseModel):
    """Education entry."""

    institution: str
    degree: str
    field: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None


class Project(BaseModel):
    """Project entry."""

    name: str
    description: str
    technologies: list[str] = []
    url: Optional[str] = None


class ResumeData(BaseModel):
    """Structured resume data."""

    contact: ContactInfo
    summary: Optional[str] = None
    experiences: list[Experience] = []
    education: list[Education] = []
    skills: list[str] = []
    projects: list[Project] = []
    certifications: list[str] = []
    languages: list[str] = []
    raw_text: str  # Original full text for reference


class TailoredSection(BaseModel):
    """A section of the tailored resume."""

    section_name: str
    content: str
    changes_made: list[str] = []


class TailoredResume(BaseModel):
    """The tailored resume output."""

    contact: ContactInfo
    summary: Optional[str] = None
    experiences: list[Experience] = []
    education: list[Education] = []
    skills: list[str] = []
    projects: list[Project] = []
    certifications: list[str] = []
    changes: list["ResumeChange"] = []


class ResumeChange(BaseModel):
    """A single change made to the resume."""

    section: str
    original: str
    modified: str
    reason: str
