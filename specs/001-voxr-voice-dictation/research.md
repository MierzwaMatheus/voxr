# Research: Voxr Voice Dictation

**Branch**: `001-voxr-voice-dictation` | **Phase**: 0 | **Date**: 2026-07-04

---

## Audio Capture

**Decision**: `sounddevice` sobre PyAudio  
**Rationale**: sounddevice é wrapper NumPy nativo do PortAudio — sem callbacks em C, buffer diretamente como `np.ndarray` float32 que faster-whisper já espera. Elimina step de conversão. PyAudio requer bytes + conversão manual.  
**Alternative discarded**: PyAudio — API mais verbosa, requer `audioop` para converter para float32; sounddevice já entrega o array na forma correta.

```python
import sounddevice as sd
audio = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype='float32')
```

---

## Hotkey Global (pynput + X11)

**Decision**: `pynput.keyboard.Listener` em thread separada  
**Rationale**: pynput funciona nativamente com X11 via Xlib. Thread dedicada não bloqueia GTK main loop. Para Push-to-talk, `on_press`/`on_release` distintos funcionam out-of-the-box.  
**Alternative discarded**: `keyboard` (requer root em sistemas modernos); `python-xlib` direta (mais verbosa sem benefício).

```python
from pynput import keyboard
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()  # thread separada
```

---

## Text Injection

**Decision**: `subprocess.run(['xdotool', 'type', '--clearmodifiers', '--', text])`  
**Rationale**: `--clearmodifiers` garante que modificadores presos (Shift, Alt) não corrompam o texto inserido. `--` evita interpretação de texto iniciando com `-` como flag. Delay padrão 12ms entre teclas é adequado para campos web (Chrome, Firefox).  
**Alternative discarded**: `xdotool type --delay 0` — muito rápido para campos que fazem debounce; pode perder caracteres em apps lentos.

---

## Transcrição (faster-whisper)

**Decision**: `WhisperModel` singleton carregado na inicialização, reutilizado entre sessões  
**Rationale**: carregamento do modelo Medium int8 leva ~2–3s. Manter em memória elimina este custo em todas as transcrições subsequentes. Memória ocupada: ~600MB RAM para Medium int8 — dentro do pressuposto de 16GB RAM do hardware de referência.  
**Alternative discarded**: carregar/descarregar por sessão — latência inaceitável (viola SC-001: < 5s end-to-end para gravação de 5s).

```python
from faster_whisper import WhisperModel
model = WhisperModel("medium", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_array, vad_filter=True)
```

---

## Concorrência: Threads vs asyncio

**Decision**: threads nativas (`threading.Thread`) com `queue.Queue`  
**Rationale**: GTK main loop não é compatível com asyncio sem adaptador. pynput e sounddevice já rodam em threads. Queue é thread-safe e suficiente para o fluxo: hotkey → audio → transcription → injection.  
**Alternative discarded**: asyncio — requer `gbulb` ou `asyncio-glib` para integrar com GTK, adiciona complexidade sem benefício real no modelo single-user.

**Thread layout**:
```
Main thread       → GTK main loop (tray + widget)
HotkeyThread      → pynput.keyboard.Listener
AudioThread       → sounddevice recording (por sessão, criada on-demand)
TranscriptionThread → faster-whisper (por sessão, pool de 1 worker)
CleanupThread     → cache cleanup (24h TTL), daemon, acorda a cada hora
```

---

## Configuração Persistente

**Decision**: JSON em `~/.config/voxr/config.json`  
**Rationale**: sem dependência extra. Python `json` stdlib. Human-readable para debugging. Estrutura plana — sem hierarquia que justifique TOML.  
**Alternative discarded**: TOML — requer `tomllib` (disponível só Python 3.11+ stdlib) ou dependência extra em 3.10; JSON é mais amplamente suportado.

---

## Cache de Áudio

**Decision**: `~/.cache/voxr/recordings/` com cleanup automático a cada hora, TTL 24h  
**Rationale**: XDG Base Directory Spec — `~/.cache` é o local correto para dados temporários. Thread daemon acorda a cada hora e deleta arquivos com mtime > 24h. Sem banco de dados necessário.  
**Naming**: `{session_id}.wav` — UUID4 por sessão.

---

## Armazenamento do Modelo

**Decision**: `~/.local/share/voxr/models/` com download via `huggingface_hub`  
**Rationale**: `~/.local/share` é o local XDG correto para dados persistentes do usuário. `huggingface_hub.snapshot_download()` já faz retry, progress callback e cache automático.  
**Alternative discarded**: download manual via `requests` — reinventa a roda; huggingface_hub já resolve checksums e partial downloads.

---

## GTK Widget Flutuante

**Decision**: `gtk.Window(gtk.WindowType.POPUP)` sem decorações, posicionado via `window.move(x, y)`  
**Rationale**: `POPUP` ignora gerenciador de janelas (sem barra de título, sem borda). `gdk.display_get_pointer()` captura posição do cursor para posicionar o widget próximo ao clique. Waveform via Cairo drawing area com timer `GLib.timeout_add(50, redraw)`.  
**Alternative discarded**: `gtk.Window(gtk.WindowType.TOPLEVEL)` com `set_decorated(False)` — alguns WMs sobrepõem decorações mesmo com essa flag.

---

## System Tray

**Decision**: `AppIndicator3` via `gi.repository.AppIndicator3`  
**Rationale**: padrão em Ubuntu/Zorin/GNOME. Suporta ícones animados via troca de categoria. Menu padrão GTK.  
**Fallback**: se AppIndicator3 não estiver disponível, `gtk.StatusIcon` (deprecated mas funcional em ambientes sem AppIndicator).

---

## systemd User Service

**Decision**: arquivo `.service` instalado em `/usr/lib/systemd/user/voxr.service`  
**Rationale**: `systemd --user` não requer privilégio de root. `After=graphical-session.target` garante que X11 e tray estejam disponíveis. `Type=simple` com `Restart=on-failure`.  
**Enable**: via `systemctl --user enable voxr` (checkbox nas configurações chama esse comando).
