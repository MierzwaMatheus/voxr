# Voxr Configuration Schema

Configuration is stored at `~/.config/voxr/config.json`. The file is created automatically on first run with default values.

## Example

```json
{
  "hotkey": "<alt>+v",
  "input_mode": "toggle",
  "model_name": "base",
  "transcription_language": "auto",
  "max_recording_seconds": 60,
  "vad_enabled": true,
  "pipeline_mode_enabled": false,
  "autostart_enabled": false,
  "interface_language": "pt-BR",
  "first_run_complete": false
}
```

## Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `hotkey` | string | `"<alt>+v"` | Global hotkey to start/stop recording. Uses pynput key notation (e.g. `"<ctrl>+<shift>+v"`). Must be non-empty. |
| `input_mode` | string enum | `"toggle"` | `"toggle"` — press once to start, press again to stop. `"ptt"` — hold to record, release to stop. |
| `model_name` | string enum | `"base"` | Whisper model size. One of: `tiny`, `base`, `small`, `medium`, `large-v3-turbo`. Larger models are more accurate but slower. |
| `transcription_language` | string | `"auto"` | Language code for transcription (e.g. `"pt"`, `"en"`). `"auto"` detects language automatically. |
| `max_recording_seconds` | integer | `60` | Maximum recording duration in seconds. Must be between `30` and `180`. |
| `vad_enabled` | boolean | `true` | Enable Voice Activity Detection to filter silence from recordings. |
| `pipeline_mode_enabled` | boolean | `false` | Reserved for future use. |
| `autostart_enabled` | boolean | `false` | Start Voxr automatically on login (requires system-level configuration). |
| `interface_language` | string | `"pt-BR"` | UI language code. |
| `first_run_complete` | boolean | `false` | Set to `true` after the first-run wizard completes. Do not edit manually. |

## Model files

Whisper models are stored at `~/.local/share/voxr/models/`. They are downloaded automatically on first use. The `model_name` field must match a downloaded model.

## Validation

The following constraints are enforced at load time:

- `hotkey` must be a non-empty string
- `max_recording_seconds` must be between 30 and 180 (inclusive)
- `model_name` must be one of the allowed values listed above

If the file is missing or contains invalid JSON, Voxr recreates it with default values.
