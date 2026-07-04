# Tasks: Voxr Voice Dictation — Phase 1 MVP

**Input**: Design documents from `/specs/001-voxr-voice-dictation/`

**Prerequisites**: plan.md, spec.md (acceptance scenarios), research.md (decisions), data-model.md, contracts/module-interfaces.md, quickstart.md

**Process**: TDD — Red-Green-Refactor. Each implementation task has a corresponding test task marked FIRST.

**Organization**: Tasks grouped by PR milestone (PR-1.1 through PR-1.8), then by execution order. User Story 1 (Voice Dictation MVP) spans PR-1.3 to PR-1.8.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no dependencies on incomplete tasks)
- **[US1]**: User Story 1 (Voice Dictation) — the MVP
- Exact file paths in all descriptions
- Checkboxes ready for marking completion

---

## Phase 1: Setup (PR-1.1 Scaffolding)

**Purpose**: Initialize project structure, dependencies, CI/CD pipeline

**Dependencies**: None — can start immediately

### Shared Infrastructure

- [ ] T001 Create directory structure: `voxr/`, `tests/unit/`, `tests/integration/`, `data/icons/`, `packaging/` at repo root
- [ ] T002 Create `pyproject.toml` with dependencies (faster-whisper, sounddevice, pynput, PyGObject, huggingface-hub, soundfile, pytest, pytest-cov, pytest-mock, ruff) and metadata. Use soundfile for WAV I/O (lighter than scipy)
- [ ] T003 Create `voxr/__init__.py` with version string (0.1.0-dev)
- [ ] T004 Create `voxr/__main__.py` entry point (print "Voxr starting", then exit 0 for now)
- [ ] T005 [P] Create `tests/__init__.py`
- [ ] T006 [P] Create `tests/unit/__init__.py`
- [ ] T007 [P] Create `tests/integration/__init__.py`
- [ ] T008 Create `README.md` with quick reference to docs/voxr-prd.md and project structure
- [ ] T009 Create `.github/workflows/ci.yml` with: pip install -e ".[dev]", pytest tests/unit/, pytest --cov=voxr --cov-fail-under=80, ruff check voxr/ tests/
- [ ] T010 Create `CONTRIBUTING.md` documenting TDD process and PR workflow (reference to plan.md PR-1.1 through PR-1.8)

**Checkpoint**: Project structure ready, CI pipeline green with empty tests

---

## Phase 2: Foundational (PR-1.2 Config + Models)

**Purpose**: Core data structures and configuration system that ALL modules depend on

**Dependencies**: Phase 1 Setup complete

**⚠️ CRITICAL**: Phase 3+ cannot start until this is complete

### Tests First (TDD)

- [ ] T011 [P] Write unit tests for Configuration.load() in `tests/unit/test_config.py` — assert loads ~/.config/voxr/config.json, creates with defaults if not exists, never raises exception
- [ ] T012 [P] Write unit tests for Configuration.save() in `tests/unit/test_config.py` — assert persists to JSON, atomic write (tmp + rename)
- [ ] T013 [P] Write unit tests for Configuration defaults in `tests/unit/test_config.py` — assert all fields present, valid hotkey format
- [ ] T014 [P] Write validation tests in `tests/unit/test_config.py` — assert max_recording_seconds (30–180), model_name in allowed values, hotkey parseable
- [ ] T015 [P] Write enum tests in `tests/unit/test_models.py` — assert all enum values serializable to string for JSON
- [ ] T016 [P] Write RecordingSession state transition tests in `tests/unit/test_models.py` — assert IN_PROGRESS → COMPLETED | CANCELLED
- [ ] T017 [P] Write ChunkResult placeholder tests in `tests/unit/test_models.py` — assert FAILED_WITH_PLACEHOLDER contains "[trecho não transcrito]"

### Implementation (TDD Green)

- [ ] T018 Create `voxr/constants.py` with paths (CONFIG_DIR, CACHE_DIR, MODEL_DIR), placeholder text, defaults
- [ ] T019 Create `voxr/enums.py` with InputMode, SessionStatus, TranscriptionStatus, ChunkStatus, AppState as string Enums
- [ ] T020 [P] Create `voxr/models.py` with dataclasses: RecordingSession, TranscriptionResult, ChunkResult, Configuration (see data-model.md)
- [ ] T021 Create `voxr/config.py` with load(), save(), get_default() functions (reference research.md JSON decisions)
- [ ] T022 Create `tests/fixtures/config_fixtures.py` with mock Configuration objects for tests

