"""QThread worker for running LLM API calls off the main thread."""

from PySide6.QtCore import QThread, Signal

from .base_provider import LLMProvider


class ApiWorker(QThread):
    """Runs a single LLM API call in a background thread.

    Signals:
        finished(str) — emitted on successful completion (full response, or
                        empty string when streaming is complete).
        error(str)   — emitted on failure with the error message.
        chunk(str)   — emitted for each token during streaming.
    """

    finished = Signal(str)
    error = Signal(str)
    chunk = Signal(str)

    def __init__(
        self,
        provider: LLMProvider,
        messages: list[dict],
        stream: bool = False,
        model: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._provider = provider
        self._messages = messages
        self._stream = stream
        self._model = model
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation. The worker checks this between chunks."""
        self._cancelled = True

    def run(self) -> None:
        try:
            if self._stream:
                full_response = ""
                for chunk_text in self._provider.stream_chat(
                    self._messages, model=self._model
                ):
                    if self._cancelled:
                        break
                    full_response += chunk_text
                    self.chunk.emit(chunk_text)
                self.finished.emit(full_response)
            else:
                response = self._provider.chat(
                    self._messages, model=self._model
                )
                if not self._cancelled:
                    self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))
