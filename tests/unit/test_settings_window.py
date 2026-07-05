import sys
from unittest.mock import MagicMock

import pytest

# Stub GTK so tests run without a display
for _mod in ("gi", "gi.repository", "gi.repository.Gtk", "gi.repository.Gdk", "gi.repository.GLib"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from voxr.models import Configuration  # noqa: E402
from voxr.enums import InputMode  # noqa: E402
from voxr.settings_window import get_model_info  # noqa: E402


from pathlib import Path  # noqa: E402


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


# --- T086: ModelInfo / get_model_info ---

def test_get_model_info_cached(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    model_subdir = model_dir / "medium"
    model_subdir.mkdir()
    (model_subdir / "model.bin").write_bytes(b"fake")

    import voxr.settings_window as sw
    monkeypatch.setattr(sw, "MODEL_DIR", model_dir)

    info = get_model_info("medium")
    assert info.is_cached is True
    assert info.model_name == "medium"
    assert info.path is not None


def test_get_model_info_not_cached(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()

    import voxr.settings_window as sw
    monkeypatch.setattr(sw, "MODEL_DIR", model_dir)

    info = get_model_info("medium")
    assert info.is_cached is False
    assert info.path is None
