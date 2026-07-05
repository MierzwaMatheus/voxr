"""Tests for model presence verification in VoxrApp._do_process()."""
import sys
from unittest.mock import MagicMock

# Stub hardware-dependent libs so unit tests run without PortAudio/libsndfile/X11/GTK
_gi_mock = MagicMock()
for _mod in (
    "sounddevice", "soundfile", "faster_whisper",
    "pynput", "pynput.keyboard",
    "gi", "gi.repository", "gi.repository.AppIndicator3",
    "gi.repository.Gtk", "gi.repository.GLib", "gi.repository.Notify",
):
    sys.modules.setdefault(_mod, _gi_mock if _mod.startswith("gi") else MagicMock())

from voxr.app import VoxrApp  # noqa: E402
from voxr.enums import AppState  # noqa: E402
from voxr.models import Configuration, RecordingSession  # noqa: E402


def make_app(tmp_path, model_name="medium", model_bin_exists=False):
    """Helper: create a VoxrApp wired for unit testing."""
    model_dir = tmp_path / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    if model_bin_exists:
        model_subdir = model_dir / model_name
        model_subdir.mkdir(parents=True, exist_ok=True)
        (model_subdir / "model.bin").write_bytes(b"fake")

    fake_config = MagicMock(spec=Configuration)
    fake_config.model_name = model_name

    app = VoxrApp(config=fake_config, model=MagicMock())
    app._session = MagicMock(spec=RecordingSession)
    app._session.audio_file_path = "/tmp/fake.wav"
    app.state = AppState.PROCESSING
    return app, model_dir


class TestDoProcessModelCheck:
    def test_notifies_and_aborts_when_model_bin_missing(self, tmp_path, monkeypatch):
        """Se model.bin ausente, _do_process() notifica via TrayIcon e aborta sem transcrever."""
        app, model_dir = make_app(tmp_path, model_bin_exists=False)
        monkeypatch.setattr("voxr.app.MODEL_DIR", model_dir)

        transcribe_called = []
        import voxr.transcription as trans_mod
        monkeypatch.setattr(trans_mod, "transcribe_session",
                            lambda *a, **kw: transcribe_called.append(True))

        notifications = []
        app._tray.show_notification = lambda msg: notifications.append(msg)

        app._do_process()

        assert not transcribe_called, "transcribe_session não deve ser chamado se model.bin ausente"
        assert len(notifications) == 1, "deve haver exatamente uma notificação"
        assert "Modelo ausente" in notifications[0]

    def test_proceeds_when_model_bin_present(self, tmp_path, monkeypatch):
        """Se model.bin existir, _do_process() chama transcribe_session normalmente."""
        app, model_dir = make_app(tmp_path, model_bin_exists=True)
        monkeypatch.setattr("voxr.app.MODEL_DIR", model_dir)

        transcribe_called = []
        fake_result = MagicMock()
        fake_result.full_text = "hello"

        import voxr.transcription as trans_mod
        monkeypatch.setattr(trans_mod, "transcribe_session",
                            lambda *a, **kw: (transcribe_called.append(True), fake_result)[1])

        import voxr.injection as inj_mod
        monkeypatch.setattr(inj_mod, "insert_or_clipboard", lambda text: "clipboard")

        app._do_process()

        assert transcribe_called, "transcribe_session deve ser chamado quando model.bin está presente"

    def test_state_returns_to_idle_when_model_missing(self, tmp_path, monkeypatch):
        """Estado deve retornar a IDLE após abortar por modelo ausente (sem travar)."""
        app, model_dir = make_app(tmp_path, model_bin_exists=False)
        monkeypatch.setattr("voxr.app.MODEL_DIR", model_dir)
        app._tray.show_notification = lambda msg: None

        assert app.state == AppState.PROCESSING

        app._do_process()

        assert app.state == AppState.IDLE, "Estado deve ser IDLE após aborto por modelo ausente"
