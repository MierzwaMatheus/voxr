import pytest
from unittest.mock import MagicMock

from voxr import transcription
from voxr.enums import ChunkStatus, InputMode, SessionStatus, TranscriptionStatus
from voxr.models import ChunkResult, RecordingSession
from voxr.transcription import ModelNotFoundError


class TestTranscribe:
    def test_returns_success_chunk_with_text_when_model_succeeds(self, mocker):

        mock_segment = MagicMock()
        mock_segment.text = "hello world"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], MagicMock())

        result = transcription.transcribe("audio.wav", mock_model)

        assert result.status == ChunkStatus.SUCCESS
        assert result.text == "hello world"

    def test_returns_failed_with_placeholder_when_model_always_raises(self, mocker):
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("model failure")

        result = transcription.transcribe("audio.wav", mock_model)

        assert result.status == ChunkStatus.FAILED_WITH_PLACEHOLDER

    def test_never_raises_exception_regardless_of_model_error(self, mocker):
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception("catastrophic failure")

        try:
            result = transcription.transcribe("audio.wav", mock_model)
        except Exception:
            assert False, "transcribe() should never raise an exception"

        assert isinstance(result, ChunkResult)

    def test_returns_success_when_model_fails_once_then_succeeds(self, mocker):
        mock_segment = MagicMock()
        mock_segment.text = "recovered text"
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = [
            RuntimeError("first failure"),
            ([mock_segment], MagicMock()),
        ]

        result = transcription.transcribe("audio.wav", mock_model)

        assert result.status == ChunkStatus.SUCCESS
        assert result.text == "recovered text"

    def test_retry_count_equals_2_when_all_attempts_fail(self, mocker):
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("always fails")

        result = transcription.transcribe("audio.wav", mock_model)

        assert result.retry_count == 2


def _make_session(audio_file_path="audio.wav"):
    return RecordingSession(
        session_id="test-session-001",
        start_time=0.0,
        end_time=1.0,
        duration_seconds=1.0,
        input_mode=InputMode.TOGGLE,
        audio_file_path=audio_file_path,
        status=SessionStatus.COMPLETED,
    )


class TestTranscribeSession:
    def test_returns_success_transcription_result_in_default_mode(self, mocker):
        mock_segment = MagicMock()
        mock_segment.text = "transcribed text"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], MagicMock())
        mock_config = MagicMock()
        mock_config.pipeline_mode_enabled = False

        result = transcription.transcribe_session(_make_session(), mock_model, mock_config)

        assert result.status == TranscriptionStatus.SUCCESS

    def test_full_text_equals_chunk_text_in_default_mode(self, mocker):
        mock_segment = MagicMock()
        mock_segment.text = "hello from whisper"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], MagicMock())
        mock_config = MagicMock()
        mock_config.pipeline_mode_enabled = False

        result = transcription.transcribe_session(_make_session(), mock_model, mock_config)

        assert result.full_text == result.chunks[0].text

    def test_produces_exactly_one_chunk_in_default_mode(self, mocker):
        mock_segment = MagicMock()
        mock_segment.text = "single chunk"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], MagicMock())
        mock_config = MagicMock()
        mock_config.pipeline_mode_enabled = False

        result = transcription.transcribe_session(_make_session(), mock_model, mock_config)

        assert len(result.chunks) == 1


class TestLoadModel:
    def test_returns_model_when_file_exists(self, tmp_path, mocker):
        model_file = tmp_path / "medium.bin"
        model_file.write_bytes(b"fake model")
        mocker.patch("voxr.transcription.MODELS_DIR", tmp_path)
        mocker.patch("voxr.transcription.WhisperModel", return_value=MagicMock())

        result = transcription.load_model("medium")

        assert result is not None

    def test_raises_model_not_found_error_when_file_missing(self, tmp_path, mocker):
        mocker.patch("voxr.transcription.MODELS_DIR", tmp_path)

        with pytest.raises(ModelNotFoundError):
            transcription.load_model("medium")
