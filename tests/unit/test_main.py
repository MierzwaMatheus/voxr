import sys
from unittest.mock import MagicMock

if "pynput" not in sys.modules:
    sys.modules["pynput"] = MagicMock()
    sys.modules["pynput.keyboard"] = MagicMock()


def test_main_instantiates_voxr_app_and_calls_run(mocker):
    """main() cria VoxrApp e chama run()."""
    mock_app = MagicMock()
    mock_cls = mocker.patch("voxr.app.VoxrApp", return_value=mock_app)

    from voxr.__main__ import main
    main()

    mock_cls.assert_called_once()
    mock_app.run.assert_called_once()


def test_voxr_main_module_defines_main_function():
    """__main__.py exporta uma função main() chamável."""
    import importlib
    mod = importlib.import_module("voxr.__main__")
    assert callable(getattr(mod, "main", None))


def test_voxrapp_without_config_sets_hotkey_none():
    """VoxrApp(config=None) inicializa _hotkey como None (sem listener)."""
    from voxr.app import VoxrApp
    app = VoxrApp(config=None, model=MagicMock())
    assert app._hotkey is None
