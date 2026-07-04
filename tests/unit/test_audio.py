import threading

from voxr import audio
from voxr.enums import InputMode, SessionStatus
from voxr.models import RecordingSession


def _make_session(session_id="test-session-001"):
    return RecordingSession(
        session_id=session_id,
        start_time=0.0,
        end_time=None,
        duration_seconds=0.0,
        input_mode=InputMode.TOGGLE,
        audio_file_path="",
        status=SessionStatus.IN_PROGRESS,
    )


class TestAudioRecord:
    def test_record_returns_path_containing_session_id(self, tmp_path, mocker):
        mocker.patch("voxr.audio.RECORDINGS_DIR", tmp_path / "recordings")
        mocker.patch("sounddevice.InputStream")
        mocker.patch("soundfile.write")

        stop_event = threading.Event()
        stop_event.set()
        session = _make_session("abc123")

        result = audio.record(session, stop_event)

        assert "abc123" in result

    def test_record_returns_wav_extension(self, tmp_path, mocker):
        mocker.patch("voxr.audio.RECORDINGS_DIR", tmp_path / "recordings")
        mocker.patch("sounddevice.InputStream")
        mocker.patch("soundfile.write")

        stop_event = threading.Event()
        stop_event.set()
        session = _make_session("abc123")

        result = audio.record(session, stop_event)

        assert result.endswith(".wav")

    def test_record_calls_soundfile_write_with_correct_path(self, tmp_path, mocker):
        recordings_dir = tmp_path / "recordings"
        mocker.patch("voxr.audio.RECORDINGS_DIR", recordings_dir)
        mock_write = mocker.patch("soundfile.write")
        mocker.patch("sounddevice.InputStream")

        stop_event = threading.Event()
        stop_event.set()
        session = _make_session("session-xyz")

        audio.record(session, stop_event)

        assert mock_write.called
        written_path = mock_write.call_args[0][0]
        assert "session-xyz" in written_path
        assert written_path.endswith(".wav")

    def test_record_stops_when_stop_event_set(self, tmp_path, mocker):
        mocker.patch("voxr.audio.RECORDINGS_DIR", tmp_path / "recordings")
        mocker.patch("soundfile.write")
        mocker.patch("sounddevice.InputStream")

        stop_event = threading.Event()
        stop_event.set()
        session = _make_session("stop-test")

        import time

        start = time.time()
        audio.record(session, stop_event, max_seconds=60)
        elapsed = time.time() - start

        assert elapsed < 2.0

    def test_record_stops_at_max_seconds(self, tmp_path, mocker):
        mocker.patch("voxr.audio.RECORDINGS_DIR", tmp_path / "recordings")
        mocker.patch("soundfile.write")
        mocker.patch("sounddevice.InputStream")
        mocker.patch("voxr.audio.time.sleep")

        call_count = {"n": 0}

        def fake_time():
            call_count["n"] += 1
            return call_count["n"] * 10.0

        mocker.patch("voxr.audio.time.time", side_effect=fake_time)

        stop_event = threading.Event()
        session = _make_session("timeout-test")

        audio.record(session, stop_event, max_seconds=5)

        assert not stop_event.is_set()
