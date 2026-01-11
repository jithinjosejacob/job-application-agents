# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Job Application Agents - A project for building AI agents to assist with job application processes.

🎯 Goal

Given:

Resume (PDF / DOCX / text)

Job Ad (URL or text)

The agent will:

Extract required skills & keywords

Compare them against the resume

Rephrase and reorder content to highlight matching skills

Preserve facts (no hallucinated experience)

Output a tailored resume + a change report

## Development Guidelines

- Keep code modular and well-organized
- Write clear, descriptive variable and function names
- Add appropriate error handling for external API calls
- Follow security best practices, especially when handling personal data

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app/main.py

# Run tests
pytest tests/

# Type checking
mypy app/
```

## Project Structure

```
app/
├── main.py                 # Streamlit entry point
├── config/settings.py      # Configuration management
├── models/                 # Pydantic data models
│   ├── resume.py          # Resume data structures
│   ├── job_ad.py          # Job posting structures
│   └── analysis.py        # Analysis result structures
├── parsers/               # Document parsing
│   ├── pdf_parser.py      # PDF extraction
│   ├── docx_parser.py     # DOCX extraction
│   └── job_scraper.py     # Web scraping for job URLs
├── agents/                # LLM agents (Claude)
│   ├── base.py            # Base agent class
│   ├── job_analyzer.py    # Extract job requirements
│   ├── resume_parser.py   # Parse resume structure
│   ├── skill_matcher.py   # Match skills to requirements
│   ├── resume_tailor.py   # Optimize resume content
│   └── fact_checker.py    # Verify accuracy
├── generators/            # Output generation
│   ├── markdown.py        # Markdown formatting
│   └── pdf.py             # PDF generation
└── services/
    └── orchestrator.py    # Pipeline coordination
```

## Key Architecture

**5-Agent Pipeline:**
1. Job Analyzer → Extract skills/keywords from job posting
2. Resume Parser → Structure resume into sections
3. Skill Matcher → Compare resume vs requirements
4. Resume Tailor → Rephrase/reorder to highlight matches
5. Fact Checker → Verify no hallucinated content

## Environment Variables

Copy `.env.example` to `.env` and set:
- `ANTHROPIC_API_KEY` - Required for Claude API
- `CLAUDE_MODEL` - Model to use (default: claude-sonnet-4-20250514)