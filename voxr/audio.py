import threading
import time
from pathlib import Path
from typing import Callable

import numpy as np

RECORDINGS_DIR = Path.home() / ".cache" / "voxr" / "recordings"

_SAMPLE_RATE = 16000
_CHANNELS = 1
_DTYPE = "float32"


def record(session, stop_event: threading.Event, max_seconds: int = 60) -> str:
    """Grava áudio até stop_event.set() ou max_seconds. Retorna path do WAV."""
    import sounddevice as sd
    import soundfile as sf

    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = str(RECORDINGS_DIR / f"{session.session_id}.wav")

    frames = []

    def _callback(indata, frames_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(samplerate=_SAMPLE_RATE, channels=_CHANNELS, dtype=_DTYPE, callback=_callback):
        start = time.time()
        while not stop_event.is_set():
            if time.time() - start >= max_seconds:
                break
            time.sleep(0.05)

    audio_data = np.concatenate(frames, axis=0) if frames else np.zeros((1, _CHANNELS), dtype=_DTYPE)
    sf.write(audio_path, audio_data, _SAMPLE_RATE)
    return audio_path


def is_microphone_available() -> bool:
    """True se pelo menos um dispositivo de input está disponível."""
    raise NotImplementedError


def list_devices() -> list[str]:
    """Retorna nomes dos dispositivos de áudio de input disponíveis."""
    raise NotImplementedError


def get_audio_level(callback: Callable[[float], None]):
    """Stream de monitoramento de nível de áudio. Caller fecha o stream."""
    raise NotImplementedError
