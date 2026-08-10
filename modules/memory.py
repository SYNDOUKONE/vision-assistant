"""
VISION — Mémoire Persistante & Épisodique
Gestion de la mémoire clé/valeur stockée en JSON local avec catégories et résumés de session.
"""

import os
import json
import time
import asyncio
from modules import state

MEMOIRE_FILE = "vision_memoire.json"


def charger_memoire():
    """Charge la mémoire et effectue la migration automatique si nécessaire."""
    if os.path.exists(MEMOIRE_FILE):
        try:
            with open(MEMOIRE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Validation et migration automatique de l'ancien format
                if not isinstance(data, dict):
                    return {"facts": {}, "sessions": []}
                
                if "facts" not in data and "sessions" not in data:
                    print("[MEMOIRE] Détection de l'ancien format plat. Migration...")
                    nouveau = {"facts": {}, "sessions": []}
                    for k, val in data.items():
                        if isinstance(val, dict) and "valeur" in val:
                            nouveau["facts"][k] = {
                                "valeur": val["valeur"],
                                "timestamp": val.get("timestamp", ""),
                                "categorie": val.get("categorie", "general")
                            }
                    return nouveau
                
                if "facts" not in data:
                    data["facts"] = {}
                if "sessions" not in data:
                    data["sessions"] = []
                return data
        except Exception as e:
            print(f"[MEMOIRE] Erreur lecture fichier mémoire : {e}")
            return {"facts": {}, "sessions": []}
    return {"facts": {}, "sessions": []}


def sauvegarder_memoire(memoire):
    try:
        with open(MEMOIRE_FILE, "w", encoding="utf-8") as f:
            json.dump(memoire, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[MEMOIRE] Erreur sauvegarde mémoire : {e}")


def ajouter_memoire(cle, valeur, categorie="general"):
    """Ajoute ou modifie un fait en mémoire dans une catégorie donnée."""
    memoire = charger_memoire()
    
    valid_categories = ["preferences", "famille", "habitudes", "projets", "anniversaires", "general"]
    cat = categorie.lower().strip()
    if cat not in valid_categories:
        cat = "general"
        
    memoire["facts"][cle] = {
        "valeur": valeur,
        "timestamp": time.strftime("%d/%m/%Y %H:%M"),
        "categorie": cat
    }
    sauvegarder_memoire(memoire)
    print(f"[MEMOIRE] Fait ajouté : {cle} = {valeur} (Catégorie: {cat})")


def supprimer_memoire(cle):
    memoire = charger_memoire()
    if "facts" in memoire and cle in memoire["facts"]:
        val = memoire["facts"].pop(cle)
        sauvegarder_memoire(memoire)
        print(f"[MEMOIRE] Fait supprimé : {cle}")
        return True
    return False


def construire_contexte_memoire():
    """Génère le texte de mémoire à insérer dans le prompt système."""
    memoire = charger_memoire()
    lignes = []
    
    # 1. Faits catégorisés
    facts = memoire.get("facts", {})
    if facts:
        lignes.append("MEMOIRE PERSISTANTE (Informations et faits sur Syndou) :")
        cats = ["preferences", "famille", "habitudes", "projets", "anniversaires", "general"]
        for cat in cats:
            elements = [f"  - {k} : {data['valeur']}" for k, data in facts.items() if data.get("categorie", "general") == cat]
            if elements:
                lignes.append(f" Catégorie [{cat.upper()}] :")
                lignes.extend(elements)
                
    # 2. Mémoire épisodique (sessions de conversation récentes)
    sessions = memoire.get("sessions", [])
    if sessions:
        lignes.append("\nMEMOIRE EPISODIQUE (Résumé de vos sessions de discussion récentes) :")
        # Afficher les 5 dernières sessions de conversation
        for s in sessions[-5:]:
            lignes.append(f"  - Le {s.get('timestamp', '')} : {s.get('resume', '')}")
            
    return "\n".join(lignes)


async def enregistrer_resume_session_actuelle():
    """Génère un résumé de la session de conversation en cours et l'enregistre en mémoire."""
    from modules.config import gemini_client, MODELS_LIST
    
    if not state.session_messages:
        return
        
    messages_copy = list(state.session_messages)
    # Réinitialiser la liste pour la session suivante
    state.session_messages = []
    
    # Formater les messages pour le prompt de résumé
    conv_text = ""
    for msg in messages_copy:
        role = "Syndou" if msg.role == "user" else "VISION"
        text = msg.parts[0].text if msg.parts else ""
        conv_text += f"{role}: {text}\n"
        
    prompt = (
        "Voici la conversation qui vient d'avoir lieu entre Syndou et son assistant vocal VISION.\n"
        "Rédige un résumé ultra-court (maximum une phrase de 10 à 15 mots) décrivant ce dont ils ont parlé "
        "(ex: 'Calculs de maths et allumage de la lumière du salon' ou 'Discussion sur Messi et le football').\n"
        "Sois direct et n'utilise pas de caractères spéciaux comme les boutons Markdown ou les hashtags.\n\n"
        f"CONVERSATION :\n{conv_text}"
    )
    
    try:
        model = MODELS_LIST[0]
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model=model,
            contents=prompt
        )
        resume = response.text.replace("\n", "").strip()
        if resume:
            memoire = charger_memoire()
            memoire["sessions"].append({
                "timestamp": time.strftime("%d/%m/%Y %H:%M"),
                "resume": resume
            })
            # Conserver uniquement les 20 plus récentes
            if len(memoire["sessions"]) > 20:
                memoire["sessions"] = memoire["sessions"][-20:]
            sauvegarder_memoire(memoire)
            print(f"[MEMOIRE] Résumé de session enregistré : {resume}")
    except Exception as e:
        print(f"[MEMOIRE] Erreur lors de la génération du résumé de session : {e}")
