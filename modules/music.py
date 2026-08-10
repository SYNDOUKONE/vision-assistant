"""
VISION — Musique
Spotify (API) et YouTube (recherche + lecture).
"""

import requests
from modules.config import sp, YOUTUBE_API_KEY
from modules.file_manager import ouvrir_navigateur


def chercher_youtube(recherche):
    try:
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "q": recherche, "type": "video", "maxResults": 1, "key": YOUTUBE_API_KEY},
            timeout=5
        )
        vid = r.json()["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={vid}"
    except Exception as e:
        print(f"Erreur YouTube : {e}")
        return None


async def jouer_musique_spotify(recherche):
    if not sp:
        return "Spotify n'est pas configuré Syndou. Veuillez renseigner vos clés dans le fichier .env."
    try:
        results = sp.search(q=recherche, limit=1, type='track')
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            track_uri = track['uri']
            devices = sp.devices()
            if devices['devices']:
                active_device = next((d for d in devices['devices'] if d['is_active']), devices['devices'][0])
                sp.start_playback(device_id=active_device['id'], uris=[track_uri])
                return f"Je lance '{track['name']}' de {track['artists'][0]['name']} sur votre Spotify."
            else:
                url = track['external_urls']['spotify']
                ouvrir_navigateur(url)
                return f"J'ai trouvé '{track['name']}', mais aucun appareil Spotify n'est actif. Je l'ouvre dans le navigateur."
        return f"Je n'ai pas trouvé '{recherche}' sur Spotify."
    except Exception as e:
        print(f"[SPOTIFY ERROR] {e}")
        return "Une erreur est survenue lors de l'accès à Spotify."
