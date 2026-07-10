import dataclasses
from typing import Callable

from voxr.constants import MODEL_DIR, MODEL_SIZES_MB
from voxr.enums import InputMode
from voxr.models import Configuration, ModelInfo

_DISPLAY_NAMES: dict[str, str] = {
    "tiny": "Tiny",
    "base": "Base",
    "small": "Small",
    "medium": "Medium (padrão)",
    "large": "Large",
    "large-v2": "Large-v2",
}


def get_model_info(model_name: str) -> ModelInfo:
    model_bin = MODEL_DIR / model_name / "model.bin"
    is_cached = model_bin.exists()
    return ModelInfo(
        model_name=model_name,
        is_cached=is_cached,
        path=str(model_bin) if is_cached else None,
        display_name=_DISPLAY_NAMES.get(model_name, model_name),
        size_mb=MODEL_SIZES_MB.get(model_name, 0),
    )


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

    def update_recording_state(self, is_recording: bool) -> None:
        if hasattr(self, "_hotkey_button"):
            self._hotkey_button.set_sensitive(not is_recording)
            self._hotkey_button.set_tooltip_text("Gravação em andamento" if is_recording else "")

    # --- Private tab builders (layout only — no logic) ---

    def _build_general_tab(self):
        from gi.repository import Gtk

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)

        hotkey_label = Gtk.Label(label="Hotkey:")
        hotkey_label.set_halign(Gtk.Align.START)
        self._hotkey_button = Gtk.Button(label=self._config.hotkey)
        self._hotkey_button.connect("clicked", self._on_key_capture_clicked)
        self._hotkey_warning_label = Gtk.Label(label="")
        self._hotkey_warning_label.set_halign(Gtk.Align.START)

        input_label = Gtk.Label(label="Modo de entrada:")
        input_label.set_halign(Gtk.Align.START)
        self._input_mode_combo = Gtk.ComboBoxText()
        for mode in InputMode:
            self._input_mode_combo.append_text(mode.value)
        self._input_mode_combo.set_active(list(InputMode).index(self._config.input_mode))

        box.pack_start(hotkey_label, False, False, 0)
        box.pack_start(self._hotkey_button, False, False, 0)
        box.pack_start(self._hotkey_warning_label, False, False, 0)
        box.pack_start(input_label, False, False, 0)
        box.pack_start(self._input_mode_combo, False, False, 0)

        return box

    def _build_transcription_tab(self):
        from gi.repository import Gtk

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)

        _LANG_OPTIONS = [("auto", "Auto"), ("pt", "Português"), ("en", "English")]
        lang_label = Gtk.Label(label="Idioma de transcrição:")
        lang_label.set_halign(Gtk.Align.START)
        self._lang_combo = Gtk.ComboBoxText()
        for value, display in _LANG_OPTIONS:
            self._lang_combo.append_text(value)
        lang_values = [v for v, _ in _LANG_OPTIONS]
        active_lang = self._config.transcription_language
        idx = lang_values.index(active_lang) if active_lang in lang_values else 0
        self._lang_combo.set_active(idx)

        model_label = Gtk.Label(label="Modelo de transcrição:")
        model_label.set_halign(Gtk.Align.START)
        self._model_combo = Gtk.ComboBoxText()
        self._model_infos = {}
        model_keys = list(MODEL_SIZES_MB.keys())
        active_model_idx = 0
        for i, name in enumerate(model_keys):
            info = get_model_info(name)
            self._model_infos[i] = name
            status = "em cache" if info.is_cached else "requer download"
            entry = f"{info.display_name} ({info.size_mb} MB) — {status}"
            self._model_combo.append_text(entry)
            if name == self._config.model_name:
                active_model_idx = i

        self._model_combo.set_active(active_model_idx)
        self._model_combo.connect("changed", self._on_model_changed)

        self._model_status_label = Gtk.Label(label="")
        self._model_status_label.set_halign(Gtk.Align.START)

        box.pack_start(lang_label, False, False, 0)
        box.pack_start(self._lang_combo, False, False, 0)
        box.pack_start(model_label, False, False, 0)
        box.pack_start(self._model_combo, False, False, 0)
        box.pack_start(self._model_status_label, False, False, 0)
        return box

    def _build_performance_tab(self):
        from gi.repository import Gtk

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)

        # Slider max_recording_seconds
        slider_label = Gtk.Label(label="Tempo máximo de gravação:")
        slider_label.set_halign(Gtk.Align.START)
        adj = Gtk.Adjustment(
            value=self._config.max_recording_seconds,
            lower=30,
            upper=180,
            step_increment=30,
        )
        self._slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        self._slider.set_digits(0)
        self._slider.set_hexpand(True)
        self._slider_label = Gtk.Label(label=f"{int(self._config.max_recording_seconds)}s")
        self._slider_label.set_halign(Gtk.Align.START)
        self._slider.connect("value-changed", self._on_slider_changed)

        # Switch VAD
        vad_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vad_label = Gtk.Label(label="Filtrar silêncio (VAD)")
        vad_label.set_halign(Gtk.Align.START)
        self._vad_switch = Gtk.Switch()
        self._vad_switch.set_active(self._config.vad_enabled)
        vad_box.pack_start(vad_label, True, True, 0)
        vad_box.pack_start(self._vad_switch, False, False, 0)

        # Campos desabilitados (Fase 3/4)
        self._pipeline_check = Gtk.Switch()
        self._pipeline_check.set_active(self._config.pipeline_mode_enabled)
        self._pipeline_check.set_sensitive(False)
        self._pipeline_check.set_tooltip_text("Disponível na Fase 3")
        pipeline_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        pipeline_label = Gtk.Label(label="Modo pipeline")
        pipeline_label.set_halign(Gtk.Align.START)
        pipeline_box.pack_start(pipeline_label, True, True, 0)
        pipeline_box.pack_start(self._pipeline_check, False, False, 0)

        self._autostart_check = Gtk.Switch()
        self._autostart_check.set_active(self._config.autostart_enabled)
        self._autostart_check.set_sensitive(False)
        self._autostart_check.set_tooltip_text("Disponível na Fase 4")
        autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        autostart_label = Gtk.Label(label="Iniciar automaticamente")
        autostart_label.set_halign(Gtk.Align.START)
        autostart_box.pack_start(autostart_label, True, True, 0)
        autostart_box.pack_start(self._autostart_check, False, False, 0)

        box.pack_start(slider_label, False, False, 0)
        box.pack_start(self._slider, False, False, 0)
        box.pack_start(self._slider_label, False, False, 0)
        box.pack_start(vad_box, False, False, 0)
        box.pack_start(pipeline_box, False, False, 0)
        box.pack_start(autostart_box, False, False, 0)
        return box

    def _on_slider_changed(self, scale) -> None:
        value = int(scale.get_value())
        if hasattr(self, "_slider_label"):
            self._slider_label.set_text(f"{value}s")

    def _on_model_changed(self, combo) -> None:
        active = combo.get_active()
        if active < 0 or active not in self._model_infos:
            return
        model_name = self._model_infos[active]
        info = get_model_info(model_name)
        if info.is_cached:
            self._model_status_label.set_text("Em cache")
        else:
            self._model_status_label.set_text(f"Requer download (~{info.size_mb} MB)")

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
        _LANG_OPTIONS = ["auto", "pt", "en"]
        active = self._input_mode_combo.get_active()
        if active >= 0:
            self._config = dataclasses.replace(self._config, input_mode=list(InputMode)[active])
        if hasattr(self, "_lang_combo"):
            lang_idx = self._lang_combo.get_active()
            if 0 <= lang_idx < len(_LANG_OPTIONS):
                self._config = dataclasses.replace(
                    self._config, transcription_language=_LANG_OPTIONS[lang_idx]
                )
        if hasattr(self, "_slider"):
            self._config = dataclasses.replace(
                self._config, max_recording_seconds=int(self._slider.get_value())
            )
        if hasattr(self, "_vad_switch"):
            self._config = dataclasses.replace(
                self._config, vad_enabled=bool(self._vad_switch.get_active())
            )
        self._on_apply(self._config)

    def _on_ok_clicked(self) -> None:
        self._on_apply(self._config)
        self.hide()

    def _on_delete(self, _widget, _event) -> bool:
        self._on_cancel_clicked()
        return True

    def _on_key_capture_clicked(self, widget) -> None:
        widget.set_label("Pressione a combinação...")
        self._key_capture_handler = self._window.connect("key-press-event", self._on_key_press)

    def _on_key_press(self, _widget, event) -> bool:
        from gi.repository import Gdk

        _MODIFIER_MAP = [
            (Gdk.ModifierType.CONTROL_MASK, "<ctrl>"),
            (Gdk.ModifierType.MOD1_MASK, "<alt>"),
            (Gdk.ModifierType.SHIFT_MASK, "<shift>"),
            (Gdk.ModifierType.SUPER_MASK, "<super>"),
        ]
        mods = [label for mask, label in _MODIFIER_MAP if event.state & mask]
        key_name = Gdk.keyval_name(event.keyval).lower()
        if not mods:
            self._hotkey_warning_label.set_text("Use ao menos um modificador")
            return True
        hotkey = "+".join(mods + [key_name])
        _CONFLICT_KEYS = {"<ctrl>+c", "<ctrl>+v", "<ctrl>+z", "<ctrl>+x", "<ctrl>+a"}
        if hotkey in _CONFLICT_KEYS:
            self._hotkey_warning_label.set_text(
                f"Atenção: '{hotkey}' pode conflitar com atalhos do sistema"
            )
        else:
            self._hotkey_warning_label.set_text("")
        self._config = dataclasses.replace(self._config, hotkey=hotkey)
        self._hotkey_button.set_label(hotkey)
        if hasattr(self, "_key_capture_handler"):
            self._window.disconnect(self._key_capture_handler)
        return True

    def _on_download_error(self, error: str) -> None:
        from gi.repository import Gtk

        self.set_sensitive(True)
        if hasattr(self, "_model_combo") and hasattr(self, "_prev_model_index"):
            self._model_combo.set_active(self._prev_model_index)
        dialog = Gtk.MessageDialog(
            transient_for=self._window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=str(error),
        )
        dialog.run()
        dialog.destroy()

    def _on_download_complete(self, model_name: str) -> None:
        self.set_sensitive(True)
        if hasattr(self, "_progress_bar"):
            self._progress_bar.hide()
        new_config = dataclasses.replace(self._config, model_name=model_name)
        self._config = new_config
        self._on_apply(new_config)

    def _on_window_key_press(self, _widget, event) -> bool:
        from gi.repository import Gdk

        if event.keyval == Gdk.KEY_Escape:
            self._on_cancel_clicked()
            return True
        return False
