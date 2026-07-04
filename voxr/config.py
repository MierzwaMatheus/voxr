import dataclasses
import json

from voxr.constants import (
    CONFIG_DIR,
    DEFAULT_HOTKEY,
    DEFAULT_MAX_SECONDS,
    DEFAULT_MODEL,
)
from voxr.enums import InputMode
from voxr.models import Configuration

CONFIG_FILE = CONFIG_DIR / "config.json"


def get_default() -> Configuration:
    return Configuration(
        hotkey=DEFAULT_HOTKEY,
        input_mode=InputMode.TOGGLE,
        model_name=DEFAULT_MODEL,
        transcription_language="auto",
        max_recording_seconds=DEFAULT_MAX_SECONDS,
        vad_enabled=True,
        pipeline_mode_enabled=False,
        autostart_enabled=False,
        interface_language="pt-BR",
        first_run_complete=False,
    )


def load() -> Configuration:
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        data["input_mode"] = InputMode(data.get("input_mode", "toggle"))
        return Configuration(**data)
    except Exception:
        config = get_default()
        _ensure_saved(config)
        return config


def save(config: Configuration) -> None:
    data = dataclasses.asdict(config)
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(CONFIG_FILE)


def _ensure_saved(config: Configuration) -> None:
    try:
        save(config)
    except Exception:
        pass
