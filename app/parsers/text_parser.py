"""Plain text parser."""

from typing import BinaryIO

from .base import BaseParser


class TextParser(BaseParser):
    """Parser for plain text files."""

    def supports(self, filename: str) -> bool:
        """Check if file is a text file."""
        return filename.lower().endswith(".txt")

    def parse(self, file: BinaryIO) -> str:
        """
        Read text from a plain text file.

        Args:
            file: Binary file object containing text data

        Returns:
            Text content
        """
        content = file.read()

        # Try to decode as UTF-8, fall back to latin-1
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        if not text.strip():
            raise ValueError("No text content found in file")

        return text
