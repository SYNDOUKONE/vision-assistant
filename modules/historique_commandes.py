"""
VISION — Historique des Commandes Persistant
Sauvegarde chaque commande/réponse avec timestamp dans un fichier JSON.
Inspiré du système command_history.json de Jarvis AI.
"""
import json
import os
from datetime import datetime

HISTORY_FILE = os.path.expanduser("~/VISION/data/historique_commandes.json")


def _charger():
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _sauvegarder(data):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def enregistrer_commande(commande: str, reponse: str, type_cmd: str = "text"):
    """Enregistre une commande et sa réponse dans l'historique."""
    historique = _charger()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": type_cmd,
        "commande": commande,
        "reponse": reponse[:500] if reponse else ""  # Limiter la taille
    }
    historique.append(entry)
    # Garder les 1000 dernières commandes
    if len(historique) > 1000:
        historique = historique[-1000:]
    _sauvegarder(historique)


def obtenir_historique(n: int = 20) -> list:
    """Retourne les n dernières commandes."""
    return _charger()[-n:]


def rechercher_historique(mot_cle: str) -> list:
    """Recherche dans l'historique par mot-clé."""
    historique = _charger()
    return [h for h in historique if mot_cle.lower() in h.get("commande", "").lower()]


def statistiques() -> dict:
    """Statistiques d'usage."""
    historique = _charger()
    if not historique:
        return {"total": 0}
    types = {}
    for h in historique:
        t = h.get("type", "text")
        types[t] = types.get(t, 0) + 1
    return {
        "total": len(historique),
        "par_type": types,
        "premiere_commande": historique[0]["date"] if historique else None,
        "derniere_commande": historique[-1]["date"] if historique else None
    }


def resumer_historique_commandes(texte: str) -> str | None:
    """Répond aux questions sur l'historique de commandes."""
    t = texte.lower()
    if any(x in t for x in ["historique", "commandes récentes", "dernières commandes", "qu'est-ce que j'ai dit"]):
        entries = obtenir_historique(10)
        if not entries:
            return "Aucune commande enregistrée pour l'instant, Monsieur."
        lignes = [f"• [{e['date']}] {e['commande'][:80]}" for e in reversed(entries)]
        return "Voici vos 10 dernières commandes :\n" + "\n".join(lignes)

    if "statistiques" in t or "combien de commandes" in t:
        stats = statistiques()
        return (f"Statistiques VISION : {stats['total']} commandes enregistrées. "
                f"Première le {stats.get('premiere_commande', 'N/A')}.")

    if "recherche" in t or "cherche" in t:
        # Extraire le mot-clé après "cherche"
        parts = t.split("cherche", 1)
        if len(parts) > 1:
            mot = parts[1].strip().split()[0] if parts[1].strip() else ""
            if mot:
                resultats = rechercher_historique(mot)
                if resultats:
                    return f"J'ai trouvé {len(resultats)} commande(s) contenant '{mot}'."
                return f"Aucune commande contenant '{mot}' dans l'historique."

    return None
