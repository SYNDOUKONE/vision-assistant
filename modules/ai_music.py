"""
VISION — Module AI Music
Intégration de l'API Musicful AI et fallback vers Hugging Face Spaces.
"""

import requests
import time
import asyncio
from modules.config import AIMUSIC_API_KEY

try:
    from gradio_client import Client
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False

API_URL = "https://api.musicful.ai"

def generer_musique_paid(prompt, style="moderne"):
    """
    Tente de générer une musique via l'API Musicful AI (Payante).
    """
    if not AIMUSIC_API_KEY:
        return False, "L'API Key pour AI Music est manquante."

    try:
        headers = {"x-api-key": AIMUSIC_API_KEY, "Content-Type": "application/json"}
        payload = {
            "action": "auto",
            "style": style,
            "mv": "MFV3.0",
            "gender": "female",
            "instrumental": 0
        }

        response = requests.post(f"{API_URL}/v1/music/generate", json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            return False, f"Erreur API ({response.status_code})"

        data = response.json()
        song_id = data.get("data", {}).get("song_id") or data.get("song_id")
        if not song_id:
            return False, "Aucun song_id trouvé."

        max_attempts = 30
        for _ in range(max_attempts):
            time.sleep(20)
            task_response = requests.get(f"{API_URL}/v1/music/tasks", params={"ids": song_id}, headers=headers, timeout=15)
            if task_response.status_code == 200:
                songs = task_response.json()
                if isinstance(songs, list) and len(songs) > 0:
                    song_data = songs[0]
                    if song_data.get("status") == "succeeded":
                        url = song_data.get("audio_url")
                        if url: return True, url
                    elif song_data.get("status") == "failed":
                        return False, "Génération échouée."
            else:
                pass
        return False, "Délai expiré."
    except Exception as e:
        return False, str(e)


# ─── Liste des Spaces HF à essayer en cascade ────────────────────────────────
# Chaque entrée : (space_id, api_name, input_param_index_or_kwargs)
HF_SPACES_CASCADE = [
    {
        "space":   "hitesh-aiml/Text-to-music-generator",
        "api":     "/generate_music",
        "inputs":  lambda p, s: (f"{s} {p}",),
        "parse":   lambda r: r[0] if isinstance(r, (list, tuple)) else r,
    },
    {
        "space":   "sanchit-gandhi/musicgen-large",
        "api":     "/predict",
        "inputs":  lambda p, s: (f"{s} {p}", 15.0),
        "parse":   lambda r: r[0] if isinstance(r, (list, tuple)) else r,
    },
    {
        "space":   "fffiloni/musicgen-large",
        "api":     "/predict",
        "inputs":  lambda p, s: (f"{s} {p}", 10.0),
        "parse":   lambda r: r[0] if isinstance(r, (list, tuple)) else r,
    },
]


def generer_musique_free(prompt, style="moderne"):
    """
    Génère une musique via une cascade de Spaces Hugging Face gratuits.
    Essaie chaque Space l'un après l'autre. En dernier recours, renvoie
    une URL YouTube de recherche pour que VISION joue quelque chose.
    """
    if not GRADIO_AVAILABLE:
        # Même sans gradio_client, on peut renvoyer une URL YouTube
        query = f"{style} {prompt}".replace(" ", "+")
        yt_url = f"https://www.youtube.com/results?search_query={query}"
        print("[AI MUSIC] gradio_client absent → fallback YouTube.")
        return True, yt_url

    for entry in HF_SPACES_CASCADE:
        space_id = entry["space"]
        api_name = entry["api"]
        try:
            print(f"[AI MUSIC] Essai Space : {space_id}...")
            client = Client(space_id, verbose=False)
            inputs = entry["inputs"](prompt, style)
            result = client.predict(*inputs, api_name=api_name)

            if result:
                audio_path = entry["parse"](result)
                if audio_path:
                    print(f"[AI MUSIC] ✅ Succès via {space_id} → {str(audio_path)[:80]}")
                    return True, audio_path

            print(f"[AI MUSIC] ⚠️  {space_id} a renvoyé un résultat vide.")

        except Exception as e:
            print(f"[AI MUSIC] ❌ {space_id} échoué : {e}")
            continue  # Passer au Space suivant

    # ── Fallback absolu : recherche YouTube ──────────────────────────────────
    query = f"{style} music {prompt}".replace(" ", "+")
    yt_url = f"https://www.youtube.com/results?search_query={query}"
    print(f"[AI MUSIC] Tous les Spaces HF ont échoué. Fallback YouTube : {yt_url}")
    return True, yt_url


def generer_musique(prompt, style="moderne"):
    """
    Fonction principale : Tente l'API payante, puis bascule sur le mode gratuit HF.
    """
    # 1. Tentative API Payante
    ok, result = generer_musique_paid(prompt, style)

    if ok:
        return True, result

    # 2. Fallback vers Hugging Face si l'API payante a échoué (ex: solde insuffisant)
    print(f"[AI MUSIC] API payante échouée ({result}), bascule vers mode Gratuit (Hugging Face)...")
    return generer_musique_free(prompt, style)

def rechercher_musique_ai(query):
    """
    Recherche un morceau via l'API Musicful AI.
    """
    if not AIMUSIC_API_KEY:
        return None, "L'API Key pour AI Music est manquante."

    try:
        headers = {"x-api-key": AIMUSIC_API_KEY}
        response = requests.get(f"{API_URL}/v1/music/search", params={"q": query}, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        return None, f"Erreur API : {response.status_code}"
    except Exception as e:
        return None, str(e)
