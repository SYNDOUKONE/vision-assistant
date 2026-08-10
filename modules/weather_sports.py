"""
VISION — Météo & Sports
Météo (Open-Meteo) et résultats sportifs (TheSportsDB + Gemini).
"""

import time
import requests
from modules.config import (
    VILLE_PAR_DEFAUT, LAT_PAR_DEFAUT, LON_PAR_DEFAUT,
    CODES_METEO, gemini_client, CHOSEN_MODEL, genai_types
)


# ── Cache Système ────────────────────────────────────────────────────────────

_cache_meteo_sport = {}
CACHE_DURATION_SEC = 600

# ── Météo ────────────────────────────────────────────────────────────────────

def geocoder_ville(ville):
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": ville, "count": 1, "language": "fr", "format": "json"},
            timeout=5
        )
        data = r.json()
        if data.get("results"):
            res = data["results"][0]
            return res["latitude"], res["longitude"], res.get("name", ville), res.get("country", "")
    except Exception as e:
        print(f"[METEO] Erreur geocoding : {e}")
    return None, None, ville, ""


def get_meteo_actuelle(ville=None):
    nom_ville = ville or VILLE_PAR_DEFAUT
    cache_key = ("meteo", nom_ville)
    if cache_key in _cache_meteo_sport and time.time() - _cache_meteo_sport[cache_key][1] < CACHE_DURATION_SEC:
        return _cache_meteo_sport[cache_key][0]

    try:
        lat, lon, nom_affiche, pays = geocoder_ville(nom_ville)
        if lat is None:
            lat, lon = LAT_PAR_DEFAUT, LON_PAR_DEFAUT
            nom_affiche = VILLE_PAR_DEFAUT
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weathercode,precipitation",
                "hourly": "temperature_2m,precipitation_probability",
                "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,wind_speed_10m_max,sunrise,sunset",
                "timezone": "Europe/Paris",
                "forecast_days": 3,
                "wind_speed_unit": "kmh",
            },
            timeout=8
        )
        data = r.json()
        cur = data["current"]
        code = cur.get("weathercode", 0)
        desc = CODES_METEO.get(code, "conditions inconnues")
        temp = round(float(cur.get("temperature_2m", 0)))
        res = f"À {nom_affiche}, il fait {temp} degrés et le ciel est {desc}. C'est tout."
        _cache_meteo_sport[cache_key] = (res, time.time())
        return res
    except Exception as e:
        print(f"[METEO] Erreur : {e}")
        return "Je n'arrive pas à récupérer la météo pour le moment."


def get_alertes_meteo(ville=None):
    nom_ville = ville or VILLE_PAR_DEFAUT
    cache_key = ("alertes", nom_ville)
    if cache_key in _cache_meteo_sport and time.time() - _cache_meteo_sport[cache_key][1] < CACHE_DURATION_SEC:
        return _cache_meteo_sport[cache_key][0]

    try:
        lat, lon, nom_affiche, _ = geocoder_ville(nom_ville)
        if lat is None:
            lat, lon, nom_affiche = LAT_PAR_DEFAUT, LON_PAR_DEFAUT, VILLE_PAR_DEFAUT
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "daily": "weathercode,precipitation_sum,wind_speed_10m_max",
                "timezone": "Europe/Paris", "forecast_days": 3,
            },
            timeout=8
        )
        data = r.json()
        daily = data["daily"]
        alertes = []
        for i in range(len(daily["weathercode"])):
            code = daily["weathercode"][i]
            pluie = daily.get("precipitation_sum", [0] * 3)[i] or 0
            vent = daily.get("wind_speed_10m_max", [0] * 3)[i] or 0
            jour = ["aujourd hui", "demain", "apres-demain"][i]
            if code in [95, 96, 99]:
                alertes.append(f"Orage prevu {jour}")
            if code in [71, 73, 75, 85, 86]:
                alertes.append(f"Neige prevue {jour}")
            if pluie > 20:
                alertes.append(f"Fortes pluies {jour} ({pluie}mm)")
            if vent > 60:
                alertes.append(f"Vents forts {jour} ({vent} km/h)")
        if alertes:
            res = f"Alertes meteo pour {nom_affiche} : " + ", ".join(alertes) + "."
        else:
            res = f"Aucune alerte meteo pour {nom_affiche} dans les 3 prochains jours."
        _cache_meteo_sport[cache_key] = (res, time.time())
        return res
    except Exception as e:
        return f"Impossible de verifier les alertes meteo : {e}"


# ── Sports ───────────────────────────────────────────────────────────────────

THESPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json/3"

LIGUE_IDS = {
    "ligue 1": "4334", "premier league": "4328", "liga": "4335",
    "bundesliga": "4331", "serie a": "4332",
    "champions league": "4480", "ligue des champions": "4480",
}


