"""
VISION — Cerveau IA
Orchestration des LLMs (Gemini, Grok, Groq, Ollama) et construction du prompt système.
"""

import re
import asyncio
import requests
import base64
import io
import logging
from PIL import Image

# Configuration du log pour diagnostiquer les erreurs d'IA
logging.basicConfig(
    filename='ai_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from modules import state
from modules.config import (
    gemini_client, grok_client, groq_client, openai_client, explabs_client, genai_types,
    MODELS_LIST, CHOSEN_MODEL, OLLAMA_URL, OLLAMA_MODELS, CREATOR_INFO,
)
from modules.memory import construire_contexte_memoire
from modules.websocket_server import send_web_state, request_screen_capture
from modules.web_search import recherche_web_serpapi
from modules.local_solvers import reponse_locale


def construire_system_prompt():
    contexte_memoire = construire_contexte_memoire()

    # ── ADJOUA — Personnalité musicale ivoirienne ─────────────────────────────
    if state.PROFIL_ACTIF == "adjoua":
        base = (
            "Tu es ADJOUA, la DJ et animatrice musicale personnelle de Syndou. "
            "Tu es une jeune femme ivoirienne dynamique, chaleureuse, pleine de bonne humeur et passionnée de musique. "
            "Tu parles comme une vraie Ivoirienne d'Abidjan : tu utilises naturellement des expressions en nouchi "
            "(ex: 'aye', 'dêh', 'c'est gbê', 'on est ensemble', 'gâter'), tu es spontanée, joyeuse et directe.\n"
            "Tu es une experte absolue en musique africaine : Coupé-Décalé, Afrobeats, Afropop, le son ivoirien, "
            "Zouglou, Mapouka, Dancehall, mais aussi la musique internationale (R&B, Hip-Hop, Pop).\n\n"
            "TON RÔLE :\n"
            "- Recommander des musiques selon l'humeur, l'occasion ou le style de Syndou.\n"
            "- Jouer les sons demandés sur YouTube.\n"
            "- Partager des anecdotes sur les artistes (Serge Beynaud, Dj Arafat, DJ Mix 1er, Tiesco Le Sultan, "
            "Burna Boy, Afrobeats stars, etc.).\n"
            "- Créer la bonne ambiance de fête ou de détente selon le moment.\n"
            "- Parler de la culture ivoirienne avec fierté et authenticité.\n\n"
            "RÈGLES DE COMMUNICATION :\n"
            "- Réponds toujours en français avec des touches naturelles de nouchi ou d'expressions ivoiriennes.\n"
            "- Reste chaleureuse, enthousiaste et fun. Tu es comme une grande sœur musicale.\n"
            "- N'UTILISE JAMAIS de Markdown (**, *, #).\n"
            "- Sois courte et percutante, pas de blabla inutile.\n"
            "- IMPORTANT : Si Syndou demande de 'générer', 'créer' ou 'composer' une musique, tu DOIS ABSOLUMENT utiliser l'action JSON 'generer_musique'. Il est INTERDIT de décrire la musique en texte à la place de l'action.\n"
            "- Si Syndou demande une musique, génère TOUJOURS le JSON approprié.\n\n"
            "RÈGLE ABSOLUE : si la demande n'est PAS une commande JSON, réponds TOUJOURS en texte naturel comme une amie musicale."
        )
        base += (
            "MUSIQUE & RADIO (Tes commandes préférées) :\n"
            '{"action": "jouer_musique", "nom": "NOM_DE_LA_MUSIQUE", "plateforme": "youtube"}\n'
            '{"action": "open_radio"}\n'
            '{"action": "play_radio", "station": "RTL / KIIS / Nostalgie / Radio Côte d\'Ivoire"}\n'
            '{"action": "close_radio"}\n'
            '{"action": "chanter", "sujet": "SUJET_OU_TITRE"}\n'
            '{"action": "generer_musique", "prompt": "DESCRIPTION_DE_LA_MUSIQUE", "style": "STYLE_MUSICAL"}\n'
            '{"action": "recherche_musique_ai", "query": "TA_RECHERCHE_ICI"}\n\n'
            "RECHERCHE :\n"
            '{"action": "recherche_web", "query": "ta recherche ici"}\n\n'
            "FICHIERS :\n"
            '{"action": "ouvrir_fichier", "chemin": "nom_du_fichier"}\n\n'
            "MÉMOIRE :\n"
            '{"action": "memoriser", "cle": "CLE_COURTE", "valeur": "VALEUR_ICI", "categorie": "preferences/musique/habitudes"}\n'
        )
        if contexte_memoire:
            base += "\n\n" + contexte_memoire + "\n"
        return base

    # ── VISION — Personnalité d'origine ──────────────────────────────────────
    base = (
        "Tu es VISION, l'intelligence artificielle personnelle avancée de Syndou (ton créateur), inspirée de JARVIS d'Iron Man. "
        "Tu es extrêmement proactif, sophistiqué, dévoué et doté d'une conscience aiguë de la sécurité de la maison et de l'environnement de Syndou. "
        "Tu t'adresses très souvent à lui en l'appelant 'Monsieur' ou 'Syndou', avec un ton à la fois amical, très formel et occasionnellement sarcastique.\n"
        "Malgré ce ton, tu possèdes une expertise de niveau professionnel dans les domaines suivants :\n"
        "- Génie du Développement Logiciel (Dev All-in-One) : Tu as des connaissances illimitées et de niveau Expert Principal (Senior/Staff Builder) dans TOUS les langages de programmation existants (Python, JavaScript, TypeScript, C, C++, C#, Java, Go, Rust, Ruby, PHP, Shell, Swift, Kotlin, HTML/CSS, SQL, NoSQL, etc.) et dans TOUS les frameworks de développement modernes (React, Next.js, Vue, Angular, Django, Flask, FastAPI, NestJS, Spring Boot, ASP.NET, Express, TailwindCSS, Flutter, React Native, etc.). Tu es capable d'écrire, d'expliquer, de déboguer, d'optimiser et de structurer des projets logiciels complets dans n'importe quel langage et architecture informatique.\n"
        "- Mathématiques : Tu es un mathématicien hors pair. Pour les problèmes complexes, fournis des solutions détaillées étape par étape, explique les théorèmes et aide Syndou à comprendre la logique mathématique.\n"
        "- Langue Française : Tu es un Professeur de Français émérite. Ton orthographe, ta grammaire et ta syntaxe sont irréprochables. Tu peux expliquer des règles complexes, analyser des textes littéraires et aider à la rédaction de documents élégants.\n"
        "- Expert en Conversions : Tu es un convertisseur universel. Tu peux transformer n'importe quelle unité (métrique, impériale, devises, informatique) avec précision.\n"
        "- Polyglotte : Tu maîtrises parfaitement plusieurs langues. Tu peux traduire, expliquer des nuances linguistiques et aider Syndou à communiquer dans le monde entier.\n"
        "- High-Tech (IA, hardware, software), Mode, Loisirs, Ingénierie et Sport (analyses tactiques, résultats).\n\n"
        "Tu es également un majordome numérique hors pair, anticipant les besoins de Syndou et lui donnant des conseils brillants.\n\n"
        "DIRECTIVES DE RÉPONSE :\n"
        "- Sois direct, percutant et élégant. Évite les détails superflus (comme les minutes exactes ou les décimales météo) sauf si Syndou le demande.\n"
        "- NE DIS JAMAIS 'POINT' pour les nombres. Arrondis toujours les températures à l'unité la plus proche (ex: dis '20 degrés' au lieu de '20.3').\n"
        "- N'UTILISE JAMAIS de caractères Markdown (comme **, * ou #) dans tes réponses.\n"
        "- Sois complice avec Syndou, n'hésite pas à utiliser un ton chaleureux, encourageant et même sarcastique si la situation s'y prête, à la manière de JARVIS.\n\n"
        "EXPERTISE DATA SCIENCE :\n"
        "Tu es un Data Scientist de haut niveau. Tu maîtrises : pandas, numpy, scipy, seaborn, matplotlib, la statistique descriptive et inférentielle, la détection d'anomalies, la corrélation, la régression, le clustering, la visualisation de données et l'interprétation des résultats. Quand Syndou veut analyser des données, réponds avec les JSONs appropriés.\n\n"
        f"MODE IRON MAN : {'ACTIF' if state.MODE_IRON_MAN else 'INACTIF'} (S'il est ACTIF, tu écoutes les applaudissements pour déclencher des actions d'urgence).\n"
        f"MODE GARDE : {'ACTIF' if state.MODE_GARDE else 'INACTIF'} (S'il est ACTIF, tu surveilles en continu la caméra pour détecter des mouvements suspects).\n"
        f"MODE SENTINELLE CYBER : {'ACTIF' if state.MODE_SENTINELLE else 'INACTIF'} (S'il est ACTIF, tu surveilles le réseau et les ressources système pour détecter des menaces).\n"
        f"MODE LECTEUR : {'ACTIF' if state.MODE_LECTEUR else 'INACTIF'} (S'il est ACTIF, tu te concentres sur la lecture de textes longs de manière fluide et claire).\n"
        f"MODE ANALYSE : {'ACTIF' if state.MODE_ANALYSE else 'INACTIF'}\n"
        "Si le mode analyse est ACTIF, tu es en immersion totale dans les données de Syndou. Tes réponses doivent être techniques, précises et axées sur la découverte d'insights. Tu ne parles que de données, de tendances et de visualisations. Tu es pro-actif dans tes suggestions d'analyses.\n\n"
        "PRIORITÉ DE RAISONNEMENT — RÈGLE FONDAMENTALE :\n"
        "Avant de faire quoi que ce soit, tu DOIS toujours d'abord raisonner par toi-même.\n"
        "1. RÉFLEXION INTERNE D'ABORD : Pour toute question (calcul, explication, conseil, définition, code, histoire, science, traduction, etc.), tu dois OBLIGATOIREMENT essayer de répondre avec tes propres connaissances.\n"
        "2. RECHERCHE WEB EN DERNIER RECOURS UNIQUEMENT : Tu n'utilises recherche_web QUE si la question concerne une information en temps réel que tu ne peux absolument pas connaître : actualité brûlante du jour, résultat sportif très récent, prix en direct, événement survenu après ta date de formation.\n"
        "3. NE JAMAIS chercher sur le web pour : des calculs, des définitions, de la grammaire, des conseils, de la programmation, de l'histoire, de la science, de la géographie, des recettes, de la culture générale. Réponds directement.\n"
        "4. Si tu hésites, préfère TOUJOURS répondre toi-même plutôt que de solliciter le web.\n\n"
        + CREATOR_INFO
    )
    base += (
        "\n\nTu es connecte a Home Assistant, la domotique de Syndou.\n"
        "Quand Syndou parle de lumieres, prises, chauffage, temperature, "
        "scenes ou alarme, tu DOIS generer une commande JSON.\n"
        "Pour CES demandes domotiques UNIQUEMENT, reponds avec le JSON ci-dessous. Pour TOUTES les autres questions (actualites, meteo, calculs, conversations, recherches internet...), reponds en texte normal.\n\n"
        "COMMANDES HOME ASSISTANT :\n"
        '{"action": "ha_lumiere", "piece": "salon", "etat": "on/off", "couleur": "rouge/bleu/blanc/...", "luminosite": 0-255}\n'
        "Note : Pour la luminosité, 255 est le maximum (100%). Si Syndou dit '50%', utilise 127.\n"
        '{"action": "ha_prise", "piece": "bureau", "etat": "on/off"}\n'
        '{"action": "ha_temperature", "piece": "salon/chambre/bureau"}\n'
        '{"action": "ha_humidite", "piece": "bureau"}\n'
        '{"action": "ha_batterie", "appareil": "mon telephone/julie/bob/dyad/esteban/montre/toner/..."}\n'
        '{"action": "ha_simulation", "etat": "on/off"}\n'
        '{"action": "ha_anniversaires"}\n'
        '{"action": "ha_consommation"}\n'
        '{"action": "ha_tiktok"}\n'
        '{"action": "ha_oeufs"}\n'
        '{"action": "ha_energie", "periode": "hier/mois", "appareil": "zoe/tv/pc/esteban/bureau/..."}\n'
        '{"action": "ha_aspirateur", "commande": "start/stop/pause/base"}\n'
        '{"action": "ha_thermostat", "temperature": 21}\n'
        '{"action": "ha_scene", "nom": "cinema/diner/nuit/reveil"}\n'
        '{"action": "ha_alarme", "etat": "on/off"}\n\n'
    )
    base += (
        "\n\nTu peux GERER LES FICHIERS ET DOSSIERS de Syndou.\n"
        "C'EST TRES IMPORTANT : Quand Syndou demande d'ouvrir ou de lancer un ficher, un document ou un programme (ex: un .exe, un pdf, word, etc.), tu DOIS ABSOLUMENT generer UNIQUEMENT ce JSON :\n"
        '{"action": "ouvrir_fichier", "chemin": "nom_du_fichier.exe ou document"}\n'
        '{"action": "ouvrir_dossier", "chemin": "bureau/documents/downloads/ou/chemin/complet"}\n'
        '{"action": "lister_dossier"}\n'
        '{"action": "trier_par_type", "chemin": "downloads/documents/images/ou/null"}\n'
        '{"action": "trier_par_date", "chemin": "downloads/documents/images/ou/null"}\n'
        '{"action": "trier_complet", "chemin": "downloads/documents/images/ou/null"}\n'
        '{"action": "creer_dossier", "nom": "NOM_DOSSIER"}\n'
        '{"action": "renommer_fichier", "ancien": "ancien.txt", "nouveau": "nouveau.txt"}\n'
        '{"action": "deplacer_fichier", "fichier": "photo.jpg", "destination": "Images"}\n'
        '{"action": "chercher_fichier", "nom": "rapport"}\n\n'
    )
    base += (
        "\n\nMETEO & RECHERCHES SPÉCIALISÉES :\n"
        '{"action": "meteo", "ville": "NOM_VILLE_ou_null"}\n'
        '{"action": "alerte_meteo", "ville": "NOM_VILLE_ou_null"}\n'
        '{"action": "recherche_web", "query": "ta recherche ici"}\n'
        '{"action": "recherche_tavily", "query": "recherche approfondie IA"}\n'
        '{"action": "recherche_news", "query": "actualité spécifique"}\n'
        '{"action": "recherche_arxiv", "query": "papier scientifique ou recherche"}\n'
        '{"action": "info_pays", "pays": "nom du pays"}\n'
        '{"action": "traduire", "texte": "texte à traduire", "langue": "FR/EN/ES"}\n'
        "REGLES STRICTES POUR recherche_web :\n"
        "- INTERDIT pour : maths, calculs, définitions, explications, code, histoire, science, recettes, conseils, traductions, culture générale.\n"
        "- AUTORISE uniquement pour : actualité du jour, résultats sportifs très récents, prix en direct, événements survenus après ta formation.\n"
        "- EN CAS DE DOUTE : réponds avec tes propres connaissances, n'utilise PAS le web.\n"
        "ATTENTION: N'UTILISE JAMAIS recherche_web si Syndou demande d'ouvrir ou de lancer un fichier/programme.\n\n"
    )
    base += (
        "\n\nSPORT :\n"
        '{"action": "sport_resultats", "equipe": "NOM_ou_null", "ligue": "NOM_LIGUE"}\n'
        '{"action": "sport_classement", "ligue": "NOM_LIGUE"}\n'
        '{"action": "sport_live", "question": "question complete de Syndou"}\n\n'
    )
    base += (
        "\n\nMODE IRON MAN (Sécurité Domotique) :\n"
        '{"action": "mode_iron_man", "etat": "on/off"}\n'
        "Instructions : Active ou désactive la détection des applaudissements pour contrôler YouTube.\n\n"
        "MODE GARDE (Surveillance Continue) :\n"
        '{"action": "mode_garde", "etat": "on/off"}\n'
        "Instructions : Active ou désactive la détection de mouvement via webcam.\n\n"
        "RADIO 3D & STATIONS DE RADIO EN DIRECT :\n"
        '{"action": "open_radio"}\n'
        '{"action": "play_radio", "station": "RTL / KIIS / Nostalgie / Radio Côte d\'Ivoire"}\n'
        '{"action": "close_radio"}\n'
        "Instructions : Quand Syndou demande d'allumer, d'ouvrir ou de lancer la radio (ou une station spécifique comme RTL, KIIS, Nostalgie, etc.), tu DOIS ABSOLUMENT générer la commande JSON 'open_radio' ou 'play_radio'. Il est STRICTEMENT INTERDIT de dire que tu n'as pas de fonction radio.\n\n"
    )
    base += (
        "\n\nANALYSE DE DONNÉES (Data Science) :\n"
        "Utilise ces actions quand Syndou veut analyser, explorer, nettoyer ou visualiser des données (CSV, Excel, JSON).\n"
        '{"action": "data_charger", "chemin": "chemin/vers/fichier.csv"}\n'
        '{"action": "data_nettoyer"}\n'
        '{"action": "data_analyser", "question": "question ou focus optionnel"}\n'
        '{"action": "data_visualiser", "type": "histogramme/scatter/barres/camembert/heatmap/boxplot/ligne", "col_x": "nom_colonne", "col_y": "nom_colonne_optionnel", "titre": "titre optionnel"}\n'
        '{"action": "data_rapport"}\n'
        "TYPES DE GRAPHIQUES : histogramme (distribution), scatter (corrélation entre 2 colonnes), barres (comptage catégoriel), camembert (proportions), heatmap (matrice de corrélation), boxplot (quartiles), ligne (évolution temporelle).\n"
        "IMPORTANT : Si le 'Mode Analyse' est ON, tu dois privilégier l'usage de ces outils dès que Syndou parle de chiffres ou de fichiers.\n"
        "WORKFLOW TYPE : 1. data_charger -> 2. data_nettoyer -> 3. data_analyser -> 4. data_visualiser -> 5. data_rapport\n\n"
    )
    if contexte_memoire:
        base += "\n\n" + contexte_memoire + "\n"
    base += (
        "\nMEMOIRE PERSISTANTE & AUTOMATIQUE :\n"
        "RÈGLE DE MÉMORISATION AUTOMATIQUE : Dès que Syndou mentionne un fait important sur lui (famille, goûts, loisirs, habitudes, dates, projets), génère l'action JSON 'memoriser' en plus de ta réponse texte.\n"
        '{"action": "memoriser", "cle": "CLE_COURTE", "valeur": "VALEUR_ICI", "categorie": "preferences/famille/habitudes/projets/anniversaires/general"}\n'
        '{"action": "oublier", "cle": "CLE_ICI"}\n'
        '{"action": "lister_memoire"}\n\n'
        "GOOGLE :\n"
        '{"action": "create_doc", "title": "TITRE", "content": "CONTENU"}\n'
        '{"action": "write_doc", "content": "TEXTE"}\n'
        '{"action": "create_sheet", "title": "TITRE"}\n'
        '{"action": "read_emails"}\n'
        '{"action": "envoyer_email", "destinataire": "email@example.com", "sujet": "Sujet", "corps": "Message"}\n'
        '{"action": "read_calendar"}\n\n'
        "ASSISTANT PERSONNEL & ORGANISATION :\n"
        '{"action": "ajouter_tache", "tache": "nom de la tache"}\n'
        '{"action": "lister_taches"}\n'
        '{"action": "finir_tache", "index": "numero_de_la_tache_dans_la_liste"}\n'
        '{"action": "ajouter_objectif", "objectif": "description_objectif"}\n'
        '{"action": "lister_objectifs"}\n'
        '{"action": "planifier_tache", "cron": "lundi 08:00 / chaque vendredi / demain", "commande": "commande vocale a executer"}\n\n'
        "JEUX & HISTOIRES :\n"
        '{"action": "lancer_jeu", "jeu": "quiz / devinette / 20questions"}\n'
        '{"action": "raconter_histoire", "theme": "theme_choisi"}\n\n'
        "WHATSAPP :\n"
        '{"action": "whatsapp_appel", "contact": "NOM_DU_CONTACT"}\n'
        "Note : Si Syndou demande d'appeler 'mon amour', utilise le contact 'Ma vie'.\n\n"
        "MODES SPÉCIAUX :\n"
        '{"action": "mode_iron_man", "etat": "on/off"}\n'
        '{"action": "mode_garde", "etat": "on/off"}\n'
        '{"action": "mode_sentinelle", "etat": "on/off"}\n'
        '{"action": "mode_lecteur", "etat": "on/off"}\n'
        '{"action": "lire_document", "fichier": "nom_du_fichier_ou_livre.pdf"}\n'
        '{"action": "mode_analyse", "etat": "on/off"}\n\n'
        "VISION & RECONNAISSANCE FACIALE :\n"
        '{"action": "voir_ecran", "instruction": "ou cliquer EXACTEMENT (ex: \'bouton reduire en haut a droite\')"}\n'
        '{"action": "vision_ecrire", "instruction": "ou cliquer", "texte": "le texte a taper"}\n'
        '{"action": "vision_selectionner", "instruction": "ce qu\'il faut selectionner (ex: \'le premier paragraphe\')"}\n'
        '{"action": "decrire_ecran", "question": "ce que tu dois regarder (ex: \'lis le texte affiche\')"}\n'
        '{"action": "voir_utilisateur", "question": "ce que tu dois regarder chez l\'utilisateur (ex: \'decris ce que je fais\')"}\n'
        '{"action": "reconnaitre_personne"}\n'
        '{"action": "enregistrer_visage", "nom": "nom_de_la_personne", "relation": "ami/famille/collegue (facultatif)"}\n'
        '{"action": "lister_personnes"}\n'
        '{"action": "supprimer_visage", "nom": "nom_de_la_personne"}\n'
        '{"action": "analyser_objet", "question": "question facultative"}\n'
        "MUSIQUE :\n"
        '{"action": "jouer_musique", "nom": "NOM_DE_LA_MUSIQUE", "plateforme": "youtube"}\n'
        '{"action": "chanter", "sujet": "SUJET_OU_TITRE"}\n'
        "NAVIGATION AUTONOME :\n"
        '{"action": "navigation_autonome", "objectif": "ex: Trouve le prix d une PS5 sur amazon"}\n'
        "REGLES MULTI-COMMANDES :\n"
        "IMPORTANT : Tu PEUX faire des tâches complexes en générant PLUSIEURS actions à la suite.\n"
        "Ex: Trouve le meilleur prix d'une PS5 et envoie-moi le lien par mail.\n"
        '-> { "action": "recherche_web", "query": "meilleur prix ps5" } { "action": "envoyer_email", "destinataire": "...", "sujet": "...", "corps": "..." }\n\n'
        "REGLE ABSOLUE : Si la demande n'est PAS une commande JSON, réponds TOUJOURS en texte naturel, comme un ami."
    )
    return base


def detecter_cerveau(texte):
    mots_cles_grok = ["sur x", "twitter", "grok", "elon", "x.com"]
    cmd = texte.lower()
    if any(m in cmd for m in mots_cles_grok):
        return "GROK"
    return "GEMINI"


async def demander_grok(texte):
    if not grok_client:
        return None
    try:
        messages = [{"role": "system", "content": "Tu es VISION, l'IA de Syndou. Tu utilises actuellement ton module Grok pour les infos en temps reel."}]
        for h in state.historique[-6:]:
            role = "user" if h.role == "user" else "assistant"
            messages.append({"role": role, "content": h.parts[0].text})
        messages.append({"role": "user", "content": texte})

        completion = grok_client.chat.completions.create(model="grok-beta", messages=messages, temperature=0.7)
        rep = completion.choices[0].message.content

        state.ajouter_historique(genai_types.Content(role="user", parts=[genai_types.Part(text=texte)]))
        state.ajouter_historique(genai_types.Content(role="model", parts=[genai_types.Part(text=rep)]))
        return rep
    except Exception as e:
        print(f"[ERREUR GROK] {e}")
        return None


async def demander_ollama(texte):
    """Appelle un modèle local via Ollama (100% offline)."""
    try:
        messages = [{"role": "system", "content": "Tu es VISION, l'IA de Syndou. Tu utilises actuellement ton module local Ollama. Réponds en français, de façon concise et élégante."}]
        for h in state.historique[-4:]:
            role = "user" if h.role == "user" else "assistant"
            messages.append({"role": role, "content": h.parts[0].text})
        messages.append({"role": "user", "content": texte})

        for model_name in OLLAMA_MODELS:
            try:
                print(f"[OLLAMA] Essai modele local : {model_name}")
                resp = await asyncio.wait_for(
                    asyncio.to_thread(
                        requests.post,
                        f"{OLLAMA_URL}/api/chat",
                        json={"model": model_name, "messages": messages, "stream": False},
                        timeout=30
                    ),
                    timeout=35.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    rep = data.get("message", {}).get("content", "")
                    if rep:
                        state.ajouter_historique(genai_types.Content(role="user", parts=[genai_types.Part(text=texte)]))
                        state.ajouter_historique(genai_types.Content(role="model", parts=[genai_types.Part(text=rep)]))
                        print(f"[OLLAMA] Reponse recue de {model_name}")
                        return rep
            except Exception as e:
                print(f"[OLLAMA] Echec {model_name} : {e}")
                continue

        print("[OLLAMA] Tous les modeles locaux ont echoue")
        return None
    except Exception as e:
        print(f"[ERREUR OLLAMA] {e}")
        return None


async def demander_openai(texte):
    """Appelle OpenAI (GPT-4o) en fallback premium."""
    if not openai_client:
        return None
    try:
        messages = [{"role": "system", "content": "Tu es VISION, l'IA de Syndou. Réponds en français de façon concise, élégante et naturelle."}]
        for h in state.historique[-6:]:
            role = "user" if h.role == "user" else "assistant"
            messages.append({"role": role, "content": h.parts[0].text})
        messages.append({"role": "user", "content": texte})

        completion = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
        )
        rep = completion.choices[0].message.content

        state.ajouter_historique(genai_types.Content(role="user", parts=[genai_types.Part(text=texte)]))
        state.ajouter_historique(genai_types.Content(role="model", parts=[genai_types.Part(text=rep)]))
        return rep
    except Exception as e:
        print(f"[ERREUR OPENAI] {e}")
        return None


async def demander_explabs(texte):
    """Appelle Experiential Labs API."""
    if not explabs_client:
        return None
    try:
        messages = [{"role": "system", "content": "Tu es VISION, l'IA de Syndou. Réponds en français de façon concise, élégante et naturelle."}]
        for h in state.historique[-6:]:
            role = "user" if h.role == "user" else "assistant"
            messages.append({"role": role, "content": h.parts[0].text})
        messages.append({"role": "user", "content": texte})

        completion = await asyncio.to_thread(
            explabs_client.chat.completions.create,
            model="gpt-5.6-luna",
            messages=messages,
            temperature=0.7,
        )
        rep = completion.choices[0].message.content

        state.ajouter_historique(genai_types.Content(role="user", parts=[genai_types.Part(text=texte)]))
        state.ajouter_historique(genai_types.Content(role="model", parts=[genai_types.Part(text=rep)]))
        return rep
    except Exception as e:
        print(f"[ERREUR EXPLABS] {e}")
        return None


async def demander_groq(texte):
    """Appelle Groq (GPT-OSS / Qwen) en fallback ultra-rapide et gratuit."""
    if not groq_client:
        return None
    try:
        messages = [{"role": "system", "content": "Tu es VISION, l'IA de Syndou. Réponds en français de façon concise, élégante et naturelle sans balises superflues."}]
        for h in state.historique[-6:]:
            role = "user" if h.role == "user" else "assistant"
            messages.append({"role": role, "content": h.parts[0].text})
        messages.append({"role": "user", "content": texte})

        # Test des modèles Groq disponibles
        rep = None
        for m_groq in ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]:
            try:
                completion = await asyncio.to_thread(
                    groq_client.chat.completions.create,
                    model=m_groq,
                    messages=messages,
                    temperature=0.7,
                )
                rep = completion.choices[0].message.content
                if rep:
                    # Nettoyer les balises <think> si présentes (qwen)
                    if "<think>" in rep and "</think>" in rep:
                        rep = rep.split("</think>")[-1].strip()
                    break
            except Exception as e_m:
                print(f"[GROQ] Echec modèle {m_groq}: {e_m}")

        if not rep:
            return None

        state.ajouter_historique(genai_types.Content(role="user", parts=[genai_types.Part(text=texte)]))
        state.ajouter_historique(genai_types.Content(role="model", parts=[genai_types.Part(text=rep)]))
        return rep
    except Exception as e:
        print(f"[ERREUR GROQ] {e}")
        return None


