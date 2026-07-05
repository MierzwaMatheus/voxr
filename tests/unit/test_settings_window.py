import dataclasses
import sys
from unittest.mock import MagicMock

import pytest

# Stub GTK so tests run without a display.
# gi.repository.Gtk must be accessible both via sys.modules AND as an attribute of
# gi.repository (since `from gi.repository import Gtk` resolves via the parent object).
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


from voxr.enums import InputMode  # noqa: E402
from voxr.models import Configuration  # noqa: E402
from voxr.settings_window import get_model_info  # noqa: E402


@pytest.fixture
def cfg() -> Configuration:
    return Configuration(
        hotkey="<alt>+v",
        input_mode=InputMode.TOGGLE,
        model_name="medium",
        transcription_language="auto",
        max_recording_seconds=60,
        vad_enabled=False,
        pipeline_mode_enabled=False,
        autostart_enabled=False,
        interface_language="pt-BR",
        first_run_complete=True,
    )


# --- T086: ModelInfo / get_model_info ---

def test_get_model_info_cached(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    model_subdir = model_dir / "medium"
    model_subdir.mkdir()
    (model_subdir / "model.bin").write_bytes(b"fake")

    import voxr.settings_window as sw
    monkeypatch.setattr(sw, "MODEL_DIR", model_dir)

    info = get_model_info("medium")
    assert info.is_cached is True
    assert info.model_name == "medium"
    assert info.path is not None


def test_get_model_info_not_cached(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()

    import voxr.settings_window as sw
    monkeypatch.setattr(sw, "MODEL_DIR", model_dir)

    info = get_model_info("medium")
    assert info.is_cached is False
    assert info.path is None


# --- US1 Tests (T095-T100): SettingsWindow GTK behavior ---

from unittest.mock import MagicMock  # noqa: E402

from voxr.settings_window import SettingsWindow  # noqa: E402


def _gtk():
    """Return the shared Gtk mock from sys.modules."""
    return sys.modules["gi.repository.Gtk"]


# T095: show() creates window with correct title and calls show_all
def test_show_creates_window_with_correct_title(cfg):
    gtk = _gtk()
    gtk.reset_mock()
    window = MagicMock()
    gtk.Window.return_value = window

    sw = SettingsWindow(cfg, on_apply=MagicMock(), on_cancel=MagicMock())
    sw.show()

    window.set_title.assert_called_with("Voxr — Configurações")
    window.show_all.assert_called()


# T096: show() appends 3 pages to Gtk.Notebook
def test_show_creates_notebook_with_3_tabs(cfg):
    gtk = _gtk()
    gtk.reset_mock()
    window = MagicMock()
    notebook = MagicMock()
    gtk.Window.return_value = window
    gtk.Notebook.return_value = notebook

    sw = SettingsWindow(cfg, on_apply=MagicMock(), on_cancel=MagicMock())
    sw.show()

    assert notebook.append_page.call_count == 3


# T097: hide() calls window.destroy(); on_cancel does not call on_apply
def test_hide_destroys_window_and_cancel_does_not_call_apply(cfg):
    gtk = _gtk()
    gtk.reset_mock()
    window = MagicMock()
    gtk.Window.return_value = window
    on_apply = MagicMock()
    on_cancel = MagicMock()

    sw = SettingsWindow(cfg, on_apply=on_apply, on_cancel=on_cancel)
    sw.show()
    sw.hide()

    window.destroy.assert_called()
    on_apply.assert_not_called()


# T099: widgets reflect cfg values at init time (FR-010c)
def test_widgets_reflect_config_values_at_init(cfg):
    sw = SettingsWindow(cfg, on_apply=MagicMock(), on_cancel=MagicMock())
    assert sw._config.hotkey == cfg.hotkey
    assert sw._config.model_name == cfg.model_name
    assert sw._config.max_recording_seconds == cfg.max_recording_seconds


# T107: clicar botão hotkey muda label e conecta key-press-event
def test_hotkey_button_click_enters_capture_mode(cfg):
    gtk = _gtk()
    gtk.reset_mock()
    window = MagicMock()
    hotkey_button = MagicMock()
    gtk.Window.return_value = window
    gtk.Button.return_value = hotkey_button

    sw = SettingsWindow(cfg, on_apply=MagicMock(), on_cancel=MagicMock())
    sw.show()

    # Encontrar o callable conectado ao sinal "clicked" do botão de hotkey
    clicked_calls = [
        call for call in hotkey_button.connect.call_args_list
        if call.args[0] == "clicked"
    ]
    assert clicked_calls, "Botão de hotkey não conectou sinal 'clicked'"
    clicked_handler = clicked_calls[0].args[1]

    # Simular clique
    clicked_handler(hotkey_button)

    hotkey_button.set_label.assert_called_with("Pressione a combinação...")
    key_press_calls = [
        call for call in window.connect.call_args_list
        if call.args[0] == "key-press-event"
    ]
    assert key_press_calls, "Janela não conectou 'key-press-event' após clique no botão"


# T108: simular GdkEventKey Ctrl+Shift+d → campo exibe "<ctrl>+<shift>+d"
def test_key_press_ctrl_shift_d_updates_hotkey(cfg):
    gtk = _gtk()
    gdk = sys.modules["gi.repository.Gdk"]
    gtk.reset_mock()
    gdk.ModifierType.CONTROL_MASK = 4
    gdk.ModifierType.SHIFT_MASK = 1
    gdk.ModifierType.MOD1_MASK = 8
    gdk.ModifierType.SUPER_MASK = 67108864
    gdk.keyval_name.return_value = "d"

    window = MagicMock()
    hotkey_button = MagicMock()
    gtk.Window.return_value = window
    gtk.Button.return_value = hotkey_button

    sw = SettingsWindow(cfg, on_apply=MagicMock(), on_cancel=MagicMock())
    sw.show()

    event = MagicMock()
    event.state = 4 | 1  # CONTROL_MASK | SHIFT_MASK

    sw._on_key_press(MagicMock(), event)

    hotkey_button.set_label.assert_called_with("<ctrl>+<shift>+d")
    assert sw._config.hotkey == "<ctrl>+<shift>+d"


# T109: tecla sem modificador → aviso "Use ao menos um modificador"
def test_key_press_without_modifier_shows_warning(cfg):
    gtk = _gtk()
    gdk = sys.modules["gi.repository.Gdk"]
    gtk.reset_mock()
    gdk.ModifierType.CONTROL_MASK = 4
    gdk.ModifierType.SHIFT_MASK = 1
    gdk.ModifierType.MOD1_MASK = 8
    gdk.ModifierType.SUPER_MASK = 67108864
    gdk.keyval_name.return_value = "a"

    window = MagicMock()
    hotkey_button = MagicMock()
    gtk.Window.return_value = window
    gtk.Button.return_value = hotkey_button

    sw = SettingsWindow(cfg, on_apply=MagicMock(), on_cancel=MagicMock())
    sw.show()

    event = MagicMock()
    event.state = 0  # sem modificador

    sw._on_key_press(MagicMock(), event)

    sw._hotkey_warning_label.set_text.assert_called_with("Use ao menos um modificador")
    assert sw._config.hotkey == "<alt>+v"  # não mudou


# T111/T114: aba Geral tem warning label vazio por padrão
def test_general_tab_has_empty_warning_label_by_default(cfg):
    gtk = _gtk()
    gtk.reset_mock()
    window = MagicMock()
    gtk.Window.return_value = window

    sw = SettingsWindow(cfg, on_apply=MagicMock(), on_cancel=MagicMock())
    sw.show()

    assert hasattr(sw, "_hotkey_warning_label")
    # label criado com texto vazio
    warning_label_calls = [
        call for call in gtk.Label.call_args_list
        if call.kwargs.get("label") == ""
    ]
    assert warning_label_calls, "Gtk.Label(label='') não foi criado para o warning"


# T115: combo de input_mode criado com índice correto
def test_input_mode_combo_created_with_correct_active(cfg):
    gtk = _gtk()
    gtk.reset_mock()
    window = MagicMock()
    combo = MagicMock()
    gtk.Window.return_value = window
    gtk.ComboBoxText.return_value = combo

    sw = SettingsWindow(cfg, on_apply=MagicMock(), on_cancel=MagicMock())
    sw.show()

    from voxr.enums import InputMode
    expected_index = list(InputMode).index(InputMode.TOGGLE)
    combo.set_active.assert_called_with(expected_index)


# T126: _on_download_complete sets sensitive, hides progress bar, calls on_apply
def test_on_download_complete_enables_ui_and_calls_on_apply(cfg):
    on_apply = MagicMock()
    sw = SettingsWindow(cfg, on_apply=on_apply, on_cancel=MagicMock())
    sw._window = MagicMock()
    sw._progress_bar = MagicMock()
    sw._config = dataclasses.replace(cfg, model_name="medium")

    sw._on_download_complete("medium")

    sw._window.set_sensitive.assert_called_with(True)
    sw._progress_bar.hide.assert_called()
    on_apply.assert_called_once()
    called_cfg = on_apply.call_args[0][0]
    assert called_cfg.model_name == "medium"


# T127: _on_download_error restores UI, restores combo selection, shows MessageDialog
def test_on_download_error_enables_ui_and_shows_dialog(cfg):
    gtk = _gtk()
    gtk.reset_mock()
    on_apply = MagicMock()
    sw = SettingsWindow(cfg, on_apply=on_apply, on_cancel=MagicMock())
    sw._window = MagicMock()
    sw._progress_bar = MagicMock()
    sw._model_combo = MagicMock()
    sw._prev_model_index = 2

    sw._on_download_error("timeout error")

    sw._window.set_sensitive.assert_called_with(True)
    sw._model_combo.set_active.assert_called_with(2)
    gtk.MessageDialog.assert_called()
    dialog = gtk.MessageDialog.return_value
    dialog.run.assert_called()
    dialog.destroy.assert_called()
    on_apply.assert_not_called()


# T100: second call to show() calls present() on existing window, does not recreate
def test_second_show_calls_present_not_recreate(cfg):
    gtk = _gtk()
    gtk.reset_mock()
    window = MagicMock()
    gtk.Window.return_value = window

    sw = SettingsWindow(cfg, on_apply=MagicMock(), on_cancel=MagicMock())
    sw.show()
    initial_call_count = gtk.Window.call_count
    sw.show()

    assert gtk.Window.call_count == initial_call_count
    window.present.assert_called()
