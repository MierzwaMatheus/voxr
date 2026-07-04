# Feature Specification: Voxr Voice Dictation

**Feature Branch**: `001-voxr-voice-dictation`

**Created**: 2026-07-04

**Status**: Draft

**Input**: Product Requirements Document: `docs/voxr-prd.md`

## User Scenarios & Testing

### User Story 1 - Voice Dictation to Active Window (Priority: P1)

A user needs to quickly insert spoken text into any application (email, document editor, chat,
form) without switching focus or using keyboard typing. The current workflow forces context
switching and manual typing, which is slow for long passages.

**Why this priority**: This is the core MVP value proposition — offline voice-to-text insertion.
Without this, Voxr has no function. It unblocks all downstream use cases.

**Independent Test**: User can press hotkey → speak → press hotkey again → text appears in the
active text field of any GTK or X11 app. Can be tested with a simple text editor.

**Acceptance Scenarios**:

1. **Given** Voxr is running and a text editor has focus, **When** user presses the configured
   hotkey (default: Alt+V), **Then** the app enters recording mode and displays a floating widget
   with animated waves.

2. **Given** the app is in recording mode, **When** user speaks for 5 seconds, **Then** the audio
   is captured without visible lag or artifacts.

3. **Given** the user has stopped speaking, **When** the user presses the hotkey again (or clicks
   the widget), **Then** recording stops, transcription begins immediately, and within 2 seconds
   the transcribed text appears in the original active window.

4. **Given** the user is in recording mode, **When** the user presses Escape, **Then** recording
   stops and no text is inserted (clean cancellation).

5. **Given** the transcription is complete, **When** no text field is active in any application,
   **Then** the transcribed text is automatically copied to the system clipboard for manual
   insertion.

---

### User Story 2 - Graphical Configuration (Priority: P2)

A user needs to customize how Voxr behaves: change the hotkey, select a different speech model,
adjust recording time limits, and switch between Toggle and Push-to-Talk modes — all without
touching configuration files.

**Why this priority**: Supports phase 2 of the roadmap (Configurações). Enables diverse hardware
and user preferences without requiring file editing or terminal skills.

**Independent Test**: User can open a Settings window from the Voxr menu → change at least 3
settings → close → verify that new settings take effect on next dictation. Can be tested by
changing the hotkey and verifying it works.

**Acceptance Scenarios**:

1. **Given** Voxr is running, **When** user clicks on the app menu or icon, **Then** a Settings
   option is visible and clickable.

2. **Given** the Settings window is open, **When** user can see tabs or sections labeled
   "General", "Transcription", and "Performance", **Then** settings can be grouped logically.

3. **Given** the Transcription tab is visible, **When** user selects a different Whisper model
   (e.g., Large instead of Medium), **Then** the new model is downloaded (if not cached) and
   used for the next dictation session.

4. **Given** the General tab, **When** user changes the hotkey from Alt+V to Ctrl+Shift+D and
   applies changes, **Then** the new hotkey works immediately without app restart.

5. **Given** the Performance tab, **When** user can toggle VAD (Voice Activity Detection) on/off
   and set max recording time (30s to 3min, default 60s), **Then** these settings are persisted
   and take effect immediately.

---

### User Story 3 - Long-Form Dictation with Automatic Recovery (Priority: P3)

A user needs to dictate long passages (2-5 minutes) without worrying about timeouts or losing
work if transcription fails mid-stream. The system should split long recordings into manageable
chunks, process them with overlap to catch broken words, and insert consolidated text only once.

**Why this priority**: Supports phase 3 (Pipeline/Resiliência). Enables use cases like email
drafts, documentation, and articles without frequent app restarts or manual workarounds.

**Independent Test**: User records a 3-minute voice message → app splits it into ~6 chunks,
processes each → any chunk that fails is marked `[trecho não transcrito]` → full text (with
placeholders) is inserted at the end. Manual verification: user can review the text and know
exactly where to re-record.

**Acceptance Scenarios**:

1. **Given** Pipeline mode is enabled in Performance settings, **When** user starts a 3-minute
   recording (approaching the 3-min max), **Then** the system processes audio in 30-second chunks
   with 2-3 second overlap to preserve sentence continuity.

2. **Given** all chunks are processed successfully, **When** transcription is complete, **Then**
   the full consolidated text is inserted once (no incremental insertions during processing).

