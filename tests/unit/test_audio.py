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


class TestIsMicrophoneAvailable:
    def test_returns_true_when_input_devices_exist(self, mocker):
        mocker.patch(
            "sounddevice.query_devices",
            return_value=[{"name": "Mic", "max_input_channels": 1}],
        )
        assert audio.is_microphone_available() is True

    def test_returns_false_when_no_input_devices(self, mocker):
        mocker.patch("sounddevice.query_devices", return_value=[])
        assert audio.is_microphone_available() is False

    def test_returns_false_on_exception(self, mocker):
        mocker.patch("sounddevice.query_devices", side_effect=Exception("no audio"))
        assert audio.is_microphone_available() is False


class TestListDevices:
    def test_returns_names_of_input_devices(self, mocker):
        mocker.patch(
            "sounddevice.query_devices",
            return_value=[
                {"name": "Mic A", "max_input_channels": 1},
                {"name": "Mic B", "max_input_channels": 2},
            ],
        )
        result = audio.list_devices()
        assert result == ["Mic A", "Mic B"]

    def test_excludes_output_only_devices(self, mocker):
        mocker.patch(
            "sounddevice.query_devices",
            return_value=[
                {"name": "Speakers", "max_input_channels": 0},
                {"name": "Mic", "max_input_channels": 1},
            ],
        )
        result = audio.list_devices()
        assert result == ["Mic"]
        assert "Speakers" not in result


class TestCacheDirectory:
    def test_record_creates_recordings_dir_if_not_exists(self, tmp_path, mocker):
        recordings_dir = tmp_path / "recordings"
        mocker.patch("voxr.audio.RECORDINGS_DIR", recordings_dir)
        mocker.patch("sounddevice.InputStream")
        mocker.patch("soundfile.write")

        stop_event = threading.Event()
        stop_event.set()
        from voxr.enums import InputMode, SessionStatus
        from voxr.models import RecordingSession
        session = RecordingSession(
            session_id="dir-test",
            start_time=0.0,
            end_time=None,
            duration_seconds=0.0,
            input_mode=InputMode.TOGGLE,
            audio_file_path="",
            status=SessionStatus.IN_PROGRESS,
        )

        audio.record(session, stop_event)

        assert recordings_dir.exists()


class TestCacheCleanup:
    def test_cleanup_deletes_files_older_than_24h(self, tmp_path):
        import time as time_mod

        recordings_dir = tmp_path / "recordings"
        recordings_dir.mkdir()

        old_file = recordings_dir / "old.wav"
        old_file.write_bytes(b"")
        old_mtime = time_mod.time() - (25 * 3600)
        import os
        os.utime(old_file, (old_mtime, old_mtime))

        audio.cleanup_old_recordings(recordings_dir=recordings_dir, max_age_seconds=86400)

        assert not old_file.exists()

    def test_cleanup_keeps_files_newer_than_24h(self, tmp_path):

        recordings_dir = tmp_path / "recordings"
        recordings_dir.mkdir()

        new_file = recordings_dir / "new.wav"
        new_file.write_bytes(b"")

        audio.cleanup_old_recordings(recordings_dir=recordings_dir, max_age_seconds=86400)

        assert new_file.exists()
