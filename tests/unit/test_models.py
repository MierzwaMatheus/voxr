import json

from voxr import constants
from voxr.enums import AppState, ChunkStatus, InputMode, SessionStatus, TranscriptionStatus
from voxr.models import ChunkResult, RecordingSession


class TestEnumSerialization:
    def test_input_mode_values_are_json_serializable(self):
        for mode in InputMode:
            assert json.dumps({"mode": mode}) is not None

    def test_session_status_values_are_json_serializable(self):
        for status in SessionStatus:
            assert json.dumps({"status": status}) is not None

    def test_transcription_status_values_are_json_serializable(self):
        for status in TranscriptionStatus:
            assert json.dumps({"status": status}) is not None

    def test_chunk_status_values_are_json_serializable(self):
        for status in ChunkStatus:
            assert json.dumps({"status": status}) is not None

    def test_app_state_values_are_json_serializable(self):
        for state in AppState:
            assert json.dumps({"state": state}) is not None

    def test_input_mode_toggle_serializes_as_string(self):
        result = json.dumps({"mode": InputMode.TOGGLE})
        assert '"toggle"' in result

    def test_input_mode_ptt_serializes_as_string(self):
        result = json.dumps({"mode": InputMode.PTT})
        assert '"ptt"' in result

    def test_session_status_in_progress_serializes_as_string(self):
        result = json.dumps({"status": SessionStatus.IN_PROGRESS})
        assert '"in_progress"' in result

    def test_chunk_status_failed_with_placeholder_serializes_as_string(self):
        result = json.dumps({"status": ChunkStatus.FAILED_WITH_PLACEHOLDER})
        assert '"failed_with_placeholder"' in result

    def test_app_state_error_serializes_as_string(self):
        result = json.dumps({"state": AppState.ERROR})
        assert '"error"' in result

    def test_all_enums_have_expected_members(self):
        assert set(InputMode) == {InputMode.TOGGLE, InputMode.PTT}
        assert SessionStatus.IN_PROGRESS in SessionStatus
        assert SessionStatus.COMPLETED in SessionStatus
        assert SessionStatus.CANCELLED in SessionStatus
        assert TranscriptionStatus.SUCCESS in TranscriptionStatus
        assert TranscriptionStatus.PARTIAL in TranscriptionStatus
        assert TranscriptionStatus.FAILED in TranscriptionStatus
        assert ChunkStatus.SUCCESS in ChunkStatus
        assert ChunkStatus.FAILED_WITH_PLACEHOLDER in ChunkStatus
        assert AppState.IDLE in AppState
        assert AppState.RECORDING in AppState
        assert AppState.PROCESSING in AppState
        assert AppState.ERROR in AppState


class TestChunkResult:
    def _make_chunk(self, **kwargs):
        defaults = {
            "chunk_id": "abc-123",
            "chunk_index": 0,
            "text": "hello",
            "confidence": 0.9,
            "retry_count": 0,
            "status": ChunkStatus.SUCCESS,
        }
        defaults.update(kwargs)
        return ChunkResult(**defaults)

    def test_failed_chunk_contains_placeholder_text(self):
        chunk = self._make_chunk(
            text=constants.PLACEHOLDER_TEXT,
            confidence=None,
            status=ChunkStatus.FAILED_WITH_PLACEHOLDER,
        )
        assert constants.PLACEHOLDER_TEXT in chunk.text

    def test_placeholder_text_is_exact_constant(self):
        chunk = self._make_chunk(
            text=constants.PLACEHOLDER_TEXT,
            confidence=None,
            status=ChunkStatus.FAILED_WITH_PLACEHOLDER,
        )
        assert chunk.text == constants.PLACEHOLDER_TEXT

    def test_placeholder_text_constant_value(self):
        assert constants.PLACEHOLDER_TEXT == "[trecho não transcrito]"

    def test_successful_chunk_has_confidence(self):
        chunk = self._make_chunk(confidence=0.95, status=ChunkStatus.SUCCESS)
        assert chunk.confidence == 0.95

    def test_failed_chunk_has_none_confidence(self):
        chunk = self._make_chunk(
            text=constants.PLACEHOLDER_TEXT,
            confidence=None,
            status=ChunkStatus.FAILED_WITH_PLACEHOLDER,
        )
        assert chunk.confidence is None

    def test_chunk_index_is_zero_based(self):
        chunk = self._make_chunk(chunk_index=0)
        assert chunk.chunk_index == 0

    def test_chunk_retry_count_default(self):
        chunk = self._make_chunk(retry_count=0)
        assert chunk.retry_count == 0


class TestRecordingSession:
    def _make_session(self, **kwargs):
        defaults = {
            "session_id": "sess-001",
            "start_time": 1000.0,
            "end_time": None,
            "duration_seconds": 0.0,
            "input_mode": InputMode.TOGGLE,
            "audio_file_path": "/tmp/sess-001.wav",
            "status": SessionStatus.IN_PROGRESS,
        }
        defaults.update(kwargs)
        return RecordingSession(**defaults)

    def test_session_starts_with_in_progress_status(self):
        session = self._make_session()
        assert session.status == SessionStatus.IN_PROGRESS

    def test_end_time_is_none_while_in_progress(self):
        session = self._make_session()
        assert session.end_time is None

    def test_status_can_change_to_completed(self):
        session = self._make_session()
        session.status = SessionStatus.COMPLETED
        assert session.status == SessionStatus.COMPLETED

    def test_status_can_change_to_cancelled(self):
        session = self._make_session()
        session.status = SessionStatus.CANCELLED
        assert session.status == SessionStatus.CANCELLED

    def test_end_time_set_on_completion(self):
        session = self._make_session()
        session.status = SessionStatus.COMPLETED
        session.end_time = 1030.0
        assert session.end_time == 1030.0

    def test_end_time_remains_none_while_in_progress(self):
        session = self._make_session(status=SessionStatus.IN_PROGRESS)
        assert session.end_time is None

    def test_session_has_session_id(self):
        session = self._make_session(session_id="abc-uuid-123")
        assert session.session_id == "abc-uuid-123"

    def test_session_input_mode_toggle(self):
        session = self._make_session(input_mode=InputMode.TOGGLE)
        assert session.input_mode == InputMode.TOGGLE

    def test_session_input_mode_ptt(self):
        session = self._make_session(input_mode=InputMode.PTT)
        assert session.input_mode == InputMode.PTT
