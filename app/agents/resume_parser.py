"""Resume parsing agent."""

from anthropic import Anthropic

from .base import BaseAgent
from app.models.resume import (
    ResumeData,
    ContactInfo,
    Experience,
    Education,
    Project,
)


class ResumeParserAgent(BaseAgent):
    """Agent for parsing resumes into structured data."""

    @property
    def system_prompt(self) -> str:
        return """You are an expert resume parser. Your task is to extract structured
information from resumes while preserving all original content exactly.

You MUST:
- Extract ALL information present in the resume
- Preserve exact wording, dates, numbers, and company names
- NOT modify, enhance, or interpret any content
- Maintain the original_text field with exact quotes from the resume

Always respond with valid JSON matching the specified schema."""

    def parse(self, resume_text: str) -> ResumeData:
        """
        Parse a resume into structured data.

        Args:
            resume_text: Raw text extracted from resume

        Returns:
            Structured ResumeData
        """
        prompt = f"""Parse the following resume and extract structured information.

<resume>
{resume_text}
</resume>

Extract and return as JSON:
{{
    "contact": {{
        "name": "Full name",
        "email": "Email address or null",
        "phone": "Phone number or null",
        "location": "City, State or null",
        "linkedin": "LinkedIn URL or null",
        "website": "Personal website or null"
    }},
    "summary": "Professional summary/objective if present, null otherwise",
    "experiences": [
        {{
            "company": "Company name",
            "title": "Job title",
            "start_date": "Start date as written",
            "end_date": "End date as written or null if current",
            "location": "Location if mentioned",
            "bullets": ["Exact bullet point 1", "Exact bullet point 2"],
            "original_text": "Complete original text for this experience entry"
        }}
    ],
    "education": [
        {{
            "institution": "School name",
            "degree": "Degree type",
            "field": "Field of study or null",
            "graduation_date": "Graduation date or null",
            "gpa": "GPA if mentioned or null",
            "honors": "Honors/awards if mentioned or null"
        }}
    ],
    "skills": ["List of all skills mentioned"],
    "projects": [
        {{
            "name": "Project name",
            "description": "Project description",
            "technologies": ["Tech used"],
            "url": "URL if provided"
        }}
    ],
    "certifications": ["List of certifications"],
    "languages": ["List of spoken languages"]
}}

CRITICAL INSTRUCTIONS:
- Preserve EXACT wording from the resume - do not paraphrase
- Keep all dates, numbers, and metrics exactly as written
- Include ALL bullet points exactly as written
- Do not add, remove, or modify any information
- Keep bullet points concise - summarize if longer than 200 characters
- Limit to 5 most recent/relevant experiences

Respond with ONLY valid JSON, no additional text or markdown."""

        response = self._call_claude(prompt, max_tokens=8192)

        # Parse response
        data = self._extract_json_from_response(response)

        # Ensure raw_text is preserved
        if "raw_text" not in data or not data["raw_text"]:
            data["raw_text"] = resume_text

        # Build contact info
        contact_data = data.get("contact", {})
        contact = ContactInfo(
            name=contact_data.get("name", "Unknown"),
            email=contact_data.get("email"),
            phone=contact_data.get("phone"),
            location=contact_data.get("location"),
            linkedin=contact_data.get("linkedin"),
            website=contact_data.get("website"),
        )

        # Build experiences
        experiences = []
        for exp_data in data.get("experiences", []):
            experiences.append(
                Experience(
                    company=exp_data.get("company", "Unknown"),
                    title=exp_data.get("title", "Unknown"),
                    start_date=exp_data.get("start_date", ""),
                    end_date=exp_data.get("end_date"),
                    location=exp_data.get("location"),
                    bullets=exp_data.get("bullets", []),
                    original_text=exp_data.get("original_text", ""),
                )
            )

        # Build education
        education = []
        for edu_data in data.get("education", []):
            education.append(
                Education(
                    institution=edu_data.get("institution", "Unknown"),
                    degree=edu_data.get("degree", ""),
                    field=edu_data.get("field"),
                    graduation_date=edu_data.get("graduation_date"),
                    gpa=edu_data.get("gpa"),
                    honors=edu_data.get("honors"),
                )
            )

        # Build projects
        projects = []
        for proj_data in data.get("projects", []):
            projects.append(
                Project(
                    name=proj_data.get("name", ""),
                    description=proj_data.get("description", ""),
                    technologies=proj_data.get("technologies", []),
                    url=proj_data.get("url"),
                )
            )

        return ResumeData(
            contact=contact,
            summary=data.get("summary"),
            experiences=experiences,
            education=education,
            skills=data.get("skills", []),
            projects=projects,
            certifications=data.get("certifications", []),
            languages=data.get("languages", []),
            raw_text=data["raw_text"],
        )
