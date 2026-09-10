"""
VISION — Module de Sécurité Graduée (N1 / N2 / N3)
Gère la classification des actions, les demandes de confirmation vocale,
et la mémorisation des permissions révocables (N2).
"""

import os
import json
from enum import Enum

PERMISSIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vision_permissions.json")

class SecurityLevel(Enum):
    N1 = "N1"  # Sûr : Exécution automatique (météo, heure, calculs, volume)
    N2 = "N2"  # Sensible : Confirmation requise / Mémorisable ("toujours autoriser")
    N3 = "N3"  # Critique : Confirmation obligatoire à CHAQUE exécution (extinction, suppression, emails)

# Classification par défaut des actions
ACTION_SECURITY_MAP = {
    # N1 : Sûr (Lecture seule / utilitaires simples)
    "get_meteo": SecurityLevel.N1,
    "get_heure": SecurityLevel.N1,
    "calculer": SecurityLevel.N1,
    "recherche_web": SecurityLevel.N1,
    "lire_emails": SecurityLevel.N1,
    "lister_taches": SecurityLevel.N1,
    "changer_volume": SecurityLevel.N1,
    "get_statut": SecurityLevel.N1,
    "reconnaître_musique": SecurityLevel.N1,

    # N2 : Sensible (Domotique / multimédia / fichiers simples)
    "allumer_lumiere": SecurityLevel.N2,
    "eteindre_lumiere": SecurityLevel.N2,
    "jouer_musique": SecurityLevel.N2,
    "creer_tache": SecurityLevel.N2,
    "ouvrir_application": SecurityLevel.N2,
    "creer_fichier": SecurityLevel.N2,
    "activer_gestes": SecurityLevel.N2,

    # N3 : Critique (Actions système / modifications majeures / communications externes)
    "eteindre_pc": SecurityLevel.N3,
    "redemarrer_pc": SecurityLevel.N3,
    "supprimer_fichier": SecurityLevel.N3,
    "envoyer_email": SecurityLevel.N3,
    "effacer_memoire": SecurityLevel.N3,
    "soumettre_formulaire_web": SecurityLevel.N3,
    "passer_appel": SecurityLevel.N3,
}

def charger_permissions():
    """Charge les permissions N2 autorisées durablement depuis le fichier JSON."""
    if os.path.exists(PERMISSIONS_FILE):
        try:
            with open(PERMISSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[SECURITE] Erreur chargement permissions : {e}")
    return {}

def sauvegarder_permissions(permissions):
    """Sauvegarde les permissions N2 dans le fichier JSON."""
    try:
        with open(PERMISSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(permissions, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SECURITE] Erreur sauvegarde permissions : {e}")

def obtenir_niveau_securite(action_name):
    """Retourne le niveau de sécurité d'une action."""
    return ACTION_SECURITY_MAP.get(action_name, SecurityLevel.N2)

def autoriser_action_n2(action_name):
    """Accorde la permission permanente N2 pour une action."""
    perms = charger_permissions()
    perms[action_name] = True
    sauvegarder_permissions(perms)
    print(f"[SECURITE] Permission N2 mémorisée pour '{action_name}'.")

def revoquer_permission_n2(action_name):
    """Révoque la permission N2 pour une action."""
    perms = charger_permissions()
    if action_name in perms:
        del perms[action_name]
        sauvegarder_permissions(perms)
        print(f"[SECURITE] Permission N2 révoquée pour '{action_name}'.")

def verifier_securite_action(action_name, est_a_distance=False):
    """
    Vérifie si une action peut s'exécuter.
    Retourne un tuple: (autorise: bool, niveau: SecurityLevel, raison: str)
    """
    niveau = obtenir_niveau_securite(action_name)

    # N3 est strictement refusé à distance
    if est_a_distance and niveau == SecurityLevel.N3:
        return False, niveau, "Les actions de niveau N3 sont strictly interdites à distance."

    # N1 : Toujours autorisé
    if niveau == SecurityLevel.N1:
        return True, niveau, "Autorisé (N1 - Sûr)"

    # N2 : Autorisé si déjà mémorisé
    if niveau == SecurityLevel.N2:
        perms = charger_permissions()
        if perms.get(action_name, False):
            return True, niveau, "Autorisé (N2 - Permission mémorisée)"
        return False, niveau, f"Confirmation requise pour N2 : '{action_name}'"

    # N3 : Toujours demander confirmation
    return False, niveau, f"Confirmation obligatoire pour N3 : '{action_name}'"
