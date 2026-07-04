from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "voxr"
CACHE_DIR = Path.home() / ".cache" / "voxr" / "recordings"
MODEL_DIR = Path.home() / ".local" / "share" / "voxr" / "models"

PLACEHOLDER_TEXT = "[trecho não transcrito]"

DEFAULT_HOTKEY = "<alt>+v"
DEFAULT_MODEL = "medium"
DEFAULT_MAX_SECONDS = 60

ALLOWED_MODELS = ["tiny", "base", "small", "medium", "large-v3-turbo"]
