from modules.config import gemini_client, CHOSEN_MODEL, genai_types
from modules import state

import asyncio

JEU_EN_COURS = None

async def lancer_jeu(nom_jeu):
    global JEU_EN_COURS
    if nom_jeu == "quiz":
        prompt = "Faisons un quiz ! Pose-moi ta première question."
    elif nom_jeu == "devinette":
        prompt = "J'adore les devinettes ! Pose m'en une difficile."
    elif nom_jeu == "20questions":
        prompt = "On joue à 20 questions ! Pense à un objet, animal ou personnage, et je vais essayer de deviner en posant des questions."
    else:
        prompt = f"On joue à {nom_jeu} ! Commence."
    
    JEU_EN_COURS = nom_jeu
    try:
        response = gemini_client.models.generate_content(
            model=CHOSEN_MODEL,
            contents=[prompt],
            config=genai_types.GenerateContentConfig(
                system_instruction="Tu es VISION, tu joues à un jeu avec ton créateur Syndou. Reste très digne et poli mais avec cette pointe de sarcasme affectueux propre à ton personnage. Pose la première question ou fais la première action pour commencer le jeu."
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"Désolé Syndou, je n'ai pas pu lancer le jeu : {e}"

async def raconter_histoire(theme):
    try:
        response = gemini_client.models.generate_content(
            model=CHOSEN_MODEL,
            contents=[f"Raconte une histoire interactive incroyable ayant pour thème : {theme}. Laisse-moi faire des choix à la fin du chapitre."],
            config=genai_types.GenerateContentConfig(
                system_instruction="Tu es VISION, raconte une histoire passionnante et demande à Syndou ce qu'il veut faire ensuite."
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"Oups, j'ai perdu le fil de l'histoire : {e}"

def blague_du_jour():
    try:
        response = gemini_client.models.generate_content(
            model=CHOSEN_MODEL,
            contents=["Raconte-moi une excellente blague du jour, avec un côté sarcastique mais poli."],
            config=genai_types.GenerateContentConfig(
                system_instruction="Tu es VISION. Raconte une seule bonne blague pour bien commencer la journée."
            )
        )
        return response.text.strip()
    except Exception:
        return "C'est l'histoire d'un pingouin qui respire par les fesses, un jour il s'assoit et il meurt. Voilà, c'était ma blague de secours."
