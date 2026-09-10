"""
VISION — Gestionnaire de Fichiers
Opérations sur les fichiers et dossiers locaux.
"""

import os
import sys
import time
import shutil
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

from modules import state
from modules.config import EXTENSIONS


def resoudre_chemin(chemin):
    if not chemin:
        return None
    chemin = chemin.strip().strip('"').strip("'")
    user_home = os.environ.get("USERPROFILE") or os.environ.get("HOME") or os.path.expanduser("~")
    raccourcis = {
        "bureau": os.path.join(user_home, "Desktop"),
        "desktop": os.path.join(user_home, "Desktop"),
        "documents": os.path.join(user_home, "Documents"),
        "telechargement": os.path.join(user_home, "Downloads"),
        "telechargements": os.path.join(user_home, "Downloads"),
        "downloads": os.path.join(user_home, "Downloads"),
        "images": os.path.join(user_home, "Pictures"),
        "photos": os.path.join(user_home, "Pictures"),
        "videos": os.path.join(user_home, "Videos"),
        "musique": os.path.join(user_home, "Music"),
        "music": os.path.join(user_home, "Music"),
    }
    chemin_resolu = raccourcis.get(chemin.lower(), chemin)

    if not os.path.exists(chemin_resolu):
        variantes = {
            "Downloads": "Téléchargements",
            "Pictures": "Images",
            "Music": "Musique"
        }
        for eng, fra in variantes.items():
            if eng in chemin_resolu:
                test_fra = chemin_resolu.replace(eng, fra)
                if os.path.exists(test_fra):
                    chemin_resolu = test_fra
                    break
    return chemin_resolu


def trouver_extension(ext):
    for categorie, extensions in EXTENSIONS.items():
        if ext.lower() in extensions:
            return categorie
    return "Autres"


def ouvrir_navigateur(url):
    """Force l'ouverture d'une URL dans le navigateur."""
    if sys.platform == 'darwin':
        try:
            subprocess.Popen(["open", url])
            return True
        except Exception as e:
            print(f"[NAVIGATEUR] Erreur mac open : {e}")
    elif os.name == 'nt':
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            try:
                subprocess.Popen([chrome_path, url])
                return True
            except Exception as e:
                print(f"[NAVIGATEUR] Erreur Chrome : {e}")
    webbrowser.open(url)
    return True


def ouvrir_dossier(chemin):
    chemin_resolu = resoudre_chemin(chemin)
    if not chemin_resolu or not os.path.exists(chemin_resolu):
        return False, f"Dossier introuvable : {chemin_resolu}"
    state.dossier_courant = chemin_resolu
    if os.name == 'nt':
        subprocess.Popen(f'explorer "{chemin_resolu}"', shell=True)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', chemin_resolu])
    else:
        subprocess.Popen(['xdg-open', chemin_resolu])
    return True, chemin_resolu


def ouvrir_fichier(chemin):
    chemin_lower = chemin.lower() if chemin else ""
    if "interface" in chemin_lower and ("graphique" in chemin_lower or "web" in chemin_lower):
        try:
            webbrowser.open("http://localhost:5173")
            return True, "Interface Graphique Web"
        except Exception:
            return False, "Impossible d'ouvrir l'interface Web"

    chemin_resolu = resoudre_chemin(chemin)
    if chemin_resolu and os.path.exists(chemin_resolu) and os.path.isfile(chemin_resolu):
        cible = chemin_resolu
    else:
        cible = None
        if state.dossier_courant and os.path.exists(os.path.join(state.dossier_courant, chemin)):
            cible = os.path.join(state.dossier_courant, chemin)
        else:
            resultats, _ = chercher_fichier(chemin, state.dossier_courant)
            if resultats:
                cible = resultats[0]

    if not cible or not os.path.exists(cible):
        cible = chemin

    try:
        if os.name == 'nt':
            if os.path.isabs(cible) and os.path.exists(cible):
                subprocess.Popen(f'start "" "{cible}"', shell=True)
            else:
                if " " not in cible:
                    subprocess.Popen(f'start {cible}', shell=True)
                else:
                    subprocess.Popen(f'start "" "{cible}"', shell=True)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', cible])
        else:
            subprocess.Popen(['xdg-open', cible])
        return True, cible
    except Exception:
        return False, f"Fichier ou programme introuvable : {chemin}"


def lister_dossier(chemin=None):
    cible = resoudre_chemin(chemin) or state.dossier_courant
    if not cible or not os.path.exists(cible):
        return None, "Aucun dossier ouvert ou chemin invalide."
    fichiers = []
    dossiers = []
    for item in os.scandir(cible):
        if item.is_file():
            fichiers.append(item.name)
        elif item.is_dir():
            dossiers.append(item.name)
    return {"chemin": cible, "fichiers": fichiers, "dossiers": dossiers}, None


def trier_par_type(chemin=None):
    cible = resoudre_chemin(chemin) or state.dossier_courant
    if not cible or not os.path.exists(cible):
        return False, "Aucun dossier ouvert ou invalide."
    deplacements = 0
    erreurs = 0
    categories = {}
    for item in os.scandir(cible):
        if not item.is_file():
            continue
        ext = Path(item.name).suffix
        categorie = trouver_extension(ext)
        dest_dir = os.path.join(cible, categorie)
        try:
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, item.name)
            if os.path.exists(dest_path):
                base = Path(item.name).stem
                ext2 = Path(item.name).suffix
                dest_path = os.path.join(dest_dir, f"{base}_{int(time.time())}{ext2}")
            shutil.move(item.path, dest_path)
            deplacements += 1
            categories[categorie] = categories.get(categorie, 0) + 1
        except Exception as e:
            print(f"[FICHIER] Erreur deplacement {item.name} : {e}")
            erreurs += 1
    resume = ", ".join([f"{v} {k}" for k, v in categories.items()])
    return True, f"{deplacements} fichiers tries : {resume}. {erreurs} erreurs."


