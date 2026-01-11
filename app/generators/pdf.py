"""PDF generation using WeasyPrint."""

import io
from pathlib import Path

import markdown
from jinja2 import Template
from loguru import logger

from app.models.resume import TailoredResume, ResumeData

# WeasyPrint requires system libraries (pango, cairo, etc.)
# Make it optional so the app can run without PDF support
WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except OSError as e:
    logger.warning(f"WeasyPrint not available (missing system libraries): {e}")
except ImportError as e:
    logger.warning(f"WeasyPrint not installed: {e}")


# Default CSS for resume PDF
DEFAULT_CSS = """
@page {
    size: letter;
    margin: 0.5in;
}

body {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.4;
    color: #333;
}

h1 {
    font-size: 18pt;
    margin-bottom: 0.2em;
    color: #1a1a1a;
    border-bottom: 2px solid #333;
    padding-bottom: 0.1em;
}

h2 {
    font-size: 12pt;
    color: #444;
    margin-top: 1em;
    margin-bottom: 0.5em;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #ddd;
    padding-bottom: 0.2em;
}

h3 {
    font-size: 11pt;
    margin-bottom: 0.1em;
    margin-top: 0.5em;
}

p {
    margin: 0.3em 0;
}

.contact-info {
    font-size: 9pt;
    color: #666;
    margin-bottom: 0.5em;
}

.contact-info a {
    color: #0066cc;
    text-decoration: none;
}

.job-header {
    margin-bottom: 0.3em;
}

.job-title {
    font-weight: bold;
    font-size: 11pt;
}

.company-info {
    font-size: 10pt;
    color: #555;
}

.date-range {
    float: right;
    font-size: 9pt;
    color: #666;
}

ul {
    margin: 0.3em 0;
    padding-left: 1.5em;
}

li {
    margin-bottom: 0.2em;
}

.skills-list {
    font-size: 9pt;
}

.education-entry {
    margin-bottom: 0.5em;
}

.clearfix::after {
    content: "";
    clear: both;
    display: table;
}
"""


def is_pdf_available() -> bool:
    """Check if PDF generation is available."""
    return WEASYPRINT_AVAILABLE


def generate_pdf(resume: TailoredResume | ResumeData) -> bytes:
    """
    Generate a PDF from resume data.

    Args:
        resume: Resume data to convert to PDF

    Returns:
        PDF file as bytes

    Raises:
        ValueError: If WeasyPrint is not available or PDF generation fails
    """
    if not WEASYPRINT_AVAILABLE:
        raise ValueError(
            "PDF generation requires WeasyPrint with system libraries. "
            "Install with: brew install pango cairo gdk-pixbuf libffi"
        )

    html_content = _resume_to_html(resume)

    try:
        html = HTML(string=html_content)
        css = CSS(string=DEFAULT_CSS)

        pdf_buffer = io.BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[css])
        pdf_buffer.seek(0)

        return pdf_buffer.read()
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise ValueError(f"Failed to generate PDF: {e}")


def _resume_to_html(resume: TailoredResume | ResumeData) -> str:
    """
    Convert resume data to HTML.

    Args:
        resume: Resume data

    Returns:
        HTML string
    """
    template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ contact.name }} - Resume</title>
</head>
<body>
    <h1>{{ contact.name }}</h1>

    <div class="contact-info">
        {% if contact.email %}{{ contact.email }}{% endif %}
        {% if contact.phone %} | {{ contact.phone }}{% endif %}
        {% if contact.location %} | {{ contact.location }}{% endif %}
        {% if contact.linkedin %} | <a href="{{ contact.linkedin }}">LinkedIn</a>{% endif %}
        {% if contact.website %} | <a href="{{ contact.website }}">Website</a>{% endif %}
    </div>

    {% if summary %}
    <h2>Summary</h2>
    <p>{{ summary }}</p>
    {% endif %}

    {% if skills %}
    <h2>Skills</h2>
    <p class="skills-list">{{ skills | join(', ') }}</p>
    {% endif %}

    {% if experiences %}
    <h2>Experience</h2>
    {% for exp in experiences %}
    <div class="job-header clearfix">
        <span class="job-title">{{ exp.title }}</span>
        <span class="date-range">{{ exp.start_date }} - {{ exp.end_date or 'Present' }}</span>
    </div>
    <div class="company-info">{{ exp.company }}{% if exp.location %} | {{ exp.location }}{% endif %}</div>
    <ul>
    {% for bullet in exp.bullets %}
        <li>{{ bullet }}</li>
    {% endfor %}
    </ul>
    {% endfor %}
    {% endif %}

    {% if education %}
    <h2>Education</h2>
    {% for edu in education %}
    <div class="education-entry">
        <strong>{{ edu.degree }}</strong>{% if edu.field %} in {{ edu.field }}{% endif %}<br>
        {{ edu.institution }}{% if edu.graduation_date %} | {{ edu.graduation_date }}{% endif %}
        {% if edu.gpa %}<br>GPA: {{ edu.gpa }}{% endif %}
        {% if edu.honors %}<br><em>{{ edu.honors }}</em>{% endif %}
    </div>
    {% endfor %}
    {% endif %}

    {% if projects %}
    <h2>Projects</h2>
    {% for proj in projects %}
    <div>
        <strong>{{ proj.name }}</strong><br>
        {{ proj.description }}
        {% if proj.technologies %}<br><em>Technologies: {{ proj.technologies | join(', ') }}</em>{% endif %}
    </div>
    {% endfor %}
    {% endif %}

    {% if certifications %}
    <h2>Certifications</h2>
    <ul>
    {% for cert in certifications %}
        <li>{{ cert }}</li>
    {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
    """)

    return template.render(
        contact=resume.contact,
        summary=resume.summary,
        skills=resume.skills,
        experiences=resume.experiences,
        education=resume.education,
        projects=resume.projects,
        certifications=resume.certifications,
    )


def generate_pdf_from_markdown(md_content: str) -> bytes:
    """
    Generate PDF from Markdown content.

    Args:
        md_content: Markdown formatted text

    Returns:
        PDF file as bytes
    """
    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code"],
    )

    # Wrap in basic HTML structure
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Resume</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    try:
        html = HTML(string=full_html)
        css = CSS(string=DEFAULT_CSS)

        pdf_buffer = io.BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[css])
        pdf_buffer.seek(0)

        return pdf_buffer.read()
    except Exception as e:
        logger.error(f"Error generating PDF from markdown: {e}")
        raise ValueError(f"Failed to generate PDF: {e}")
