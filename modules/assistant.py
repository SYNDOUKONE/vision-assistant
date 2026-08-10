import json
import os
import time
import asyncio
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vision_perso.json")
SCHEDULE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vision_schedule.json")

def _load_data(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_data(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ── Tâches ─────────────────────────────────────────────────────────────

def ajouter_tache(tache):
    data = _load_data(DATA_FILE)
    taches = data.get("taches", [])
    taches.append({"nom": tache, "date": datetime.now().isoformat(), "statut": "en cours"})
    data["taches"] = taches
    _save_data(DATA_FILE, data)
    return f"J'ai ajouté '{tache}' à votre liste de tâches, Syndou."

def lister_taches():
    data = _load_data(DATA_FILE)
    taches = data.get("taches", [])
    if not taches:
        return "Vous n'avez aucune tâche en cours, Syndou."
    res = "Voici tes tâches à faire :\n"
    for i, t in enumerate(taches, 1):
        res += f"{i}. {t['nom']} ({t['statut']})\n"
    return res

def finir_tache(index):
    data = _load_data(DATA_FILE)
    taches = data.get("taches", [])
    index = int(index) - 1
    if 0 <= index < len(taches):
        t = taches[index]
        t["statut"] = "terminé"
        _save_data(DATA_FILE, data)
        return f"Bien joué ! J'ai marqué '{t['nom']}' comme terminé."
    return "Je ne trouve pas cette tâche."

# ── Objectifs ──────────────────────────────────────────────────────────

def ajouter_objectif(objectif):
    data = _load_data(DATA_FILE)
    obj = data.get("objectifs", [])
    obj.append({"nom": objectif, "date": datetime.now().isoformat()})
    data["objectifs"] = obj
    _save_data(DATA_FILE, data)
    return f"Super, j'ai noté ce nouvel objectif : '{objectif}'. On va y arriver !"

def lister_objectifs():
    data = _load_data(DATA_FILE)
    obj = data.get("objectifs", [])
    if not obj:
        return "Tu n'as pas encore défini d'objectifs."
    res = "Voici tes objectifs du moment :\n"
    for i, o in enumerate(obj, 1):
        res += f"{i}. {o['nom']}\n"
    return res

# ── Scheduler ──────────────────────────────────────────────────────────

def planifier_tache(cron_expr, commande):
    data = _load_data(SCHEDULE_FILE)
    sched = data.get("schedules", [])
    sched.append({"frequence": cron_expr, "commande": commande, "last_run": 0})
    data["schedules"] = sched
    _save_data(SCHEDULE_FILE, data)
    return f"C'est noté ! Je ferai ça '{cron_expr}' : {commande}."
