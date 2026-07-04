import threading
import time
import uuid

from voxr import audio, injection, transcription
from voxr.enums import AppState, InputMode, SessionStatus
from voxr.hotkey import HotkeyCallbacks, HotkeyListener
from voxr.models import Configuration, RecordingSession
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

        self._widget = RecordingWidget()
        self._tray = TrayIcon(
            on_settings=lambda: None,
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

    def _gtk(self, fn, *args) -> None:
        """Schedule fn(*args) on the GTK main thread when a loop is running, else call directly.

        Allows unit/integration tests (no main loop) to verify widget calls synchronously
        while production code (Gtk.main() running) stays thread-safe.
        """
        try:
            from gi.repository import GLib
            if GLib.main_depth() > 0:
                GLib.idle_add(fn, *args)
                return
        except Exception:
            pass
        fn(*args)

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
        self._record_thread = threading.Thread(
            target=self._record_loop, daemon=True, name="voxr-record"
        )
        self._record_thread.start()

        # In production (GLib main loop active), fire on_timeout after max_recording_seconds
        # so the timeout path goes through the same _stop_and_process as a manual stop.
        try:
            from gi.repository import GLib
            if GLib.main_depth() > 0:
                max_ms = (self._config.max_recording_seconds if self._config else 60) * 1000

                def _timeout_cb() -> bool:
                    if self.state == AppState.RECORDING:
                        self.on_timeout()
                    return False  # one-shot timer

                GLib.timeout_add(max_ms, _timeout_cb)
        except Exception:
            pass

    def _record_loop(self) -> None:
        # Runs in the recording thread. Only records — never processes.
        # Processing is always triggered externally (second hotkey or on_timeout).
        print("[voxr] gravando…")
        audio_path = audio.record(
            self._session, self._stop_event, self._config.max_recording_seconds
        )
        self._audio_path = audio_path
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
        print("[voxr] transcrevendo…")
        result = transcription.transcribe_session(self._session, self._model, self._config)
        print(f"[voxr] texto: {result.full_text!r}")
        mode = injection.insert_or_clipboard(result.full_text)
        print(f"[voxr] inserido via {mode}")
        self._gtk(self._widget.hide)
        self._gtk(self._tray.set_state, AppState.IDLE)
        self.state = AppState.IDLE

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

        self._hotkey.start()
        audio.start_cache_cleanup_daemon()

        print(f"[voxr] Pronto. Hotkey: {self._config.hotkey} | Modelo: {self._config.model_name}")
        Gtk.main()
