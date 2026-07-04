# Voxr

Offline voice dictation for Linux via a global hotkey. Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

## Requirements

- Python 3.11+
- Linux with X11
- `xdotool` and `xclip`/`xsel` for text injection

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```bash
python -m voxr
```

Press the configured hotkey (default: `Alt+V`) to start recording. Press again to transcribe and insert text into the active window.

## Development

```bash
pytest tests/unit/ -v
pytest --cov=voxr --cov-fail-under=80
ruff check voxr/ tests/
```

## License

MIT