3. **Given** a single chunk fails transcription after 2 retries, **When** the final text is
   ready, **Then** that chunk is replaced with `[trecho não transcrito]` and the rest of the
   text is intact.

4. **Given** the user is aware of the placeholder, **When** they review the inserted text,
   **Then** they can immediately re-record just the missing portion and insert it in the right
   place.

5. **Given** the app is processing chunks in pipeline mode, **When** the user needs to cancel,
   **Then** pressing Escape stops further processing and inserts only the successfully transcribed
   chunks so far (no data loss).

---

### User Story 4 - Installation and Automatic Startup (Priority: P4)

A user needs to install Voxr once, configure the model on first run, and have it available
every time they log in — without manual startup commands or daemon management.

**Why this priority**: Supports phase 4 (Distribuição .deb). Enables seamless user experience
for Linux desktop users familiar with standard package management.

**Independent Test**: User installs the .deb package → launches Voxr → prompted with model
download wizard → model downloads and app starts → after logout/login cycle, Voxr is available
without manual intervention. Can be tested by simulating a session restart.

**Acceptance Scenarios**:

1. **Given** Voxr .deb package is downloaded, **When** user installs it via `apt install` or
   graphical package manager, **Then** no broken dependencies error; installation completes
   without requiring manual configuration.

2. **Given** Voxr is launched for the first time, **When** no local Whisper model is detected,
   **Then** a GTK wizard prompts user to confirm model download (~1.5GB), with clear progress
   feedback.

3. **Given** the model is downloading, **When** download completes, **Then** app automatically
   starts and is ready for dictation.

4. **Given** Voxr has been configured, **When** user logs out and logs back in, **Then** Voxr
   is automatically running without user manually launching it (via systemd user service).

5. **Given** automatic startup is enabled, **When** user wants to disable it, **Then** a simple
   checkbox or button in settings allows toggling autostart without file editing.

---

### Edge Cases

- **Timeout at max recording time**: User is mid-sentence when 3-minute limit is hit. System
  emits a visual warning (countdown in last 10s), automatically stops recording, and processes
  the captured audio. User can immediately start a new recording for the next sentence.

- **Transcription failure on a chunk**: Network failure, model crash, or corrupted audio causes
  one 30s chunk to fail after 2 retries. Instead of losing the entire passage, that chunk
  becomes `[trecho não transcrito]` and surrounding chunks are inserted normally.

- **No active text field at insertion time**: User pressed hotkey to insert but switched focus
  to a different window or minimized the target app. Text is copied to clipboard automatically,
  and user can paste it manually when ready.

- **Microphone not detected or permission denied**: User runs Voxr but audio device is not
  enumerable or user rejected microphone permission in OS settings. App displays a non-blocking
  notification explaining the issue and blocks recording until fixed (does not crash or hang).

- **Very short recording (< 0.5s of speech)**: User presses hotkey but says nothing or only
  captures silence (VAD filters it out). App inserts nothing and does not error; user can
  immediately try again with actual speech.

---

## Requirements

### Functional Requirements

- **FR-001** (Phase 1): System MUST function entirely offline — no internet connection required for any core
  functionality (recording, transcription, text insertion).

- **FR-002** (Phase 1): System MUST capture audio from the default microphone via a global, user-configurable
  hotkey that works even when the app window is not in focus.

- **FR-003** (Phase 1): System MUST transcribe captured audio to text using a locally stored Whisper model
  and immediately insert the result into the active text field (or clipboard if no field is active).

- **FR-004** (Phase 1): System MUST display continuous visual feedback during recording — a floating widget
  with animated waveform, timer, and audio level indicator.

- **FR-005** (Phase 1): System MUST end recording and begin transcription when the user presses the hotkey
  a second time or clicks a button on the recording widget (toggle mode).

- **FR-006** (Phase 1): System MUST cancel recording and discard the audio when the user presses the Escape
  key, with no text inserted.

- **FR-007** (Phase 1): System MUST enforce a maximum recording duration (default 60s, configurable 30s–3min)
  and display a countdown timer in the widget during the final 10 seconds. Automatically stop
  recording when the limit is reached.

- **FR-008** (Phase 3): System MUST support two input modes: Toggle (press hotkey to start/stop, default)
  and Push-to-Talk (hold hotkey to record, release to stop).

- **FR-009** (Phase 1): System MUST insert a visible placeholder text `[trecho não transcrito]` for any
  transcription chunk that fails after 2 automatic retries, ensuring no silent data loss.

