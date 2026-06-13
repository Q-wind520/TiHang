"""Store for application settings."""

from pathlib import Path
from models.settings_model import Settings
from .base_store import BaseStore


class SettingsStore(BaseStore):
    """Persists Settings model to settings.json."""

    def __init__(self, filepath: str | Path):
        default = Settings.defaults().to_dict()
        super().__init__(filepath, default)

    def load(self) -> Settings:
        data = self._read()
        if not data:
            return Settings.defaults()
        # Merge missing default providers into existing settings
        defaults = Settings.defaults()
        for key, cfg in defaults.providers.items():
            if key not in data.get("providers", {}):
                data.setdefault("providers", {})[key] = cfg.to_dict()
        return Settings.from_dict(data)

    def save(self, settings: Settings) -> None:
        self._write(settings.to_dict())
