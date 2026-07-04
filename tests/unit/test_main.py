import sys
from unittest.mock import MagicMock


def test_main_instantiates_voxr_app_and_calls_run(mocker):
    """main() cria VoxrApp e chama run()."""
    mock_app = MagicMock()
    mock_cls = mocker.patch("voxr.__main__.VoxrApp", return_value=mock_app)

    from voxr.__main__ import main
    main()

    mock_cls.assert_called_once()
    mock_app.run.assert_called_once()


def test_voxr_module_is_executable():
    """O módulo pode ser invocado via -m voxr sem ImportError."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-c", "import voxr.__main__"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
