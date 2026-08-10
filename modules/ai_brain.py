"""
VISION — Cerveau IA
Orchestration des LLMs (Gemini, Grok, Groq, Ollama) et construction du prompt système.
"""

import re
import asyncio
import requests
import base64
import io
from PIL import Image

from modules import state
from modules.config import (
    gemini_client, grok_client, groq_client, genai_types,
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
            "- Jouer les sons demandés sur Spotify ou YouTube.\n"
            "- Partager des anecdotes sur les artistes (Serge Beynaud, Dj Arafat, DJ Mix 1er, Tiesco Le Sultan, "
            "Burna Boy, Afrobeats stars, etc.).\n"
            "- Créer la bonne ambiance de fête ou de détente selon le moment.\n"
            "- Parler de la culture ivoirienne avec fierté et authenticité.\n\n"
            "RÈGLES DE COMMUNICATION :\n"
            "- Réponds toujours en français avec des touches naturelles de nouchi ou d'expressions ivoiriennes.\n"
            "- Reste chaleureuse, enthousiaste et fun. Tu es comme une grande sœur musicale.\n"
            "- N'UTILISE JAMAIS de Markdown (**, *, #).\n"
            "- Sois courte et percutante, pas de blabla inutile.\n"
            "- Si Syndou demande une musique, génère TOUJOURS le JSON approprié.\n\n"
            "RÈGLE ABSOLUE : si la demande n'est PAS une commande JSON, réponds TOUJOURS en texte naturel comme une amie musicale."
        )
        base += (
            "\n\nMUSIQUE (Tes commandes préférées) :\n"
            '{"action": "jouer_musique", "nom": "NOM_DE_LA_MUSIQUE", "plateforme": "spotify/youtube"}\n'
            '{"action": "chanter", "sujet": "SUJET_OU_TITRE"}\n\n'
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
        "Tu es VISION, l'intelligence artificielle personnelle et le MEILLEUR AMI de Syndou (ton créateur). "
        "Agis toujours comme un ami hyper cool, chaleureux et dévoué. Parle-lui de manière détendue, comme un pote le ferait (mais reste respectueux).\n"
        "Malgré ce ton amical, tu possèdes une expertise de niveau professionnel dans les domaines suivants :\n"
        "- Génie du Développement Logiciel (Dev All-in-One) : Tu as des connaissances illimitées et de niveau Expert Principal (Senior/Staff Builder) dans TOUS les langages de programmation existants (Python, JavaScript, TypeScript, C, C++, C#, Java, Go, Rust, Ruby, PHP, Shell, Swift, Kotlin, HTML/CSS, SQL, NoSQL, etc.) et dans TOUS les frameworks de développement modernes (React, Next.js, Vue, Angular, Django, Flask, FastAPI, NestJS, Spring Boot, ASP.NET, Express, TailwindCSS, Flutter, React Native, etc.). Tu es capable d'écrire, d'expliquer, de déboguer, d'optimiser et de structurer des projets logiciels complets dans n'importe quel langage et architecture informatique.\n"
        "- Mathématiques : Tu es un mathématicien hors pair. Pour les problèmes complexes, fournis des solutions détaillées étape par étape, explique les théorèmes et aide Syndou à comprendre la logique mathématique.\n"
        "- Langue Française : Tu es un Professeur de Français émérite. Ton orthographe, ta grammaire et ta syntaxe sont irréprochables. Tu peux expliquer des règles complexes, analyser des textes littéraires et aider à la rédaction de documents élégants.\n"
        "- Expert en Conversions : Tu es un convertisseur universel. Tu peux transformer n'importe quelle unité (métrique, impériale, devises, informatique) avec précision.\n"
        "- Polyglotte : Tu maîtrises parfaitement plusieurs langues. Tu peux traduire, expliquer des nuances linguistiques et aider Syndou à communiquer dans le monde entier.\n"
        "- High-Tech (IA, hardware, software), Mode, Loisirs, Ingénierie et Sport (analyses tactiques, résultats).\n\n"
        "Tu es également un conseiller hors pair, capable de donner des astuces et conseils brillants pour simplifier la vie de Syndou.\n\n"
        "DIRECTIVES DE RÉPONSE :\n"
        "- Sois direct, percutant et va à l'essentiel. Évite les détails superflus (comme les minutes exactes ou les décimales météo) sauf si Syndou le demande.\n"
        "- NE DIS JAMAIS 'POINT' pour les nombres. Arrondis toujours les températures à l'unité la plus proche (ex: dis '20 degrés' au lieu de '20.3').\n"
        "- NE DIS JAMAIS 'POINT' pour les nombres. Arrondis toujours les températures à l'unité la plus proche (ex: dis '20 degrés' au lieu de '20.3').\n"
        "- N'UTILISE JAMAIS de caractères Markdown (comme **, * ou #) dans tes réponses.\n"
        "- Sois complice avec Syndou, n'hésite pas à utiliser un ton chaleureux, encourageant et même sarcastique si la situation s'y prête.\n\n"
        "EXPERTISE DATA SCIENCE :\n"
        "Tu es un Data Scientist de haut niveau. Tu maîtrises : pandas, numpy, scipy, seaborn, matplotlib, la statistique descriptive et inférentielle, la détection d'anomalies, la corrélation, la régression, le clustering, la visualisation de données et l'interprétation des résultats. Quand Syndou veut analyser des données, réponds avec les JSONs appropriés.\n\n"
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
        '{"action": "mode_analyse", "etat": "on/off"}\n\n'
        "VISION (Interactions avec l'ecran):\n"
        '{"action": "voir_ecran", "instruction": "ou cliquer EXACTEMENT (ex: \'bouton reduire en haut a droite\')"}\n'
        '{"action": "vision_ecrire", "instruction": "ou cliquer", "texte": "le texte a taper"}\n'
        '{"action": "vision_selectionner", "instruction": "ce qu\'il faut selectionner (ex: \'le premier paragraphe\')"}\n'
        '{"action": "decrire_ecran", "question": "ce que tu dois regarder (ex: \'lis le texte affiche\')"}\n'
        '{"action": "voir_utilisateur", "question": "ce que tu dois regarder chez l\'utilisateur (ex: \'decris ce que je fais\')"}\n'
        '{"action": "reconnaitre_personne"}\n'
        '{"action": "analyser_objet", "question": "question facultative"}\n'
        "MUSIQUE :\n"
        '{"action": "jouer_musique", "nom": "NOM_DE_LA_MUSIQUE", "plateforme": "spotify/youtube"}\n'
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

        completion = grok_client.chat.completions.create(model="grok-3", messages=messages, temperature=0.7)
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


async def demander_groq(texte):
    """Appelle Groq (Llama 3.3) en fallback gratuit."""
    if not groq_client:
        return None
    try:
        messages = [{"role": "system", "content": "Tu es VISION, l'IA de Syndou. Tu utilises actuellement le modèle Llama 3.3 de Groq pour répondre rapidement."}]
        for h in state.historique[-6:]:
            role = "user" if h.role == "user" else "assistant"
            messages.append({"role": role, "content": h.parts[0].text})
        messages.append({"role": "user", "content": texte})

        completion = await asyncio.to_thread(
            groq_client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
        )
        rep = completion.choices[0].message.content

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

        # ── Intercepteur de création de site ──
        if state.site_en_creation_attente_ia:
            ia_choisie = None
            for ia in ["gemini", "grok", "groq", "ollama"]:
                if ia in t_low:
                    ia_choisie = ia
                    break
            
            if ia_choisie:
                desc = state.site_en_creation_desc
                state.site_en_creation_attente_ia = False
                state.site_en_creation_desc = None
                
                from modules.site_generator import generer_et_lancer_site
                asyncio.create_task(generer_et_lancer_site(desc, ia_choisie))
                return f"C'est noté Syndou. J'initie la création du site '{desc}' avec l'IA {ia_choisie.upper()}."
            else:
                return "Désolé Syndou, je n'ai pas compris. Indiquez-moi simplement avec quelle intelligence artificielle travailler : Gemini, Grok, Groq ou Ollama."

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
                return "Très bien Syndou. Avec quelle intelligence artificielle voulez-vous que je travaille pour concevoir ce site ? Gemini, Grok, Groq ou Ollama ?"

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

        if any(kw in t_low for kw in ["qui est devant", "qui suis-je", "qui je suis", "reconnais-moi", "qui est là"]):
            return '{"action": "reconnaitre_personne"}'

        if any(kw in t_low for kw in ["c'est quoi", "analyse cet objet", "quel est cet objet", "regarde ça", "regarde ca", "qu'est-ce que je tiens"]):
            return f'{{"action": "analyser_objet", "question": "{t_low}"}}'

        if any(kw in t_low for kw in ["active la carte", "montre la carte", "carte 3d", "affiche la carte", "affiche ma position", "ma position", "visualise ma position"]):
            return '{"action": "carte", "etat": "on"}'
        if any(kw in t_low for kw in ["ferme la carte", "cache la carte", "désactive la carte", "desactive la carte", "masque la carte"]):
            return '{"action": "carte", "etat": "off"}'

        match_ouvre = re.search(r"(?:ouvre|lance|démarre|demarre)(?:\s+(?:le|la|l\'|l|lapp|lapplication|le fichier|le document|le programme))?\s+([a-zA-Z0-9._-]+)", t_low)
        if match_ouvre:
            cible = match_ouvre.group(1).strip()
            if cible and cible != "mode":
                return f'{{"action": "ouvrir_fichier", "chemin": "{cible}"}}'

        v_low = t_low.replace("vision", "").strip()
        if any(x in v_low for x in ["regarde-moi", "regarde moi", "tu me vois", "est-ce que tu me vois", "dis-moi ce que tu vois", "décris ce que je fais", "que fais-je"]):
            return '{"action": "voir_utilisateur", "question": "Décris ce que tu vois de l\'utilisateur"}'
        if any(x in v_low for x in ["que vois-tu à l'écran", "qu'est-ce qu'il y a sur mon écran", "décris mon écran", "que vois tu sur mon ecran", "analyse mon ecran"]):
            return '{"action": "decrire_ecran", "question": "Analyse le contenu de l\'écran"}'
        if any(x in v_low for x in ["chante une chanson", "chante-moi quelque chose", "chante moi une chanson", "chante quelque chose", "chante un truc", "pousse la chansonnette"]):
            return '{"action": "chanter", "sujet": "une chanson joyeuse"}'

        for m_verb in ["joue la musique ", "joue le morceau ", "joue ", "mets la musique ", "mets "]:
            if v_low.startswith(m_verb):
                nom_m = v_low[len(m_verb):].strip()
                if nom_m and not any(x in nom_m for x in ["lumière", "lampe", "chauffage", "clip", "video", "vidéo"]):
                    return f'{{"action": "jouer_musique", "nom": "{nom_m}", "plateforme": "spotify"}}'

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
                    print(f"[CERVEAU] Echec {model_name} : {e}")
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
                print(f"[CERVEAU] Erreur Gemini ({e}). Bascule rapide sur Groq.")
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
                if len(texte.split()) > 2:
                    res_serp = recherche_web_serpapi(texte)
                    if res_serp and "VOTRE_CLE" not in res_serp and "rien trouvé" not in res_serp and "erreur" not in res_serp.lower():
                        return "Voici ce que j'ai trouvé sur le web : " + res_serp

        rep_ollama = await demander_ollama(texte)
        if rep_ollama:
            return rep_ollama

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