def get_resultats_football(equipe=None, ligue=None):
    cache_key = ("foot_res", equipe, ligue)
    if cache_key in _cache_meteo_sport and time.time() - _cache_meteo_sport[cache_key][1] < CACHE_DURATION_SEC:
        return _cache_meteo_sport[cache_key][0]

    try:
        if equipe:
            print(f"[SPORT] Recherche pour l'equipe : {equipe}")
            r = requests.get(f"{THESPORTSDB_BASE}/searchteams.php", params={"t": equipe}, timeout=5)
            data = r.json()
            teams = data.get("teams")
            if not teams:
                return f"Je n'ai pas trouvé l'équipe {equipe}."
            team_id = teams[0]["idTeam"]
            team_name = teams[0]["strTeam"]

            res_last = requests.get(f"{THESPORTSDB_BASE}/eventslast.php", params={"id": team_id}, timeout=5).json()
            res_next = requests.get(f"{THESPORTSDB_BASE}/eventsnext.php", params={"id": team_id}, timeout=5).json()

            matchs_passes = res_last.get("results", [])
            matchs_futurs = res_next.get("events", [])

            reponse = f"Concernant le {team_name} : "
            if matchs_futurs:
                m = matchs_futurs[0]
                date_m = m.get("dateEvent", "date inconnue")
                heure_m = m.get("strTime", "")
                reponse += f"Le prochain match aura lieu le {date_m} à {heure_m} contre {m.get('strOpponent')}. "
            if matchs_passes:
                m = matchs_passes[0]
                reponse += f"Leur dernier résultat était {m.get('intHomeScore')} à {m.get('intAwayScore')} contre {m.get('strOpponent')}."
            if not matchs_futurs and not matchs_passes:
                return f"Je n'ai pas d'informations récentes ou futures pour {team_name}."
            _cache_meteo_sport[cache_key] = (reponse, time.time())
            return reponse
        else:
            nom_ligue = ligue or "Ligue 1"
            ligue_id = LIGUE_IDS.get(nom_ligue.lower(), "4334")
            r = requests.get(f"{THESPORTSDB_BASE}/eventspastleague.php", params={"id": ligue_id}, timeout=5)
            data = r.json()
            matchs = data.get("events", [])
            if not matchs:
                return f"Aucun resultat trouve pour {nom_ligue}."
            reponse = f"Derniers resultats {nom_ligue} : "
            lignes = []
            for m in matchs[-6:]:
                home = m.get("strHomeTeam", "?")
                away = m.get("strAwayTeam", "?")
                score_h = m.get("intHomeScore", "?")
                score_a = m.get("intAwayScore", "?")
                date = m.get("dateEvent", "?")
                lignes.append(f"{home} {score_h}-{score_a} {away} ({date})")
            res = reponse + " | ".join(lignes)
            _cache_meteo_sport[cache_key] = (res, time.time())
            return res
    except Exception as e:
        print(f"[SPORT] Erreur football : {e}")
        return f"Impossible de recuperer les resultats football : {e}"


def get_classement_football(ligue=None):
    nom_ligue = ligue or "Ligue 1"
    cache_key = ("foot_classement", nom_ligue)
    if cache_key in _cache_meteo_sport and time.time() - _cache_meteo_sport[cache_key][1] < CACHE_DURATION_SEC:
        return _cache_meteo_sport[cache_key][0]

    try:
        ligue_id = LIGUE_IDS.get(nom_ligue.lower(), "4334")
        r = requests.get(f"{THESPORTSDB_BASE}/lookuptable.php", params={"l": ligue_id, "s": "2024-2025"}, timeout=8)
        data = r.json()
        tableau = data.get("table", [])
        if not tableau:
            return f"Classement {nom_ligue} non disponible pour le moment."
        reponse = f"Classement {nom_ligue} : "
        lignes = []
        for eq in tableau[:10]:
            pos = eq.get("intRank", "?")
            nom = eq.get("strTeam", "?")
            pts = eq.get("intPoints", "?")
            joues = eq.get("intPlayed", "?")
            lignes.append(f"{pos}. {nom} - {pts}pts ({joues}J)")
        res = reponse + " | ".join(lignes)
        _cache_meteo_sport[cache_key] = (res, time.time())
        return res
    except Exception as e:
        print(f"[SPORT] Erreur classement : {e}")
        return f"Impossible de recuperer le classement : {e}"


def get_resultats_sport_gemini(question_sport):
    cache_key = ("sport_gemini", question_sport)
    if cache_key in _cache_meteo_sport and time.time() - _cache_meteo_sport[cache_key][1] < CACHE_DURATION_SEC:
        return _cache_meteo_sport[cache_key][0]

    try:
        response = gemini_client.models.generate_content(
            model=CHOSEN_MODEL,
            contents=[genai_types.Content(role="user", parts=[genai_types.Part(text=
                f"Donne-moi les derniers resultats et actualites sportives en 2026 "
                f"pour : {question_sport}. "
                f"Sois precis, donne les scores et dates. Reponds en francais."
            )])],
            config=genai_types.GenerateContentConfig(
                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                system_instruction=(
                    "Tu es un expert sportif. Donne des resultats precis et a jour. "
                    "Reponds de facon concise et conversationnelle en francais."
                )
            )
        )
        res = response.text.strip()
        _cache_meteo_sport[cache_key] = (res, time.time())
        return res
    except Exception as e:
        print(f"[SPORT] Erreur Gemini sport : {e}")
        return "Je n arrive pas a recuperer les resultats sportifs pour le moment."
