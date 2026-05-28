from pathlib import Path

# 当打包成可执行文件时，__file__ 会被设置为可执行文件的路径
# 但对于 Nuitka 打包，需要使用 sys.executable 或其他方法来确定路径
import sys

if getattr(sys, "frozen", False):
    # 如果是打包后的可执行文件
    BASE_PATH: Path = Path(sys.executable).parent
else:
    # 如果是直接运行的 Python 脚本
    BASE_PATH: Path = Path(__file__).resolve().parent

ICONS_PATH: Path = BASE_PATH / "icons"
MODELS_PATH: Path = BASE_PATH / "models"
CACHE_PATH: Path = BASE_PATH / "data" / "cache"
LOGS_PATH: Path = BASE_PATH / "logs"
