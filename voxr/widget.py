from typing import Optional

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk
    _HAS_GTK = True
except Exception:
    _HAS_GTK = False


class RecordingWidget:
    def __init__(self) -> None:
        self._visible: bool = False
        self._mode: Optional[str] = None
        self._window = None
        self._timer_id = None
        self._elapsed: float = 0.0
        self._max_seconds: int = 0
        self._countdown_active: bool = False
        self._animation_interval_ms: int = 50
        self._audio_stream = None

    def show_recording(self, audio_level_stream) -> None:
        self._mode = "recording"
        self._visible = True
        self._audio_stream = audio_level_stream
        if _HAS_GTK:
            self._create_window()
            self._start_animation()

    def show_processing(self) -> None:
        self._mode = "processing"
        if _HAS_GTK and self._window:
            self._window.queue_draw()

    def hide(self) -> None:
        self._visible = False
        self._mode = None
        if _HAS_GTK:
            self._stop_animation()
            if self._window:
                self._window.destroy()
                self._window = None

    def update_timer(self, elapsed: float, max_seconds: int) -> None:
        self._elapsed = elapsed
        self._max_seconds = max_seconds
        self._countdown_active = (max_seconds - elapsed) <= 10
        if _HAS_GTK and self._window:
            self._window.queue_draw()

    def _create_window(self) -> None:
        self._window = Gtk.Window(type=Gtk.WindowType.POPUP)
        self._window.set_decorated(False)
        self._window.set_keep_above(True)
        try:
            display = Gdk.Display.get_default()
            if display:
                seat = display.get_default_seat()
                pointer = seat.get_pointer()
                result = pointer.get_position()
                if len(result) == 3:
                    _, x, y = result
                    self._window.move(x + 16, y + 16)
        except Exception:
            pass
        self._window.show_all()

    def _start_animation(self) -> None:
        if _HAS_GTK:
            self._timer_id = GLib.timeout_add(50, self._redraw)

    def _stop_animation(self) -> None:
        if _HAS_GTK and self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _redraw(self) -> bool:
        if self._window and self._visible:
            self._window.queue_draw()
            return True
        return False
