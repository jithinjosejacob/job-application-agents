"""Job advertisement analysis agent."""

from anthropic import Anthropic

from .base import BaseAgent
from app.models.job_ad import JobAd, JobRequirements


class JobAnalyzerAgent(BaseAgent):
    """Agent for analyzing job postings and extracting requirements."""

    @property
    def system_prompt(self) -> str:
        return """You are an expert job posting analyzer. Your task is to extract
structured information from job postings.

You MUST:
- Only extract information explicitly stated in the job posting
- NOT infer or assume requirements that aren't mentioned
- Distinguish between required and preferred qualifications
- Identify key technical skills, soft skills, and industry keywords

Always respond with valid JSON matching the specified schema."""

    def analyze(self, job_text: str) -> JobAd:
        """
        Analyze a job posting and extract structured requirements.

        Args:
            job_text: Raw text of the job posting

        Returns:
            Structured JobAd with extracted requirements
        """
        prompt = f"""Analyze the following job posting and extract structured information.

<job_posting>
{job_text}
</job_posting>

Extract the following information and return as JSON:
{{
    "title": "Job title",
    "company": "Company name if mentioned, null otherwise",
    "location": "Location if mentioned, null otherwise",
    "description": "Brief summary of the role (1-2 sentences)",
    "requirements": {{
        "required_skills": ["List of explicitly required technical skills"],
        "preferred_skills": ["List of nice-to-have skills"],
        "experience_years": null or number of years required,
        "experience_description": "Description of experience needed",
        "education_requirements": ["Required degrees or certifications"],
        "certifications": ["Specific certifications mentioned"],
        "soft_skills": ["Communication, leadership, etc."],
        "keywords": ["Important industry terms and buzzwords to include"]
    }},
    "responsibilities": ["List of main job responsibilities"],
    "benefits": ["List of benefits if mentioned"],
    "raw_text": "Original job posting text"
}}

IMPORTANT:
- Only include skills/requirements EXPLICITLY mentioned in the posting
- Do NOT infer requirements that aren't stated
- Categorize accurately between required and preferred
- Include the full original text in raw_text

Respond with ONLY the JSON object, no additional text."""

        response = self._call_claude(prompt)

        # Parse and validate
        data = self._extract_json_from_response(response)

        # Ensure raw_text is preserved
        if "raw_text" not in data or not data["raw_text"]:
            data["raw_text"] = job_text

        # Parse requirements
        req_data = data.get("requirements", {})
        requirements = JobRequirements(
            required_skills=req_data.get("required_skills", []),
            preferred_skills=req_data.get("preferred_skills", []),
            experience_years=req_data.get("experience_years"),
            experience_description=req_data.get("experience_description"),
            education_requirements=req_data.get("education_requirements", []),
            certifications=req_data.get("certifications", []),
            soft_skills=req_data.get("soft_skills", []),
            keywords=req_data.get("keywords", []),
        )

        return JobAd(
            title=data.get("title", "Unknown Position"),
            company=data.get("company"),
            location=data.get("location"),
            description=data.get("description", ""),
            requirements=requirements,
            responsibilities=data.get("responsibilities", []),
            benefits=data.get("benefits", []),
            raw_text=data["raw_text"],
        )