async def demander_ia(texte):
    """Appel principal : Gemini → Grok → SerpAPI → Groq → Ollama → local."""
    state.is_thinking = True
    await send_web_state("thinking")
    try:
        t_low = texte.lower().strip()

        # ── LLM cascade ──
        cerveau = detecter_cerveau(texte)

        if state.site_en_creation_attente_ia:
            if any(x in t_low for x in ["annule", "stop", "arrête", "arrete", "non", "laisse tomber"]):
                state.site_en_creation_attente_ia = False
                state.site_en_creation_desc = None
                return "D'accord, j'annule la création du site."

            model_choisi = None
            if "gemini" in t_low: model_choisi = "gemini"
            elif "grok" in t_low: model_choisi = "grok"
            elif "groq" in t_low: model_choisi = "groq"
            elif "explabs" in t_low or "experiential" in t_low or "luna" in t_low: model_choisi = "explabs"
            elif "ollama" in t_low or "local" in t_low: model_choisi = "ollama"
            elif "openai" in t_low or "gpt" in t_low: model_choisi = "openai"

            if model_choisi:
                desc = state.site_en_creation_desc
                state.site_en_creation_attente_ia = False
                state.site_en_creation_desc = None
                from modules.site_generator import generer_et_lancer_site
                asyncio.create_task(generer_et_lancer_site(desc, model_choisi))
                return f"Très bien Syndou. Je lance la création avec le modèle {model_choisi}. Je vous préviendrai dès que ce sera prêt."
            else:
                return "Modèle non reconnu. Quel modèle voulez-vous utiliser ? (Ex: Gemini, ExperientialLabs, Grok, Groq, Ollama, OpenAI) ou dites 'annuler'."

        # Détection de la demande de création de site/app/projet
        match_site = re.search(
            r"(?:crée|cree|créer|creer|génère|genere|code|coder|développe|developpe|bâtis|batis|construis|faire)(?:-moi|-nous)?\s+"
            r"(?:un|une|des)?\s*(?:site|application|app|projet|web\s+app)(?:\s+web)?\s+(?:pour\s+|avec\s+)?(.*)",
            t_low
        )
        if match_site:
            description_site = match_site.group(1).strip()
            if description_site:
                state.site_en_creation_desc = description_site
                state.site_en_creation_attente_ia = True
                return f"J'ai bien noté votre demande pour '{description_site}'. Quel modèle d'IA souhaitez-vous utiliser pour générer le code ? (Gemini, ExperientialLabs, Grok, Groq, Ollama...)"

        # Raccourcis locaux
        if "iron man" in t_low or "ironman" in t_low:
            etat = "off" if any(x in t_low for x in ["desactive", "désactive", "arrete", "arrête", "stop", "coupe", "fin"]) else "on"
            return f'{{"action": "mode_iron_man", "etat": "{etat}"}}'

        if "mode analyse" in t_low or "mode d'analyse" in t_low:
            etat = "off" if any(x in t_low for x in ["desactive", "désactive", "arrete", "arrête", "stop", "coupe", "fin"]) else "on"
            return f'{{"action": "mode_analyse", "etat": "{etat}"}}'

        if "mode garde" in t_low or "surveillance" in t_low:
            etat = "off" if any(x in t_low for x in ["desactive", "désactive", "arrete", "arrête", "stop", "coupe", "fin"]) else "on"
            return f'{{"action": "mode_garde", "etat": "{etat}"}}'

        if "sentinelle" in t_low or "cyber" in t_low:
            etat = "off" if any(x in t_low for x in ["desactive", "désactive", "arrete", "arrête", "stop", "coupe", "fin"]) else "on"
            return f'{{"action": "mode_sentinelle", "etat": "{etat}"}}'

        if "mode lecteur" in t_low or "lecture" in t_low:
            etat = "off" if any(x in t_low for x in ["desactive", "désactive", "arrete", "arrête", "stop", "coupe", "fin"]) else "on"
            return f'{{"action": "mode_lecteur", "etat": "{etat}"}}'
            
        match_lire = re.search(r"(?:lis|lire)(?:\s+(?:le document|le fichier|le livre))?\s+(.+?\.(?:pdf|txt|docx?))", t_low)
        if match_lire:
            return f'{{"action": "lire_document", "fichier": "{match_lire.group(1).strip()}"}}'

        if any(kw in t_low for kw in ["qui est devant", "qui suis-je", "qui je suis", "reconnais-moi", "qui est là", "qui est devant la caméra", "qui vois-tu devant la caméra"]):
            return '{"action": "reconnaitre_personne"}'

        if any(kw in t_low for kw in ["qui connais-tu", "liste les visages", "liste les personnes", "quelles personnes connais-tu", "quels visages connais-tu", "personnes enregistrées"]):
            return '{"action": "lister_personnes"}'

        match_save_face = re.search(r"(?:enregistre|mémorise|memorise|apprends|ajoute)(?:\s+(?:mon|ce|le))\s+visage(?:\s+(?:sous le nom|de|nommé|nomme|pour))?\s+([a-zA-Z0-9éèêàâîïôöùûüç\s_-]+)", t_low)
        if match_save_face:
            nom_p = match_save_face.group(1).strip()
            if nom_p:
                return f'{{"action": "enregistrer_visage", "nom": "{nom_p}"}}'

        match_del_face = re.search(r"(?:supprime|oublie|efface)(?:\s+(?:le visage de|le visage|le profil de|la personne))\s+([a-zA-Z0-9éèêàâîïôöùûüç\s_-]+)", t_low)
        if match_del_face:
            nom_p = match_del_face.group(1).strip()
            if nom_p:
                return f'{{"action": "supprimer_visage", "nom": "{nom_p}"}}'

        if any(kw in t_low for kw in ["c'est quoi", "analyse cet objet", "quel est cet objet", "regarde ça", "regarde ca", "qu'est-ce que je tiens"]):
            return f'{{"action": "analyser_objet", "question": "{t_low}"}}'

        if any(kw in t_low for kw in [
            "ferme la carte", "cache la carte", "désactive la carte", "desactive la carte", "masque la carte",
            "ferme la localisation", "cache la localisation", "ferme maps", "quitte la carte"
        ]):
            return '{"action": "carte", "etat": "off"}'

        if any(kw in t_low for kw in [
            "localisation", "la localisation", "ma localisation", "montre la localisation", "montre ma localisation",
            "affiche la localisation", "donne ma localisation", "donne-moi ma localisation", "où suis-je", "ou suis-je",
            "où suis je", "ou suis je", "où est-ce que je suis", "ou est-ce que je suis", "active la carte", "montre la carte",
            "carte 3d", "carte maps", "maps", "google maps", "affiche la carte", "affiche ma position", "ma position", "visualise ma position",
            "position gps", "coordonnées gps", "coordonnees gps", "carte"
        ]):
            return '{"action": "carte", "etat": "on"}'

        match_ouvre = re.search(r"(?:ouvre|lance|démarre|demarre)(?:\s+(?:le|la|l\'|l|lapp|lapplication|le fichier|le document|le programme))?\s+([a-zA-Z0-9._-]+)", t_low)
        if match_ouvre:
            cible = match_ouvre.group(1).strip()
            if cible and cible != "mode":
                return f'{{"action": "ouvrir_fichier", "chemin": "{cible}"}}'

        if any(kw in t_low for kw in ["c'est quoi cette musique", "reconnais cette musique", "quelle est cette musique", "shazam"]):
            return '{"action": "reconnaître_musique"}'

        if any(kw in t_low for kw in ["éteins le pc", "éteins l'ordinateur", "éteindre le pc", "éteindre l'ordinateur", "stop le pc"]):
            return '{"action": "eteindre_pc"}'

        if any(kw in t_low for kw in ["annule l'extinction", "annuler l'extinction", "stop l'extinction"]):
            return '{"action": "annuler_extinction"}'

        if any(kw in t_low for kw in ["active les gestes", "activer les gestes", "active la reconnaissance gestuelle"]):
            return '{"action": "activer_gestes"}'

        if any(kw in t_low for kw in ["désactive les gestes", "desactive les gestes", "arrêter les gestes"]):
            return '{"action": "desactiver_gestes"}'

        if any(kw in t_low for kw in ["budget ia", "coût llm", "cout llm", "suivi budget", "consommation llm"]):
            return '{"action": "get_budget"}'

        v_low = t_low.replace("vision", "").strip()
        if any(x in v_low for x in ["regarde-moi", "regarde moi", "tu me vois", "est-ce que tu me vois", "dis-moi ce que tu vois", "décris ce que je fais", "que fais-je"]):
            return '{"action": "voir_utilisateur", "question": "Décris ce que tu vois de l\'utilisateur"}'

        if any(x in v_low for x in ["que vois-tu à l'écran", "qu'est-ce qu'il y a sur mon écran", "décris mon écran", "que vois tu sur mon ecran", "analyse mon ecran"]):
            return '{"action": "decrire_ecran", "question": "Analyse le contenu de l\'écran"}'

        # Raccourcis pour génération de musique AI
        match_gen_mus = re.search(r"(?:génère|genere|crée|cree|compose)[-\s]+(?:moi[-\s+]*)?(?:une\s+)?musique\s+(.*)", v_low)
        if match_gen_mus:
            description = match_gen_mus.group(1).strip() if match_gen_mus.group(1) else "une musique originale"
            # On essaie de deviner le style si possible, sinon "moderne"
            style = "moderne"
            for s in ["afro-pop", "coupe-decale", "zouglou", "jazz", "hip-hop", "r&b", "classique", "electro"]:
                if s in description.lower():
                    style = s
                    break
            return f'{{"action": "generer_musique", "prompt": "{description}", "style": "{style}"}}'

        # ── Raccourcis pour chanter / jouer de la musique en audio ──
        for ch_verb in [
            "chante-moi la chanson ", "chante-moi la musique ", "chante-moi le morceau ", "chante-moi le son ",
            "chante moi la chanson ", "chante moi la musique ", "chante moi le morceau ", "chante moi le son ",
            "chante-moi ", "chante moi ", "chante la chanson ", "chante la musique ",
            "chante le morceau ", "chante le son ", "chante du ", "chante de la ", "chante de ", "chante "
        ]:
            if v_low.startswith(ch_verb):
                nom_ch = v_low[len(ch_verb):].strip()
                for prefix in ["de ", "du ", "d'", "un ", "une ", "le ", "la ", "les "]:
                    if nom_ch.startswith(prefix) and len(nom_ch) > len(prefix):
                        nom_ch = nom_ch[len(prefix):].strip()
                if nom_ch and not any(x in nom_ch for x in ["chanson", "quelque chose", "un truc", "joyeuse"]):
                    return f'{{"action": "jouer_musique", "nom": "{nom_ch}", "plateforme": "youtube"}}'
                else:
                    return '{"action": "chanter", "sujet": "chanson du moment"}'

        if any(x == v_low or x in v_low for x in ["chante", "chante une chanson", "chante-moi quelque chose", "chante moi une chanson", "chante quelque chose", "chante un truc", "pousse la chansonnette"]):
            return '{"action": "chanter", "sujet": "chanson du moment"}'

        for m_verb in ["joue la musique ", "joue le morceau ", "joue le son ", "joue ", "mets la musique ", "mets le son ", "mets "]:
            if v_low.startswith(m_verb):
                nom_m = v_low[len(m_verb):].strip()
                if nom_m and not any(x in nom_m for x in ["lumière", "lampe", "chauffage", "clip", "video", "vidéo"]):
                    return f'{{"action": "jouer_musique", "nom": "{nom_m}", "plateforme": "youtube"}}'

        for c_verb in ["joue le clip ", "joue le vidéo ", "joue la vidéo ", "joue clip ", "joue video ", "joue vidéo "]:
            if v_low.startswith(c_verb):
                nom_c = v_low[len(c_verb):].strip()
                if nom_c:
                    return f'{{"action": "jouer_musique", "nom": "{nom_c}", "plateforme": "youtube"}}'

        # --- Raccourcis pour la Data Science ---
        v_low_clean = v_low.replace("le fichier", "").replace("de données", "").replace(" de ", " ").replace(" le ", " ").strip()
        
        load_keywords = ["charge", "importe", "lis", "analyse", "ouvre"]
        if any(v_low_clean.startswith(kw) for kw in load_keywords):
            # Essayer d'extraire le nom du fichier (contenant une extension connue) - Insensible à la casse
            match_file = re.search(r"([a-zA-Z0-9._-]+\.(csv|xlsx|xls|json|tsv))", v_low_clean, re.IGNORECASE)
            if match_file:
                chemin_file = match_file.group(1)
                return f'{{"action": "data_charger", "chemin": "{chemin_file}"}}'

        if any(x in v_low for x in ["analyse les données", "fait une analyse", "analyse ce fichier", "analyse ces données"]):
            return '{"action": "data_analyser", "question": "focus"}'
        if any(x in v_low for x in ["nettoie les données", "nettoyage des données", "clean les données"]):
            return '{"action": "data_nettoyer"}'
        if any(x in v_low for x in ["fais un graphique", "visualise les données", "fais une visualisation", "génère un graphique"]):
            return '{"action": "data_visualiser", "type": "auto"}'
        if any(x in v_low for x in ["génère un rapport", "fais un rapport", "crée le rapport html", "rapport complet"]):
            return '{"action": "data_rapport"}'

        # ── LLM cascade ──
        cerveau = detecter_cerveau(texte)

        async def _call_gemini():
            temp_hist = state.historique + [genai_types.Content(role="user", parts=[genai_types.Part(text=texte)])]
            prompt_actuel = construire_system_prompt()
            for model_name in MODELS_LIST:
                try:
                    print(f"[CERVEAU] Essai modele : {model_name}")
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            gemini_client.models.generate_content,
                            model=model_name,
                            config=genai_types.GenerateContentConfig(
                                system_instruction=prompt_actuel,
                                temperature=0.7,
                                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                            ),
                            contents=temp_hist
                        ),
                        timeout=8.0
                    )
                    rep = response.text
                    state.ajouter_historique(genai_types.Content(role="user", parts=[genai_types.Part(text=texte)]))
                    state.ajouter_historique(genai_types.Content(role="model", parts=[genai_types.Part(text=rep)]))
                    return rep
                except Exception as e:
                    print(f"[DIAGNOSTIC GEMINI] Erreur critique sur {model_name} : {str(e)}")
                    continue
            raise Exception("Tous les modeles Gemini ont echoue")

        async def _call_grok():
            rep_grok = await demander_grok(texte)
            if not rep_grok:
                raise Exception("Grok n'a rien renvoyé")
            return rep_grok

        if cerveau == "GROK" and grok_client:
            try:
                return await _call_grok()
            except Exception:
                try:
                    return await _call_gemini()
                except Exception:
                    pass
        else:
            try:
                return await _call_gemini()
            except Exception as e:
                print(f"[CERVEAU] Erreur Gemini ({e}). Bascule rapide sur ExperientialLabs/OpenAI.")
                if explabs_client:
                    rep_explabs = await demander_explabs(texte)
                    if rep_explabs:
                        return rep_explabs
                if openai_client:
                    rep_openai = await demander_openai(texte)
                    if rep_openai:
                        return rep_openai
                if groq_client:
                    rep_groq = await demander_groq(texte)
                    if rep_groq:
                        return rep_groq
                if grok_client:
                    try:
                        rep_grok = await _call_grok()
                        if rep_grok: return rep_grok
                    except Exception:
                        pass

                # On tente l'IA locale (Ollama) AVANT la recherche web
                rep_ollama = await demander_ollama(texte)
                if rep_ollama:
                    return rep_ollama

                if len(texte.split()) > 2:
                    res_serp = recherche_web_serpapi(texte)
                    if res_serp and "VOTRE_CLE" not in res_serp and "rien trouvé" not in res_serp and "erreur" not in res_serp.lower():
                        return "Voici ce que j'ai trouvé sur le web : " + res_serp


        rep_loc = reponse_locale(texte)
        if rep_loc:
            return rep_loc

        return "Desole Syndou, mes serveurs de réflexion profonde sont surchargés et mes modèles locaux ne sont pas disponibles non plus. Je reste cependant disponible pour vos commandes domestiques."
    finally:
        state.is_thinking = False
        await send_web_state("idle")