**Checkpoint**: Config + Models fully tested and functional, CI green

---

## Phase 3: User Story 1 — Voice Dictation to Active Window (P1) 🎯 MVP

**Goal**: User can press hotkey → speak → press hotkey → text inserted in active window, all within 5 seconds for 5-second audio

**Independent Test**: Run `pytest tests/unit/test_dictation_flow.py` — mocks all external I/O (sounddevice, WhisperModel, xdotool), verifies full flow end-to-end

**Acceptance Criteria** (from spec.md):
1. Hotkey press → recording widget appears
2. User speaks → audio captured
3. Hotkey press again → recording stops, transcription begins
4. Text appears in editor within 2 seconds (SC-002)
5. Escape key → cancel, no text inserted
6. No active field → text to clipboard

---

### PR-1.3: Audio Capture Module

**Tests First (TDD)**:

- [ ] T023 [P] Write unit test for `record()` in `tests/unit/test_audio.py` — mock sounddevice, assert saves WAV to cache, returns path, respects max_recording_seconds, stop_event triggers end
- [ ] T024 [P] Write unit test for `is_microphone_available()` — mock sounddevice.query_devices(), assert True if device found, False if empty
- [ ] T025 [P] Write unit test for `list_devices()` — mock sounddevice, assert returns list of device names
- [ ] T026 Write integration test for audio capture in `tests/integration/test_audio.py` — records 2s of silence, saves, verifies file exists and is valid WAV

**Implementation**:

- [ ] T027 Create `voxr/audio.py` with: `record(session: RecordingSession, stop_event: threading.Event) -> str`, `is_microphone_available() -> bool`, `list_devices() -> list[str]`
- [ ] T028 Use sounddevice for recording (16kHz, mono, float32), save to ~/.cache/voxr/recordings/{session_id}.wav via soundfile.write()
- [ ] T029 Create cache directory if not exists, implement 24h TTL cleanup (thread-safe)

**Checkpoint**: Audio capture fully tested, CI green for PR-1.3

---

### PR-1.4: Transcription Engine

**Tests First (TDD)**:

- [ ] T030 [P] Write unit test for `transcribe()` in `tests/unit/test_transcription.py` — mock WhisperModel, assert returns ChunkResult(SUCCESS) or ChunkResult(FAILED_WITH_PLACEHOLDER), respects 2 retries
- [ ] T031 [P] Write unit test for retry logic in `tests/unit/test_transcription.py` — mock failed transcribe, assert retries 2x, then returns placeholder
- [ ] T032 [P] Write unit test for `transcribe_session()` (default mode) in `tests/unit/test_transcription.py` — mocks audio + model, returns TranscriptionResult(SUCCESS)
- [ ] T033 Write unit test for model loading in `tests/unit/test_transcription.py` — assert loads from ~/.local/share/voxr/models/, raises ModelNotFoundError if absent

**Implementation**:

- [ ] T034 Create `voxr/transcription.py` with: `transcribe(audio_path, model, language, vad_filter) -> ChunkResult`, `transcribe_session(session, model, config) -> TranscriptionResult`
- [ ] T035 Use faster-whisper WhisperModel singleton pattern (load once, reuse)
- [ ] T036 Implement retry logic: 2 retries on exception, then ChunkResult(FAILED_WITH_PLACEHOLDER) with text = `"[trecho não transcrito]"`
- [ ] T037 Default mode: transcribe entire file as 1 chunk

**Checkpoint**: Transcription fully tested, CI green for PR-1.4

---

### PR-1.5: Text Injection

**Tests First (TDD)**:

- [ ] T038 [P] Write unit test for `inject_text()` in `tests/unit/test_injection.py` — mock subprocess.run(xdotool), assert calls with ["xdotool", "type", "--clearmodifiers", "--", text], returns True on success
- [ ] T039 [P] Write unit test for `copy_to_clipboard()` — mock xclip, assert copies text
- [ ] T040 [P] Write unit test for `insert_or_clipboard()` in `tests/unit/test_injection.py` — mock inject failing, assert falls back to clipboard, returns "clipboard"

**Implementation**:

- [ ] T041 Create `voxr/injection.py` with: `inject_text(text: str) -> bool`, `copy_to_clipboard(text: str) -> None`, `insert_or_clipboard(text: str) -> str`
- [ ] T042 Use subprocess.run(['xdotool', 'type', '--clearmodifiers', '--', text]) for injection (research.md decision)
- [ ] T043 Use xclip (or xsel fallback) for clipboard

