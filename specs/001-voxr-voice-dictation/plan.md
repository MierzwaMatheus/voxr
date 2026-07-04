# Implementation Plan: Voxr Voice Dictation

**Branch**: `001-voxr-voice-dictation` | **Date**: 2026-07-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-voxr-voice-dictation/spec.md`

---

## Summary

Implementar o Voxr como app desktop Linux de ditado por voz 100% offline: serviço em background com GTK 3 + AppIndicator3, hotkey global via pynput, captura de áudio via sounddevice, transcrição via faster-whisper (Whisper Medium int8), e injeção de texto via xdotool. O desenvolvimento segue as 4 fases do PRD — este plano cobre todas as fases, mas a implementação deve respeitar a gate de fases da constituição (Phase 1 primeiro).

---

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `faster-whisper` — transcrição offline (CTranslate2 int8)
- `sounddevice` — captura de áudio via PortAudio (entrega `np.ndarray float32` diretamente)
- `pynput` — hotkey global X11
- `PyGObject` (gi) — GTK 3 + AppIndicator3
- `huggingface_hub` — download do modelo na primeira execução

**System Dependencies** (instaladas via .deb):
- `xdotool` — injeção de texto X11
- `portaudio19-dev` — backend do sounddevice
- `python3-gi`, `gir1.2-appindicator3-0.1` — GTK bindings

**Storage**:
- Config: `~/.config/voxr/config.json` (JSON stdlib)
- Cache áudio: `~/.cache/voxr/recordings/` (TTL 24h)
- Modelos: `~/.local/share/voxr/models/` (via huggingface_hub)

**Testing**: pytest + pytest-mock

**Target Platform**: Linux X11 (Zorin OS / Ubuntu-based)

**Project Type**: desktop-app (systemd user service + GTK tray)

**Performance Goals**:
- SC-001: end-to-end < 5s para gravação de 5s
- SC-002: transcrição < 2s para áudio de 30s com Whisper Medium int8

**Constraints**:
- 100% offline após download inicial do modelo
- X11 apenas (Wayland fora de escopo)
- ~600MB RAM para modelo Medium int8 em memória

**Scale/Scope**: single-user desktop app, sem concorrência multi-usuário

---

## Constitution Check

*GATE: verificado antes de Phase 0. Re-verificado após Phase 1 design.*

- [x] **I. Offline**: nenhuma dependência de rede em runtime. Rede apenas no download inicial do modelo (wizard). ✅
- [x] **II. Integração Linux**: GTK 3 (UI), xdotool (injeção), pynput (hotkey), systemd user service (autostart), .deb (distribuição), X11 only. ✅
- [x] **III. Performance**: faster-whisper Medium int8, modelo singleton em memória, VAD ativo por padrão. Alvo < 2s para 30s de áudio. ✅
- [x] **IV. Resiliência**: ChunkResult com FAILED_WITH_PLACEHOLDER após 2 retries, TranscriptionResult nunca descarta texto já transcrito, notificação via tray. ✅
- [x] **V. Fase correta**: Phase 1 MVP antes de qualquer feature de Fase 2–4. Plan estruturado com gates entre fases. ✅

| Violação | Justificativa | Alternativa Simples Descartada Por |
|---|---|---|
| Nenhuma | — | — |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-voxr-voice-dictation/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 — decisões de tecnologia
├── data-model.md        # Phase 1 — entidades e enums
├── quickstart.md        # Phase 1 — guia de validação E2E
├── contracts/
│   └── module-interfaces.md  # Phase 1 — contratos entre módulos
└── tasks.md             # Phase 2 — criado por /speckit-tasks
```

### Source Code (repository root)

```text
voxr/                        # Pacote principal Python
├── __main__.py              # Entry point: python3 -m voxr
├── app.py                   # VoxrApp — orchestrator central
├── config.py                # load/save Configuration (JSON)
├── constants.py             # PLACEHOLDER_TEXT, XDG paths, defaults
├── models.py                # Dataclasses: RecordingSession, TranscriptionResult, etc.
├── enums.py                 # InputMode, SessionStatus, AppState, etc.
├── audio.py                 # sounddevice — captura e monitoramento de nível
├── transcription.py         # faster-whisper — load_model, transcribe, transcribe_session
├── injection.py             # xdotool type / clipboard fallback
├── hotkey.py                # pynput — HotkeyListener + HotkeyCallbacks
├── tray.py                  # AppIndicator3 — TrayIcon
├── widget.py                # GTK Popup — RecordingWidget (waveform + timer)
├── settings_window.py       # GTK — janela de configurações (3 abas)
├── setup_wizard.py          # GTK — wizard de primeira execução
└── cache.py                 # Cleanup automático 24h em ~/.cache/voxr/

tests/
├── unit/
│   ├── test_config.py       # load/save/defaults/validation
│   ├── test_models.py       # dataclass state transitions
│   ├── test_transcription.py # mock WhisperModel, retry logic, placeholder
│   ├── test_injection.py    # mock xdotool subprocess, clipboard fallback
│   └── test_cache.py        # TTL cleanup logic
└── integration/
    └── test_dictation_flow.py  # mock audio + model, verifica fluxo completo

data/
└── icons/
    ├── voxr-idle.svg
    ├── voxr-recording.svg
    └── voxr-processing.svg

packaging/
├── voxr.service             # systemd user service
├── voxr.desktop             # .desktop entry para menu
└── build-deb.sh             # script de empacotamento

pyproject.toml               # dependências + metadata do pacote
```

