import sys
from unittest.mock import MagicMock

# Stub GTK/AppIndicator3 so tests run without a display
gi_mock = MagicMock()
sys.modules.setdefault("gi", gi_mock)
sys.modules.setdefault("gi.repository", gi_mock.repository)
sys.modules.setdefault("gi.repository.AppIndicator3", gi_mock.repository.AppIndicator3)
sys.modules.setdefault("gi.repository.Gtk", gi_mock.repository.Gtk)
sys.modules.setdefault("gi.repository.Notify", gi_mock.repository.Notify)

from voxr.enums import AppState
from voxr.tray import TrayIcon


def make_tray() -> TrayIcon:
    return TrayIcon(on_settings=MagicMock(), on_quit=MagicMock())


class TestTrayIconShowNotification:
    def test_show_notification_does_not_raise(self):
        tray = make_tray()
        tray.show_notification("Texto transcrito com sucesso")

    def test_show_notification_empty_message_does_not_raise(self):
        tray = make_tray()
        tray.show_notification("")

    def test_show_notification_records_last_message(self):
        tray = make_tray()
        tray.show_notification("gravação finalizada")
        assert tray._last_notification == "gravação finalizada"


class TestTrayIconSetState:
    def test_set_state_recording_marks_state_and_updates_indicator(self):
        tray = make_tray()
        tray.set_state(AppState.RECORDING)
        assert tray._state == AppState.RECORDING
        tray._indicator.set_status.assert_called()

    def test_set_state_idle_restores_state_and_updates_indicator(self):
        tray = make_tray()
        tray.set_state(AppState.RECORDING)
        tray.set_state(AppState.IDLE)
        assert tray._state == AppState.IDLE
        tray._indicator.set_status.assert_called()

    def test_set_state_error_marks_state_and_updates_indicator(self):
        tray = make_tray()
        tray.set_state(AppState.ERROR)
        assert tray._state == AppState.ERROR
        tray._indicator.set_status.assert_called()
