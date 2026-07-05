import sys
from unittest.mock import MagicMock

import pytest

# Stub hardware-dependent libs
for _mod in ("sounddevice", "soundfile", "faster_whisper"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Stub GTK — gi.repository.Gtk must also be an attribute of gi.repository
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


from voxr.app import VoxrApp  # noqa: E402

# --- T088: apply_settings ---

def _make_app(cfg):
    app = VoxrApp(config=cfg)
    app._hotkey = MagicMock()
    app._model = MagicMock()
    return app


def test_apply_settings_calls_update_hotkey_when_hotkey_changed(cfg):
    app = _make_app(cfg)
    new_cfg = Configuration(
        hotkey="<ctrl>+<shift>+d",
        input_mode=cfg.input_mode,
        model_name=cfg.model_name,
        transcription_language=cfg.transcription_language,
        max_recording_seconds=cfg.max_recording_seconds,
        vad_enabled=cfg.vad_enabled,
        pipeline_mode_enabled=cfg.pipeline_mode_enabled,
        autostart_enabled=cfg.autostart_enabled,
        interface_language=cfg.interface_language,
        first_run_complete=cfg.first_run_complete,
    )
    app.apply_settings(new_cfg)
    app._hotkey.update_hotkey.assert_called_once_with("<ctrl>+<shift>+d")


def test_apply_settings_does_not_call_update_hotkey_when_hotkey_unchanged(cfg):
    app = _make_app(cfg)
    app.apply_settings(cfg)
    app._hotkey.update_hotkey.assert_not_called()


def test_apply_settings_calls_reload_model_when_model_changed(cfg, mocker):
    app = _make_app(cfg)
    mock_reload = mocker.patch("voxr.app.transcription.reload_model", return_value=MagicMock())
    new_cfg = Configuration(
        hotkey=cfg.hotkey,
        input_mode=cfg.input_mode,
        model_name="small",
        transcription_language=cfg.transcription_language,
        max_recording_seconds=cfg.max_recording_seconds,
        vad_enabled=cfg.vad_enabled,
        pipeline_mode_enabled=cfg.pipeline_mode_enabled,
        autostart_enabled=cfg.autostart_enabled,
        interface_language=cfg.interface_language,
        first_run_complete=cfg.first_run_complete,
    )
    app.apply_settings(new_cfg)
    mock_reload.assert_called_once_with("small")


def test_apply_settings_does_not_reload_model_when_model_unchanged(cfg, mocker):
    app = _make_app(cfg)
    mock_reload = mocker.patch("voxr.app.transcription.reload_model")
    app.apply_settings(cfg)
    mock_reload.assert_not_called()


def test_apply_settings_saves_config(cfg, mocker):
    app = _make_app(cfg)
    mock_save = mocker.patch("voxr.app.config.save")
    app.apply_settings(cfg)
    mock_save.assert_called_once_with(cfg)


# --- T098: open_settings ---

def test_open_settings_creates_settings_window_and_calls_show(cfg, mocker):
    app = _make_app(cfg)
    mock_sw_class = mocker.patch("voxr.app.SettingsWindow")
    mock_sw = MagicMock()
    mock_sw_class.return_value = mock_sw

    app.open_settings()

    mock_sw_class.assert_called_once_with(
        config=cfg,
        on_apply=app.apply_settings,
        on_cancel=app._close_settings,
    )
    mock_sw.show.assert_called_once()


def test_open_settings_stores_reference(cfg, mocker):
    app = _make_app(cfg)
    mock_sw_class = mocker.patch("voxr.app.SettingsWindow")
    mock_sw = MagicMock()
    mock_sw_class.return_value = mock_sw

    app.open_settings()

    assert app._settings_window is mock_sw


# T100: second open_settings call calls present on existing window
def test_open_settings_second_call_calls_present(cfg, mocker):
    app = _make_app(cfg)
    mock_sw = MagicMock()
    app._settings_window = mock_sw

    app.open_settings()

    mock_sw.show.assert_called_once()
