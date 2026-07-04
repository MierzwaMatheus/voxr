"""Integration tests for VoxrApp dictation flows."""
import sys
from unittest.mock import MagicMock, patch

# Stub pynput/GTK so tests run without X11/display
if "pynput" not in sys.modules:
    sys.modules["pynput"] = MagicMock()
    sys.modules["pynput.keyboard"] = MagicMock()

import pytest

from voxr.app import VoxrApp
from voxr.enums import AppState, InputMode
from voxr.models import Configuration


def make_config() -> Configuration:
    return Configuration(
        hotkey="<alt>+v",
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


FAKE_AUDIO_PATH = "/tmp/session-001.wav"
FAKE_TRANSCRIBED_TEXT = "olá mundo"


class TestFullDictationFlow:
    """T057 — hotkey → gravação → transcrição → inject."""

    def test_full_flow_calls_inject_text_with_transcribed_text(self, mocker):
        """Dois acionamentos do hotkey produzem injeção do texto transcrito."""
        config = make_config()
        mock_model = MagicMock()

        mocker.patch("voxr.app.audio.record", return_value=FAKE_AUDIO_PATH)
        mock_transcribe = mocker.patch(
            "voxr.app.transcription.transcribe_session",
            return_value=MagicMock(full_text=FAKE_TRANSCRIBED_TEXT),
        )
        mock_inject = mocker.patch("voxr.app.injection.inject_text", return_value=True)

        app = VoxrApp(config=config, model=mock_model)

        # Primeiro acionamento: IDLE → RECORDING
        app.on_hotkey_activate()
        assert app.state == AppState.RECORDING

        # Segundo acionamento: RECORDING → PROCESSING → IDLE
        app.on_hotkey_activate()
        assert app.state == AppState.IDLE

        mock_inject.assert_called_once_with(FAKE_TRANSCRIBED_TEXT)

    def test_state_starts_as_idle(self):
        """VoxrApp inicia no estado IDLE."""
        config = make_config()
        mock_model = MagicMock()
        app = VoxrApp(config=config, model=mock_model)
        assert app.state == AppState.IDLE


class TestCancelFlow:
    """T058 — hotkey → gravação → Escape cancela sem injetar texto (FR-006)."""

    def test_cancel_does_not_call_inject_text(self, mocker):
        """on_cancel() durante gravação não injeta texto."""
        config = make_config()
        mock_model = MagicMock()

        mocker.patch("voxr.app.audio.record", return_value=FAKE_AUDIO_PATH)
        mock_inject = mocker.patch("voxr.app.injection.inject_text", return_value=True)

        app = VoxrApp(config=config, model=mock_model)
        app.on_hotkey_activate()  # IDLE → RECORDING
        app.on_cancel()           # cancela

        mock_inject.assert_not_called()

    def test_cancel_returns_state_to_idle(self, mocker):
        """on_cancel() retorna o estado para IDLE."""
        config = make_config()
        mock_model = MagicMock()

        mocker.patch("voxr.app.audio.record", return_value=FAKE_AUDIO_PATH)

        app = VoxrApp(config=config, model=mock_model)
        app.on_hotkey_activate()
        app.on_cancel()

        assert app.state == AppState.IDLE

    def test_cancel_when_idle_is_noop(self):
        """on_cancel() quando IDLE não levanta exceção e mantém IDLE."""
        config = make_config()
        mock_model = MagicMock()
        app = VoxrApp(config=config, model=mock_model)
        app.on_cancel()
        assert app.state == AppState.IDLE


class TestClipboardFallback:
    """T059 — quando inject_text falha, copia para clipboard (FR-003)."""

    def test_clipboard_used_when_inject_fails(self, mocker):
        """Se inject_text() retorna False, copy_to_clipboard() é chamado com o texto."""
        config = make_config()
        mock_model = MagicMock()

        mocker.patch("voxr.app.audio.record", return_value=FAKE_AUDIO_PATH)
        mocker.patch(
            "voxr.app.transcription.transcribe_session",
            return_value=MagicMock(full_text=FAKE_TRANSCRIBED_TEXT),
        )
        mocker.patch("voxr.app.injection.inject_text", return_value=False)
        mock_clipboard = mocker.patch("voxr.app.injection.copy_to_clipboard")

        app = VoxrApp(config=config, model=mock_model)
        app.on_hotkey_activate()  # IDLE → RECORDING
        app.on_hotkey_activate()  # RECORDING → PROCESSING → IDLE

        mock_clipboard.assert_called_once_with(FAKE_TRANSCRIBED_TEXT)

    def test_clipboard_not_used_when_inject_succeeds(self, mocker):
        """Se inject_text() retorna True, copy_to_clipboard() não é chamado."""
        config = make_config()
        mock_model = MagicMock()

        mocker.patch("voxr.app.audio.record", return_value=FAKE_AUDIO_PATH)
        mocker.patch(
            "voxr.app.transcription.transcribe_session",
            return_value=MagicMock(full_text=FAKE_TRANSCRIBED_TEXT),
        )
        mocker.patch("voxr.app.injection.inject_text", return_value=True)
        mock_clipboard = mocker.patch("voxr.app.injection.copy_to_clipboard")

        app = VoxrApp(config=config, model=mock_model)
        app.on_hotkey_activate()
        app.on_hotkey_activate()

        mock_clipboard.assert_not_called()


class TestMaxDurationTimeout:
    """T060 — gravação para automaticamente ao atingir max_recording_seconds (FR-007)."""

    def test_timeout_triggers_transcription_and_inject(self, mocker):
        """Quando audio.record retorna (timeout), app processa e injeta normalmente."""
        config = make_config()
        mock_model = MagicMock()

        mocker.patch("voxr.app.audio.record", return_value=FAKE_AUDIO_PATH)
        mocker.patch(
            "voxr.app.transcription.transcribe_session",
            return_value=MagicMock(full_text=FAKE_TRANSCRIBED_TEXT),
        )
        mock_inject = mocker.patch("voxr.app.injection.inject_text", return_value=True)

        app = VoxrApp(config=config, model=mock_model)
        app.on_hotkey_activate()  # inicia gravação; audio.record retorna imediatamente (mock)

        # Simula timeout: app deve detectar que record finalizou e processar
        app.on_timeout()

        mock_inject.assert_called_once_with(FAKE_TRANSCRIBED_TEXT)
        assert app.state == AppState.IDLE

    def test_timeout_state_goes_idle(self, mocker):
        """Após timeout, estado final é IDLE."""
        config = make_config()
        mock_model = MagicMock()

        mocker.patch("voxr.app.audio.record", return_value=FAKE_AUDIO_PATH)
        mocker.patch(
            "voxr.app.transcription.transcribe_session",
            return_value=MagicMock(full_text=FAKE_TRANSCRIBED_TEXT),
        )
        mocker.patch("voxr.app.injection.inject_text", return_value=True)

        app = VoxrApp(config=config, model=mock_model)
        app.on_hotkey_activate()
        app.on_timeout()

        assert app.state == AppState.IDLE


class TestVoxrAppInit:
    """T061 — VoxrApp.__init__ inicializa todos os componentes (config, model, hotkey, tray, widget)."""

    def test_init_stores_config_and_model(self):
        config = make_config()
        mock_model = MagicMock()
        app = VoxrApp(config=config, model=mock_model)
        assert app._config is config
        assert app._model is mock_model

    def test_init_creates_hotkey_listener(self, mocker):
        """VoxrApp cria um HotkeyListener com o config fornecido."""
        mock_listener_cls = mocker.patch("voxr.app.HotkeyListener")
        config = make_config()
        app = VoxrApp(config=config, model=MagicMock())
        mock_listener_cls.assert_called_once()
        call_args = mock_listener_cls.call_args
        passed_config = call_args[1].get("config") or call_args[0][0]
        assert passed_config is config

    def test_init_creates_tray_icon(self, mocker):
        """VoxrApp cria um TrayIcon."""
        mocker.patch("voxr.app.HotkeyListener")
        mock_tray_cls = mocker.patch("voxr.app.TrayIcon")
        app = VoxrApp(config=make_config(), model=MagicMock())
        mock_tray_cls.assert_called_once()

    def test_init_creates_recording_widget(self, mocker):
        """VoxrApp cria um RecordingWidget."""
        mocker.patch("voxr.app.HotkeyListener")
        mocker.patch("voxr.app.TrayIcon")
        mock_widget_cls = mocker.patch("voxr.app.RecordingWidget")
        app = VoxrApp(config=make_config(), model=MagicMock())
        mock_widget_cls.assert_called_once()
