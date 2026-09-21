"""
VISION — Suivi de Santé
Enregistre et suit les données de santé : calories, eau, sommeil, exercice.
Inspiré de health_data.json de Jarvis AI.
"""
import json
import os
from datetime import datetime, date

SANTE_FILE = os.path.expanduser("~/VISION/data/sante.json")


def _charger():
    os.makedirs(os.path.dirname(SANTE_FILE), exist_ok=True)
    if os.path.exists(SANTE_FILE):
        with open(SANTE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _sauvegarder(data):
    os.makedirs(os.path.dirname(SANTE_FILE), exist_ok=True)
    with open(SANTE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _jour_courant():
    return date.today().strftime("%Y-%m-%d")


def _entree_du_jour():
    data = _charger()
    today = _jour_courant()
    if today not in data:
        data[today] = {
            "calories": 0,
            "eau_ml": 0,
            "sommeil_h": 0,
            "exercice_min": 0,
            "activites": [],
            "repas": [],
            "humeur": None
        }
        _sauvegarder(data)
    return data, today


def ajouter_calories(quantite: int, repas: str = "") -> str:
    data, today = _entree_du_jour()
    data[today]["calories"] += quantite
    if repas:
        data[today]["repas"].append({"nom": repas, "calories": quantite, "heure": datetime.now().strftime("%H:%M")})
    _sauvegarder(data)
    total = data[today]["calories"]
    return f"✅ {quantite} kcal ajoutées. Total du jour : {total} kcal."


def ajouter_eau(quantite_ml: int) -> str:
    data, today = _entree_du_jour()
    data[today]["eau_ml"] += quantite_ml
    _sauvegarder(data)
    total = data[today]["eau_ml"]
    verres = round(total / 250)
    return f"💧 {quantite_ml}ml d'eau ajoutés. Total : {total}ml ({verres} verres)."


def ajouter_sommeil(heures: float) -> str:
    data, today = _entree_du_jour()
    data[today]["sommeil_h"] = heures
    _sauvegarder(data)
    qualite = "excellent" if heures >= 8 else "bon" if heures >= 7 else "insuffisant"
    return f"😴 {heures}h de sommeil enregistrées. Qualité : {qualite}."


def ajouter_exercice(minutes: int, activite: str = "") -> str:
    data, today = _entree_du_jour()
    data[today]["exercice_min"] += minutes
    if activite:
        data[today]["activites"].append({"nom": activite, "duree_min": minutes})
    _sauvegarder(data)
    total = data[today]["exercice_min"]
    return f"🏃 {minutes} min d'exercice{f' ({activite})' if activite else ''}. Total : {total} min."


def enregistrer_humeur(humeur: str) -> str:
    data, today = _entree_du_jour()
    data[today]["humeur"] = humeur
    _sauvegarder(data)
    return f"Humeur enregistrée : {humeur}. Merci Monsieur."


def resume_du_jour() -> str:
    data, today = _entree_du_jour()
    d = data[today]
    
    resume = f"📊 **Résumé santé du {today}**\n"
    resume += f"🍽️ Calories : {d['calories']} kcal\n"
    resume += f"💧 Eau : {d['eau_ml']} ml\n"
    resume += f"😴 Sommeil : {d['sommeil_h']}h\n"
    resume += f"🏃 Exercice : {d['exercice_min']} min\n"
    if d.get("humeur"):
        resume += f"💭 Humeur : {d['humeur']}\n"

    # Conseils
    if d["eau_ml"] < 1500:
        resume += "\n⚠️ Pensez à boire davantage d'eau !"
    if d["exercice_min"] < 30:
        resume += "\n⚠️ Essayez d'être plus actif aujourd'hui."
    
    return resume


def traiter_commande_sante(texte: str) -> str | None:
    """Interprète les commandes vocales liées à la santé."""
    t = texte.lower()

    # Calories
    if "calorie" in t or "kcal" in t:
        import re
        nums = re.findall(r'\d+', t)
        if nums:
            cal = int(nums[0])
            repas = ""
            for mot in ["petit-déjeuner", "déjeuner", "dîner", "collation", "snack"]:
                if mot in t:
                    repas = mot
                    break
            return ajouter_calories(cal, repas)

    # Eau
    if "eau" in t or "verre" in t or "litre" in t or "ml" in t:
        import re
        nums = re.findall(r'\d+', t)
        if nums:
            ml = int(nums[0])
            if "litre" in t:
                ml *= 1000
            elif "verre" in t and ml < 10:
                ml *= 250
            return ajouter_eau(ml)
        elif "verre" in t:
            return ajouter_eau(250)

    # Sommeil
    if "sommeil" in t or "dormi" in t or "j'ai dormi" in t:
        import re
        nums = re.findall(r'\d+[.,]?\d*', t)
        if nums:
            heures = float(nums[0].replace(",", "."))
            return ajouter_sommeil(heures)

    # Exercice
    if any(x in t for x in ["exercice", "sport", "couru", "nagé", "marché", "gym", "entraînement"]):
        import re
        nums = re.findall(r'\d+', t)
        minutes = int(nums[0]) if nums else 30
        activite = ""
        for a in ["course", "natation", "marche", "vélo", "gym", "yoga", "football"]:
            if a in t:
                activite = a
                break
        return ajouter_exercice(minutes, activite)

    # Résumé santé
    if any(x in t for x in ["santé", "résumé santé", "bilan santé", "état de santé"]):
        return resume_du_jour()

    # Humeur
    if "humeur" in t or "je me sens" in t or "je suis" in t:
        for humeur in ["bien", "mal", "fatigué", "stressé", "heureux", "triste", "motivé", "anxieux"]:
            if humeur in t:
                return enregistrer_humeur(humeur)

    return None
