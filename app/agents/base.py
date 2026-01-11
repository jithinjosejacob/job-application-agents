"""Base agent class with Claude client."""

import json
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Type

from anthropic import Anthropic
from pydantic import BaseModel
from loguru import logger

from app.config.settings import get_settings

T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC):
    """Base class for all LLM agents."""

    def __init__(self, client: Anthropic | None = None):
        """
        Initialize the agent.

        Args:
            client: Anthropic client instance. If None, creates a new one.
        """
        settings = get_settings()
        self.client = client or Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for this agent."""
        pass

    def _call_claude(
        self,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0,
    ) -> str:
        """
        Make a call to Claude API.

        Args:
            user_message: The user message to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0 for deterministic)

        Returns:
            Claude's response text
        """
        logger.debug(f"Calling Claude with {len(user_message)} chars")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text

    def _parse_json_response(
        self, response: str, model_class: Type[T]
    ) -> T:
        """
        Parse a JSON response into a Pydantic model.

        Args:
            response: Raw response text from Claude
            model_class: Pydantic model class to parse into

        Returns:
            Parsed model instance
        """
        # Try to extract JSON from the response
        text = response.strip()

        # Handle markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()

        try:
            data = json.loads(text)
            return model_class.model_validate(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to validate model: {e}")
            raise ValueError(f"Failed to validate response data: {e}")

    def _extract_json_from_response(self, response: str) -> dict[str, Any]:
        """
        Extract JSON object from response text.

        Args:
            response: Raw response text

        Returns:
            Parsed JSON as dict
        """
        text = response.strip()

        # Handle markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()

        # Try to parse as-is first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object by brackets
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

        # Try fixing common issues: trailing commas, unescaped quotes
        import re
        # Remove trailing commas before ] or }
        fixed = re.sub(r',(\s*[}\]])', r'\1', text)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw text: {text[:500]}")
            raise
