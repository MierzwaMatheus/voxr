import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Remover stubs de hardware que podem ter sido registrados pelos testes unitários,
# garantindo que os testes de integração usem as libs reais quando disponíveis.
for _mod in ("soundfile",):
    sys.modules.pop(_mod, None)

# Stub pynput/GTK para ambientes sem X11/display (CI headless)
for _mod in ("pynput", "pynput.keyboard", "gi", "gi.repository"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()


@pytest.fixture(autouse=True)
def fake_model_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a MODEL_DIR with a fake model.bin for every integration test.

    Tests that call _do_process() need the model presence check to pass.
    The default config uses model_name="base", so we create base/model.bin.
    """
    model_dir = tmp_path / "models"
    for model_name in ("base", "small", "medium", "large", "large-v2", "large-v3"):
        model_subdir = model_dir / model_name
        model_subdir.mkdir(parents=True)
        (model_subdir / "model.bin").write_bytes(b"fake")
    monkeypatch.setattr("voxr.app.MODEL_DIR", model_dir)
    return model_dir
