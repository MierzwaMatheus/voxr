import subprocess


def inject_text(text: str) -> bool:
    """Injeta text no campo ativo via xdotool type.
    Retorna True se sucesso, False se xdotool não disponível ou falhou."""
    try:
        result = subprocess.run(
            # --clearmodifiers: releases active modifier keys (e.g. Alt from the hotkey)
            # before typing, otherwise they leak and produce wrong characters.
            # --: prevents text starting with '-' from being parsed as a flag.
            ["xdotool", "type", "--clearmodifiers", "--delay", "20", "--", text],
            check=False,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def copy_to_clipboard(text: str) -> None:
    """Copia text para clipboard via xclip ou xsel."""
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text,
            text=True,
            check=False,
        )
        return
    except FileNotFoundError:
        pass
    try:
        subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=text,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        pass


def insert_or_clipboard(text: str) -> str:
    """Sempre copia text para o clipboard e também tenta injetar no campo ativo.

    Copiar sempre garante que o texto nunca se perde quando não há campo editável
    focado (ex.: desktop em foco), sem depender de detecção frágil de janela ativa.
    Retorna 'injected' se a injeção teve sucesso, senão 'clipboard'."""
    copy_to_clipboard(text)
    if inject_text(text):
        return "injected"
    return "clipboard"
