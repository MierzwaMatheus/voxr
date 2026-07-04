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
            time.sleep(0.05)  # 50ms: low CPU cost, ≤50ms stop latency

    audio_data = np.concatenate(frames, axis=0) if frames else np.zeros((1, _CHANNELS), dtype=_DTYPE)
    sf.write(audio_path, audio_data, _SAMPLE_RATE)
    return audio_path


def is_microphone_available() -> bool:
    """True se pelo menos um dispositivo de input está disponível."""
    import sounddevice as sd

    try:
        devices = sd.query_devices()
        return any(d.get("max_input_channels", 0) > 0 for d in devices)
    except Exception:
        return False


def list_devices() -> list[str]:
    """Retorna nomes dos dispositivos de áudio de input disponíveis."""
    import sounddevice as sd

    devices = sd.query_devices()
    return [d["name"] for d in devices if d.get("max_input_channels", 0) > 0]


def get_audio_level(callback: Callable[[float], None]):
    """Stream de monitoramento de nível de áudio. Caller fecha o stream."""
    raise NotImplementedError


def cleanup_old_recordings(
    recordings_dir: Path = RECORDINGS_DIR,
    max_age_seconds: int = 86400,
) -> None:
    """Deleta arquivos WAV com mtime superior a max_age_seconds."""
    if not recordings_dir.exists():
        return
    cutoff = time.time() - max_age_seconds
    for f in recordings_dir.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)


def start_cache_cleanup_daemon(
    recordings_dir: Path = RECORDINGS_DIR,
    max_age_seconds: int = 86400,
    interval_seconds: int = 3600,
) -> threading.Thread:
    """Inicia thread daemon que limpa gravações antigas a cada interval_seconds."""

    def _run():
        while True:
            cleanup_old_recordings(recordings_dir=recordings_dir, max_age_seconds=max_age_seconds)
            time.sleep(interval_seconds)

    t = threading.Thread(target=_run, daemon=True, name="voxr-cache-cleanup")
    t.start()
    return t
