"""
VISION — Vision Écran
Analyse d'écran, clics, écriture, sélection, description via IA vision.
"""

import os
import json
import time
import base64
import io
import asyncio
import pyautogui
from PIL import Image

from modules import state
from modules.config import gemini_client, CHOSEN_MODEL, genai_types
from modules.websocket_server import send_web_state, request_webcam_capture


def extract_box_from_response(response_text):
    rep_text = response_text.strip()
    start = rep_text.find('{')
    end = rep_text.rfind('}')
    if start != -1 and end != -1:
        rep_text = rep_text[start:end + 1]
    data = json.loads(rep_text)
    return data.get("box", [500, 500, 500, 500])


async def ask_vision_model(prompt):
    """Récupère une image (via WebSocket ou localement) et l'envoie au modèle Vision."""
    from modules.websocket_server import request_screen_capture
    
    # 1. Tentative via l'interface Web (haute résolution, support mobile)
    img_b64 = await request_screen_capture()
    
    if img_b64:
        img_data = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_data))
        print("[VISION] Analyse via capture Web")
    else:
        # 2. Fallback via capture d'écran locale (pyautogui)
        print("[VISION] Échec capture Web, tentative locale (pyautogui)")
        path_ss = "vision_temp.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(path_ss)
        img = Image.open(path_ss)
        # On supprime après si c'est un fichier, mais ici on va juste l'utiliser
    
    try:
        response = gemini_client.models.generate_content(model=CHOSEN_MODEL, contents=[prompt, img])
        return response.text.strip()
    finally:
        if not img_b64 and os.path.exists("vision_temp.png"):
            os.remove("vision_temp.png")



async def vision_cliquer(instruction):
    try:
        prompt = (
            f"Tu es la vision de VISION. Voici une capture de l'ecran de Syndou.\n"
            f"Instruction : {instruction}\n"
            "Trouve EXACTEMENT la position de cet element.\n"
            "Reponds UNIQUEMENT sous forme de JSON avec la bounding box normalisee (0 a 1000) sous le format [ymin, xmin, ymax, xmax].\n"
            'Exemple : {"box": [250, 480, 290, 520]}'
        )
        rep = await ask_vision_model(prompt)
        ymin, xmin, ymax, xmax = extract_box_from_response(rep)
        center_y = (ymin + ymax) / 2
        center_x = (xmin + xmax) / 2

        screen_w, screen_h = pyautogui.size()
        target_x = int((center_x / 1000) * screen_w)
        target_y = int((center_y / 1000) * screen_h)
        pyautogui.moveTo(target_x, target_y, duration=0.4)
        pyautogui.click()
        return f"C'est fait Syndou. J'ai cliqué sur l'élément correspondant à : {instruction}."
    except Exception as e:
        print(f"[VISION ERROR] {e}")
        return "J'ai eu un souci pour identifier cet élément à l'écran, Syndou."


async def vision_ecrire(instruction, texte_a_taper):
    try:
        prompt = (
            f"Tu es la vision de VISION. Syndou veut ecrire dans le champ : {instruction}.\n"
            "Trouve EXACTEMENT la position de ce champ de saisie.\n"
            "Reponds UNIQUEMENT sous forme de JSON avec la bounding box normalisee (0 a 1000) sous le format [ymin, xmin, ymax, xmax].\n"
            'Exemple : {"box": [250, 480, 290, 520]}'
        )
        rep = await ask_vision_model(prompt)
        ymin, xmin, ymax, xmax = extract_box_from_response(rep)
        center_y = (ymin + ymax) / 2
        center_x = (xmin + xmax) / 2

        screen_w, screen_h = pyautogui.size()
        target_x = int((center_x / 1000) * screen_w)
        target_y = int((center_y / 1000) * screen_h)
        pyautogui.moveTo(target_x, target_y, duration=0.4)
        pyautogui.click()
        time.sleep(0.3)
        pyautogui.write(texte_a_taper, interval=0.03)
        pyautogui.press('enter')
        return f"C'est fait Syndou. J'ai tapé '{texte_a_taper}' dans {instruction}."
    except Exception as e:
        print(f"[VISION ERROR] {e}")
        return "J'ai rencontré une erreur en essayant d'écrire, Syndou."


