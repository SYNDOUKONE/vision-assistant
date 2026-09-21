"""
VISION — Système de Reconnaissance Faciale & Profils Utilisateurs
Gestion de l'apprentissage de visages, identification de personnes, profils et relations.
"""

import os
import json
import time
import io
import base64
import asyncio
from datetime import datetime
from PIL import Image

from modules import state
from modules.config import gemini_client, CHOSEN_MODEL, genai_types
from modules.websocket_server import send_web_state, request_webcam_capture

# Dossier des visages et fichier des métadonnées
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACES_DIR = os.path.join(BASE_DIR, "faces")
PERSONNES_FILE = os.path.join(BASE_DIR, "vision_personnes.json")


def _init_storage():
    """Initialise le dossier faces et le fichier JSON de profils si besoin."""
    if not os.path.exists(FACES_DIR):
        os.makedirs(FACES_DIR, exist_ok=True)
    if not os.path.exists(PERSONNES_FILE):
        with open(PERSONNES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def charger_personnes():
    """Charge les données des profils enregistrés."""
    _init_storage()
    try:
        with open(PERSONNES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[RECONNAISSANCE] Erreur chargement personnes : {e}")
        return {}


def sauvegarder_personnes(personnes):
    """Sauvegarde les données des profils."""
    _init_storage()
    try:
        with open(PERSONNES_FILE, "w", encoding="utf-8") as f:
            json.dump(personnes, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[RECONNAISSANCE] Erreur sauvegarde personnes : {e}")


def _nettoyer_nom_fichier(nom):
    """Normalise un nom pour en faire un nom de fichier propre."""
    nom_propre = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in nom)
    return nom_propre.strip().lower().replace(" ", "_")


async def enregistrer_visage(nom: str, relation: str = "ami", notes: str = "") -> str:
    """
    Capture une photo depuis la webcam et l'associe à un profil utilisateur.
    """
    if not nom or not nom.strip():
        return "Veuillez préciser le nom de la personne à enregistrer, Syndou."

    nom_clean = nom.strip()
    slug = _nettoyer_nom_fichier(nom_clean)
    if not slug:
        return "Nom invalide pour l'enregistrement."

    _init_storage()

    # Capture d'une image webcam
    img_b64 = await request_webcam_capture()
    if not img_b64:
        return "Impossible d'accéder à la webcam pour capturer le visage. Assurez-vous que la caméra est branchée et autorisée."

    try:
        img_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_bytes))

        # Enregistrement du fichier image dans faces/
        filename = f"{slug}.jpg"
        filepath = os.path.join(FACES_DIR, filename)
        img.convert("RGB").save(filepath, "JPEG", quality=90)

        # Enregistrement dans vision_personnes.json
        personnes = charger_personnes()
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        personnes[nom_clean] = {
            "nom": nom_clean,
            "slug": slug,
            "fichier": filename,
            "relation": relation.strip() if relation else "ami(e)",
            "notes": notes.strip() if notes else "",
            "date_enregistrement": date_str,
            "derniere_vue": date_str
        }
        sauvegarder_personnes(personnes)

        print(f"[RECONNAISSANCE] Visage enregistré avec succès : {nom_clean} ({filename})")
        
        relation_text = f" ({relation})" if relation and relation != "ami" else ""
        return f"C'est fait Syndou ! J'ai mémorisé le visage de {nom_clean}{relation_text}. Je pourrai désormais le reconnaître automatiquement devant la caméra."
    except Exception as e:
        print(f"[RECONNAISSANCE ERROR ENREGISTRER] {e}")
        return f"Une erreur est survenue lors de l'enregistrement du visage de {nom_clean}."


