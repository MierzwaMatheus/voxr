import uuid

from voxr.enums import ChunkStatus
from voxr.models import ChunkResult


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