**Checkpoint**: Injection fully tested, CI green for PR-1.5

---

### PR-1.6: Hotkey Listener

**Tests First (TDD)**:

- [ ] T044 [P] Write unit test for HotkeyListener in `tests/unit/test_hotkey.py` — mock pynput.keyboard.Listener, assert on_activate callback called on hotkey press
- [ ] T045 [P] Write unit test for Toggle mode logic — assert first press triggers on_activate, second press triggers same callback again (different state handled by app.py)
- [ ] T046 Write unit test for Escape cancellation — assert on_cancel callback triggered

**Implementation**:

- [ ] T047 Create `voxr/hotkey.py` with HotkeyListener class, HotkeyCallbacks dataclass
- [ ] T048 Use pynput.keyboard.Listener in separate thread, parse hotkey string from config (research.md: pynput decision)
- [ ] T049 Implement start(), stop(), update_hotkey() methods, test without exception

**Checkpoint**: Hotkey fully tested, CI green for PR-1.6

---

### PR-1.7: GTK Widget + System Tray

**Tests First (TDD)**:

- [ ] T050 [P] Write unit test for TrayIcon state changes in `tests/unit/test_tray.py` — mock AppIndicator3, assert set_state(RECORDING) changes icon
- [ ] T051 [P] Write unit test for notification in `tests/unit/test_tray.py` — mock libnotify, assert show_notification() called correctly
- [ ] T052 [P] Write unit test for RecordingWidget show/hide in `tests/unit/test_widget.py` — mock GTK.Window, assert created, positioned, destroyed

**Implementation**:

- [ ] T053 Create `voxr/tray.py` with TrayIcon class — AppIndicator3 or fallback to StatusIcon (research.md decision)
- [ ] T054 Create `voxr/widget.py` with RecordingWidget class — GTK POPUP window, no decorations, draws waveform via Cairo
- [ ] T055 Implement waveform animation (GLib.timeout_add 50ms redraw), timer display, countdown in last 10s
- [ ] T056 Test manual smoke: run app, verify ícone appears, click menu works

**Checkpoint**: GTK widget + tray functional, smoke test passes

---

### PR-1.8: App Orchestrator (E2E MVP)

**Tests First (TDD)**:

- [ ] T057 Write integration test for full dictation flow in `tests/integration/test_dictation_flow.py` — mock audio (2s sample), WhisperModel, xdotool, records audio, transcrever, verifies text injected
- [ ] T058 Write integration test for cancel flow — hotkey → audio → Escape → verify no text injected
- [ ] T059 Write integration test for no active field → clipboard fallback
- [ ] T060 Write integration test for timeout at max duration

**Implementation**:

- [ ] T061 Create `voxr/app.py` with VoxrApp orchestrator class — integrates all modules without circular imports (see contracts/module-interfaces.md)
- [ ] T062 Implement on_hotkey_activate() — Toggle: IDLE → recording; RECORDING → transcribe
- [ ] T063 Implement on_cancel() — stop recording, close widget, discard audio
- [ ] T064 Update `voxr/__main__.py` to instantiate VoxrApp().run() (GTK.main_loop)
- [ ] T065 Create `tests/fixtures/audio_fixture.wav` — 2-second WAV file for testing
- [ ] T066 Run full integration tests: `pytest tests/integration/test_dictation_flow.py -v`
- [ ] T067 Run quickstart.md validation: Cenários 1–4 (Phase 1 scope: dictation, cancel, clipboard, timeout) — Cenários 5–6 are Phase 2+ features

**Checkpoint**: Full E2E dictation MVP working, all acceptance criteria met

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, documentation, final validation

**Dependencies**: All user story work complete

- [ ] T068 [P] Run full unit test suite: `pytest tests/unit/ -v` — assert all green
- [ ] T069 [P] Check coverage: `pytest --cov=voxr --cov-fail-under=80` — assert ≥ 80%
- [ ] T070 [P] Lint code: `ruff check voxr/ tests/` — assert no errors
- [ ] T071 [P] Type hints validation (if using mypy): `mypy voxr/` (optional but recommended)
- [ ] T072 Clean up any test fixtures in `tests/fixtures/` — ensure reproducible tests
- [ ] T073 Update README.md with "How to Run" section: setup.py install, python3 -m voxr, expected output
- [ ] T074 Update CONTRIBUTING.md with test commands and PR checklist
- [ ] T075 Add inline code comments only where WHY is non-obvious (per architecture doc)
- [ ] T076 Verify all file paths in tasks match actual created files
- [ ] T077 Document config.json schema in `docs/config-schema.md` (optional reference)
- [ ] T078 Final smoke test per quickstart.md: Cenários 1–6 all pass

