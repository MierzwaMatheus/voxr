import sys
from unittest.mock import MagicMock

# Stub pynput so tests run without X11
if "pynput" not in sys.modules:
    sys.modules["pynput"] = MagicMock()
    sys.modules["pynput.keyboard"] = MagicMock()

from voxr.enums import InputMode
from voxr.hotkey import HotkeyCallbacks, HotkeyListener
from voxr.models import Configuration


def make_config(hotkey: str = "<alt>+v") -> Configuration:
    return Configuration(
        hotkey=hotkey,
        input_mode=InputMode.TOGGLE,
        model_name="base",
        transcription_language="auto",
        max_recording_seconds=60,
        vad_enabled=True,
        pipeline_mode_enabled=False,
        autostart_enabled=False,
        interface_language="pt-BR",
        first_run_complete=True,
    )


class TestOnActivateCallback:
    def test_on_activate_is_called_when_hotkey_fires(self, mocker):
        on_activate = MagicMock()
        callbacks = HotkeyCallbacks(
            on_activate=on_activate,
            on_cancel=MagicMock(),
            on_ptt_start=MagicMock(),
            on_ptt_stop=MagicMock(),
        )
        config = make_config(hotkey="<alt>+v")
        mock_hotkeys_cls = mocker.patch("voxr.hotkey.keyboard.GlobalHotKeys")
        listener = HotkeyListener(config, callbacks)
        listener.start()

        # Grab the mapping passed to GlobalHotKeys and invoke the hotkey handler
        hotkeys_map = mock_hotkeys_cls.call_args[0][0]
        hotkeys_map["<alt>+v"]()

        on_activate.assert_called_once()

    def test_listener_starts_in_daemon_thread(self, mocker):
        callbacks = HotkeyCallbacks(
            on_activate=MagicMock(),
            on_cancel=MagicMock(),
            on_ptt_start=MagicMock(),
            on_ptt_stop=MagicMock(),
        )
        config = make_config()
        mock_hotkeys_cls = mocker.patch("voxr.hotkey.keyboard.GlobalHotKeys")
        mock_instance = mock_hotkeys_cls.return_value
        listener = HotkeyListener(config, callbacks)
        listener.start()

        assert mock_instance.daemon is True
        mock_instance.start.assert_called_once()


class TestLifecycleMethods:
    def _make_listener(self, mocker, hotkey: str = "<alt>+v"):
        callbacks = HotkeyCallbacks(
            on_activate=MagicMock(),
            on_cancel=MagicMock(),
            on_ptt_start=MagicMock(),
            on_ptt_stop=MagicMock(),
        )
        mock_cls = mocker.patch("voxr.hotkey.keyboard.GlobalHotKeys")
        listener = HotkeyListener(make_config(hotkey), callbacks)
        return listener, mock_cls.return_value

    def test_stop_joins_thread_after_stopping(self, mocker):
        listener, mock_instance = self._make_listener(mocker)
        listener.start()
        listener.stop()

        mock_instance.stop.assert_called_once()
        mock_instance.join.assert_called_once()

    def test_stop_before_start_does_nothing(self, mocker):
        listener, mock_instance = self._make_listener(mocker)
        listener.stop()  # must not raise

        mock_instance.stop.assert_not_called()
        mock_instance.join.assert_not_called()

    def test_update_hotkey_changes_configured_hotkey(self, mocker):
        listener, _ = self._make_listener(mocker, hotkey="<alt>+v")
        listener.update_hotkey("<ctrl>+shift+r")

        assert listener._config.hotkey == "<ctrl>+shift+r"
