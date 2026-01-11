"""Markdown resume generator."""

from app.models.resume import TailoredResume, ResumeData
from app.models.analysis import ChangeReport


def generate_resume_markdown(resume: TailoredResume | ResumeData) -> str:
    """
    Generate a Markdown formatted resume.

    Args:
        resume: Resume data to format

    Returns:
        Markdown string
    """
    lines = []

    # Header
    lines.append(f"# {resume.contact.name}")
    lines.append("")

    # Contact info
    contact_parts = []
    if resume.contact.email:
        contact_parts.append(resume.contact.email)
    if resume.contact.phone:
        contact_parts.append(resume.contact.phone)
    if resume.contact.location:
        contact_parts.append(resume.contact.location)
    if resume.contact.linkedin:
        contact_parts.append(f"[LinkedIn]({resume.contact.linkedin})")
    if resume.contact.website:
        contact_parts.append(f"[Website]({resume.contact.website})")

    if contact_parts:
        lines.append(" | ".join(contact_parts))
        lines.append("")

    # Summary
    if resume.summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(resume.summary)
        lines.append("")

    # Skills
    if resume.skills:
        lines.append("## Skills")
        lines.append("")
        lines.append(", ".join(resume.skills))
        lines.append("")

    # Experience
    if resume.experiences:
        lines.append("## Experience")
        lines.append("")

        for exp in resume.experiences:
            date_range = f"{exp.start_date} - {exp.end_date or 'Present'}"
            lines.append(f"### {exp.title}")
            lines.append(f"**{exp.company}** | {date_range}")
            if exp.location:
                lines.append(f"*{exp.location}*")
            lines.append("")

            for bullet in exp.bullets:
                lines.append(f"- {bullet}")
            lines.append("")

    # Education
    if resume.education:
        lines.append("## Education")
        lines.append("")

        for edu in resume.education:
            lines.append(f"### {edu.degree}")
            degree_line = f"**{edu.institution}**"
            if edu.graduation_date:
                degree_line += f" | {edu.graduation_date}"
            lines.append(degree_line)

            if edu.field:
                lines.append(f"*{edu.field}*")
            if edu.gpa:
                lines.append(f"GPA: {edu.gpa}")
            if edu.honors:
                lines.append(f"*{edu.honors}*")
            lines.append("")

    # Projects
    if resume.projects:
        lines.append("## Projects")
        lines.append("")

        for proj in resume.projects:
            lines.append(f"### {proj.name}")
            lines.append(proj.description)
            if proj.technologies:
                lines.append(f"*Technologies: {', '.join(proj.technologies)}*")
            if proj.url:
                lines.append(f"[View Project]({proj.url})")
            lines.append("")

    # Certifications
    if resume.certifications:
        lines.append("## Certifications")
        lines.append("")
        for cert in resume.certifications:
            lines.append(f"- {cert}")
        lines.append("")

    return "\n".join(lines)


def generate_change_report_markdown(report: ChangeReport) -> str:
    """
    Generate a Markdown formatted change report.

    Args:
        report: Change report data

    Returns:
        Markdown string
    """
    lines = []

    lines.append("# Resume Tailoring Report")
    lines.append("")

    # Score improvement
    lines.append("## Match Score")
    lines.append("")
    lines.append(f"- **Original Score:** {report.original_match_score:.0f}%")
    lines.append(f"- **Improved Score:** {report.improved_match_score:.0f}%")
    improvement = report.improved_match_score - report.original_match_score
    lines.append(f"- **Improvement:** +{improvement:.0f}%")
    lines.append("")

    # Summary stats
    lines.append("## Changes Summary")
    lines.append("")
    lines.append(f"**Total Changes Made:** {report.total_changes}")
    lines.append("")

    if report.changes_by_section:
        lines.append("### Changes by Section")
        for section, count in report.changes_by_section.items():
            lines.append(f"- {section}: {count} changes")
        lines.append("")

    # Key improvements
    if report.key_improvements:
        lines.append("## Key Improvements")
        lines.append("")
        for improvement in report.key_improvements:
            lines.append(f"- {improvement}")
        lines.append("")

    # Verification status
    lines.append("## Verification Status")
    lines.append("")
    status_emoji = "✅" if report.verification.status.value == "approved" else "⚠️"
    lines.append(f"**Status:** {status_emoji} {report.verification.status.value.upper()}")
    lines.append("")

    if report.verification.issues:
        lines.append("### Issues Found")
        lines.append("")
        for issue in report.verification.issues:
            severity_emoji = "🔴" if issue.severity == "critical" else "🟡"
            lines.append(f"{severity_emoji} **{issue.location}**")
            lines.append(f"   - Issue: {issue.issue}")
            lines.append(f"   - Original: \"{issue.original_text}\"")
            lines.append(f"   - Modified: \"{issue.modified_text}\"")
            lines.append("")

    # Warnings
    if report.warnings:
        lines.append("### Warnings")
        lines.append("")
        for warning in report.warnings:
            lines.append(f"- ⚠️ {warning}")
        lines.append("")

    return "\n".join(lines)