- **FR-010** (Phase 2): System MUST provide a graphical settings interface with tabs for General (hotkey,
  mode), Transcription (model selection, VAD), and Performance (pipeline mode, max duration).
  All settings persist across app restarts.

- **FR-011** (Phase 4): System MUST start automatically when the user logs into their desktop session
  (via systemd user service) without requiring manual launch.

- **FR-012** (Phase 4): System MUST be installable via standard Debian/Ubuntu package management (`.deb`
  package) with no manual dependency resolution or external script execution required.

### Key Entities

- **Recording Session**: Represents a single recording from hotkey press to completion or cancellation.
  Attributes: `session_id`, `start_time`, `end_time`, `duration_seconds`, `input_mode` (toggle/ptt),
  `audio_file_path`, `status` (in_progress/completed/cancelled).

- **Transcription Result**: Represents the output of processing a recording session. Attributes:
  `result_id`, `session_id`, `full_text`, `chunks` (array of chunk results), `status` (success/partial/failed),
  `timestamp`.

- **Chunk Result**: Represents transcription of a single audio chunk (for long recordings). Attributes:
  `chunk_id`, `chunk_index`, `text`, `confidence`, `retry_count`, `status` (success/failed_with_placeholder).

- **Configuration**: User preferences stored persistently. Attributes: `hotkey`, `input_mode`,
  `model_name`, `max_recording_seconds`, `vad_enabled`, `pipeline_mode_enabled`, `autostart_enabled`.

---

## Success Criteria

### Measurable Outcomes

- **SC-001** (Phase 1): End-to-end latency from hotkey press to text insertion for a 5-second recording
  is less than 5 seconds total for subsequent recordings (model pre-loaded in memory). Measured: timer from hotkey press to
  text appearance in editor. Note: first-run model load is a separate non-critical initialization path.

- **SC-002** (Phase 1): Transcription of a 30-second audio sample completes within 2 seconds of recording
  end, using the default Whisper Medium model with int8 quantization.

- **SC-003** (Phase 1): Zero silent failures — any transcription failure (partial or total) results in
  either inserted text + `[trecho não transcrito]` or text in clipboard. No cases where audio
  is captured but no output appears with no user notification.

- **SC-004** (Phase 4): Full installation (including first-run model download from URL) completes in less
  than 10 minutes on a machine with typical home internet (>5 Mbps). Measured from `apt install`
  to "Voxr is ready to use".

- **SC-005** (Phase 4): After system restart, Voxr is available and functional (hotkey active) without user
  manually launching the app. Verified by logging out, logging in, and testing hotkey before
  opening any app.

---

## Assumptions

- **Linux platform**: Users run a Linux distribution with X11 display server (Wayland is not
  supported in this scope). Typically Ubuntu/Debian-based systems with standard desktop
  environments (GNOME, KDE, XFCE, i3, etc.).

- **User permissions**: User has sufficient privileges to install system packages and enable
  systemd user services without requiring `sudo` for routine app operations.

- **Hardware**: System has a functional microphone (detected by PulseAudio/ALSA) and the user
  has granted microphone permissions in OS settings.

- **Disk space**: User has at least 2GB free disk space to download and store the Whisper model
  (~1.5GB) plus application files and temporary cache. Additional space for audio cache: ~500MB
  (rolling 24-hour retention of recordings).

- **Package ecosystem**: Distribution uses APT package manager (Debian/Ubuntu family). Other
  distributions (RPM, pacman) are out of scope for v1.

- **Model source**: Whisper model files are fetched from Hugging Face Hub or similar trusted
  source during first run; internet access is required only once for model download, not for
  subsequent use.

- **Application runtime**: Python 3.11+ is available in the user's environment (typically via
  distribution package or system Python). No requirement for conda/virtualenv in the user's
  workflow.

---

## Clarifications

### Session 2026-07-04

- **Q**: After successful transcription, should audio files be discarded, cached temporarily, or
  persisted indefinitely? → **A**: Cached temporarily for 24 hours. Enables debugging and manual
  re-editing without indefinite storage overhead or privacy risk.

**Impact**: Adds requirement to Disk space assumption (500MB rolling 24h cache). Implies system
must implement automatic cleanup of recordings older than 24 hours. FR-003 now clarified: text
is inserted, audio is retained in cache for 24h, then discarded.
