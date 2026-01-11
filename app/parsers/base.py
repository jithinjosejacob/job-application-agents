"""Base parser interface."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, file: BinaryIO) -> str:
        """
        Parse a document and extract text content.

        Args:
            file: Binary file object to parse

        Returns:
            Extracted text content as a string
        """
        pass

    @abstractmethod
    def supports(self, filename: str) -> bool:
        """
        Check if this parser supports the given file type.

        Args:
            filename: Name of the file to check

        Returns:
            True if this parser can handle the file
        """
        pass
