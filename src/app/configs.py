from dataclasses import dataclass, field

import yaml

from path import BASE_PATH


@dataclass
class AppConfig:
    theme: str = "dark"
    data: dict = field(default_factory=dict)
    label: dict = field(default_factory=dict)
    shortcuts: dict = field(default_factory=dict)


class ConfigManager:
    _CONFIG_FILE = "config.yaml"

    def __init__(self):
        self._config_path = BASE_PATH / self._CONFIG_FILE

    def load(self) -> AppConfig:
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    window_data = data.get("window", {})
                    app_data = data.get("data", {})
                    app_label = data.get("label", {})
                    app_shortcuts = data.get("shortcuts", {})
                    return AppConfig(
                        theme=window_data.get("theme", "dark"),
                        data=app_data,
                        label=app_label,
                        shortcuts=app_shortcuts,
                    )
        except (FileNotFoundError, yaml.YAMLError):
            pass
        return AppConfig()

    def save(self, config: AppConfig):
        data = {
            "window": {"theme": config.theme},
            "data": config.data,
            "label": config.label,
            "shortcuts": config.shortcuts,
        }
        with open(self._config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
