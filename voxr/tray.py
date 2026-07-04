from typing import Callable

try:
    import gi
    gi.require_version("AppIndicator3", "0.1")
    gi.require_version("Gtk", "3.0")
    gi.require_version("Notify", "0.7")
    from gi.repository import AppIndicator3, Gtk, Notify
    _HAS_APP_INDICATOR = True
except Exception:
    _HAS_APP_INDICATOR = False

from voxr.enums import AppState

_ICON_MAP = {
    AppState.IDLE: "microphone-sensitivity-high-symbolic",
    AppState.RECORDING: "media-record-symbolic",
    AppState.PROCESSING: "emblem-synchronizing-symbolic",
    AppState.ERROR: "dialog-error-symbolic",
}

_STATUS_MAP = {
    AppState.IDLE: "PASSIVE",
    AppState.RECORDING: "ACTIVE",
    AppState.PROCESSING: "ATTENTION",
    AppState.ERROR: "ATTENTION",
}


class TrayIcon:
    def __init__(self, on_settings: Callable, on_quit: Callable) -> None:
        self._state = AppState.IDLE
        self._on_settings = on_settings
        self._on_quit = on_quit

        self._last_notification: str = ""
        if _HAS_APP_INDICATOR:
            self._indicator = AppIndicator3.Indicator.new(
                "voxr",
                _ICON_MAP[AppState.IDLE],
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )
            self._indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
            self._indicator.set_menu(self._build_menu())
            Notify.init("voxr")
        else:
            self._indicator = _FallbackIndicator()

    def set_state(self, state: AppState) -> None:
        self._state = state
        if _HAS_APP_INDICATOR:
            self._indicator.set_icon_full(_ICON_MAP[state], str(state.value))
            status = getattr(
                AppIndicator3.IndicatorStatus,
                _STATUS_MAP[state],
                AppIndicator3.IndicatorStatus.PASSIVE,
            )
            self._indicator.set_status(status)
        else:
            self._indicator.set_status(_STATUS_MAP[state])

    def show_notification(self, message: str) -> None:
        self._last_notification = message
        if _HAS_APP_INDICATOR:
            n = Notify.Notification.new("voxr", message, _ICON_MAP[self._state])
            n.show()
        else:
            self._indicator.show_notification(message)

    def _build_menu(self):
        menu = Gtk.Menu()
        item_settings = Gtk.MenuItem(label="Configurações")
        item_settings.connect("activate", lambda _: self._on_settings())
        menu.append(item_settings)
        menu.append(Gtk.SeparatorMenuItem())
        item_quit = Gtk.MenuItem(label="Sair")
        item_quit.connect("activate", lambda _: self._on_quit())
        menu.append(item_quit)
        menu.show_all()
        return menu


class _FallbackIndicator:
    """Minimal stub used when AppIndicator3 is unavailable (e.g. in tests)."""

    def __init__(self) -> None:
        self._status = "PASSIVE"

    def set_status(self, status: str) -> None:
        self._status = status

    def show_notification(self, message: str) -> None:
        pass