def trier_par_date(chemin=None):
    cible = resoudre_chemin(chemin) or state.dossier_courant
    if not cible or not os.path.exists(cible):
        return False, "Aucun dossier ouvert ou invalide."
    deplacements = 0
    erreurs = 0
    for item in os.scandir(cible):
        if not item.is_file():
            continue
        try:
            mtime = item.stat().st_mtime
            date = datetime.fromtimestamp(mtime)
            annee = str(date.year)
            mois = date.strftime("%m - %B")
            dest_dir = os.path.join(cible, annee, mois)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, item.name)
            if os.path.exists(dest_path):
                base = Path(item.name).stem
                ext2 = Path(item.name).suffix
                dest_path = os.path.join(dest_dir, f"{base}_{int(time.time())}{ext2}")
            shutil.move(item.path, dest_path)
            deplacements += 1
        except Exception as e:
            print(f"[FICHIER] Erreur deplacement {item.name} : {e}")
            erreurs += 1
    return True, f"{deplacements} fichiers tries par date. {erreurs} erreurs."


def trier_par_type_puis_date(chemin=None):
    cible = chemin or state.dossier_courant
    if not cible or not os.path.exists(cible):
        return False, "Aucun dossier ouvert."
    ok1, msg1 = trier_par_type(cible)
    if not ok1:
        return False, msg1
    for item in os.scandir(cible):
        if item.is_dir() and item.name in EXTENSIONS.keys():
            trier_par_date(item.path)
    return True, "Dossier trie par type puis par date dans chaque categorie."


def creer_sous_dossier(nom, chemin=None):
    cible = resoudre_chemin(chemin) or state.dossier_courant
    if not cible:
        return False, "Aucun dossier ouvert."
    nouveau = os.path.join(cible, nom)
    try:
        os.makedirs(nouveau, exist_ok=True)
        return True, f"Dossier {nom} cree."
    except Exception as e:
        return False, f"Erreur creation dossier : {e}"


def renommer_fichier(ancien_nom, nouveau_nom, chemin=None):
    cible = resoudre_chemin(chemin) or state.dossier_courant
    if not cible:
        return False, "Aucun dossier ouvert."
    ancien = os.path.join(cible, ancien_nom)
    nouveau = os.path.join(cible, nouveau_nom)
    try:
        os.rename(ancien, nouveau)
        return True, f"Fichier renomme en {nouveau_nom}."
    except Exception as e:
        return False, f"Erreur renommage : {e}"


def deplacer_fichier(nom_fichier, dossier_dest, chemin=None):
    cible = resoudre_chemin(chemin) or state.dossier_courant
    if not cible:
        return False, "Aucun dossier ouvert."
    source = os.path.join(cible, nom_fichier)
    dest = os.path.join(cible, dossier_dest, nom_fichier)
    try:
        os.makedirs(os.path.join(cible, dossier_dest), exist_ok=True)
        shutil.move(source, dest)
        return True, f"{nom_fichier} deplace dans {dossier_dest}."
    except Exception as e:
        return False, f"Erreur deplacement : {e}"


def chercher_fichier(nom, chemin=None):
    """Cherche un fichier par son nom. Si aucun chemin n'est fourni, cherche dans le dossier courant, 
    le bureau, les documents et les téléchargements."""
    # 1. Dossiers à fouiller
    dirs_to_search = []
    
    # Chemin spécifique fourni ou dossier ouvert
    cible = resoudre_chemin(chemin) or state.dossier_courant
    if cible:
        dirs_to_search.append(cible)
    else:
        # Pas de dossier actif : on fouille les dossiers standards + la racine du projet
        users_root = os.environ.get("USERPROFILE", "")
        dirs_to_search = [
            os.getcwd(), # Racine du projet
            os.path.join(users_root, "Downloads"),
            os.path.join(users_root, "Documents"),
            os.path.join(users_root, "Desktop"),
        ]

    resultats = []
    for base in dirs_to_search:
        if not base or not os.path.exists(base):
            continue
        try:
            # Recherche récursive limitée (max 2 niveaux pour la rapidité si pas de cible fixe)
            if not cible:
                for item in os.listdir(base):
                    if nom.lower() in item.lower():
                        resultats.append(os.path.join(base, item))
                    # Un niveau de sous-dossier
                    sub = os.path.join(base, item)
                    if os.path.isdir(sub):
                        try:
                            for sub_item in os.listdir(sub):
                                if nom.lower() in sub_item.lower():
                                    resultats.append(os.path.join(sub, sub_item))
                        except Exception: pass
            else:
                # Recherche exhaustive si le dossier est ciblé
                for root, dirs, files in os.walk(base):
                    for f in files:
                        if nom.lower() in f.lower():
                            resultats.append(os.path.join(root, f))
        except Exception as e:
            print(f"[FICHIER] Erreur recherche dans {base} : {e}")

    return list(set(resultats)), None # set() pour dédoublonner

