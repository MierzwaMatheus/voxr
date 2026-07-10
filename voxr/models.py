from dataclasses import dataclass

from voxr.constants import ALLOWED_MODELS
from voxr.enums import ChunkStatus, InputMode, SessionStatus, TranscriptionStatus


@dataclass
class ChunkResult:
    chunk_id: str
    chunk_index: int
    text: str
    confidence: float | None
    retry_count: int
    status: ChunkStatus


@dataclass
class TranscriptionResult:
    result_id: str
    session_id: str
    full_text: str
    chunks: list[ChunkResult]
    status: TranscriptionStatus
    timestamp: float


@dataclass
class Configuration:
    hotkey: str
    input_mode: InputMode
    model_name: str
    transcription_language: str
    max_recording_seconds: int
    vad_enabled: bool
    pipeline_mode_enabled: bool
    autostart_enabled: bool
    interface_language: str
    first_run_complete: bool

    def __post_init__(self):
        if not self.hotkey:
            raise ValueError("hotkey must be a non-empty string")
        if not (30 <= self.max_recording_seconds <= 180):
            raise ValueError("max_recording_seconds must be between 30 and 180")
        if self.model_name not in ALLOWED_MODELS:
            raise ValueError(f"model_name must be one of {ALLOWED_MODELS}")


@dataclass
class ModelInfo:
    model_name: str
    is_cached: bool
    path: str | None = None
    display_name: str = ""
    size_mb: int = 0


@dataclass
class DownloadProgress:
    downloaded_bytes: int
    total_bytes: int


@dataclass
class RecordingSession:
    session_id: str
    start_time: float
    end_time: float | None
    duration_seconds: float
    input_mode: InputMode
    audio_file_path: str
    status: SessionStatus
