"""
VISION — Home Assistant
Fonctions d'interaction avec la domotique Home Assistant.
"""

import requests
from datetime import datetime
from modules.config import HA_URL, HA_HEADERS


def ha_appeler_service(domaine, service, entity_id, donnees=None):
    try:
        payload = {"entity_id": entity_id}
        if donnees:
            payload.update(donnees)
        print(f"[HA DEBUG] Calling {domaine}/{service} for {entity_id} with {donnees}")
        r = requests.post(
            f"{HA_URL}/api/services/{domaine}/{service}",
            headers=HA_HEADERS, json=payload, timeout=5
        )
        print(f"[HA DEBUG] Response {r.status_code}: {r.text}")
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"[HA] Erreur service : {e}")
        return False


def ha_get_etat(entity_id, attribut=None):
    try:
        r = requests.get(f"{HA_URL}/api/states/{entity_id}", headers=HA_HEADERS, timeout=5)
        data = r.json()
        if attribut:
            return data.get("attributes", {}).get(attribut, "inconnu")
        return data.get("state", "inconnu")
    except Exception as e:
        print(f"[HA] Erreur get etat : {e}")
        return "inconnu"


def ha_get_calendrier(entity_id):
    try:
        now = datetime.now()
        start = now.strftime("%Y-%m-%dT00:00:00Z")
        end = now.strftime("%Y-%m-%dT23:59:59Z")
        r = requests.get(
            f"{HA_URL}/api/calendars/{entity_id}",
            headers=HA_HEADERS,
            params={"start": start, "end": end},
            timeout=5
        )
        return r.json()
    except Exception as e:
        print(f"[HA] Erreur calendrier : {e}")
        return []


def ha_lumiere(entity_id, etat="on", luminosite=None, rgb=None):
    service_name = "toggle" if etat == "toggle" else ("turn_on" if etat == "on" else "turn_off")
    donnees = {}
    if etat == "on":
        if luminosite is not None:
            donnees["brightness"] = int(luminosite)
        if rgb is not None:
            donnees["rgb_color"] = rgb
    return ha_appeler_service("light", service_name, entity_id, donnees)


def ha_interrupteur(entity_id, etat="on"):
    service_name = "turn_on" if etat == "on" else "turn_off"
    return ha_appeler_service("switch", service_name, entity_id)


def ha_thermostat(entity_id, temperature):
    return ha_appeler_service("climate", "set_temperature", entity_id, {"temperature": temperature})


def ha_scene(scene_id):
    return ha_appeler_service("scene", "turn_on", scene_id)
