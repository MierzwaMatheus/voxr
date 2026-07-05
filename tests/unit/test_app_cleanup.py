"""Tests for VoxrApp._cleanup_partial_downloads() behavior."""
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


class TestCleanupPartialDownloads:
    def test_removes_subdirectory_without_model_bin(self, tmp_path, monkeypatch):
        """Subdiretório sem model.bin é removido durante a limpeza."""
        model_dir = tmp_path / "models"
        model_dir.mkdir()
        partial_dir = model_dir / "small"
        partial_dir.mkdir()

        monkeypatch.setattr("voxr.app.MODEL_DIR", model_dir)

        app = VoxrApp()
        app._cleanup_partial_downloads()

        assert not partial_dir.exists(), "Subdiretório sem model.bin deve ser removido"

    def test_preserves_subdirectory_with_model_bin(self, tmp_path, monkeypatch):
        """Subdiretório com model.bin presente NÃO deve ser removido."""
        model_dir = tmp_path / "models"
        model_dir.mkdir()
        complete_dir = model_dir / "medium"
        complete_dir.mkdir()
        (complete_dir / "model.bin").write_bytes(b"fake model data")

        monkeypatch.setattr("voxr.app.MODEL_DIR", model_dir)

        app = VoxrApp()
        app._cleanup_partial_downloads()

        assert complete_dir.exists(), "Subdiretório com model.bin deve ser preservado"

    def test_does_not_raise_when_model_dir_does_not_exist(self, tmp_path, monkeypatch):
        """Não deve lançar exceção se MODEL_DIR não existir."""
        nonexistent_dir = tmp_path / "models_that_do_not_exist"
        monkeypatch.setattr("voxr.app.MODEL_DIR", nonexistent_dir)

        app = VoxrApp()
        app._cleanup_partial_downloads()  # must not raise

    def test_run_calls_cleanup(self, tmp_path, monkeypatch):
        """run() deve chamar _cleanup_partial_downloads()."""
        cleanup_called = []

        fake_config = MagicMock()
        fake_config.hotkey = "<alt>+v"
        fake_config.model_name = "medium"

        monkeypatch.setattr("voxr.app.MODEL_DIR", tmp_path / "models")

        import voxr.config as cfg_mod
        monkeypatch.setattr(cfg_mod, "load", lambda: fake_config)

        import voxr.audio as audio_mod
        monkeypatch.setattr(audio_mod, "is_microphone_available", lambda: True)
        monkeypatch.setattr(audio_mod, "start_cache_cleanup_daemon", lambda: None)

        import voxr.transcription as trans_mod
        monkeypatch.setattr(trans_mod, "load_model", lambda name: MagicMock())

        import gi as gi_mod
        monkeypatch.setattr(gi_mod, "require_version", lambda *a: None)

        fake_gtk = MagicMock()
        fake_gtk.main = MagicMock()
        fake_gi_repo = MagicMock()
        fake_gi_repo.Gtk = fake_gtk
        monkeypatch.setitem(sys.modules, "gi.repository", fake_gi_repo)

        app = VoxrApp(config=fake_config, model=MagicMock())

        original_cleanup = app._cleanup_partial_downloads
        def tracked_cleanup():
            cleanup_called.append(True)
            original_cleanup()
        app._cleanup_partial_downloads = tracked_cleanup
        app._hotkey = MagicMock()

        app.run()

        assert cleanup_called, "_cleanup_partial_downloads() deve ser chamado durante run()"
