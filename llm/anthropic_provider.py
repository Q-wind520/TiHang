"""Anthropic provider implementation using the anthropic SDK."""

from typing import Generator

from .base_provider import LLMProvider


class AnthropicProvider(LLMProvider):
    """LLM provider backed by the Anthropic (Claude) API."""

    @property
    def provider_name(self) -> str:
        return "Anthropic"

    def validate_api_key(self) -> bool:
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self.config.get("api_key", ""))
            # A minimal API call to verify the key works
            client.messages.create(
                model=self.config.get("model", "claude-sonnet-4-20250514"),
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception:
            return False

    def _build_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """Extract system message (if any) and build the messages list.

        Anthropic requires system as a top-level parameter, not in messages.
        """
        system = ""
        chat_messages = []
        for m in messages:
            if m.get("role") == "system":
                system = m.get("content", "")
            else:
                chat_messages.append({"role": m["role"], "content": m["content"]})
        return system, chat_messages

    def chat(
        self, messages: list[dict], model: str = "", **kwargs
    ) -> str:
        from anthropic import Anthropic

        client = Anthropic(api_key=self.config.get("api_key", ""))

        model = model or self.config.get("model", "claude-sonnet-4-20250514")
        temperature = kwargs.get(
            "temperature", self.config.get("temperature", 0.7)
        )
        max_tokens = kwargs.get(
            "max_tokens", self.config.get("max_tokens", 4096)
        )

        system, chat_messages = self._build_messages(messages)

        kwargs_args = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": chat_messages,
        }
        if system:
            kwargs_args["system"] = system
        if temperature > 0:
            kwargs_args["temperature"] = temperature

        response = client.messages.create(**kwargs_args)
        # Anthropic returns content blocks; extract text
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    def stream_chat(
        self, messages: list[dict], model: str = "", **kwargs
    ) -> Generator[str, None, None]:
        from anthropic import Anthropic

        client = Anthropic(api_key=self.config.get("api_key", ""))

        model = model or self.config.get("model", "claude-sonnet-4-20250514")
        temperature = kwargs.get(
            "temperature", self.config.get("temperature", 0.7)
        )
        max_tokens = kwargs.get(
            "max_tokens", self.config.get("max_tokens", 4096)
        )

        system, chat_messages = self._build_messages(messages)

        kwargs_args = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": chat_messages,
        }
        if system:
            kwargs_args["system"] = system
        if temperature > 0:
            kwargs_args["temperature"] = temperature

        with client.messages.stream(**kwargs_args) as stream:
            for text in stream.text_stream:
                yield text

    def get_available_models(self) -> list[str]:
        return [
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-haiku-3-5-sonnet-20251001",
            "claude-fable-5",
        ]
