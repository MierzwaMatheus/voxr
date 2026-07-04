from voxr.config import get_default
from voxr.enums import InputMode
from voxr.models import Configuration


def default_config() -> Configuration:
    return get_default()


def custom_hotkey_config(hotkey: str) -> Configuration:
    config = get_default()
    config.hotkey = hotkey
    return config


def ptt_config() -> Configuration:
    config = get_default()
    config.input_mode = InputMode.PTT
    return config
