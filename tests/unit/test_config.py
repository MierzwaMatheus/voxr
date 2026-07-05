from unittest.mock import patch

import pytest

import voxr.config as config_module
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

    def test_default_hotkey_matches_pynput_format(self):
        # pynput hotkey format: one or more <modifier>+ followed by a key
        import re
        assert re.match(r"^(<[^>]+>\+)+\w+$", constants.DEFAULT_HOTKEY)

    def test_model_name_default_is_allowed(self):
        assert constants.DEFAULT_MODEL in constants.ALLOWED_MODELS


class TestConfigurationValidation:
    def _make_config(self, **overrides):
        defaults = {
            "hotkey": constants.DEFAULT_HOTKEY,
            "input_mode": InputMode.TOGGLE,
            "model_name": constants.DEFAULT_MODEL,
            "transcription_language": "auto",
            "max_recording_seconds": constants.DEFAULT_MAX_SECONDS,
            "vad_enabled": True,
            "pipeline_mode_enabled": False,
            "autostart_enabled": False,
            "interface_language": "pt-BR",
            "first_run_complete": False,
        }
        defaults.update(overrides)
        return Configuration(**defaults)

    def test_max_recording_seconds_below_30_raises(self):
        with pytest.raises(ValueError):
            self._make_config(max_recording_seconds=29)

    def test_max_recording_seconds_above_180_raises(self):
        with pytest.raises(ValueError):
            self._make_config(max_recording_seconds=181)

    def test_max_recording_seconds_at_30_is_valid(self):
        config = self._make_config(max_recording_seconds=30)
        assert config.max_recording_seconds == 30

    def test_max_recording_seconds_at_180_is_valid(self):
        config = self._make_config(max_recording_seconds=180)
        assert config.max_recording_seconds == 180

    def test_invalid_model_name_raises(self):
        with pytest.raises(ValueError):
            self._make_config(model_name="gpt-4")

    def test_each_allowed_model_is_valid(self):
        for model in constants.ALLOWED_MODELS:
            config = self._make_config(model_name=model)
            assert config.model_name == model

    def test_empty_hotkey_raises(self):
        with pytest.raises(ValueError):
            self._make_config(hotkey="")


class TestConfigLoad:
    def test_load_returns_configuration(self, tmp_path, monkeypatch):
        import voxr.config as config_module
        monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
        result = config_module.load()
        assert isinstance(result, Configuration)

    def test_load_creates_file_with_defaults_when_absent(self, tmp_path, monkeypatch):
        import voxr.config as config_module
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
        config_module.load()
        assert config_file.exists()

    def test_load_reads_existing_file(self, tmp_path, monkeypatch):
        import json

        import voxr.config as config_module
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
        data = {
            "hotkey": "<ctrl>+d",
            "input_mode": "toggle",
            "model_name": "small",
            "transcription_language": "pt",
            "max_recording_seconds": 90,
            "vad_enabled": False,
            "pipeline_mode_enabled": False,
            "autostart_enabled": False,
            "interface_language": "pt-BR",
            "first_run_complete": True,
        }
        config_file.write_text(json.dumps(data))
        result = config_module.load()
        assert result.model_name == "small"
        assert result.max_recording_seconds == 90
        assert result.vad_enabled is False

    def test_load_never_raises_file_not_found(self, tmp_path, monkeypatch):
        import voxr.config as config_module
        monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "nonexistent.json")
        try:
            config_module.load()
        except FileNotFoundError:
            pytest.fail("load() raised FileNotFoundError")

    def test_load_never_raises_json_decode_error(self, tmp_path, monkeypatch):
        import voxr.config as config_module
        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid json !!!")
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
        try:
            config_module.load()
        except Exception as e:
            if "JSONDecodeError" in type(e).__name__:
                pytest.fail("load() raised JSONDecodeError")

    def test_load_returns_default_values_when_json_is_corrupted(self, tmp_path, monkeypatch):
        import voxr.config as config_module
        config_file = tmp_path / "config.json"
        config_file.write_text("{ not valid json !!! }")
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
        result = config_module.load()
        assert isinstance(result, Configuration)
        assert result.model_name == constants.DEFAULT_MODEL
        assert result.hotkey == constants.DEFAULT_HOTKEY
        assert result.max_recording_seconds == constants.DEFAULT_MAX_SECONDS
        assert result.vad_enabled is True

    def test_load_propagates_permission_error(self, tmp_path, monkeypatch):
        """Unexpected OS errors must not be silently swallowed."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
        with patch.object(config_file.__class__, "read_text", side_effect=PermissionError("no access")):
            with pytest.raises(PermissionError):
                config_module.load()

    def test_get_default_returns_configuration(self):
        result = config_module.get_default()
        assert isinstance(result, Configuration)

    def test_get_default_has_expected_defaults(self):
        result = config_module.get_default()
        assert result.max_recording_seconds == constants.DEFAULT_MAX_SECONDS
        assert result.vad_enabled is True
        assert result.model_name == constants.DEFAULT_MODEL


class TestConfigSave:
    def _default_config(self):
        from voxr.config import get_default
        return get_default()

    def test_save_persists_as_valid_json(self, tmp_path, monkeypatch):
        import json

        import voxr.config as config_module
        monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
        config = self._default_config()
        config_module.save(config)
        raw = (tmp_path / "config.json").read_text()
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_save_creates_parent_directory(self, tmp_path, monkeypatch):
        import voxr.config as config_module
        config_file = tmp_path / "nested" / "dir" / "config.json"
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
        config = self._default_config()
        config_module.save(config)
        assert config_file.exists()

    def test_saved_file_can_be_read_back_with_load(self, tmp_path, monkeypatch):
        import voxr.config as config_module
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
        config = self._default_config()
        config.model_name = "small"
        config_module.save(config)
        loaded = config_module.load()
        assert loaded.model_name == "small"

    def test_save_uses_atomic_write(self, tmp_path, monkeypatch):
        import voxr.config as config_module
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
        config = self._default_config()
        config_module.save(config)
        # tmp file should not exist after successful save
        assert not (tmp_path / "config.tmp").exists()
        assert config_file.exists()

    def test_save_preserves_all_fields(self, tmp_path, monkeypatch):
        import json

        import voxr.config as config_module
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
        config = self._default_config()
        config_module.save(config)
        data = json.loads(config_file.read_text())
        expected_keys = {
            "hotkey", "input_mode", "model_name", "transcription_language",
            "max_recording_seconds", "vad_enabled", "pipeline_mode_enabled",
            "autostart_enabled", "interface_language", "first_run_complete",
        }
        assert expected_keys == set(data.keys())
