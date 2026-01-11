"""Job posting web scraper."""

import httpx
from bs4 import BeautifulSoup
from loguru import logger


class JobScraper:
    """Scraper for extracting job posting content from URLs."""

    # Common selectors for job content on popular job sites
    JOB_SELECTORS = [
        # LinkedIn
        ".description__text",
        ".show-more-less-html__markup",
        # Indeed
        "#jobDescriptionText",
        ".jobsearch-jobDescriptionText",
        # Greenhouse
        "#content",
        ".job-description",
        # Lever
        ".posting-page",
        ".content",
        # Workday
        ".job-posting",
        # Generic
        "[class*='job-description']",
        "[class*='jobDescription']",
        "[id*='job-description']",
        "article",
        "main",
    ]

    def __init__(self, timeout: int = 30):
        """
        Initialize the job scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def scrape(self, url: str) -> str:
        """
        Scrape job posting content from a URL.

        Args:
            url: URL of the job posting

        Returns:
            Extracted job posting text
        """
        logger.info(f"Scraping job posting from: {url}")

        async with httpx.AsyncClient(
            timeout=self.timeout, follow_redirects=True
        ) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching URL: {e}")
                raise ValueError(f"Failed to fetch job posting: {e}")

        return self._extract_content(response.text)

    def scrape_sync(self, url: str) -> str:
        """
        Synchronous version of scrape for use in Streamlit.

        Args:
            url: URL of the job posting

        Returns:
            Extracted job posting text
        """
        logger.info(f"Scraping job posting from: {url}")

        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching URL: {e}")
                raise ValueError(f"Failed to fetch job posting: {e}")

        return self._extract_content(response.text)

    def _extract_content(self, html: str) -> str:
        """
        Extract job content from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Extracted text content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()

        # Try specific job content selectors
        for selector in self.JOB_SELECTORS:
            elements = soup.select(selector)
            if elements:
                text = "\n\n".join(elem.get_text(separator="\n", strip=True) for elem in elements)
                if len(text) > 200:  # Reasonable job description length
                    logger.debug(f"Found content using selector: {selector}")
                    return self._clean_text(text)

        # Fall back to body content
        body = soup.find("body")
        if body:
            text = body.get_text(separator="\n", strip=True)
            return self._clean_text(text)

        raise ValueError("Could not extract job posting content from URL")

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line:
                lines.append(line)

        # Remove duplicate consecutive lines
        cleaned_lines = []
        prev_line = None
        for line in lines:
            if line != prev_line:
                cleaned_lines.append(line)
                prev_line = line

        return "\n".join(cleaned_lines)
