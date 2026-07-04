import sys

# Remover stubs de hardware que podem ter sido registrados pelos testes unitários,
# garantindo que os testes de integração usem as libs reais quando disponíveis.
for _mod in ("soundfile",):
    sys.modules.pop(_mod, None)
