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
# This is enforced unconditionally so it holds even when another conftest (e.g.
# the integration one) already registered a simpler MagicMock for gi.
_gtk_mock = sys.modules.get("gi.repository.Gtk") or MagicMock()
_gdk_mock = sys.modules.get("gi.repository.Gdk") or MagicMock()
_glib_mock = sys.modules.get("gi.repository.GLib") or MagicMock()
_gi_repo = sys.modules.get("gi.repository") or MagicMock()
_gi_repo.Gtk = _gtk_mock
_gi_repo.Gdk = _gdk_mock
_gi_repo.GLib = _glib_mock
_gi_mock = sys.modules.get("gi") or MagicMock()
_gi_mock.repository = _gi_repo
sys.modules.setdefault("gi", _gi_mock)
sys.modules["gi.repository"] = _gi_repo
sys.modules["gi.repository.Gtk"] = _gtk_mock
sys.modules["gi.repository.Gdk"] = _gdk_mock
sys.modules["gi.repository.GLib"] = _glib_mock
