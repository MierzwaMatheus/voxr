import shutil
import threading
import time
import uuid

from voxr import audio, config, injection, transcription
from voxr.constants import MODEL_DIR
from voxr.enums import AppState, InputMode, SessionStatus
from voxr.hotkey import HotkeyCallbacks, HotkeyListener
from voxr.models import Configuration, RecordingSession
from voxr.settings_window import SettingsWindow
from voxr.tray import TrayIcon
from voxr.widget import RecordingWidget


class VoxrApp:
    def __init__(self, config: Configuration | None = None, model=None) -> None:
        self._config = config
        self._model = model
        self.state = AppState.IDLE
        self._stop_event: threading.Event | None = None
        self._session: RecordingSession | None = None
        self._record_thread: threading.Thread | None = None
        # True once run() starts the GTK main loop. Hotkey callbacks fire on the
        # pynput thread, where GLib.main_depth() is 0 — so we can't rely on it to
        # know a loop is running. This flag makes _gtk() and the countdown timer
        # schedule work on the main loop from any thread.
        self._gtk_loop_running: bool = False
        self._settings_window = None

        self._widget = RecordingWidget()
        self._tray = TrayIcon(
            on_settings=self.open_settings,
            on_quit=lambda: None,
        )
        if config is not None:
            self._hotkey = HotkeyListener(
                config=config,
                callbacks=HotkeyCallbacks(
                    on_activate=self.on_hotkey_activate,
                    on_cancel=self.on_cancel,
                    on_ptt_start=lambda: None,
                    on_ptt_stop=lambda: None,
                ),
            )
        else:
            self._hotkey = None

    def apply_settings(self, new_config: Configuration) -> None:
        if new_config.hotkey != self._config.hotkey and self._hotkey:
            self._hotkey.update_hotkey(new_config.hotkey)
        if new_config.model_name != self._config.model_name and self.state == AppState.IDLE:
            self._model = transcription.reload_model(new_config.model_name)
        config.save(new_config)
        self._config = new_config

    def open_settings(self) -> None:
        if self._settings_window is not None:
            self._settings_window.show()
            return
        self._settings_window = SettingsWindow(
            config=self._config,
            on_apply=self.apply_settings,
            on_cancel=self._close_settings,
        )
        self._settings_window.show()

    def _close_settings(self) -> None:
        self._settings_window = None

    def _gtk(self, fn, *args) -> None:
        """Schedule fn(*args) on the GTK main thread when a loop is running, else call directly.

        Allows unit/integration tests (no main loop) to verify widget calls synchronously
        while production code (Gtk.main() running) stays thread-safe.
        """
        if self._gtk_loop_running:
            try:
                from gi.repository import GLib
                GLib.idle_add(fn, *args)
                return
            except Exception:
                pass
        fn(*args)

    def _cleanup_partial_downloads(self) -> None:
        """Remove subdirectories inside MODEL_DIR that lack a model.bin file.

        These are left over from interrupted downloads and would cause
        load_model() to fail silently or raise unexpected errors.
        """
        if not MODEL_DIR.exists():
            return
        for entry in MODEL_DIR.iterdir():
            if entry.is_dir() and not (entry / "model.bin").exists():
                shutil.rmtree(entry)

    def on_hotkey_activate(self) -> None:
        if self.state == AppState.IDLE:
            self._start_recording()
        elif self.state == AppState.RECORDING:
            self._stop_and_process()

    def _start_recording(self) -> None:
        self.state = AppState.RECORDING
        self._stop_event = threading.Event()
        self._session = RecordingSession(
            session_id=str(uuid.uuid4()),
            start_time=time.time(),
            end_time=None,
            duration_seconds=0.0,
            input_mode=self._config.input_mode if self._config else InputMode.TOGGLE,
            audio_file_path="",
            status=SessionStatus.IN_PROGRESS,
        )
        self._gtk(self._widget.show_recording, None)
        if self._settings_window is not None:
            self._settings_window.update_recording_state(True)
        self._record_thread = threading.Thread(
            target=self._record_loop, daemon=True, name="voxr-record"
        )
        self._record_thread.start()

        # In production (GLib main loop active), drive the countdown timer and
        # fire on_timeout — both via a 1-second GLib tick so the widget stays in sync.
        # timeout_add is thread-safe: even called from the pynput thread, the tick
        # runs on the main loop.
        if self._gtk_loop_running:
            try:
                from gi.repository import GLib
                max_seconds = self._config.max_recording_seconds if self._config else 60
                start_time = time.time()

                def _tick() -> bool:
                    if self.state != AppState.RECORDING:
                        return False  # recording ended, stop ticking
                    elapsed = time.time() - start_time
                    self._widget.update_timer(elapsed, max_seconds)
                    if elapsed >= max_seconds:
                        self.on_timeout()
                        return False
                    return True  # continue ticking

                GLib.timeout_add(1000, _tick)
            except Exception:
                pass

    def _record_loop(self) -> None:
        # Runs in the recording thread. Only records — never processes.
        # Processing is always triggered externally (second hotkey or on_timeout).
        # Capture session reference locally: on_cancel() may set self._session = None
        # while this thread is still running.
        session = self._session
        if session is None:
            return
        print("[voxr] gravando…")
        audio_path = audio.record(
            session, self._stop_event, self._config.max_recording_seconds
        )
        self._audio_path = audio_path
        if self._session is not None:
            self._session.audio_file_path = audio_path
        print(f"[voxr] áudio salvo: {audio_path}")

    def _stop_and_process(self) -> None:
        print("[voxr] parando gravação…")
        self.state = AppState.PROCESSING
        if self._stop_event:
            self._stop_event.set()
        self._gtk(self._widget.show_processing)
        # Join the record thread so audio_file_path is set before processing.
        if self._record_thread:
            self._record_thread.join()
        self._do_process()

    def _do_process(self) -> None:
        if self._session is None:
            return

        # Verify that the model file is present before attempting transcription.
        model_name = self._config.model_name if self._config else None
        if model_name and not (MODEL_DIR / model_name / "model.bin").exists():
            self._tray.show_notification(
                "Modelo ausente — abra Configurações para baixá-lo novamente"
            )
            self._gtk(self._widget.hide)
            self.state = AppState.IDLE
            return

        print("[voxr] transcrevendo…")
        result = transcription.transcribe_session(self._session, self._model, self._config)
        print(f"[voxr] texto: {result.full_text!r}")
        mode = injection.insert_or_clipboard(result.full_text)
        print(f"[voxr] inserido via {mode}")
        self._gtk(self._widget.hide)
        self._gtk(self._tray.set_state, AppState.IDLE)
        self.state = AppState.IDLE
        if self._settings_window is not None:
            self._settings_window.update_recording_state(False)

    def on_timeout(self) -> None:
        if self.state == AppState.RECORDING:
            self._stop_and_process()

    def on_cancel(self) -> None:
        if self.state != AppState.RECORDING:
            return
        # Set IDLE before joining so _record_loop sees stop_event and exits cleanly.
        self.state = AppState.IDLE
        if self._stop_event:
            self._stop_event.set()
        self._session = None
        self._gtk(self._widget.hide)
        if self._settings_window is not None:
            self._settings_window.update_recording_state(False)

    def run(self) -> None:
        import gi
        gi.require_version("Gtk", "3.0")
        from faster_whisper import WhisperModel
        from gi.repository import Gtk

        from voxr import config as cfg
        from voxr.transcription import ModelNotFoundError, load_model

        # Load config from disk if not injected (e.g. in tests).
        if self._config is None:
            self._config = cfg.load()

        # Wire the quit callback now that we have a config.
        def _quit() -> None:
            if self._hotkey:
                self._hotkey.stop()
            Gtk.main_quit()

        self._tray._on_quit = _quit

        # (Re-)create hotkey listener with the loaded config.
        self._hotkey = HotkeyListener(
            config=self._config,
            callbacks=HotkeyCallbacks(
                on_activate=self.on_hotkey_activate,
                on_cancel=self.on_cancel,
                on_ptt_start=lambda: None,
                on_ptt_stop=lambda: None,
            ),
        )

        # Load Whisper model — fall back to HuggingFace auto-download if not cached locally.
        if self._model is None:
            try:
                self._model = load_model(self._config.model_name)
            except ModelNotFoundError:
                print(f"[voxr] Baixando modelo '{self._config.model_name}'…")
                self._model = WhisperModel(
                    self._config.model_name,
                    device="cpu",
                    compute_type="int8",
                    # Limit to half the cores so the system stays responsive during transcription.
                    cpu_threads=max(2, __import__("os").cpu_count() // 2),
                    num_workers=1,
                )

        # Warn if no microphone is detected.
        if not audio.is_microphone_available():
            self._tray.set_state(AppState.ERROR)
            self._tray.show_notification("Nenhum microfone detectado")

        self._cleanup_partial_downloads()
        self._hotkey.start()
        audio.start_cache_cleanup_daemon()

        print(f"[voxr] Pronto. Hotkey: {self._config.hotkey} | Modelo: {self._config.model_name}")
        self._gtk_loop_running = True
        Gtk.main()
