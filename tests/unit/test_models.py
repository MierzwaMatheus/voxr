import json

from voxr.enums import AppState, ChunkStatus, InputMode, SessionStatus, TranscriptionStatus


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
