import time
import uuid
from pathlib import Path

from faster_whisper import WhisperModel

from voxr.enums import ChunkStatus, TranscriptionStatus
from voxr.models import ChunkResult, TranscriptionResult

MODELS_DIR = Path.home() / ".local" / "share" / "voxr" / "models"


class ModelNotFoundError(Exception):
    pass


_model_cache: dict = {}


def load_model(model_name: str) -> WhisperModel:
    if model_name in _model_cache:
        return _model_cache[model_name]
    model_path = MODELS_DIR / f"{model_name}.bin"
    if not model_path.exists():
        raise ModelNotFoundError(f"Model '{model_name}' not found at {model_path}")
    model = WhisperModel(str(model_path), device="cpu", compute_type="int8")
    _model_cache[model_name] = model
    return model


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
