"""
VISION — Musique
YouTube (recherche intelligente + lecture automatique).
"""

import re
import urllib.parse
import requests
from modules.config import YOUTUBE_API_KEY
from modules.file_manager import ouvrir_navigateur


def chercher_youtube_id(recherche):
    """Recherche une vidéo/musique sur YouTube et renvoie son videoId."""
    if not recherche:
        return None

    # 1. Essai avec l'API YouTube officielle si la clé est fournie
    if YOUTUBE_API_KEY and YOUTUBE_API_KEY != "VOTRE_CLE_ICI":
        try:
            r = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "q": recherche, "type": "video", "maxResults": 1, "key": YOUTUBE_API_KEY},
                timeout=5
            )
            items = r.json().get("items", [])
            if items and "id" in items[0] and "videoId" in items[0]["id"]:
                return items[0]["id"]["videoId"]
        except Exception as e:
            print(f"[YOUTUBE API ERROR] {e}")

    # 2. Recherche HTML directe sans clé API (fallback ultra-fiable)
    try:
        query_enc = urllib.parse.quote_plus(recherche)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(f"https://www.youtube.com/results?search_query={query_enc}", headers=headers, timeout=5)
        video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', r.text)
        if video_ids:
            return video_ids[0]
    except Exception as e:
        print(f"[YOUTUBE SCRAPING ERROR] {e}")

    return None


def chercher_youtube(recherche):
    """Recherche une vidéo/musique sur YouTube et renvoie l'URL de la vidéo."""
    vid = chercher_youtube_id(recherche)
    if vid:
        return f"https://www.youtube.com/watch?v={vid}"
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(recherche)}"


async def jouer_musique_youtube(recherche):
    """Lance une musique ou vidéo sur YouTube."""
    if not recherche:
        return "Quelle musique souhaitez-vous écouter sur YouTube, Syndou ?"
    
    url = chercher_youtube(recherche)
    if url:
        ouvrir_navigateur(url)
        return f"C'est parti Syndou, je lance '{recherche}' sur YouTube."
    return f"Désolé Syndou, je n'ai pas pu trouver '{recherche}' sur YouTube."


# Alias pour rétrocompatibilité
async def jouer_musique_spotify(recherche):
    """Redirige systématiquement vers YouTube."""
    return await jouer_musique_youtube(recherche)


async def reconnaître_musique_actuelle(duree_sec=5):
    """
    Capture l'audio du microphone pendant `duree_sec` secondes
    et identifie la musique en cours via Shazam (`shazamio`).
    """
    print(f"[RECONNAISSANCE MUSICALE] Écoute de l'extrait audio pendant {duree_sec}s...")
    temp_audio_file = "temp_shazam_capture.wav"
    
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.record(source, duration=duree_sec)
            with open(temp_audio_file, "wb") as f:
                f.write(audio.get_wav_data())

        from shazamio import Shazam
        shazam = Shazam()
        out = await shazam.recognize(temp_audio_file)

        import os
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)

        track = out.get("track", {})
        if track:
            titre = track.get("title", "Inconnu")
            artiste = track.get("subtitle", "Artiste inconnu")
            genre = track.get("genres", {}).get("primary", "")
            return f"C'est '{titre}' par {artiste}" + (f" (Genre: {genre})." if genre else ".")
        else:
            return "Désolé Syndou, je n'ai pas réussi à identifier cette musique."
    except ImportError:
        import os
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)
        return "Le module 'shazamio' n'est pas installé. Veuillez l'installer avec `pip install shazamio`."
    except Exception as e:
        print(f"[RECONNAISSANCE MUSICALE] Erreur : {e}")
        import os
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)
        return f"Erreur lors de la reconnaissance musicale : {e}"