**Checkpoint**: Phase 1 MVP complete, ready for Phase 2 (Configurações)

---

## Dependencies & Execution Order

### Phase Dependencies

1. **Phase 1 Setup (PR-1.1)**: No dependencies
2. **Phase 2 Foundational (PR-1.2)**: Depends on Phase 1 ✓
3. **Phase 3 User Story 1 (PR-1.3 → PR-1.8)**: Depends on Phase 2 ✓
   - PR-1.3 (Audio): Can run immediately after Phase 2
   - PR-1.4 (Transcription): Can run immediately after Phase 2
   - PR-1.5 (Injection): Can run immediately after Phase 2
   - PR-1.6 (Hotkey): Can run immediately after Phase 2
   - PR-1.7 (Widget): Can run immediately after Phase 2
   - PR-1.8 (App): Depends on PR-1.3 through PR-1.7 (all previous PRs) — brings everything together
4. **Phase 4 Polish**: Depends on Phase 3 complete

### Within Phase 3: PR Dependencies

- **PR-1.3, PR-1.4, PR-1.5, PR-1.6, PR-1.7**: Can be worked in parallel (no inter-dependencies)
- **PR-1.8**: Depends on all of PR-1.3 through PR-1.7 (integrates all modules)

### Parallel Opportunities (Single Developer)

**Sequential (safest for single developer)**:
```
PR-1.1 Setup
  ↓
PR-1.2 Config + Models
  ↓
PR-1.3 Audio Capture
  ↓
PR-1.4 Transcription
  ↓
PR-1.5 Injection
  ↓
PR-1.6 Hotkey
  ↓
PR-1.7 Widget + Tray
  ↓
PR-1.8 App E2E (integrates all)
  ↓
Polish & Validation
```

**Parallel (if multiple developers)**:
```
Phase 1 Setup (1 dev)
  ↓
Phase 2 Foundational (1 dev)
  ↓ (then fan out)
Dev A: PR-1.3 + PR-1.4 (Audio + Transcription)
Dev B: PR-1.5 + PR-1.6 (Injection + Hotkey)
Dev C: PR-1.7 (Widget + Tray)
  ↓ (converge)
One dev: PR-1.8 (App orchestrator integrates all)
  ↓
All: Polish & Validation
```

---

## Implementation Strategy

### TDD Cycle per PR

For each PR:

1. **Read** corresponding contract from `contracts/module-interfaces.md`
2. **Write tests first** (RED) — tests fail because no implementation
3. **Implement** minimum code to pass tests (GREEN)
4. **Refactor** — clean up, add docstrings, verify tests still pass
5. **Create PR** → code review → CI gate (coverage ≥ 80%, lint, all tests green)

### MVP Scope

The entire Phase 1 MVP (PR-1.1 through PR-1.8) is the minimum viable product:

```
User presses hotkey
  ↓
Widget appears, audio captured
  ↓
User presses hotkey again
  ↓
Audio transcribed (< 2s for 30s audio, SC-002)
  ↓
Text inserted in active window (< 5s total, SC-001)
```

**Stop after PR-1.8 to validate**: Run quickstart.md Cenários 1–4. If all pass, MVP is complete.

### Incremental Delivery

1. PR-1.1 → Setup ready
2. PR-1.2 → Foundation ready
3. PR-1.3–PR-1.7 → Individual modules ready (can test with mocks)
4. PR-1.8 → Full flow works
5. Polish → Production-ready for Phase 2

---

## Success Criteria (Phase 1 MVP)

- [x] All 78 tasks completed and checked off
- [x] All unit tests pass (`pytest tests/unit/ -v` green)
- [x] Coverage ≥ 80% (`pytest --cov=voxr --cov-fail-under=80`)
- [x] All code linted (`ruff check voxr/ tests/`)
- [x] Quickstart.md Cenários 1–4 validated manually
- [x] CI pipeline green on final PR-1.8 merge
- [x] No blocking issues from code review

---

## Notes

- **[P] tasks**: Can run in parallel (different files, no dependencies)
- **[US1]**: Maps to User Story 1 — Voice Dictation MVP
- TDD = tests FIRST, then implementation, then refactor
- Each PR is independently reviewable and testable
- Commit after each task or logical group (e.g., all tests for module, then implementation)
- Reference plan.md PR sections for branch names and scope details
