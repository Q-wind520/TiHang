"""Default values for all application settings."""

DEFAULT_QUESTION_STATUS = "unanswered"

DEFAULT_SETTINGS = {
    "active_provider": "openai",
    "providers": {
        "openai": {
            "name": "OpenAI",
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o",
            "enabled": True,
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "anthropic": {
            "name": "Anthropic",
            "api_key": "",
            "base_url": "https://api.anthropic.com",
            "model": "claude-sonnet-4-20250514",
            "enabled": True,
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "deepseek": {
            "name": "DeepSeek",
            "api_key": "",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-v4-flash",
            "enabled": True,
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    },
    "editor": {
        "font_family": "Consolas",
        "font_size": 13,
        "tab_width": 4,
        "show_line_numbers": True,
        "word_wrap": False,
        "theme": "monokai",
    },
    "app": {
        "language": "zh",
        "data_dir": "./data",
    },
}

# Mapping from Pygments theme name to background/text colors
PYGMENTS_THEMES = {
    "monokai": {"background": "#272822", "text": "#f8f8f2"},
    "github": {"background": "#ffffff", "text": "#24292e"},
    "dracula": {"background": "#282a36", "text": "#f8f8f2"},
    "one-dark": {"background": "#282c34", "text": "#abb2bf"},
    "solarized-light": {"background": "#fdf6e3", "text": "#657b83"},
    "solarized-dark": {"background": "#002b36", "text": "#839496"},
}
