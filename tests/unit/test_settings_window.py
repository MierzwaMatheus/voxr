import sys
from unittest.mock import MagicMock

import pytest

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
