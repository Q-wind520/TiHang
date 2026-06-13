"""LLM Manager — orchestrates provider creation, caching, and API calls."""

from typing import Optional

from PySide6.QtCore import QObject, Signal

from .base_provider import LLMProvider
from .provider_registry import get_provider_class, list_providers
from .api_worker import ApiWorker
from models.settings_model import Settings


class LLMManager(QObject):
    """Central manager for LLM operations.

    Caches provider instances and spawns ApiWorkers for non-blocking calls.

    Signals:
        response_ready(str) — full response received.
        stream_chunk(str)   — a token chunk during streaming.
        response_error(str) — error message.
        stream_done()       — streaming completed.
    """

    response_ready = Signal(str)
    stream_chunk = Signal(str)
    response_error = Signal(str)
    stream_done = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._providers: dict[str, LLMProvider] = {}
        self._settings: Optional[Settings] = None
        self._active_worker: Optional[ApiWorker] = None

    def configure(self, settings: Settings) -> None:
        """Apply new settings and invalidate cached providers."""
        self._settings = settings
        self._providers.clear()

    def _get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """Get or create a cached provider instance."""
        if not self._settings:
            return None

        if provider_name in self._providers:
            return self._providers[provider_name]

        provider_config = self._settings.providers.get(provider_name)
        if not provider_config or not provider_config.enabled:
            return None

        try:
            cls = get_provider_class(provider_name)
            instance = cls()
            instance.configure(provider_config.to_dict())
            self._providers[provider_name] = instance
            return instance
        except ValueError:
            return None

    def send_message(
        self,
        messages: list[dict],
        provider_name: str = "",
        model: str = "",
        stream: bool = True,
    ) -> Optional[ApiWorker]:
        """Send a message to the LLM asynchronously.

        Returns the ApiWorker (already started) or None on failure.
        """
        if not provider_name and self._settings:
            provider_name = self._settings.active_provider

        provider = self._get_provider(provider_name)
        if not provider:
            self.response_error.emit(
                f"Provider '{provider_name}' is not configured or disabled."
            )
            return None

        if not model:
            provider_config = self._settings.providers.get(provider_name)
            if provider_config:
                model = provider_config.model

        worker = ApiWorker(provider, messages, stream=stream, model=model)
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)
        worker.chunk.connect(self._on_worker_chunk)
        self._active_worker = worker
        worker.start()
        return worker

    def cancel_current(self) -> None:
        """Cancel the currently running API call."""
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.cancel()

    def validate_api_key(self, provider_name: str) -> bool:
        """Synchronously test an API key. Call from a worker thread."""
        provider = self._get_provider(provider_name)
        if not provider:
            return False
        try:
            return provider.validate_api_key()
        except Exception:
            return False

    def get_available_providers(self) -> list[str]:
        """Return registered providers that have config entries."""
        return list_providers()

    def get_available_models(self, provider_name: str) -> list[str]:
        """Return models available for a provider."""
        provider = self._get_provider(provider_name)
        if provider:
            return provider.get_available_models()
        return []

    def _on_worker_finished(self, text: str) -> None:
        if text:
            self.response_ready.emit(text)
        self.stream_done.emit()

    def _on_worker_error(self, error_msg: str) -> None:
        self.response_error.emit(error_msg)

    def _on_worker_chunk(self, chunk_text: str) -> None:
        self.stream_chunk.emit(chunk_text)
