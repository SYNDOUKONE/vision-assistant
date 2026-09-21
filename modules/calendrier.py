"""
VISION — Calendrier Local
Gestion de rendez-vous et événements sans dépendance Google.
Inspiré de jarvis_calendar.json de Jarvis AI.
"""
import json
import os
from datetime import datetime, date
import re

CALENDAR_FILE = os.path.expanduser("~/VISION/data/calendrier.json")


def _charger():
    os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _sauvegarder(events):
    os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def ajouter_evenement(titre: str, date_str: str, heure_str: str = "09:00", description: str = "") -> str:
    """Ajoute un événement au calendrier."""
    events = _charger()
    event = {
        "id": len(events) + 1,
        "titre": titre,
        "date": date_str,
        "heure": heure_str,
        "description": description,
        "cree_le": datetime.now().isoformat()
    }
    events.append(event)
    _sauvegarder(events)
    return f"✅ Événement '{titre}' ajouté le {date_str} à {heure_str}."


def lister_evenements_du_jour() -> str:
    """Retourne les événements d'aujourd'hui."""
    today = date.today().strftime("%Y-%m-%d")
    events = [e for e in _charger() if e.get("date", "") == today]
    if not events:
        return "Aucun événement prévu aujourd'hui, Monsieur."
    lignes = [f"• {e['heure']} — {e['titre']}" + (f" ({e['description']})" if e.get("description") else "")
              for e in sorted(events, key=lambda x: x.get("heure", ""))]
    return "📅 Agenda d'aujourd'hui :\n" + "\n".join(lignes)


def lister_evenements_semaine() -> str:
    """Retourne les événements de la semaine."""
    from datetime import timedelta
    today = date.today()
    dates_semaine = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    events = [e for e in _charger() if e.get("date", "") in dates_semaine]
    if not events:
        return "Aucun événement cette semaine, Monsieur."
    events_tries = sorted(events, key=lambda x: (x.get("date", ""), x.get("heure", "")))
    lignes = [f"• {e['date']} {e['heure']} — {e['titre']}" for e in events_tries]
    return "📅 Agenda de la semaine :\n" + "\n".join(lignes)


def supprimer_evenement(titre: str) -> str:
    """Supprime un événement par son titre."""
    events = _charger()
    avant = len(events)
    events = [e for e in events if titre.lower() not in e.get("titre", "").lower()]
    if len(events) < avant:
        _sauvegarder(events)
        return f"✅ Événement '{titre}' supprimé."
    return f"Aucun événement trouvé avec le titre '{titre}'."


def prochain_evenement() -> str:
    """Retourne le prochain événement à venir."""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    events = sorted(_charger(), key=lambda x: f"{x.get('date','')} {x.get('heure','')}")
    futurs = [e for e in events if f"{e.get('date','')} {e.get('heure','')}" >= today]
    if not futurs:
        return "Aucun événement à venir dans votre calendrier, Monsieur."
    e = futurs[0]
    return f"⏭️ Prochain événement : '{e['titre']}' le {e['date']} à {e['heure']}."


def traiter_commande_calendrier(texte: str) -> str | None:
    """Interprète les commandes vocales liées au calendrier."""
    t = texte.lower()

    if any(x in t for x in ["agenda", "calendrier", "planning", "rendez-vous", "événement"]):

        # Afficher aujourd'hui
        if any(x in t for x in ["aujourd'hui", "du jour", "today"]):
            return lister_evenements_du_jour()

        # Afficher la semaine
        if "semaine" in t:
            return lister_evenements_semaine()

        # Prochain événement
        if "prochain" in t or "prochaine" in t:
            return prochain_evenement()

        # Ajouter un événement
        if any(x in t for x in ["ajoute", "crée", "planifie", "schedule", "fixe"]):
            # Tenter d'extraire titre + date
            # Exemple: "ajoute un rendez-vous dentiste demain à 14h"
            maintenant = datetime.now()
            date_event = maintenant.strftime("%Y-%m-%d")
            heure_event = "09:00"

            if "demain" in t:
                from datetime import timedelta
                date_event = (maintenant + timedelta(days=1)).strftime("%Y-%m-%d")
            elif "lundi" in t:
                date_event = _prochain_jour_semaine(0)
            elif "mardi" in t:
                date_event = _prochain_jour_semaine(1)
            elif "mercredi" in t:
                date_event = _prochain_jour_semaine(2)
            elif "jeudi" in t:
                date_event = _prochain_jour_semaine(3)
            elif "vendredi" in t:
                date_event = _prochain_jour_semaine(4)
            elif "samedi" in t:
                date_event = _prochain_jour_semaine(5)
            elif "dimanche" in t:
                date_event = _prochain_jour_semaine(6)

            # Extraire l'heure (ex: "14h", "14h30", "à 14:30")
            match_h = re.search(r'à (\d{1,2})h(\d{0,2})', t)
            if match_h:
                h = match_h.group(1).zfill(2)
                m = match_h.group(2).zfill(2) if match_h.group(2) else "00"
                heure_event = f"{h}:{m}"

            # Extraire le titre (supprimer les mots de commande)
            titre = texte
            for mot in ["ajoute", "crée", "planifie", "fixe", "un rendez-vous", "une réunion",
                        "un événement", "demain", "lundi", "mardi", "mercredi", "jeudi",
                        "vendredi", "samedi", "dimanche", "agenda", "calendrier", "à", "pour"]:
                titre = re.sub(mot, "", titre, flags=re.IGNORECASE).strip()
            titre = re.sub(r'\d{1,2}h\d{0,2}', '', titre).strip() or "Événement"

            return ajouter_evenement(titre.capitalize(), date_event, heure_event)

        # Supprimer
        if any(x in t for x in ["supprime", "annule", "efface"]):
            mot_cle = t.replace("supprime", "").replace("annule", "").replace("l'événement", "").strip()
            return supprimer_evenement(mot_cle)

        # Fallback
        return lister_evenements_du_jour()

    return None


def _prochain_jour_semaine(jour: int) -> str:
    """Retourne la date du prochain jour de la semaine (0=lundi, 6=dimanche)."""
    from datetime import timedelta
    today = date.today()
    jours_jusqua = (jour - today.weekday()) % 7
    if jours_jusqua == 0:
        jours_jusqua = 7
    return (today + timedelta(days=jours_jusqua)).strftime("%Y-%m-%d")
