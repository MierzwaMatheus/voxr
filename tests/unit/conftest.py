import sys
from unittest.mock import MagicMock

# Stub hardware-dependent libs so unit tests run without PortAudio/libsndfile
for _mod in ("sounddevice", "soundfile", "faster_whisper"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Stub GTK so unit tests run without a display.
# gi.repository.Gtk must also be reachable as an *attribute* of gi.repository,
# because `from gi.repository import Gtk` resolves via the parent object — not only
# via sys.modules["gi.repository.Gtk"].
if "gi" not in sys.modules:
    _gi_mock = MagicMock()
    _gtk_mock = MagicMock()
    _gdk_mock = MagicMock()
    _glib_mock = MagicMock()
    _gi_mock.repository.Gtk = _gtk_mock
    _gi_mock.repository.Gdk = _gdk_mock
    _gi_mock.repository.GLib = _glib_mock
    sys.modules["gi"] = _gi_mock
    sys.modules["gi.repository"] = _gi_mock.repository
    sys.modules["gi.repository.Gtk"] = _gtk_mock
    sys.modules["gi.repository.Gdk"] = _gdk_mock
    sys.modules["gi.repository.GLib"] = _glib_mock
