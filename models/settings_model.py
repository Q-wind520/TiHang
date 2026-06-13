from dataclasses import dataclass, field
from config.defaults import DEFAULT_SETTINGS


@dataclass
class ProviderConfig:
    name: str = ""
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    enabled: bool = True
    temperature: float = 0.7
    max_tokens: int = 4096

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "enabled": self.enabled,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderConfig":
        return cls(
            name=data.get("name", ""),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            model=data.get("model", ""),
            enabled=data.get("enabled", True),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
        )


@dataclass
class EditorConfig:
    font_family: str = "Consolas"
    font_size: int = 13
    tab_width: int = 4
    show_line_numbers: bool = True
    word_wrap: bool = False
    theme: str = "monokai"

    def to_dict(self) -> dict:
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "tab_width": self.tab_width,
            "show_line_numbers": self.show_line_numbers,
            "word_wrap": self.word_wrap,
            "theme": self.theme,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EditorConfig":
        return cls(
            font_family=data.get("font_family", "Consolas"),
            font_size=data.get("font_size", 13),
            tab_width=data.get("tab_width", 4),
            show_line_numbers=data.get("show_line_numbers", True),
            word_wrap=data.get("word_wrap", False),
            theme=data.get("theme", "monokai"),
        )


@dataclass
class AppConfig:
    language: str = "zh"
    data_dir: str = "./data"

    def to_dict(self) -> dict:
        return {"language": self.language, "data_dir": self.data_dir}

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        return cls(
            language=data.get("language", "zh"),
            data_dir=data.get("data_dir", "./data"),
        )


@dataclass
class Settings:
    active_provider: str = "openai"
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    editor: EditorConfig = field(default_factory=EditorConfig)
    app: AppConfig = field(default_factory=AppConfig)

    def get_active_provider_config(self) -> ProviderConfig:
        return self.providers.get(
            self.active_provider, ProviderConfig(name="OpenAI")
        )

    def to_dict(self) -> dict:
        return {
            "active_provider": self.active_provider,
            "providers": {k: v.to_dict() for k, v in self.providers.items()},
            "editor": self.editor.to_dict(),
            "app": self.app.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        providers = {}
        for key, val in data.get("providers", {}).items():
            providers[key] = ProviderConfig.from_dict(val)
        return cls(
            active_provider=data.get("active_provider", "openai"),
            providers=providers,
            editor=EditorConfig.from_dict(data.get("editor", {})),
            app=AppConfig.from_dict(data.get("app", {})),
        )

    @classmethod
    def defaults(cls) -> "Settings":
        return cls.from_dict(DEFAULT_SETTINGS)
