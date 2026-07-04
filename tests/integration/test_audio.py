import threading

import pytest

from voxr import audio
from voxr.enums import InputMode, SessionStatus
from voxr.models import RecordingSession


def _microphone_available() -> bool:
    try:
        return audio.is_microphone_available()
    except Exception:
        return False


def _make_session(session_id="integration-test-001"):
    return RecordingSession(
        session_id=session_id,
        start_time=0.0,
        end_time=None,
        duration_seconds=0.0,
        input_mode=InputMode.TOGGLE,
        audio_file_path="",
        status=SessionStatus.IN_PROGRESS,
    )


@pytest.mark.skipif(
    not _microphone_available(),
    reason="Requer microfone disponível",
)
def test_record_creates_valid_wav_file(tmp_path, monkeypatch):
    import soundfile as sf

    monkeypatch.setattr(audio, "RECORDINGS_DIR", tmp_path / "recordings")
    stop_event = threading.Event()
    session = _make_session("integ-001")

    def _stop_after_2s():
        import time

        time.sleep(2)
        stop_event.set()

    stopper = threading.Thread(target=_stop_after_2s, daemon=True)
    stopper.start()

    result = audio.record(session, stop_event, max_seconds=10)
    stopper.join(timeout=5)

    assert (tmp_path / "recordings" / "integ-001.wav").exists()
    assert result.endswith(".wav")
    sf.read(result)  # lança exceção se WAV inválido
