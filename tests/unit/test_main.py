import subprocess
import sys


def test_voxr_module_runs_and_prints_starting():
    result = subprocess.run(
        [sys.executable, "-m", "voxr"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Voxr starting" in result.stdout


def test_main_function_is_importable_and_callable(capsys):
    from voxr.__main__ import main
    assert callable(main)
    main()
    captured = capsys.readouterr()
    assert "Voxr starting" in captured.out
