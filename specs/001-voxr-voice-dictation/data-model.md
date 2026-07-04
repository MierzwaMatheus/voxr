# Data Model: Voxr Voice Dictation

**Branch**: `001-voxr-voice-dictation` | **Phase**: 1 | **Date**: 2026-07-04

Todas as entidades são in-memory (dataclasses Python). Não há banco de dados. Persistência apenas em `config.json` e arquivos `.wav` no cache.

---

## Entities

### RecordingSession

Representa uma única sessão de gravação, do hotkey press até conclusão ou cancelamento.

```python
@dataclass
class RecordingSession:
    session_id: str          # UUID4
    start_time: float        # time.time()
    end_time: float | None   # None enquanto gravando
    duration_seconds: float  # calculado no encerramento
    input_mode: InputMode    # InputMode.TOGGLE | InputMode.PTT
    audio_file_path: str     # ~/.cache/voxr/recordings/{session_id}.wav
    status: SessionStatus    # IN_PROGRESS | COMPLETED | CANCELLED
```

**State transitions**: `IN_PROGRESS` → `COMPLETED` (hotkey 2x ou timeout) | `CANCELLED` (Escape)

---

### TranscriptionResult

Representa a saída do processamento de uma RecordingSession.

```python
@dataclass
class TranscriptionResult:
    result_id: str                 # UUID4
    session_id: str                # FK → RecordingSession.session_id
    full_text: str                 # texto concatenado final (com placeholders se falha parcial)
    chunks: list[ChunkResult]      # lista de chunks (len=1 para modo padrão)
    status: TranscriptionStatus    # SUCCESS | PARTIAL | FAILED
    timestamp: float               # time.time() ao completar
```

---

### ChunkResult

Representa a transcrição de um único chunk de áudio (30s em modo pipeline, gravação inteira no modo padrão).

```python
@dataclass
class ChunkResult:
    chunk_id: str              # UUID4
    chunk_index: int           # 0-based order
    text: str                  # texto transcrito ou PLACEHOLDER se falhou
    confidence: float | None   # média de probabilidade dos segments (None se falhou)
    retry_count: int           # 0–2
    status: ChunkStatus        # SUCCESS | FAILED_WITH_PLACEHOLDER
```

**Placeholder**: `"[trecho não transcrito]"` — constante em `voxr/constants.py`

---

### Configuration

Preferências do usuário, persistidas em `~/.config/voxr/config.json`.

```python
@dataclass
class Configuration:
    hotkey: str                     # ex: "<alt>v"  (formato pynput Key)
    input_mode: InputMode           # TOGGLE | PTT
    model_name: str                 # "tiny"|"base"|"small"|"medium"|"large-v3-turbo"
    transcription_language: str     # "auto" ou código ISO 639-1 (ex: "pt", "en")
    max_recording_seconds: int      # 30–180, padrão 60
    vad_enabled: bool               # padrão True
    pipeline_mode_enabled: bool     # padrão False
    autostart_enabled: bool         # padrão False
    interface_language: str         # "pt-BR" | "en"
    first_run_complete: bool        # False → exibe setup wizard
```

**Validation rules**:
- `max_recording_seconds`: 30 ≤ value ≤ 180
- `model_name`: deve ser um dos valores aceitos
- `hotkey`: deve ser parseable pelo pynput

**Serialization**: `dataclasses.asdict()` → `json.dump()`. Enums serializadas como string.

---

## Enums

```python
class InputMode(str, Enum):
    TOGGLE = "toggle"
    PTT = "ptt"

class SessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TranscriptionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"

class ChunkStatus(str, Enum):
    SUCCESS = "success"
    FAILED_WITH_PLACEHOLDER = "failed_with_placeholder"

class AppState(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"  # microfone não detectado
```

---

## Armazenamento em Disco

| Local | Conteúdo | Retenção |
|---|---|---|
| `~/.config/voxr/config.json` | Configuration serializada | Permanente |
| `~/.cache/voxr/recordings/` | `{session_id}.wav` — áudio bruto de cada sessão | 24h (TTL automático) |
| `~/.local/share/voxr/models/` | Arquivos do modelo Whisper (gerenciado por huggingface_hub) | Permanente |

---

## Fluxo de Dados

```
[pynput hotkey] ──→ RecordingSession(IN_PROGRESS)
                         ↓
                    sounddevice capture → {session_id}.wav
                         ↓
                    RecordingSession(COMPLETED)
                         ↓
                    faster-whisper → ChunkResult(s)
                         ↓
                    TranscriptionResult(full_text)
                         ↓
                    xdotool type / clipboard
```
