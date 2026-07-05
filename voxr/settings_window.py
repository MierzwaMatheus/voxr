from typing import Callable

from voxr.constants import MODEL_DIR
from voxr.models import Configuration, ModelInfo


def get_model_info(model_name: str) -> ModelInfo:
    model_bin = MODEL_DIR / model_name / "model.bin"
    if model_bin.exists():
        return ModelInfo(model_name=model_name, is_cached=True, path=str(model_bin))
    return ModelInfo(model_name=model_name, is_cached=False, path=None)


class SettingsWindow:
    def __init__(
        self,
        config: Configuration,
        on_apply: Callable[[Configuration], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self._config = config
        self._on_apply = on_apply
        self._on_cancel = on_cancel
        self._window = None

    def show(self) -> None:
        from gi.repository import Gtk
        if self._window is not None:
            self._window.present()
            return
        self._window = Gtk.Window()
        self._window.set_title("Voxr — Configurações")
        self._window.set_default_size(480, 360)

        notebook = Gtk.Notebook()
        notebook.append_page(self._build_general_tab(), Gtk.Label(label="Geral"))
        notebook.append_page(self._build_transcription_tab(), Gtk.Label(label="Transcrição"))
        notebook.append_page(self._build_performance_tab(), Gtk.Label(label="Performance"))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.pack_start(notebook, True, True, 0)
        box.pack_end(self._build_footer(), False, False, 0)

        self._window.add(box)
        self._window.connect("delete-event", self._on_delete)
        self._window.connect("key-press-event", self._on_window_key_press)
        self._window.show_all()

    def hide(self) -> None:
        if self._window is not None:
            self._window.destroy()
            self._window = None

    def set_sensitive(self, enabled: bool) -> None:
        if self._window is not None:
            self._window.set_sensitive(enabled)

    # --- Private tab builders (layout only — no logic) ---

    def _build_general_tab(self):
        from gi.repository import Gtk
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)

        hotkey_label = Gtk.Label(label="Hotkey:")
        hotkey_label.set_halign(Gtk.Align.START)
        self._hotkey_button = Gtk.Button(label=self._config.hotkey)
        box.pack_start(hotkey_label, False, False, 0)
        box.pack_start(self._hotkey_button, False, False, 0)

        return box

    def _build_transcription_tab(self):
        from gi.repository import Gtk
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)
        placeholder = Gtk.Label(label="Configurações de transcrição (US3)")
        placeholder.set_halign(Gtk.Align.START)
        box.pack_start(placeholder, False, False, 0)
        return box

    def _build_performance_tab(self):
        from gi.repository import Gtk
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)
        placeholder = Gtk.Label(label="Configurações de performance (US4)")
        placeholder.set_halign(Gtk.Align.START)
        box.pack_start(placeholder, False, False, 0)
        return box

    def _build_footer(self):
        from gi.repository import Gtk
        bar = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        bar.set_layout(Gtk.ButtonBoxStyle.END)
        bar.set_spacing(6)
        bar.set_border_width(8)

        cancel_btn = Gtk.Button(label="Cancelar")
        apply_btn = Gtk.Button(label="Aplicar")
        ok_btn = Gtk.Button(label="OK")

        cancel_btn.connect("clicked", lambda _: self._on_cancel_clicked())
        apply_btn.connect("clicked", lambda _: self._on_apply_clicked())
        ok_btn.connect("clicked", lambda _: self._on_ok_clicked())

        bar.pack_start(cancel_btn, False, False, 0)
        bar.pack_start(apply_btn, False, False, 0)
        bar.pack_start(ok_btn, False, False, 0)
        return bar

    # --- Internal event handlers ---

    def _on_cancel_clicked(self) -> None:
        self.hide()
        self._on_cancel()

    def _on_apply_clicked(self) -> None:
        self._on_apply(self._config)

    def _on_ok_clicked(self) -> None:
        self._on_apply(self._config)
        self.hide()

    def _on_delete(self, _widget, _event) -> bool:
        self._on_cancel_clicked()
        return True

    def _on_window_key_press(self, _widget, event) -> bool:
        from gi.repository import Gdk
        if event.keyval == Gdk.KEY_Escape:
            self._on_cancel_clicked()
            return True
        return False
