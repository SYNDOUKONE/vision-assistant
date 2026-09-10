"""
VISION — Module de Gestion d'Énergie & Wake-on-LAN
Permet l'extinction propre du PC avec décompte vocal annulable (sécurité N3),
le redémarrage, et le réveil à distance d'équipements via Wake-on-LAN.
"""

import os
import sys
import time
import socket
import threading
import subprocess

from modules.voice import parler
from modules import state

_extinction_timer = None
_extinction_annulee = False

def wake_on_lan(mac_address):
    """
    Envoie un paquet magique Wake-on-LAN à l'adresse MAC spécifiée.
    Format MAC : 'XX:XX:XX:XX:XX:XX' ou 'XX-XX-XX-XX-XX-XX'
    """
    try:
        mac_clean = mac_address.replace(":", "").replace("-", "")
        if len(mac_clean) != 12:
            return "Adresse MAC invalide (attendu 12 caractères hexadécimaux)."
        
        data = bytes.fromhex("FF" * 6 + mac_clean * 16)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(data, ("<broadcast>", 9))
        
        print(f"[POWER] Paquet Wake-on-LAN envoyé à {mac_address}.")
        return f"Paquet Wake-on-LAN envoyé à l'appareil {mac_address}."
    except Exception as e:
        print(f"[POWER] Erreur Wake-on-LAN : {e}")
        return f"Erreur lors de l'envoi du Wake-on-LAN : {e}"

def annuler_extinction_pc():
    """Annule l'extinction du PC en cours si le décompte n'est pas terminé."""
    global _extinction_annulee
    _extinction_annulee = True
    print("[POWER] Extinction du PC annulée par l'utilisateur.")
    return "Extinction du PC annulée avec succès Syndou."

def _boucle_extinction(delai_secondes=30):
    """Exécute le compte à rebours vocal avant l'extinction système."""
    global _extinction_annulee
    _extinction_annulee = False

    parler(f"Attention Syndou, le système s'éteindra dans {delai_secondes} secondes. Dites 'Annuler' pour interrompre.")

    restant = delai_secondes
    while restant > 0:
        if _extinction_annulee:
            parler("Extinction de l'ordinateur annulée.")
            return
        time.sleep(1)
        restant -= 1
        if restant in [15, 5]:
            parler(f"Extinction dans {restant} secondes.")

    if not _extinction_annulee:
        parler("Extinction du système en cours. À bientôt Syndou.")
        time.sleep(2)
        if sys.platform == "win32":
            os.system("shutdown /s /t 0")
        elif sys.platform == "darwin":
            os.system("sudo shutdown -h now")
        else:
            os.system("shutdown -h now")

def eteindre_pc_securise(delai_secondes=30):
    """Déclenche le processus d'extinction sécurisé N3 du PC."""
    t = threading.Thread(target=_boucle_extinction, args=(delai_secondes,), daemon=True)
    t.start()
    return f"Procédure d'extinction démarrée. Compte à rebours de {delai_secondes} secondes activé."
