import sys
from unittest.mock import MagicMock

import pytest

# Stub hardware-dependent libs
for _mod in ("sounddevice", "soundfile", "faster_whisper"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
# Stub GTK so tests run without a display
for _mod in ("gi", "gi.repository", "gi.repository.Gtk", "gi.repository.Gdk", "gi.repository.GLib"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from voxr.models import Configuration  # noqa: E402
from voxr.enums import InputMode  # noqa: E402


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
from voxr.enums import AppState  # noqa: E402


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
