# Module Interface Contracts

**Branch**: `001-voxr-voice-dictation` | **Phase**: 1 | **Date**: 2026-07-04

Contratos das interfaces públicas entre módulos internos. Voxr não expõe API HTTP ou CLI pública — os contratos aqui são as fronteiras entre módulos Python.

---

## `voxr.config` — Config Manager

```python
def load() -> Configuration
    """Carrega config de ~/.config/voxr/config.json.
    Cria com defaults se não existir. Nunca lança exceção."""

def save(config: Configuration) -> None
    """Persiste config em ~/.config/voxr/config.json. Atomic write (tmp + rename)."""

def get_default() -> Configuration
    """Retorna Configuration com todos os valores padrão."""
```

---

## `voxr.audio` — Audio Capture

```python
def list_devices() -> list[str]
    """Retorna nomes dos dispositivos de áudio disponíveis (input apenas)."""

def is_microphone_available() -> bool
    """True se pelo menos um dispositivo de input está disponível."""

def record(session: RecordingSession, stop_event: threading.Event) -> str
    """Grava áudio até stop_event.set() ou max_recording_seconds.
    Salva em audio_file_path. Retorna o path do arquivo gravado.
    Lança AudioDeviceError se microfone não disponível."""

def get_audio_level(callback: Callable[[float], None]) -> sounddevice.InputStream
    """Stream de monitoramento de nível de áudio para animação de waveform.
    callback recebe valor 0.0–1.0 a ~20fps. Caller fecha o stream."""
```

---

## `voxr.transcription` — Transcription Engine

```python
def load_model(model_name: str) -> WhisperModel
    """Carrega modelo da pasta ~/.local/share/voxr/models/.
    Lança ModelNotFoundError se não baixado."""

def transcribe(
    audio_path: str,
    model: WhisperModel,
    language: str = "auto",
    vad_filter: bool = True,
) -> ChunkResult
    """Transcreve arquivo WAV. Retorna ChunkResult(SUCCESS) ou
    ChunkResult(FAILED_WITH_PLACEHOLDER) após 2 retries internos."""

def transcribe_session(
    session: RecordingSession,
    model: WhisperModel,
    config: Configuration,
) -> TranscriptionResult
    """Modo padrão: transcreve o arquivo inteiro como 1 chunk.
    Modo pipeline: divide em chunks 30s c/ overlap 2s, processa em paralelo.
    Sempre retorna TranscriptionResult — nunca lança exceção."""
```

---

## `voxr.injection` — Text Injection

```python
def inject_text(text: str) -> bool
    """Injeta text no campo ativo via xdotool type.
    Retorna True se sucesso, False se xdotool não disponível ou falhou."""

def copy_to_clipboard(text: str) -> None
    """Copia text para clipboard via xclip ou xsel."""

def insert_or_clipboard(text: str) -> str
    """Tenta inject_text. Se retornar False, usa copy_to_clipboard.
    Retorna 'injected' | 'clipboard'."""
```

---

## `voxr.hotkey` — Global Hotkey Listener

```python
class HotkeyListener:
    def __init__(self, config: Configuration, callbacks: HotkeyCallbacks): ...

    def start(self) -> None
        """Inicia listener em thread daemon."""

    def stop(self) -> None
        """Para listener. Bloqueante até thread encerrar."""

    def update_hotkey(self, new_hotkey: str) -> None
        """Atualiza hotkey sem reiniciar o listener."""

@dataclass
class HotkeyCallbacks:
    on_activate: Callable[[], None]   # hotkey pressionada (Toggle: start/stop)
    on_cancel: Callable[[], None]     # Escape pressionado
    on_ptt_start: Callable[[], None]  # PTT: tecla pressionada
    on_ptt_stop: Callable[[], None]   # PTT: tecla solta
```

---

## `voxr.tray` — System Tray

```python
class TrayIcon:
    def __init__(self, on_settings: Callable, on_quit: Callable): ...

    def set_state(self, state: AppState) -> None
        """Atualiza ícone e tooltip do tray (idle/recording/processing/error)."""

    def show_notification(self, message: str) -> None
        """Exibe notificação do sistema (libnotify)."""
```

---

## `voxr.widget` — Floating Recording Widget

```python
class RecordingWidget:
    def show_recording(self, audio_level_stream: sounddevice.InputStream) -> None
        """Exibe widget no modo gravação com waveform animada.
        Posiciona próximo ao cursor atual."""

    def show_processing(self) -> None
        """Muda widget para modo processamento (spinner)."""

    def hide(self) -> None
        """Fecha e destrói o widget."""

    def update_timer(self, elapsed: float, max_seconds: int) -> None
        """Atualiza contador. Ativa countdown visual nos últimos 10s."""
```

---

## `voxr.app` — Application Orchestrator

```python
class VoxrApp:
    def run(self) -> None
        """Entry point. Inicia GTK main loop."""

    def on_hotkey_activate(self) -> None
        """Toggle: se IDLE → inicia gravação; se RECORDING → encerra e transcreve."""

    def on_cancel(self) -> None
        """Cancela gravação/processamento em andamento."""
```

`VoxrApp` é o único lugar que conhece todos os outros módulos. Nenhum módulo importa outro diretamente — tudo passa pelo `app.py`.
