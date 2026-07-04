import sys
from unittest.mock import MagicMock

# Stub GTK/GLib/GDK so tests run without a display
gi_mock = MagicMock()
sys.modules.setdefault("gi", gi_mock)
sys.modules.setdefault("gi.repository", gi_mock.repository)
sys.modules.setdefault("gi.repository.Gtk", gi_mock.repository.Gtk)
sys.modules.setdefault("gi.repository.Gdk", gi_mock.repository.Gdk)
sys.modules.setdefault("gi.repository.GLib", gi_mock.repository.GLib)
sys.modules.setdefault("gi.repository.cairo", gi_mock.repository.cairo)

from voxr.widget import RecordingWidget


def make_widget() -> RecordingWidget:
    return RecordingWidget()


class TestRecordingWidgetAnimation:
    def test_show_recording_starts_animation_timer(self):
        widget = make_widget()
        widget.show_recording(MagicMock())
        assert widget._animation_interval_ms == 50

    def test_hide_stops_animation(self):
        widget = make_widget()
        widget.show_recording(MagicMock())
        widget.hide()
        assert widget._timer_id is None

    def test_show_processing_switches_mode_for_spinner(self):
        widget = make_widget()
        widget.show_recording(MagicMock())
        widget.show_processing()
        assert widget._mode == "processing"

    def test_show_recording_stores_audio_stream(self):
        widget = make_widget()
        stream = MagicMock()
        widget.show_recording(stream)
        assert widget._audio_stream is stream


class TestRecordingWidgetUpdateTimer:
    def test_update_timer_stores_elapsed_and_max(self):
        widget = make_widget()
        widget.show_recording(MagicMock())
        widget.update_timer(elapsed=15.0, max_seconds=60)
        assert widget._elapsed == 15.0
        assert widget._max_seconds == 60

    def test_update_timer_countdown_flag_set_in_last_10s(self):
        widget = make_widget()
        widget.show_recording(MagicMock())
        widget.update_timer(elapsed=52.0, max_seconds=60)
        assert widget._countdown_active is True

    def test_update_timer_countdown_not_set_before_last_10s(self):
        widget = make_widget()
        widget.show_recording(MagicMock())
        widget.update_timer(elapsed=40.0, max_seconds=60)
        assert widget._countdown_active is False


class TestRecordingWidgetShowHide:
    def test_show_recording_marks_widget_as_visible(self):
        widget = make_widget()
        audio_stream = MagicMock()
        widget.show_recording(audio_stream)
        assert widget._visible is True

    def test_hide_marks_widget_as_not_visible(self):
        widget = make_widget()
        audio_stream = MagicMock()
        widget.show_recording(audio_stream)
        widget.hide()
        assert widget._visible is False

    def test_show_processing_switches_to_processing_mode(self):
        widget = make_widget()
        widget.show_recording(MagicMock())
        widget.show_processing()
        assert widget._mode == "processing"

    def test_show_recording_sets_mode_to_recording(self):
        widget = make_widget()
        widget.show_recording(MagicMock())
        assert widget._mode == "recording"

    def test_hide_resets_mode(self):
        widget = make_widget()
        widget.show_recording(MagicMock())
        widget.hide()
        assert widget._mode is None
