"""Job advertisement data models."""

from pydantic import BaseModel
from typing import Optional


class JobRequirements(BaseModel):
    """Extracted job requirements."""

    required_skills: list[str] = []
    preferred_skills: list[str] = []
    experience_years: Optional[int] = None
    experience_description: Optional[str] = None
    education_requirements: list[str] = []
    certifications: list[str] = []
    soft_skills: list[str] = []
    keywords: list[str] = []  # Important terms to include


class JobAd(BaseModel):
    """Structured job advertisement data."""

    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: str
    requirements: JobRequirements
    responsibilities: list[str] = []
    benefits: list[str] = []
    raw_text: str  # Original full text
