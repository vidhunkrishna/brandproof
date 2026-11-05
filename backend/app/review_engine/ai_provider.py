"""
AI Provider abstraction for BrandProof Review Engine (Lane 3).

Provides a decoupled interface for external LLM interactions with:
- Environment-based configuration (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL).
- Strict request timeouts and network failure handling.
- Deterministic fallback when the API key is missing or calls fail.
- Zero credential exposure to frontend or unauthorized layers.
"""
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger("brandproof.ai_provider")


class BaseAIProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_json(self, prompt: str, system_instruction: str) -> Optional[Dict[str, Any]]:
        """
        Send a prompt to the LLM and return a parsed JSON dictionary.
        Returns None if the provider is unavailable or if the request fails.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and ready for requests."""
        pass


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini REST API provider using standard HTTP requests.
    Supports Gemini 1.5 Flash / Pro via generateContent.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 8.0,
    ):
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if an API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    def generate_json(self, prompt: str, system_instruction: str) -> Optional[Dict[str, Any]]:
        """
        Send prompt to Gemini endpoint and parse JSON response.
        Falls back to None on any error or missing API key.
        """
        if not self.is_available():
            logger.info("AI Provider unavailable: missing or empty LLM_API_KEY. Using deterministic fallback.")
            return None

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # Extract text from response structure
                candidates = data.get("candidates", [])
                if not candidates:
                    logger.warning("Gemini returned response with no candidates.")
                    return None

                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts or "text" not in parts[0]:
                    logger.warning("Gemini returned candidate with no text parts.")
                    return None

                raw_text = parts[0]["text"].strip()
                # Strip markdown code fences if model enclosed JSON in ```json ... ```
                cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
                return json.loads(cleaned_text)

        except httpx.TimeoutException:
            logger.warning("AI Provider request timed out after %.1f seconds. Falling back.", self.timeout)
            return None
        except httpx.HTTPStatusError as e:
            logger.warning("AI Provider returned HTTP error status %s. Falling back.", e.response.status_code)
            return None
        except httpx.RequestError as e:
            logger.warning("AI Provider network failure: %s. Falling back.", str(e))
            return None
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("AI Provider returned malformed JSON: %s. Falling back.", str(e))
            return None
        except Exception as e:
            logger.warning("Unexpected error during AI generation: %s. Falling back.", str(e))
            return None


def get_ai_provider() -> BaseAIProvider:
    """Factory to retrieve configured AI provider."""
    return GeminiProvider()
