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
    def __init__(self, config: Configuration, model) -> None:
        self._config = config
        self._model = model
        self.state = AppState.IDLE
        self._stop_event: threading.Event | None = None
        self._session: RecordingSession | None = None

        self._widget = RecordingWidget()
        self._tray = TrayIcon(
            on_settings=lambda: None,
            on_quit=lambda: None,
        )
        self._hotkey = HotkeyListener(
            config=config,
            callbacks=HotkeyCallbacks(
                on_activate=self.on_hotkey_activate,
                on_cancel=self.on_cancel,
                on_ptt_start=lambda: None,
                on_ptt_stop=lambda: None,
            ),
        )

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
            input_mode=InputMode.TOGGLE,
            audio_file_path="",
            status=SessionStatus.IN_PROGRESS,
        )
        self._widget.show_recording(None)
        self._audio_path = audio.record(self._session, self._stop_event, self._config.max_recording_seconds)

    def _stop_and_process(self) -> None:
        self.state = AppState.PROCESSING
        if self._stop_event:
            self._stop_event.set()

        result = transcription.transcribe_session(self._session, self._model, self._config)
        injection.insert_or_clipboard(result.full_text)
        self._widget.hide()
        self.state = AppState.IDLE

    def on_timeout(self) -> None:
        if self.state == AppState.RECORDING:
            self._stop_and_process()

    def on_cancel(self) -> None:
        if self.state != AppState.RECORDING:
            return
        if self._stop_event:
            self._stop_event.set()
        self._session = None
        self._widget.hide()
        self.state = AppState.IDLE

    def run(self) -> None:
        raise NotImplementedError
