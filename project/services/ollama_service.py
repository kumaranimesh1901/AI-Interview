"""Ollama LLM client with streaming, retries, model switching, and thinking-tag stripping."""

from __future__ import annotations

import json
import logging
import time
from typing import Generator, List, Optional

import httpx

from config.settings import settings
from utils.helpers import strip_thinking_tags

logger = logging.getLogger(__name__)


class OllamaService:
    """Client for Ollama HTTP API with retry logic and model management."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """
        Initialize Ollama service.

        Args:
            base_url: Ollama server URL.
            model: Default model name.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
        """
        self.base_url: str = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model: str = model or settings.OLLAMA_DEFAULT_MODEL
        self.timeout: int = timeout or settings.OLLAMA_TIMEOUT
        self.max_retries: int = max_retries or settings.OLLAMA_MAX_RETRIES
        self.retry_delay: float = settings.OLLAMA_RETRY_DELAY

    def set_model(self, model: str) -> None:
        """
        Switch the active model dynamically.

        Args:
            model: New model name string.
        """
        try:
            if model and model.strip():
                self.model = model.strip()
                logger.info("Ollama model switched to: %s", self.model)
        except Exception as exc:
            logger.exception("set_model failed: %s", exc)

    def list_models(self) -> List[str]:
        """
        Fetch available models from Ollama.

        Returns:
            List of model name strings, empty on failure.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return [m for m in models if m]
        except Exception as exc:
            logger.warning("list_models failed: %s", exc)
            return []

    def check_health(self) -> bool:
        """
        Return True if the Ollama server is reachable.

        Uses a short timeout to avoid blocking the UI.
        """
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as exc:
            logger.warning("Ollama health check failed: %s", exc)
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a complete non-streaming response.

        Automatically strips ``<think>`` tags from models like qwen3 that
        emit chain-of-thought reasoning blocks.

        Args:
            prompt: User prompt.
            system: Optional system message.
            model: Override model for this call.
            temperature: Sampling temperature.

        Returns:
            Generated text content with thinking tags removed.
        """
        model_name = model or self.model
        payload: dict = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/api/generate",
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    raw_text = data.get("response", "").strip()
                    # Strip thinking tags from qwen3 / reasoning models
                    return strip_thinking_tags(raw_text)
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning(
                    "Ollama timeout attempt %s/%s: %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Ollama generate attempt %s/%s failed: %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)

        raise RuntimeError(
            f"Ollama generate failed after {self.max_retries} attempts: {last_error}"
        )

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """
        Stream tokens from Ollama.

        Note: Thinking tags are NOT stripped during streaming since they arrive
        incrementally.  Callers that need clean output should buffer the full
        response and call ``strip_thinking_tags`` on the result.

        Args:
            prompt: User prompt.
            system: Optional system message.
            model: Override model.
            temperature: Sampling temperature.

        Yields:
            Text chunks as they arrive from the model.
        """
        model_name = model or self.model
        payload: dict = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    with client.stream(
                        "POST",
                        f"{self.base_url}/api/generate",
                        json=payload,
                    ) as response:
                        response.raise_for_status()
                        for line in response.iter_lines():
                            if not line:
                                continue
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done"):
                                return
                return
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Ollama stream attempt %s/%s failed: %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        raise RuntimeError(
            f"Ollama stream failed after {self.max_retries} attempts: {last_error}"
        )

    def chat(
        self,
        messages: List[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Chat completion API (non-streaming).

        Args:
            messages: List of role/content dicts.
            model: Optional model override.
            temperature: Sampling temperature.

        Returns:
            Assistant message content with thinking tags stripped.
        """
        model_name = model or self.model
        payload: dict = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    message = data.get("message", {})
                    raw_text = message.get("content", "").strip()
                    # Strip thinking tags from qwen3 / reasoning models
                    return strip_thinking_tags(raw_text)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Ollama chat attempt %s/%s failed: %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        raise RuntimeError(
            f"Ollama chat failed after {self.max_retries} attempts: {last_error}"
        )


# Singleton for app-wide use
ollama_service = OllamaService()
