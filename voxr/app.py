import threading

from voxr import audio, injection, transcription
from voxr.enums import AppState
from voxr.models import Configuration


class VoxrApp:
    def __init__(self, config: Configuration, model) -> None:
        self._config = config
        self._model = model
        self.state = AppState.IDLE
        self._stop_event: threading.Event | None = None
        self._session = None

    def on_hotkey_activate(self) -> None:
        if self.state == AppState.IDLE:
            self._start_recording()
        elif self.state == AppState.RECORDING:
            self._stop_and_process()

    def _start_recording(self) -> None:
        import time
        import uuid

        from voxr.enums import InputMode, SessionStatus
        from voxr.models import RecordingSession

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
        self._audio_path = audio.record(self._session, self._stop_event, self._config.max_recording_seconds)

    def _stop_and_process(self) -> None:
        self.state = AppState.PROCESSING
        if self._stop_event:
            self._stop_event.set()

        result = transcription.transcribe_session(self._session, self._model, self._config)
        injection.inject_text(result.full_text)
        self.state = AppState.IDLE

    def run(self) -> None:
        raise NotImplementedError
