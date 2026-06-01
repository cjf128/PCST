import sys
from pathlib import Path


if getattr(sys, "frozen", False) or "__compiled__" in globals():
    BASE_PATH: Path = Path(sys.executable).parent
else:
    BASE_PATH: Path = Path(__file__).resolve().parent

ICONS_PATH: Path = BASE_PATH / "icons"
MODELS_PATH: Path = BASE_PATH / "models"
CACHE_PATH: Path = BASE_PATH / "data" / "cache"
LOGS_PATH: Path = BASE_PATH / "logs"
