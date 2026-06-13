"""OpenAI provider implementation using the openai SDK."""

from typing import Generator

from .base_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """LLM provider backed by the OpenAI API."""

    @property
    def provider_name(self) -> str:
        return "OpenAI"

    def validate_api_key(self) -> bool:
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.config.get("api_key", ""),
                base_url=self.config.get("base_url", "https://api.openai.com/v1"),
            )
            client.models.list(limit=1)
            return True
        except Exception:
            return False

    def chat(
        self, messages: list[dict], model: str = "", **kwargs
    ) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=self.config.get("api_key", ""),
            base_url=self.config.get("base_url", "https://api.openai.com/v1"),
        )

        model = model or self.config.get("model", "gpt-4o")
        temperature = kwargs.get(
            "temperature", self.config.get("temperature", 0.7)
        )
        max_tokens = kwargs.get(
            "max_tokens", self.config.get("max_tokens", 4096)
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def stream_chat(
        self, messages: list[dict], model: str = "", **kwargs
    ) -> Generator[str, None, None]:
        from openai import OpenAI

        client = OpenAI(
            api_key=self.config.get("api_key", ""),
            base_url=self.config.get("base_url", "https://api.openai.com/v1"),
        )

        model = model or self.config.get("model", "gpt-4o")
        temperature = kwargs.get(
            "temperature", self.config.get("temperature", 0.7)
        )
        max_tokens = kwargs.get(
            "max_tokens", self.config.get("max_tokens", 4096)
        )

        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_available_models(self) -> list[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "o1",
            "o1-mini",
        ]
