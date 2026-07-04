import sys
from unittest.mock import MagicMock

# Stub hardware-dependent libs so unit tests run without PortAudio/libsndfile
for _mod in ("sounddevice", "soundfile"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
