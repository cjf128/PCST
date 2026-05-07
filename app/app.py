from app.configs import AppConfig, ConfigManager
from widgets.theme import ThemeManager
from widgets.MainWindow import MainWindow


class App:
    def __init__(self):
        self._config_manager = ConfigManager()
        self._config = self._config_manager.load()
        ThemeManager.set_theme(self._config.theme)
        self._main_window = MainWindow(self._config)

    @property
    def config(self) -> AppConfig:
        return self._config

    def run(self):
        self._main_window.show()

    def shutdown(self):
        self._config_manager.save(self._config)
