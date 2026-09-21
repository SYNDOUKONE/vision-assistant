"""
VISION — Mode Dictée Vocale (macOS)
Transcrit la voix et colle le texte dans l'application active.
"""
import asyncio
import subprocess
import pyperclip
from modules import state

MODE_DICTEE = False


def activer_dictee() -> str:
    global MODE_DICTEE
    MODE_DICTEE = True
    return "Mode dictée activé. Parlez, et je transcrirai dans l'application active."


def desactiver_dictee() -> str:
    global MODE_DICTEE
    MODE_DICTEE = False
    return "Mode dictée désactivé."


def coller_texte(texte: str):
    """Copie le texte et le colle dans l'application active via AppleScript."""
    pyperclip.copy(texte)
    script = 'tell application "System Events" to keystroke "v" using command down'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def est_en_mode_dictee() -> bool:
    return MODE_DICTEE


def traiter_commande_dictee(texte: str) -> str | None:
    """Interprète les commandes liées à la dictée."""
    t = texte.lower()
    if any(x in t for x in ["mode dictée", "active la dictée", "commence à dicter", "dicte"]):
        return activer_dictee()
    if any(x in t for x in ["arrête la dictée", "stop dictée", "désactive la dictée"]):
        return desactiver_dictee()
    if MODE_DICTEE:
        # En mode dictée, on colle le texte dans l'app active
        coller_texte(texte)
        return f"✍️ Texte dicté : '{texte[:50]}...'" if len(texte) > 50 else f"✍️ Texte dicté : '{texte}'"
    return None
