"""
VISION — État Mutable Global
Toutes les variables d'état partagées entre modules.
Chaque module importe `from modules import state` et accède via `state.variable`.
"""

from google.genai import types as genai_types

# ── Historique de conversation IA ────────────────────────────────────────────
historique = []

# ── États du système ─────────────────────────────────────────────────────────
is_listening  = False
is_speaking   = False
is_thinking   = False
speak_volume  = 0.0

# ── Session vocale ───────────────────────────────────────────────────────────
vision_actif    = False
dernier_message = 0
STOP_PARLER     = False

import threading
speak_lock = threading.Lock()

# ── Paramètres Voix TTS ──────────────────────────────────────────────────────
tts_rate   = "+0%"   # edge-tts rate (ex: "+25%", "+0%", "-15%")
tts_speed  = 160     # pyttsx3 rate (ex: 130, 160, 190)
tts_volume = 1.0     # Volume de lecture (0.0 à 1.0)

# ── Modes ────────────────────────────────────────────────────────────────────
MODE_IRON_MAN = False
MODE_GARDE    = False
MODE_ANALYSE  = False
VIDEO_LANCEE  = False
PROFIL_ACTIF  = "vision"  # "vision" | "adjoua"

# ── Audio mobile ─────────────────────────────────────────────────────────────
_skip_pc_audio = False

# ── Fichiers ─────────────────────────────────────────────────────────────────
dossier_courant = None

# ── Google Docs ──────────────────────────────────────────────────────────────
dernier_doc_id    = None
dernier_doc_titre = None

# ── Data Science ─────────────────────────────────────────────────────────────
_data_df   = None   # DataFrame courant
_data_path = None   # Chemin du fichier source

# ── WebSocket ────────────────────────────────────────────────────────────────
CONNECTED_CLIENTS = set()
interface_deja_connectee = False
PENDING_CAPTURES = {}
main_loop = None

# ── Génération de sites ──────────────────────────────────────────────────────
site_en_creation_desc = None
site_en_creation_attente_ia = False

# ── Historique limité ─────────────────────────────────────────────────────────
MAX_HISTORIQUE = 40  # 20 échanges × 2 messages (user + model)
session_messages = []
history_ui = []  # Pour l'UI front-end (les 50 derniers messages)

def ajouter_histoire_ui(role, message):
    """Ajoute un message à l'historique UI (les 50 derniers)."""
    global history_ui
    if message:
        history_ui.append({"role": role, "text": message})
        if len(history_ui) > 50:
            history_ui = history_ui[-50:]

def ajouter_historique(contenu):
    """Ajoute un message à l'historique et tronque aux MAX_HISTORIQUE derniers."""
    global historique, session_messages
    historique.append(contenu)
    if len(historique) > MAX_HISTORIQUE:
        historique = historique[-MAX_HISTORIQUE:]
    if vision_actif:
        session_messages.append(contenu)
