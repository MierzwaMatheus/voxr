from typing import Callable

from voxr.constants import MODEL_DIR
from voxr.models import Configuration, ModelInfo


def get_model_info(model_name: str) -> ModelInfo:
    model_bin = MODEL_DIR / model_name / "model.bin"
    if model_bin.exists():
        return ModelInfo(model_name=model_name, is_cached=True, path=str(model_bin))
    return ModelInfo(model_name=model_name, is_cached=False, path=None)


class SettingsWindow:
    def __init__(
        self,
        config: Configuration,
        on_apply: Callable[[Configuration], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self._config = config
        self._on_apply = on_apply
        self._on_cancel = on_cancel
        self._window = None

    def show(self) -> None:
        pass

    def hide(self) -> None:
        pass

    def set_sensitive(self, enabled: bool) -> None:
        pass
