"""Provider registry — maps provider type strings to LLMProvider classes."""

from typing import Type

_provider_registry: dict[str, Type] = {}


def register_provider(name: str, provider_cls: Type) -> None:
    """Register a provider class under a unique name."""
    _provider_registry[name] = provider_cls


def get_provider_class(name: str) -> Type:
    """Look up a provider class by name. Raises ValueError if unknown."""
    if name not in _provider_registry:
        available = ", ".join(_provider_registry.keys())
        raise ValueError(
            f"Unknown provider '{name}'. Available: {available}"
        )
    return _provider_registry[name]


def list_providers() -> list[str]:
    """Return the names of all registered providers."""
    return list(_provider_registry.keys())
