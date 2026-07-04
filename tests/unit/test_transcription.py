from unittest.mock import MagicMock

from voxr import transcription
from voxr.enums import ChunkStatus
from voxr.models import ChunkResult


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
