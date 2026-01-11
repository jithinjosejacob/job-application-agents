"""PDF document parser using pdfplumber."""

from typing import BinaryIO
import pdfplumber
from loguru import logger

from .base import BaseParser


class PDFParser(BaseParser):
    """Parser for PDF documents."""

    def supports(self, filename: str) -> bool:
        """Check if file is a PDF."""
        return filename.lower().endswith(".pdf")

    def parse(self, file: BinaryIO) -> str:
        """
        Extract text from a PDF file.

        Args:
            file: Binary file object containing PDF data

        Returns:
            Extracted text content
        """
        text_parts = []

        try:
            with pdfplumber.open(file) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    else:
                        logger.warning(f"No text extracted from page {page_num}")

        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise ValueError(f"Failed to parse PDF: {e}")

        if not text_parts:
            raise ValueError("No text content found in PDF")

        return "\n\n".join(text_parts)
