"""T065 — verifica que tests/fixtures/audio_fixture.wav existe e é válido."""
from pathlib import Path

import soundfile as sf

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "audio_fixture.wav"
EXPECTED_SAMPLE_RATE = 16000
EXPECTED_DURATION_S = 2.0


def test_audio_fixture_exists():
    assert FIXTURE_PATH.exists(), f"Fixture não encontrado: {FIXTURE_PATH}"


def test_audio_fixture_is_valid_wav():
    info = sf.info(str(FIXTURE_PATH))
    assert info.samplerate == EXPECTED_SAMPLE_RATE
    assert info.duration >= EXPECTED_DURATION_S * 0.9


def test_audio_fixture_is_mono():
    info = sf.info(str(FIXTURE_PATH))
    assert info.channels == 1
