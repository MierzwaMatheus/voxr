from unittest.mock import MagicMock

from voxr import injection


class TestInjectText:
    def test_inject_text_returns_true_on_success(self, mocker):
        mock_run = mocker.patch("voxr.injection.subprocess.run")
        mock_run.return_value = MagicMock(returncode=0)

        result = injection.inject_text("hello world")

        mock_run.assert_called_once_with(
            ["xdotool", "type", "--clearmodifiers", "--", "hello world"],
            check=False,
        )
        assert result is True

    def test_inject_text_returns_false_when_xdotool_not_found(self, mocker):
        mocker.patch(
            "voxr.injection.subprocess.run",
            side_effect=FileNotFoundError,
        )

        result = injection.inject_text("hello world")

        assert result is False

    def test_inject_text_returns_false_when_xdotool_fails(self, mocker):
        mock_run = mocker.patch("voxr.injection.subprocess.run")
        mock_run.return_value = MagicMock(returncode=1)

        result = injection.inject_text("hello world")

        assert result is False