**Structure Decision**: single-project Python package (`voxr/`) com módulos planos (sem subpacotes). Cada módulo tem responsabilidade única. `app.py` é o único ponto de integração — nenhum módulo importa outro diretamente.

---

## Complexity Tracking

> Nenhuma violação da constituição identificada.

---

## Development Process

### TDD — Red-Green-Refactor

Todo código de produção nasce de um teste falhando. O ciclo obrigatório para cada módulo:

1. **Red**: escrever teste que falha (assert no comportamento esperado, sem implementação)
2. **Green**: escrever a implementação mínima para o teste passar
3. **Refactor**: limpar código sem quebrar o teste

**Regra**: nenhum arquivo em `voxr/` é criado sem que exista pelo menos um teste em `tests/` que o cubra.

**Camadas de teste**:
- `tests/unit/` — sem I/O real: mocks para WhisperModel, subprocess (xdotool), sounddevice, GTK. Rodam em CI sem X11 ou microfone.
- `tests/integration/` — testam o fluxo completo com mocks de borda (audio fixture + modelo mock), requerem X11.

### Git Workflow

```
master (branch principal, sempre verde)
  └── feature/voxr-001-<scope>   ← nova branch por milestone
        ↓ PR → master
        ↓ Code Review
        ↓ CI/CD (build + tests + coverage)
        ↓ Merge (squash ou merge commit)
```

- Toda branch parte de `master`
- Nenhum merge sem CI verde (build + testes + coverage ≥ 80%)
- Nenhum merge sem code review aprovado
- Cada PR corresponde a um milestone abaixo

### CI/CD Pipeline (GitHub Actions ou equivalente)

```yaml
# Rodado em todo PR → master
jobs:
  build:    pip install -e ".[dev]"
  test:     pytest tests/unit/ -v
  coverage: pytest --cov=voxr --cov-fail-under=80
  lint:     ruff check voxr/ tests/
```

Coverage mínimo: **80%** para merge. Integração (`tests/integration/`) roda apenas na branch principal pós-merge (requer X11).

---

## Phases Gate Summary & PR Milestones

Cada fase é subdividida em PRs atômicos. A ordem é rígida — PR seguinte só abre quando o anterior está mergeado e CI verde.

### Phase 1 — MVP (bloqueante)

| PR | Scope | Branch | Entregável verificável |
|---|---|---|---|
| **PR-1.1** | Scaffolding | `feature/voxr-001-scaffold` | `pyproject.toml`, `voxr/__main__.py`, CI pipeline verde, 0 testes falhando |
| **PR-1.2** | Config + Models | `feature/voxr-001-config` | `config.py`, `models.py`, `enums.py`, `constants.py` — 100% cobertos por testes unitários |
| **PR-1.3** | Audio Capture | `feature/voxr-001-audio` | `audio.py` — `record()` e `get_audio_level()` com mocks sounddevice, testes verdes |
| **PR-1.4** | Transcription Engine | `feature/voxr-001-transcription` | `transcription.py` — `transcribe()` com mock WhisperModel, retry logic, placeholder — testes verdes |
| **PR-1.5** | Text Injection | `feature/voxr-001-injection` | `injection.py` — `inject_text()`, `copy_to_clipboard()`, `insert_or_clipboard()` com mock subprocess |
| **PR-1.6** | Hotkey Listener | `feature/voxr-001-hotkey` | `hotkey.py` — HotkeyListener Toggle mode com mock pynput |
| **PR-1.7** | GTK Widget + Tray | `feature/voxr-001-ui` | `widget.py`, `tray.py` — smoke test manual: ícone no tray, widget abre/fecha |
| **PR-1.8** | App Orchestrator (MVP E2E) | `feature/voxr-001-app` | `app.py` — fluxo completo: hotkey → áudio → transcrição → injeção. Todos cenários do quickstart.md passando |

### Phase 2 — Configurações

| PR | Scope | Branch |
|---|---|---|
| **PR-2.1** | Settings Window (3 abas) | `feature/voxr-002-settings` |
| **PR-2.2** | Setup Wizard + Hardware Detection | `feature/voxr-002-wizard` |
| **PR-2.3** | Model Download + Bilinguismo | `feature/voxr-002-i18n` |

### Phase 3 — Pipeline e Resiliência

| PR | Scope | Branch |
|---|---|---|
| **PR-3.1** | Chunked Transcription + Overlap | `feature/voxr-003-pipeline` |
| **PR-3.2** | Retry + Placeholder + PTT Mode | `feature/voxr-003-resilience` |

### Phase 4 — Distribuição

| PR | Scope | Branch |
|---|---|---|
| **PR-4.1** | .deb Packaging + systemd service | `feature/voxr-004-packaging` |
| **PR-4.2** | Zorin OS E2E Tests + Docs | `feature/voxr-004-release` |

---

## Verification

Ver [quickstart.md](./quickstart.md) para cenários E2E completos.

**Testes automatizados**:
```bash
pytest tests/unit/ -v                         # CI: roda sem X11/áudio/GPU
pytest --cov=voxr --cov-fail-under=80         # CI: gate de coverage
pytest tests/integration/                     # local: requer X11 + microfone mock
```

**Smoke test manual mínimo (Phase 1, PR-1.8)**:
1. `python3 -m voxr` → ícone no tray aparece
2. `Alt+V` → widget flutuante aparece
3. Falar → `Alt+V` → texto inserido no editor ativo
4. `Alt+V` → `Escape` → widget fecha, editor sem alteração