async def reconnaitre_personne() -> str:
    """
    Capture la caméra et identifie la personne présente en comparant aux visages connus et profils.
    """
    _init_storage()

    img_b64 = await request_webcam_capture()
    if not img_b64:
        return "Je ne parviens pas à voir à travers la caméra, Syndou. Vérifiez que la webcam est active."

    try:
        img_bytes = base64.b64decode(img_b64)
        current_img = Image.open(io.BytesIO(img_bytes))

        personnes = charger_personnes()
        
        contents = [
            "Tu es V.I.S.I.O.N, l'assistant IA intelligent de Syndou. Tu disposes d'un module de reconnaissance visuelle et faciale.",
            "Voici les visages et profils de référence enregistrés dans ta base de connaissances :"
        ]

        photos_chargees = 0
        for nom, info in personnes.items():
            fname = info.get("fichier")
            if fname:
                fpath = os.path.join(FACES_DIR, fname)
                if os.path.exists(fpath):
                    try:
                        ref_img = Image.open(fpath)
                        relation = info.get("relation", "")
                        notes = info.get("notes", "")
                        details = f"Profil : {nom}"
                        if relation:
                            details += f" (Relation : {relation})"
                        if notes:
                            details += f" (Notes : {notes})"
                        contents.append(details)
                        contents.append(ref_img)
                        photos_chargees += 1
                    except Exception as err:
                        print(f"[RECONNAISSANCE] Impossible de charger {fpath} : {err}")

        # Si aucune photo enregistrée
        if photos_chargees == 0:
            prompt_sans_ref = (
                "Voici l'image de la webcam. Tu n'as pas encore de visages enregistrés dans ta base.\n"
                "Décris la personne présente devant la caméra (expression, humeur apparente, ce qu'elle fait) "
                "et invite-la gentiment à s'enregistrer avec la commande 'Enregistre mon visage sous le nom [Nom]'.\n"
                "Réponds en français naturel, chaleureux et concis."
            )
            contents = [prompt_sans_ref, current_img]
        else:
            prompt_avec_ref = (
                "Voici maintenant la photo actuelle capturée par la webcam de l'utilisateur.\n"
                "Compare attentivement le visage présent sur cette capture avec toutes les photos de référence fournies ci-dessus.\n"
                "Tâches :\n"
                "1. Si tu reconnais avec certitude l'une des personnes de référence, salue-la par son prénom/nom, fais référence à sa relation avec Syndou si pertinent, et commente brièvement son expression (ex: souriant, concentré, etc.).\n"
                "2. Si la personne ne ressemble à aucune des références ou s'il n'y a personne de reconnaissable, dis-le poliment et propose d'enregistrer son visage.\n"
                "Réponds directement en français naturel, sans markdown inutile ni puces, sur un ton élégant et bienveillant."
            )
            contents.append(prompt_avec_ref)
            contents.append(current_img)

        state.is_thinking = True
        await send_web_state("thinking")

        texte_reponse = None
        from modules.config import MODELS_LIST
        for model_name in MODELS_LIST:
            try:
                response = await asyncio.to_thread(
                    gemini_client.models.generate_content,
                    model=model_name,
                    contents=contents
                )
                if response and response.text:
                    texte_reponse = response.text.strip()
                    break
            except Exception as e_mod:
                print(f"[RECONNAISSANCE] Modèle {model_name} indisponible : {e_mod}")
                continue

        if not texte_reponse:
            return "Je n'ai pas pu analyser le visage pour le moment, mes serveurs de vision sont temporairement surchargés."

        # Met à jour la dernière vue si une personne est reconnue
        for nom in personnes.keys():
            if nom.lower() in texte_reponse.lower():
                personnes[nom]["derniere_vue"] = datetime.now().strftime("%d/%m/%Y à %H:%M")
                sauvegarder_personnes(personnes)
                break

        return texte_reponse
    except Exception as e:
        print(f"[RECONNAISSANCE ERROR RECONNAITRE] {e}")
        return "J'ai rencontré une difficulté technique lors de l'analyse du visage devant la caméra."
    finally:
        state.is_thinking = False
        await send_web_state("idle")


def lister_personnes_connues() -> str:
    """
    Retourne la liste des personnes actuellement enregistrées dans le système.
    """
    personnes = charger_personnes()
    if not personnes:
        return "Aucun visage n'est actuellement enregistré dans ma mémoire, Syndou. Vous pouvez me dire par exemple : 'Enregistre mon visage sous le nom Syndou'."

    lignes = [f"J'ai {len(personnes)} personne(s) mémorisée(s) dans ma base :"]
    for nom, info in personnes.items():
        rel = f" ({info.get('relation')})" if info.get("relation") else ""
        date_e = info.get("date_enregistrement", "inconnue")
        lignes.append(f"• {nom}{rel} — enregistré le {date_e}")

    return "\n".join(lignes)


