"""Main Streamlit application for the Job Application Agent."""

import sys
from pathlib import Path

# Add project root to path for imports
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from io import BytesIO

from app.parsers.pdf_parser import PDFParser
from app.parsers.docx_parser import DOCXParser
from app.parsers.text_parser import TextParser
from app.parsers.job_scraper import JobScraper
from app.services.orchestrator import ResumeOrchestrator
from app.generators.markdown import (
    generate_resume_markdown,
    generate_change_report_markdown,
)
from app.generators.pdf import generate_pdf, is_pdf_available

# Page configuration
st.set_page_config(
    page_title="Resume Tailor AI",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 1
if "resume_text" not in st.session_state:
    st.session_state.resume_text = None
if "job_text" not in st.session_state:
    st.session_state.job_text = None
if "result" not in st.session_state:
    st.session_state.result = None
if "processing" not in st.session_state:
    st.session_state.processing = False


def parse_resume(uploaded_file) -> str:
    """Parse uploaded resume file."""
    filename = uploaded_file.name.lower()
    content = BytesIO(uploaded_file.read())

    if filename.endswith(".pdf"):
        parser = PDFParser()
    elif filename.endswith(".docx"):
        parser = DOCXParser()
    elif filename.endswith(".txt"):
        parser = TextParser()
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    return parser.parse(content)


def get_job_text(job_input: str, is_url: bool) -> str:
    """Get job posting text from URL or direct input."""
    if is_url:
        scraper = JobScraper()
        return scraper.scrape_sync(job_input)
    return job_input


def render_step_1():
    """Render the input step."""
    st.header("Step 1: Upload Your Resume and Job Posting")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Your Resume")
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF, DOCX, or TXT)",
            type=["pdf", "docx", "txt"],
            key="resume_upload",
        )

        if uploaded_file:
            try:
                resume_text = parse_resume(uploaded_file)
                st.session_state.resume_text = resume_text
                st.success(f"Resume parsed: {len(resume_text)} characters")

                with st.expander("Preview Resume Text"):
                    st.text(resume_text[:2000] + "..." if len(resume_text) > 2000 else resume_text)
            except Exception as e:
                st.error(f"Error parsing resume: {e}")

    with col2:
        st.subheader("Job Posting")

        input_type = st.radio(
            "How would you like to provide the job posting?",
            ["Paste Text", "Enter URL"],
            horizontal=True,
        )

        if input_type == "Enter URL":
            job_url = st.text_input(
                "Job Posting URL",
                placeholder="https://example.com/jobs/12345",
            )
            if job_url:
                try:
                    with st.spinner("Fetching job posting..."):
                        job_text = get_job_text(job_url, is_url=True)
                    st.session_state.job_text = job_text
                    st.success(f"Job posting fetched: {len(job_text)} characters")

                    with st.expander("Preview Job Posting"):
                        st.text(job_text[:2000] + "..." if len(job_text) > 2000 else job_text)
                except Exception as e:
                    st.error(f"Error fetching job posting: {e}")
        else:
            job_text = st.text_area(
                "Paste the job posting here",
                height=300,
                placeholder="Paste the full job description...",
            )
            if job_text:
                st.session_state.job_text = job_text

    # Process button
    st.markdown("---")

    can_process = (
        st.session_state.resume_text is not None
        and st.session_state.job_text is not None
        and len(st.session_state.job_text) > 50
    )

    if st.button(
        "Analyze and Tailor Resume",
        type="primary",
        disabled=not can_process,
        use_container_width=True,
    ):
        st.session_state.step = 2
        st.rerun()

    if not can_process:
        st.info("Please upload a resume and provide a job posting to continue.")


def render_step_2():
    """Render the processing step."""
    st.header("Step 2: Analyzing and Tailoring Your Resume")

    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(message: str, pct: float):
        progress_bar.progress(pct)
        status_text.text(message)

    try:
        orchestrator = ResumeOrchestrator()
        result = orchestrator.process(
            st.session_state.resume_text,
            st.session_state.job_text,
            on_progress=update_progress,
        )

        st.session_state.result = result

        if result.success:
            st.success("Resume tailoring complete!")
            st.session_state.step = 3
            st.rerun()
        else:
            st.error(f"Processing failed: {result.error}")
            if st.button("Go Back"):
                st.session_state.step = 1
                st.rerun()

    except Exception as e:
        st.error(f"An error occurred: {e}")
        if st.button("Go Back"):
            st.session_state.step = 1
            st.rerun()


