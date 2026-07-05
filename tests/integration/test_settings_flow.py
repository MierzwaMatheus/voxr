import dataclasses
import sys
from unittest.mock import MagicMock

import pytest

# Stub hardware-dependent libs
for _mod in ("sounddevice", "soundfile", "faster_whisper"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Stub GTK
if "gi" not in sys.modules:
    _gi_mock = MagicMock()
    _gtk_mock = MagicMock()
    _gdk_mock = MagicMock()
    _glib_mock = MagicMock()
    _gi_mock.repository.Gtk = _gtk_mock
    _gi_mock.repository.Gdk = _gdk_mock
    _gi_mock.repository.GLib = _glib_mock
    sys.modules["gi"] = _gi_mock
    sys.modules["gi.repository"] = _gi_mock.repository
    sys.modules["gi.repository.Gtk"] = _gtk_mock
    sys.modules["gi.repository.Gdk"] = _gdk_mock
    sys.modules["gi.repository.GLib"] = _glib_mock

from voxr.app import VoxrApp  # noqa: E402
from voxr.enums import InputMode  # noqa: E402
from voxr.models import Configuration  # noqa: E402


@pytest.fixture
def cfg() -> Configuration:
    return Configuration(
        hotkey="<alt>+v",
        input_mode=InputMode.TOGGLE,
        model_name="medium",
        transcription_language="auto",
        max_recording_seconds=60,
        vad_enabled=False,
        pipeline_mode_enabled=False,
        autostart_enabled=False,
        interface_language="pt-BR",
        first_run_complete=True,
    )


def _make_app(cfg):
    app = VoxrApp(config=cfg)
    app._hotkey = MagicMock()
    app._model = MagicMock()
    return app


# T138: fluxo completo open_settings → alterar hotkey → apply_settings → update_hotkey chamado
def test_full_settings_flow_apply_hotkey(cfg, mocker):
    app = _make_app(cfg)
    mock_sw_class = mocker.patch("voxr.app.SettingsWindow")
    mock_sw = MagicMock()
    mock_sw_class.return_value = mock_sw
    mock_save = mocker.patch("voxr.app.config.save")

    # 1. Abrir settings
    app.open_settings()
    mock_sw_class.assert_called_once_with(
        config=cfg,
        on_apply=app.apply_settings,
        on_cancel=app._close_settings,
    )
    mock_sw.show.assert_called_once()

    # 2. Simular alteração de hotkey via apply_settings diretamente
    new_cfg = dataclasses.replace(cfg, hotkey="<ctrl>+<shift>+d")
    app.apply_settings(new_cfg)

    # 3. update_hotkey deve ter sido chamado com o novo hotkey
    app._hotkey.update_hotkey.assert_called_once_with("<ctrl>+<shift>+d")
    mock_save.assert_called_once_with(new_cfg)


def test_full_settings_flow_open_settings_stores_window(cfg, mocker):
    app = _make_app(cfg)
    mock_sw_class = mocker.patch("voxr.app.SettingsWindow")
    mock_sw = MagicMock()
    mock_sw_class.return_value = mock_sw

    app.open_settings()
    assert app._settings_window is mock_sw


def test_full_settings_flow_close_settings_clears_window(cfg, mocker):
    app = _make_app(cfg)
    mock_sw = MagicMock()
    app._settings_window = mock_sw

    app._close_settings()

    assert app._settings_window is None
