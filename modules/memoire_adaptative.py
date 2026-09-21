"""
VISION — Mémoire Adaptative
Analyse les habitudes d'usage et adapte les suggestions/comportements de VISION.
Inspiré de adaptive_memory.json et jarvis_usage.json de Jarvis AI.
"""
import json
import os
from datetime import datetime, timedelta
from collections import Counter

ADAPTIVE_FILE = os.path.expanduser("~/VISION/data/memoire_adaptative.json")


def _charger():
    os.makedirs(os.path.dirname(ADAPTIVE_FILE), exist_ok=True)
    if os.path.exists(ADAPTIVE_FILE):
        with open(ADAPTIVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "commandes_frequentes": {},
        "heures_actives": {},
        "sujets_preferes": {},
        "style_reponse": "formel",
        "historique_sessions": [],
        "derniere_mise_a_jour": None
    }


def _sauvegarder(data):
    os.makedirs(os.path.dirname(ADAPTIVE_FILE), exist_ok=True)
    data["derniere_mise_a_jour"] = datetime.now().isoformat()
    with open(ADAPTIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def enregistrer_usage(commande: str):
    """Enregistre l'usage d'une commande pour les statistiques adaptatives."""
    data = _charger()
    heure = str(datetime.now().hour)
    
    # Commandes fréquentes
    cmd_key = commande.lower()[:50]
    data["commandes_frequentes"][cmd_key] = data["commandes_frequentes"].get(cmd_key, 0) + 1
    
    # Heures actives
    data["heures_actives"][heure] = data["heures_actives"].get(heure, 0) + 1
    
    # Détecter les sujets (mots-clés)
    mots = [m for m in commande.lower().split() if len(m) > 4]
    for mot in mots:
        data["sujets_preferes"][mot] = data["sujets_preferes"].get(mot, 0) + 1
    
    _sauvegarder(data)


def obtenir_suggestions() -> list:
    """Retourne les suggestions basées sur les habitudes."""
    data = _charger()
    suggestions = []
    
    heure_courante = datetime.now().hour
    
    # Suggestions matin
    if 6 <= heure_courante <= 9:
        suggestions.append("Voulez-vous un résumé des actualités matinales ?")
    
    # Suggestions midi
    if 11 <= heure_courante <= 13:
        suggestions.append("C'est l'heure du déjeuner. Avez-vous enregistré vos repas aujourd'hui ?")
    
    # Suggestions soir
    if 18 <= heure_courante <= 22:
        suggestions.append("Bonsoir ! Voulez-vous votre résumé de journée ?")

    # Basé sur les commandes fréquentes
    if data["commandes_frequentes"]:
        top = sorted(data["commandes_frequentes"].items(), key=lambda x: x[1], reverse=True)[:3]
        for cmd, count in top:
            if count > 5:
                suggestions.append(f"Je remarque que vous utilisez souvent '{cmd[:30]}...'")
    
    return suggestions[:3]  # Max 3 suggestions


def heure_plus_active() -> str | None:
    """Retourne l'heure où l'utilisateur est le plus actif."""
    data = _charger()
    if not data["heures_actives"]:
        return None
    heure = max(data["heures_actives"], key=data["heures_actives"].get)
    return f"{heure}h00"


def commandes_top(n: int = 5) -> list:
    """Retourne les n commandes les plus fréquentes."""
    data = _charger()
    sorted_cmds = sorted(data["commandes_frequentes"].items(), key=lambda x: x[1], reverse=True)
    return sorted_cmds[:n]


def rapport_adaptatif() -> str:
    """Génère un rapport sur les habitudes d'usage."""
    data = _charger()
    heure = heure_plus_active()
    top = commandes_top(3)
    
    rapport = "📊 **Rapport adaptatif VISION**\n"
    if heure:
        rapport += f"⏰ Vous êtes le plus actif vers {heure}\n"
    if top:
        rapport += "🔝 Vos commandes préférées :\n"
        for cmd, count in top:
            rapport += f"  • '{cmd[:40]}' ({count} fois)\n"
    
    return rapport


def traiter_commande_adaptative(texte: str) -> str | None:
    """Traite les commandes liées aux habitudes."""
    t = texte.lower()
    if any(x in t for x in ["mes habitudes", "mon usage", "rapport adaptatif", "statistiques d'usage"]):
        return rapport_adaptatif()
    if "suggestions" in t and "vision" in t:
        suggs = obtenir_suggestions()
        if suggs:
            return "Voici mes suggestions pour vous :\n" + "\n".join(f"• {s}" for s in suggs)
        return "Je n'ai pas encore assez de données pour vous suggérer quelque chose."
    return None
