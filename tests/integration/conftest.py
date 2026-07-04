import sys
from unittest.mock import MagicMock

# Remover stubs de hardware que podem ter sido registrados pelos testes unitários,
# garantindo que os testes de integração usem as libs reais quando disponíveis.
for _mod in ("soundfile",):
    sys.modules.pop(_mod, None)

# Stub pynput/GTK para ambientes sem X11/display (CI headless)
for _mod in ("pynput", "pynput.keyboard", "gi", "gi.repository"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
