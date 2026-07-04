# Voxr

Offline voice dictation for Linux via a global hotkey. Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

## Requirements

- Python 3.11+
- Linux with X11
- `xdotool` and `xclip`/`xsel` for text injection

## How to Run

### 1. Install system dependencies

```bash
sudo apt install xdotool xclip portaudio19-dev python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3-0.1
```

### 2. Install Python package

```bash
pip install -e ".[dev]"
```

### 3. Run

```bash
python3 -m voxr
```

Press the configured hotkey (default: `Alt+V`) to start recording. Press again to stop and insert the transcribed text into the active window.

> **Note:** Voxr requires an active X11 session (Wayland is not supported). Make sure a Whisper model is available at the path specified in `~/.config/voxr/config.json`.

## Installation (development)

```bash
pip install -e ".[dev]"
```

## Development

```bash
pytest tests/unit/ -v
pytest --cov=voxr --cov-fail-under=80
ruff check voxr/ tests/
```

## License

MIT
