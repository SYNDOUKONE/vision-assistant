import os
import asyncio
import PyPDF2
from pathlib import Path
from modules import state
from modules.voice import parler
from modules.websocket_server import send_web_state

# Variable pour arrêter la lecture en cours si besoin
lecture_task = None

async def lire_fichier_audio(fichier_nom):
    """Cherche le fichier et le lit par petits blocs pour ne pas bloquer l'IA."""
    global lecture_task
    
    dossiers_a_chercher = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Documents")
    ]
    
    chemin_trouve = None
    for dossier in dossiers_a_chercher:
        potentiel = os.path.join(dossier, fichier_nom)
        if os.path.exists(potentiel):
            chemin_trouve = potentiel
            break
            
    if not chemin_trouve:
        await parler(f"Je suis désolé Monsieur, mais je n'ai pas pu trouver le fichier {fichier_nom} dans vos dossiers principaux.")
        return

    await parler(f"Fichier trouvé. Je commence la lecture de {fichier_nom}.")
    await send_web_state("thinking")
    
    texte_complet = ""
    try:
        if chemin_trouve.endswith(".pdf"):
            with open(chemin_trouve, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    texte_complet += page.extract_text() + "\n"
        elif chemin_trouve.endswith(".txt"):
            with open(chemin_trouve, "r", encoding="utf-8") as f:
                texte_complet = f.read()
        else:
            await parler("Format de fichier non supporté pour la lecture.")
            return
            
    except Exception as e:
        print(f"[LECTEUR] Erreur lecture : {e}")
        await parler("Une erreur est survenue lors de l'ouverture du fichier.")
        return

    if not texte_complet.strip():
        await parler("Le fichier semble être vide ou illisible.")
        return

    # Nettoyage et découpage grossier
    texte_complet = texte_complet.replace('\n', ' ')
    phrases = [p.strip() for p in texte_complet.split('.') if len(p.strip()) > 5]
    
    state.MODE_LECTEUR = True
    
    for phrase in phrases:
        if not state.MODE_LECTEUR:
            await parler("Lecture interrompue.")
            break
        await parler(phrase + ".")
        await asyncio.sleep(0.5)

    if state.MODE_LECTEUR:
        await parler("Lecture du document terminée, Monsieur.")
        state.MODE_LECTEUR = False
    
    await send_web_state("idle")

def demarrer_lecture(fichier_nom):
    global lecture_task
    if lecture_task and not lecture_task.done():
        lecture_task.cancel()
    lecture_task = asyncio.create_task(lire_fichier_audio(fichier_nom))
