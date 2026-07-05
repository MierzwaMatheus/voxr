from typing import Callable

from voxr.models import Configuration


class SettingsWindow:
    def __init__(
        self,
        config: Configuration,
        on_apply: Callable[[Configuration], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self._config = config
        self._on_apply = on_apply
        self._on_cancel = on_cancel
        self._window = None

    def show(self) -> None:
        pass

    def hide(self) -> None:
        pass

    def set_sensitive(self, enabled: bool) -> None:
        pass