async def vision_selectionner(instruction):
    try:
        prompt = (
            f"Tu es la vision de VISION. Syndou veut selectionner le texte ou l'element correspondant a : {instruction}.\n"
            "Trouve EXACTEMENT la position de ce texte.\n"
            "Reponds UNIQUEMENT sous forme de JSON avec la bounding box normalisee (0 a 1000) sous le format [ymin, xmin, ymax, xmax].\n"
            'Exemple : {"box": [250, 480, 290, 520]}'
        )
        rep = await ask_vision_model(prompt)
        ymin, xmin, ymax, xmax = extract_box_from_response(rep)
        center_y = (ymin + ymax) / 2

        screen_w, screen_h = pyautogui.size()
        target_xmin = int((xmin / 1000) * screen_w)
        target_xmax = int((xmax / 1000) * screen_w)
        target_y = int((center_y / 1000) * screen_h)

        pyautogui.moveTo(target_xmin, target_y, duration=0.4)
        pyautogui.dragTo(target_xmax, target_y, duration=0.8, button='left')
        return f"C'est fait, Syndou. J'ai selectionné {instruction}."
    except Exception as e:
        print(f"[VISION ERROR] {e}")
        return "Je n'ai pas pu selectionner cet élément, Syndou."


async def vision_decrire(question):
    try:
        prompt = (
            f"Tu es la vision de VISION. L'utilisateur te demande : {question}.\n"
            "Analyse ce que tu vois à l'écran et réponds de façon concise et naturelle, sans formatage spécial (pas de markdown)."
        )
        rep = await ask_vision_model(prompt)
        return rep
    except Exception as e:
        print(f"[VISION ERROR] {e}")
        return "Je ne parviens pas à analyser l'écran pour le moment."


async def vision_voir_utilisateur(question):
    try:
        img_b64 = await request_webcam_capture()
        if not img_b64:
            return "Désolé Syndou, je ne peux pas accéder à votre caméra. Assurez-vous d'avoir cliqué sur 'Autoriser la caméra' sur l'interface."

        img_data = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_data))

        prompt = (
            f"Tu es VISION. Tu regardes Syndou via sa webcam. Il te demande : {question}.\n"
            "Décris ce que tu vois de façon naturelle, chaleureuse et concise."
        )

        state.is_thinking = True
        await send_web_state("thinking")

        response = gemini_client.models.generate_content(model=CHOSEN_MODEL, contents=[prompt, img])
        rep = response.text.strip()

        state.historique.append(genai_types.Content(role="user", parts=[genai_types.Part(text=f"[Webcam] {question}")]))
        state.historique.append(genai_types.Content(role="model", parts=[genai_types.Part(text=rep)]))

        return rep
    except Exception as e:
        print(f"[WEBCAM ERROR] {e}")
        return "Je n'ai pas pu accéder à votre image caméra pour le moment."
    finally:
        state.is_thinking = False
        await send_web_state("idle")


async def vision_reconnaitre_personne():
    try:
        img_b64 = await request_webcam_capture()
        if not img_b64:
            return "Je ne vois rien, la caméra est inaccessible."

        img_data = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_data))
        
        # Load reference photos
        contents = [
            "Tu es VISION. Ton but est d'identifier la personne sur cette image webcam fournie à la fin.",
            "Voici les photos de référence des personnes connues :"
        ]
        
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faces")
        if os.path.exists(faces_dir):
            for file in os.listdir(faces_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        ref_img = Image.open(os.path.join(faces_dir, file))
                        name = os.path.splitext(file)[0].replace('_', ' ')
                        contents.append(f"Photo de référence pour : {name}")
                        contents.append(ref_img)
                    except Exception:
                        pass

        contents.append("Voici maintenant l'image de la webcam à analyser. Dis-moi de qui il s'agit, ou signale si c'est une personne inconnue.")
        contents.append(img)

        state.is_thinking = True
        await send_web_state("thinking")
        
        response = gemini_client.models.generate_content(model=CHOSEN_MODEL, contents=contents)
        return response.text.strip()
    except Exception as e:
        print(f"[VISION ERROR RECOGNIZE] {e}")
        return "Erreur lors de la reconnaissance de la personne."
    finally:
        state.is_thinking = False
        await send_web_state("idle")


async def vision_analyser_objet(question):
    try:
        img_b64 = await request_webcam_capture()
        if not img_b64:
            return "Je ne vois rien, la caméra est inaccessible."

        img_data = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_data))
        
        prompt = f"L'utilisateur pointe un objet devant la webcam. Analyse précisément l'image et l'objet mis en évidence. Question : {question}"
        
        state.is_thinking = True
        await send_web_state("thinking")
        
        response = gemini_client.models.generate_content(model=CHOSEN_MODEL, contents=[prompt, img])
        return response.text.strip()
    except Exception as e:
        print(f"[VISION ERROR OBJECT] {e}")
        return "J'ai eu un souci pour analyser cet objet."
    finally:
        state.is_thinking = False
        await send_web_state("idle")


async def navigation_autonome(objectif):
    from modules.file_manager import ouvrir_navigateur
    import asyncio
    
    # Ouvre le navigateur
    ouvrir_navigateur("https://www.google.fr")
    await asyncio.sleep(3)

    return f"Je lance la navigation pour : {objectif}. Je vous préviens dès que c'est fait ou s'il y a un souci, Syndou."
