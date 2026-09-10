"""
VISION — Module de Suivi des Coûts & Routage LLM par Budget
Suit l'utilisation des tokens API (Gemini, Groq, Grok, OpenAI), calcule les dépenses,
déclenche des alertes vocales à 80% du budget et bascule automatiquement sur Ollama (local).
"""

import os
import json
from datetime import datetime

BUDGET_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vision_budget.json")

# Tarifs estimés par million de tokens ($/1M tokens)
PRICES_PER_1M = {
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.5-flash-lite": {"input": 0.0375, "output": 0.15},
    "grok-2": {"input": 2.00, "output": 10.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "groq-llama-3.3-70b": {"input": 0.59, "output": 0.79},
    "ollama-local": {"input": 0.0, "output": 0.0},
}

BUDGET_MAX_MENSUEL = 10.00  # Limite par défaut : 10$ par mois
ALERTE_PCT = 0.80           # Seuil alerte à 80%

def charger_budget():
    """Charge l'historique des dépenses."""
    if os.path.exists(BUDGET_FILE):
        try:
            with open(BUDGET_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[BUDGET] Erreur chargement budget : {e}")
    
    mois_actuel = datetime.now().strftime("%Y-%m")
    return {
        "mois": mois_actuel,
        "cout_total_mois": 0.0,
        "tokens_input_total": 0,
        "tokens_output_total": 0,
        "detail_par_modele": {},
        "alerte_80_emise": False,
        "force_local_budget": False
    }

def sauvegarder_budget(data):
    """Sauvegarde le budget dans le fichier JSON."""
    try:
        with open(BUDGET_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[BUDGET] Erreur sauvegarde budget : {e}")

def enregistrer_consommation_llm(model_name, tokens_in, tokens_out):
    """
    Enregistre les tokens consommés et met à jour le coût total du mois.
    Retourne (statut_budget, message_alerte).
    """
    data = charger_budget()
    mois_actuel = datetime.now().strftime("%Y-%m")

    # Réinitialisation mensuelle si nouveau mois
    if data.get("mois") != mois_actuel:
        data = {
            "mois": mois_actuel,
            "cout_total_mois": 0.0,
            "tokens_input_total": 0,
            "tokens_output_total": 0,
            "detail_par_modele": {},
            "alerte_80_emise": False,
            "force_local_budget": False
        }

    tarifs = PRICES_PER_1M.get(model_name, {"input": 0.10, "output": 0.40})
    cout_in = (tokens_in / 1_000_000) * tarifs["input"]
    cout_out = (tokens_out / 1_000_000) * tarifs["output"]
    cout_appel = cout_in + cout_out

    data["cout_total_mois"] += cout_appel
    data["tokens_input_total"] += tokens_in
    data["tokens_output_total"] += tokens_out

    if model_name not in data["detail_par_modele"]:
        data["detail_par_modele"][model_name] = {"cout": 0.0, "in": 0, "out": 0}
    
    data["detail_par_modele"][model_name]["cout"] += cout_appel
    data["detail_par_modele"][model_name]["in"] += tokens_in
    data["detail_par_modele"][model_name]["out"] += tokens_out

    statut = "OK"
    message_alerte = None

    cout_actuel = data["cout_total_mois"]
    ratio = cout_actuel / BUDGET_MAX_MENSUEL

    if ratio >= 1.0:
        data["force_local_budget"] = True
        statut = "DEPASSEMENT"
        message_alerte = "Alerte budget : Le plafond mensuel LLM est atteint. Bascule automatique en mode local 100% gratuit."
    elif ratio >= ALERTE_PCT and not data.get("alerte_80_emise", False):
        data["alerte_80_emise"] = True
        statut = "ALERTE_80"
        message_alerte = f"Attention Syndou, vous avez consommé {ratio*100:.0f}% de votre budget LLM mensuel ({cout_actuel:.2f}$ / {BUDGET_MAX_MENSUEL:.2f}$). Erreur d'accès futur prévenue."

    sauvegarder_budget(data)
    return statut, message_alerte

def dois_forcer_local():
    """Vérifie si le budget impose un basculement strict vers le modèle local."""
    data = charger_budget()
    return data.get("force_local_budget", False)

def obtenir_resume_budget():
    """Retourne une synthèse textuelle du budget courant."""
    data = charger_budget()
    return (
        f"Budget mensuel : {data['cout_total_mois']:.3f}$ sur {BUDGET_MAX_MENSUEL:.2f}$ "
        f"({(data['cout_total_mois']/BUDGET_MAX_MENSUEL)*100:.1f}%). "
        f"Tokens utilisés : {data['tokens_input_total'] + data['tokens_output_total']:,}."
    )
