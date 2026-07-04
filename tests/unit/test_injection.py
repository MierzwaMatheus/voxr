from unittest.mock import MagicMock

from voxr import injection


class TestInjectText:
    def test_inject_text_returns_true_on_success(self, mocker):
        mock_run = mocker.patch("voxr.injection.subprocess.run")
        mock_run.return_value = MagicMock(returncode=0)

        result = injection.inject_text("hello world")

        mock_run.assert_called_once_with(
            ["xdotool", "type", "--clearmodifiers", "--delay", "20", "--", "hello world"],
            check=False,
            timeout=10,
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


class TestCopyToClipboard:
    def test_copy_to_clipboard_uses_xclip_when_available(self, mocker):
        mock_run = mocker.patch("voxr.injection.subprocess.run")

        injection.copy_to_clipboard("hello world")

        mock_run.assert_called_once_with(
            ["xclip", "-selection", "clipboard"],
            input="hello world",
            text=True,
            check=False,
        )

    def test_copy_to_clipboard_falls_back_to_xsel_when_xclip_not_found(self, mocker):
        def run_side_effect(cmd, **kwargs):
            if cmd[0] == "xclip":
                raise FileNotFoundError
            return MagicMock(returncode=0)

        mocker.patch("voxr.injection.subprocess.run", side_effect=run_side_effect)

        injection.copy_to_clipboard("hello world")


class TestInsertOrClipboard:
    def test_insert_or_clipboard_returns_injected_when_inject_text_succeeds(self, mocker):
        mocker.patch("voxr.injection.inject_text", return_value=True)
        mock_copy = mocker.patch("voxr.injection.copy_to_clipboard")

        result = injection.insert_or_clipboard("hello world")

        assert result == "injected"
        mock_copy.assert_not_called()

    def test_insert_or_clipboard_copies_and_returns_clipboard_when_inject_fails(self, mocker):
        mocker.patch("voxr.injection.inject_text", return_value=False)
        mock_copy = mocker.patch("voxr.injection.copy_to_clipboard")

        result = injection.insert_or_clipboard("hello world")

        assert result == "clipboard"
        mock_copy.assert_called_once_with("hello world")
