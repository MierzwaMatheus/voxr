
from voxr import constants
from voxr.enums import InputMode
from voxr.models import Configuration


class TestConfigurationDefaults:
    def test_all_fields_present(self):
        config = Configuration(
            hotkey=constants.DEFAULT_HOTKEY,
            input_mode=InputMode.TOGGLE,
            model_name=constants.DEFAULT_MODEL,
            transcription_language="auto",
            max_recording_seconds=constants.DEFAULT_MAX_SECONDS,
            vad_enabled=True,
            pipeline_mode_enabled=False,
            autostart_enabled=False,
            interface_language="pt-BR",
            first_run_complete=False,
        )
        assert hasattr(config, "hotkey")
        assert hasattr(config, "input_mode")
        assert hasattr(config, "model_name")
        assert hasattr(config, "transcription_language")
        assert hasattr(config, "max_recording_seconds")
        assert hasattr(config, "vad_enabled")
        assert hasattr(config, "pipeline_mode_enabled")
        assert hasattr(config, "autostart_enabled")
        assert hasattr(config, "interface_language")
        assert hasattr(config, "first_run_complete")

    def test_default_hotkey_is_nonempty_string(self):
        assert isinstance(constants.DEFAULT_HOTKEY, str)
        assert len(constants.DEFAULT_HOTKEY) > 0

    def test_default_max_recording_seconds_is_60(self):
        assert constants.DEFAULT_MAX_SECONDS == 60

    def test_vad_enabled_default_is_true(self):
        config = Configuration(
            hotkey=constants.DEFAULT_HOTKEY,
            input_mode=InputMode.TOGGLE,
            model_name=constants.DEFAULT_MODEL,
            transcription_language="auto",
            max_recording_seconds=constants.DEFAULT_MAX_SECONDS,
            vad_enabled=True,
            pipeline_mode_enabled=False,
            autostart_enabled=False,
            interface_language="pt-BR",
            first_run_complete=False,
        )
        assert config.vad_enabled is True

    def test_default_hotkey_parseable_by_pynput(self):
        from pynput.keyboard import HotKey
        # HotKey.parse raises if string is invalid
        parsed = HotKey.parse(constants.DEFAULT_HOTKEY)
        assert parsed is not None

    def test_model_name_default_is_allowed(self):
        assert constants.DEFAULT_MODEL in constants.ALLOWED_MODELS