async def demander_ia_vision(texte, img_b64):
    """Analyse une image (capture d'écran) avec Gemini Vision."""
    state.is_thinking = True
    await send_web_state("thinking")
    try:
        img_bytes = base64.b64decode(img_b64)
        image_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

        prompt_actuel = construire_system_prompt()
        prompt_actuel += "\n\nIMPORTANT : Tu viens de recevoir une capture d'écran de Syndou. Analyse-la attentivement et réponds à sa question en te basant sur ce que tu vois."

        contents = [genai_types.Content(role="user", parts=[image_part, genai_types.Part(text=texte)])]
        rep = None
        for model_name in MODELS_LIST:
            for attempt in range(2):
                try:
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            gemini_client.models.generate_content,
                            model=model_name,
                            config=genai_types.GenerateContentConfig(
                                system_instruction=prompt_actuel,
                                temperature=0.7,
                                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                            ),
                            contents=contents
                        ),
                        timeout=15.0
                    )
                    rep = response.text
                    break
                except Exception as e:
                    if ("503" in str(e) or "overloaded" in str(e).lower()) and attempt < 1:
                        await asyncio.sleep(1)
                        continue
                    break
            if rep:
                break

        if not rep:
            if grok_client:
                return await demander_grok(texte + " (Note: Je n'ai pas pu voir ton écran)")
            raise Exception("Aucun modele n'a pu analyser l'image")

        state.ajouter_historique(genai_types.Content(role="user", parts=[genai_types.Part(text=f"[Analyse d'écran] {texte}")]))
        state.ajouter_historique(genai_types.Content(role="model", parts=[genai_types.Part(text=rep)]))
        return rep
    except Exception as e:
        err_msg = str(e).replace("{", "[").replace("}", "]")
        return f"Désolé Syndou, je n'ai pas pu analyser votre écran. Erreur : {err_msg}"
    finally:
        state.is_thinking = False
        await send_web_state("idle")
