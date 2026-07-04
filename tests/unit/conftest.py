import sys
from unittest.mock import MagicMock

# Stub hardware-dependent libs so unit tests run without PortAudio/libsndfile
for _mod in ("sounddevice", "soundfile", "faster_whisper"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
