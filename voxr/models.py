from dataclasses import dataclass

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


@dataclass
class RecordingSession:
    session_id: str
    start_time: float
    end_time: float | None
    duration_seconds: float
    input_mode: InputMode
    audio_file_path: str
    status: SessionStatus
