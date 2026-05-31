"""Groq LLM client with streaming, retries, model switching, and rate-limit handling."""

from __future__ import annotations

import logging
import os
import time
from typing import Generator, List, Optional

from groq import Groq

from config.settings import settings
from utils.helpers import strip_thinking_tags

logger = logging.getLogger(__name__)


class LLMService:
    """Client for Groq API with retry logic and model management."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> None:
        """
        Initialize Groq LLM service.

        Args:
            api_key: Groq API key (defaults to env var).
            model: Default model name.
            max_retries: Maximum retry attempts.
            retry_delay: Base delay between retries in seconds.
        """
        self.api_key: str = api_key or settings.GROQ_API_KEY
        self.client: Groq = Groq(api_key=self.api_key)
        self.model: str = model or settings.GROQ_MODEL
        self.max_retries: int = max_retries
        self.retry_delay: float = retry_delay

    def set_model(self, model: str) -> None:
        """
        Switch the active model dynamically.

        Args:
            model: New model name string.
        """
        try:
            if model and model.strip():
                self.model = model.strip()
                logger.info("LLM model switched to: %s", self.model)
        except Exception as exc:
            logger.exception("set_model failed: %s", exc)

    def list_models(self) -> List[str]:
        """
        Return available Groq models.

        Returns:
            List of model name strings from settings.
        """
        return list(settings.AVAILABLE_MODELS)

    def check_health(self) -> bool:
        """
        Return True if the Groq API is reachable and configured.

        Uses a lightweight models.list() call to verify connectivity.
        """
        try:
            if not self.api_key:
                return False
            self.client.models.list()
            return True
        except Exception as exc:
            logger.warning("Groq health check failed: %s", exc)
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate a complete non-streaming response.

        Automatically strips ``<think>`` tags from models that
        emit chain-of-thought reasoning blocks.

        Args:
            prompt: User prompt.
            system: Optional system message.
            model: Override model for this call.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text content with thinking tags removed.
        """
        model_name = model or self.model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False,
                )
                raw_text = response.choices[0].message.content or ""
                # Strip thinking tags from reasoning models
                return strip_thinking_tags(raw_text.strip())
            except Exception as exc:
                last_error = exc
                error_str = str(exc).lower()
                if "rate_limit" in error_str or "429" in error_str:
                    wait_time = self.retry_delay * attempt * 2
                    logger.warning(
                        "Groq rate limit hit, attempt %s/%s. Waiting %.1fs",
                        attempt,
                        self.max_retries,
                        wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    logger.warning(
                        "Groq generate attempt %s/%s failed: %s",
                        attempt,
                        self.max_retries,
                        exc,
                    )
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * attempt)

        raise RuntimeError(
            f"Groq generate failed after {self.max_retries} attempts: {last_error}"
        )

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Generator[str, None, None]:
        """
        Stream tokens from Groq.

        Note: Thinking tags are NOT stripped during streaming since they arrive
        incrementally.  Callers that need clean output should buffer the full
        response and call ``strip_thinking_tags`` on the result.

        Args:
            prompt: User prompt.
            system: Optional system message.
            model: Override model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Yields:
            Text chunks as they arrive from the model.
        """
        model_name = model or self.model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                stream = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Groq stream attempt %s/%s failed: %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        raise RuntimeError(
            f"Groq stream failed after {self.max_retries} attempts: {last_error}"
        )

    def chat(
        self,
        messages: List[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Chat completion API (non-streaming).

        Args:
            messages: List of role/content dicts.
            model: Optional model override.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Assistant message content with thinking tags stripped.
        """
        model_name = model or self.model

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False,
                )
                raw_text = response.choices[0].message.content or ""
                # Strip thinking tags from reasoning models
                return strip_thinking_tags(raw_text.strip())
            except Exception as exc:
                last_error = exc
                error_str = str(exc).lower()
                if "rate_limit" in error_str or "429" in error_str:
                    wait_time = self.retry_delay * attempt * 2
                    logger.warning(
                        "Groq rate limit hit (chat), attempt %s/%s. Waiting %.1fs",
                        attempt,
                        self.max_retries,
                        wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    logger.warning(
                        "Groq chat attempt %s/%s failed: %s",
                        attempt,
                        self.max_retries,
                        exc,
                    )
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * attempt)

        raise RuntimeError(
            f"Groq chat failed after {self.max_retries} attempts: {last_error}"
        )


# Singleton for app-wide use
llm_service = LLMService()