def supprimer_visage(nom: str) -> str:
    """
    Supprime un visage et son profil de la base.
    """
    if not nom or not nom.strip():
        return "Veuillez préciser le nom de la personne à supprimer, Syndou."

    nom_clean = nom.strip()
    personnes = charger_personnes()

    trouve_cle = None
    for cle in personnes.keys():
        if cle.lower() == nom_clean.lower():
            trouve_cle = cle
            break

    if not trouve_cle:
        return f"Je n'ai trouvé aucun profil enregistré au nom de {nom_clean}."

    info = personnes.pop(trouve_cle)
    sauvegarder_personnes(personnes)

    # Supprime l'image du disque si elle existe
    fname = info.get("fichier")
    if fname:
        fpath = os.path.join(FACES_DIR, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception as e:
                print(f"[RECONNAISSANCE] Erreur suppression fichier image : {e}")

    return f"Le visage et le profil de {trouve_cle} ont été supprimés avec succès de ma mémoire."


def enregistrer_visage_direct(nom: str, relation: str = "ami", notes: str = "", img_b64: str = "") -> dict:
    """Enregistre un visage directement à partir d'une image base64 fournie par le frontend."""
    if not nom or not nom.strip():
        return {"success": False, "message": "Nom manquant pour l'enregistrement."}
    if not img_b64:
        return {"success": False, "message": "Capture d'image manquante."}

    nom_clean = nom.strip()
    slug = _nettoyer_nom_fichier(nom_clean)
    if not slug:
        return {"success": False, "message": "Nom invalide."}

    _init_storage()

    try:
        # Nettoyage header data:image/jpeg;base64,... si présent
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]

        img_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_bytes))

        filename = f"{slug}.jpg"
        filepath = os.path.join(FACES_DIR, filename)
        img.convert("RGB").save(filepath, "JPEG", quality=90)

        personnes = charger_personnes()
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        personnes[nom_clean] = {
            "nom": nom_clean,
            "slug": slug,
            "fichier": filename,
            "relation": relation.strip() if relation else "ami(e)",
            "notes": notes.strip() if notes else "",
            "date_enregistrement": date_str,
            "derniere_vue": date_str
        }
        sauvegarder_personnes(personnes)
        print(f"[RECONNAISSANCE] Visage enregistré via UI : {nom_clean} ({filename})")
        return {
            "success": True,
            "message": f"Visage de {nom_clean} enregistré avec succès.",
            "personne": personnes[nom_clean]
        }
    except Exception as e:
        print(f"[RECONNAISSANCE ERROR ENREGISTRER DIRECT] {e}")
        return {"success": False, "message": f"Erreur : {str(e)}"}


def get_personnes_with_photos() -> list:
    """Retourne la liste des personnes enregistrées avec leur photo en base64 pour la galerie UI."""
    personnes = charger_personnes()
    res = []
    for nom, info in personnes.items():
        item = dict(info)
        fname = info.get("fichier")
        item["photo_b64"] = ""
        if fname:
            fpath = os.path.join(FACES_DIR, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "rb") as f:
                        item["photo_b64"] = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")
                except Exception as e:
                    print(f"[RECONNAISSANCE] Erreur lecture photo {fname}: {e}")
        res.append(item)
    return res


async def reconnaitre_frame_direct(img_b64: str) -> dict:
    """Analyse rapide d'une frame webcam pour identifier le nom de la personne parmi les profils enregistrés."""
    _init_storage()
    if not img_b64:
        return {"identified": False, "name": "Inconnu", "confidence": 0.0}

    try:
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]

        img_bytes = base64.b64decode(img_b64)
        current_img = Image.open(io.BytesIO(img_bytes))
        personnes = charger_personnes()

        if not personnes:
            return {"identified": False, "name": "Visage non enregistré", "confidence": 0.0, "details": "Aucun profil dans la base"}

        contents = [
            "Tu es un module de reconnaissance faciale biométrique ultra-précis.",
            "Voici les visages et profils enregistrés dans la base :"
        ]

        for nom, info in personnes.items():
            fname = info.get("fichier")
            if fname:
                fpath = os.path.join(FACES_DIR, fname)
                if os.path.exists(fpath):
                    try:
                        ref_img = Image.open(fpath)
                        contents.append(f"Personne : {nom}")
                        contents.append(ref_img)
                    except Exception:
                        pass

        prompt = (
            "Voici l'image actuelle capturée par la caméra.\n"
            "Compare attentivement le visage présent avec les photos de référence fournies.\n"
            "Réponds STRICTEMENT au format JSON valide suivant, sans aucun texte autour :\n"
            '{"identified": true, "name": "Nom de la personne", "confidence": 0.95, "relation": "..."} ou {"identified": false, "name": "Inconnu", "confidence": 0.0}'
        )
        contents.append(prompt)
        contents.append(current_img)

        from modules.config import gemini_client, MODELS_LIST
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model=MODELS_LIST[0] if MODELS_LIST else "gemini-2.5-flash",
            contents=contents
        )
        if response and response.text:
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in text:
                text = text.split("```", 1)[1].split("```", 1)[0].strip()
            data = json.loads(text)
            return data
    except Exception as e:
        print(f"[RECONNAISSANCE FRAME DIRECT ERROR] {e}")

    return {"identified": False, "name": "Inconnu", "confidence": 0.0}

