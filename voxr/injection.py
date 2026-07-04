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
    except FileNotFoundError:
        subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=text,
            text=True,
            check=False,
        )


def insert_or_clipboard(text: str) -> str:
    """Tenta inject_text. Se retornar False, usa copy_to_clipboard.
    Retorna 'injected' | 'clipboard'."""
    if inject_text(text):
        return "injected"
    copy_to_clipboard(text)
    return "clipboard"
