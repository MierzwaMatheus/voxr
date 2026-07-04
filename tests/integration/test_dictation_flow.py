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