def render_step_3():
    """Render the results step."""
    result = st.session_state.result

    if not result or not result.success:
        st.error("No results available.")
        if st.button("Start Over"):
            st.session_state.step = 1
            st.rerun()
        return

    st.header("Step 3: Your Tailored Resume")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Tailored Resume",
        "Skills Analysis",
        "Change Report",
        "Download",
    ])

    with tab1:
        st.subheader("Your Tailored Resume")

        # Verification status banner
        if result.verification:
            if result.verification.status.value == "approved":
                st.success("Verified: All changes preserve factual accuracy")
            else:
                st.warning(
                    "Some changes may need review. "
                    "Check the Change Report tab for details."
                )

        # Display tailored resume
        if result.tailored_resume:
            md_content = generate_resume_markdown(result.tailored_resume)
            st.markdown(md_content)

    with tab2:
        st.subheader("Skills Analysis")

        if result.skill_matches:
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Match Score",
                    f"{result.skill_matches.match_score:.0f}%",
                )

            with col2:
                matched = len(result.skill_matches.matched_skills)
                missing = len(result.skill_matches.missing_skills)
                st.metric(
                    "Skills Matched",
                    f"{matched}/{matched + missing}",
                )

            st.markdown("---")

            # Matched skills
            st.markdown("**Matched Skills**")
            for match in result.skill_matches.matched_skills:
                icon = "🟢" if match.strength.value == "strong" else "🟡"
                with st.expander(f"{icon} {match.skill}"):
                    st.write(f"**Evidence:** {', '.join(match.resume_evidence)}")
                    if match.suggestion:
                        st.write(f"**Suggestion:** {match.suggestion}")

            # Missing skills
            if result.skill_matches.missing_skills:
                st.markdown("**Missing Skills**")
                for match in result.skill_matches.missing_skills:
                    with st.expander(f"🔴 {match.skill}"):
                        if match.suggestion:
                            st.write(f"**Note:** {match.suggestion}")

            # Summary
            st.markdown("---")
            st.markdown("**Analysis Summary**")
            st.write(result.skill_matches.summary)

    with tab3:
        st.subheader("Change Report")

        if result.change_report:
            report_md = generate_change_report_markdown(result.change_report)
            st.markdown(report_md)

            # Individual changes
            st.markdown("---")
            st.markdown("### Detailed Changes")

            if result.tailored_resume and result.tailored_resume.changes:
                for i, change in enumerate(result.tailored_resume.changes, 1):
                    with st.expander(f"Change {i}: {change.section}"):
                        st.markdown("**Original:**")
                        st.text(change.original)
                        st.markdown("**Modified:**")
                        st.text(change.modified)
                        st.markdown(f"**Reason:** {change.reason}")
            else:
                st.info("No changes were made to the resume.")

    with tab4:
        st.subheader("Download Your Resume")

        if result.tailored_resume:
            col1, col2 = st.columns(2)

            with col1:
                # Markdown download
                md_content = generate_resume_markdown(result.tailored_resume)
                st.download_button(
                    "Download as Markdown",
                    data=md_content,
                    file_name="tailored_resume.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            with col2:
                # PDF download
                if is_pdf_available():
                    try:
                        pdf_bytes = generate_pdf(result.tailored_resume)
                        st.download_button(
                            "Download as PDF",
                            data=pdf_bytes,
                            file_name="tailored_resume.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"PDF generation failed: {e}")
                        st.info("Please download the Markdown version instead.")
                else:
                    st.warning("PDF generation not available")
                    st.caption(
                        "To enable PDF export, install system libraries:\n"
                        "`brew install pango cairo gdk-pixbuf libffi`"
                    )

            # Change report download
            st.markdown("---")
            if result.change_report:
                report_md = generate_change_report_markdown(result.change_report)
                st.download_button(
                    "Download Change Report",
                    data=report_md,
                    file_name="change_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

    # Start over button
    st.markdown("---")
    if st.button("Start Over", use_container_width=True):
        st.session_state.step = 1
        st.session_state.resume_text = None
        st.session_state.job_text = None
        st.session_state.result = None
        st.rerun()


def main():
    """Main application entry point."""
    # Sidebar
    with st.sidebar:
        st.title("Resume Tailor AI")
        st.markdown(
            """
            This tool helps you tailor your resume for specific job applications.

            **How it works:**
            1. Upload your resume
            2. Provide a job posting
            3. Get a tailored resume optimized for the role

            **Features:**
            - Extracts key requirements from job postings
            - Matches your skills to job requirements
            - Rephrases content to highlight relevant experience
            - Preserves all facts (no fabrication)
            - Provides a detailed change report
            """
        )

        st.markdown("---")

        # Progress indicator
        st.markdown("**Progress**")
        steps = ["Upload", "Process", "Results"]
        for i, step_name in enumerate(steps, 1):
            if i < st.session_state.step:
                st.markdown(f"~~{step_name}~~")
            elif i == st.session_state.step:
                st.markdown(f"**{i}. {step_name}**")
            else:
                st.markdown(f"{i}. {step_name}")

    # Main content based on current step
    if st.session_state.step == 1:
        render_step_1()
    elif st.session_state.step == 2:
        render_step_2()
    elif st.session_state.step == 3:
        render_step_3()


if __name__ == "__main__":
    main()
