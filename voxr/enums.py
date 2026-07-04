from enum import Enum


class InputMode(str, Enum):
    TOGGLE = "toggle"
    PTT = "ptt"


class SessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TranscriptionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ChunkStatus(str, Enum):
    SUCCESS = "success"
    FAILED_WITH_PLACEHOLDER = "failed_with_placeholder"


class AppState(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"
