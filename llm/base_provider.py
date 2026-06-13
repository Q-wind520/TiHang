"""Abstract base class for all LLM providers."""

from abc import ABC, abstractmethod
from typing import Generator


class LLMProvider(ABC):
    """Abstract interface every LLM backend must implement."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name, e.g. 'OpenAI', 'Anthropic'."""
        ...

    @abstractmethod
    def validate_api_key(self) -> bool:
        """Check whether the configured API key is valid.

        Returns True if the key works, False otherwise.
        """
        ...

    @abstractmethod
    def chat(
        self, messages: list[dict], model: str = "", **kwargs
    ) -> str:
        """Send a conversation and return the full response text.

        This is a BLOCKING call — must run in a background thread.
        """
        ...

    @abstractmethod
    def stream_chat(
        self, messages: list[dict], model: str = "", **kwargs
    ) -> Generator[str, None, None]:
        """Send a conversation and yield response tokens.

        This is a BLOCKING generator — must iterate in a background thread.
        """
        ...

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Return model identifiers available for this provider."""
        ...

    def configure(self, config: dict) -> None:
        """Apply a provider configuration dict (api_key, base_url, etc.)."""
        self._config = config

    @property
    def config(self) -> dict:
        return getattr(self, "_config", {})
