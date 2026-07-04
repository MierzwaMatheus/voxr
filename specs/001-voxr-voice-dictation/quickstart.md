# Quickstart Validation Guide

**Branch**: `001-voxr-voice-dictation` | **Phase**: 1 | **Date**: 2026-07-04

Guia para validar o funcionamento end-to-end do Voxr após implementação.

---

## Pré-requisitos

```bash
# Dependências de sistema
sudo apt install xdotool portaudio19-dev python3-gi gir1.2-appindicator3-0.1

# Dependências Python (após criar pyproject.toml)
pip install faster-whisper sounddevice pynput

# Verificar X11 ativo
echo $DISPLAY  # deve retornar :0 ou similar (não vazio)

# Verificar microfone
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

---

## Setup Inicial (primeira execução)

```bash
cd /path/to/voxr
python3 -m voxr
```

**Esperado**: janela de setup GTK aparece → detecta hardware → recomenda modelo Medium → usuário confirma download → modelo baixado em `~/.local/share/voxr/models/` → app inicia com ícone no system tray.

**Verificar**: `ls ~/.local/share/voxr/models/` deve conter os arquivos do modelo.

---

## Cenário 1: Ditado Básico (US-1, SC-001)

**Objetivo**: hotkey → fala → texto no campo ativo em < 5s para gravação de 5s.

1. Abrir `gedit` ou qualquer editor de texto
2. Clicar no campo de texto (dar foco)
3. Pressionar `Alt+V` — widget flutuante deve aparecer próximo ao cursor
4. Falar por ~5 segundos: *"Olá, este é um teste do Voxr."*
5. Pressionar `Alt+V` novamente
6. **Esperado**: texto aparece no editor em menos de 5 segundos

**Verificar SC-002**: gravação de 30s deve transcrever em < 2s. Medir com:
```bash
time python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('medium', compute_type='int8')
segs, _ = m.transcribe('tests/fixtures/30s_sample.wav', vad_filter=True)
print(list(segs))
"
```

---

## Cenário 2: Cancelamento com Escape (US-1, Acceptance 4)

1. Pressionar `Alt+V` — widget aparece, gravação inicia
2. Falar algo
3. Pressionar `Escape`
4. **Esperado**: widget fecha, **nenhum texto** inserido no editor

---

## Cenário 3: Sem Campo Ativo → Clipboard (US-1, Acceptance 5 / Edge Case)

1. Não ter nenhum editor aberto (ou minimizar todos)
2. Pressionar `Alt+V` → falar → pressionar `Alt+V`
3. **Esperado**: notificação do tray: *"Texto copiado para clipboard"*
4. Colar com `Ctrl+V` em qualquer app — texto deve aparecer

---

## Cenário 4: Limite de Tempo (FR-007)

1. Configurar limite para 30s: `~/.config/voxr/config.json` → `"max_recording_seconds": 30`
2. Iniciar gravação, aguardar
3. **Esperado nos últimos 10s**: countdown visível no widget (10, 9, 8... 0)
4. **Ao atingir 0**: gravação encerra automaticamente, processamento inicia

---

## Cenário 5: Microfone Não Detectado (Edge Case)

```bash
# Simular: desabilitar dispositivo de áudio
pactl suspend-source 0
```

1. **Esperado**: ícone do tray muda para estado de erro
2. Pressionar `Alt+V` — dialog GTK informa que nenhum microfone foi detectado
3. Reabilitar: `pactl suspend-source 0 0`
4. **Esperado**: app retorna automaticamente ao estado idle sem reiniciar

---

## Cenário 6: Config Persiste Entre Reinicializações (FR-010)

```bash
# Editar config
cat ~/.config/voxr/config.json
# Mudar hotkey, reiniciar app, verificar novo hotkey ativo
```

---

## Verificação do Cache (24h TTL)

```bash
# Após uma sessão de gravação
ls ~/.cache/voxr/recordings/  # deve conter *.wav

# Simular cleanup (modificar mtime para > 24h no passado)
find ~/.cache/voxr/recordings/ -name "*.wav" -exec touch -t 202406040000 {} \;
# Aguardar próximo ciclo de cleanup (ou reiniciar app), verificar que arquivos foram removidos
```

---

## Referências

- Data model: [data-model.md](./data-model.md)
- Module contracts: [contracts/module-interfaces.md](./contracts/module-interfaces.md)
- Requisitos: [spec.md](./spec.md)
- Constituição (gates): [.specify/memory/constitution.md](../../.specify/memory/constitution.md)
