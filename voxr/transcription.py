import time
import uuid

from voxr.enums import ChunkStatus, TranscriptionStatus
from voxr.models import ChunkResult, TranscriptionResult


_MAX_RETRIES = 2
_PLACEHOLDER_TEXT = "[transcrição indisponível]"


def transcribe(audio_path: str, model, language: str = "auto", vad_filter: bool = True) -> ChunkResult:
    last_exc = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            segments, _ = model.transcribe(audio_path, language=language, vad_filter=vad_filter)
            text = "".join(s.text for s in segments)
            return ChunkResult(
                chunk_id=str(uuid.uuid4()),
                chunk_index=0,
                text=text,
                confidence=None,
                retry_count=attempt,
                status=ChunkStatus.SUCCESS,
            )
        except Exception as exc:
            last_exc = exc

    return ChunkResult(
        chunk_id=str(uuid.uuid4()),
        chunk_index=0,
        text=_PLACEHOLDER_TEXT,
        confidence=None,
        retry_count=_MAX_RETRIES,
        status=ChunkStatus.FAILED_WITH_PLACEHOLDER,
    )


def transcribe_session(session, model, config) -> TranscriptionResult:
    chunk = transcribe(session.audio_file_path, model)
    full_text = chunk.text
    return TranscriptionResult(
        result_id=str(uuid.uuid4()),
        session_id=session.session_id,
        full_text=full_text,
        chunks=[chunk],
        status=TranscriptionStatus.SUCCESS,
        timestamp=time.time(),
    )
