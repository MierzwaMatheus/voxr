from dataclasses import dataclass
from typing import Callable

from pynput import keyboard

from voxr.models import Configuration


@dataclass
class HotkeyCallbacks:
    on_activate: Callable[[], None]
    on_cancel: Callable[[], None]
    on_ptt_start: Callable[[], None]
    on_ptt_stop: Callable[[], None]


class HotkeyListener:
    def __init__(self, config: Configuration, callbacks: HotkeyCallbacks) -> None:
        self._config = config
        self._callbacks = callbacks
        self._listener = None

    def start(self) -> None:
        hotkeys = {self._config.hotkey: self._callbacks.on_activate}
        self._listener = keyboard.GlobalHotKeys(hotkeys)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener.join()

    def update_hotkey(self, new_hotkey: str) -> None:
        self._config.hotkey = new_hotkey
