"""
VISION — Générateur de Sites Web
Module pour piloter les LLMs, concevoir les codes sources HTML/CSS/JS et lancer le site généré.
"""

import os
import re
import asyncio
import json
import requests
from modules import state
from modules.config import (
    gemini_client, grok_client, groq_client, MODELS_LIST, OLLAMA_URL, OLLAMA_MODELS
)
from google.genai import types as genai_types
from modules.voice import parler
from modules.file_manager import ouvrir_navigateur

def extraire_fichiers_demarcation(texte):
    """
    Extrait les fichiers d'un texte formaté avec :
    ==== FILE: chemin ====
    contenu
    ==== END FILE ====
    """
    pattern = r"==== FILE:\s*(.*?)\s*====\r?\n(.*?)\r?\n==== END FILE ===="
    matches = re.findall(pattern, texte, re.DOTALL)
    
    files = []
    for path, content in matches:
        files.append({
            "path": path.strip(),
            "content": content
        })
    return files

async def generer_et_lancer_site(desc, ia_choisie):
    """
    Pilote l'IA choisie pour coder un site web moderne ou une application complète avec backend,
    l'enregistre en local et l'ouvre.
    """
    print(f"[SITE GENERATION] Début compilation pour : '{desc}' via {ia_choisie.upper()}")
    
    # 1. Détecter si un backend est requis
    keywords_backend = ["backend", "serveur", "base de", "database", "api", "fullstack", "full-stack", "node", "express", "flask", "fastapi", "python backend", "réservation", "reservation", "sql", "login", "auth"]
    demand_backend = any(x in desc.lower() for x in keywords_backend)
    
    # Message de confirmation initial
    if demand_backend:
        message_attente = f"Très bien Syndou. Je lance la création de votre application complexe '{desc}' avec son backend en faisant travailler {ia_choisie.upper()}. Je m'occupe de concevoir l'architecture frontend, le serveur backend, la base de données SQLite et le guide d'utilisation. Veuillez patienter..."
    else:
        message_attente = f"Très bien Syndou. Je lance la création du site '{desc}' en travaillant avec {ia_choisie.upper()}. Je m'occupe de concevoir l'architecture, le design moderne et l'interactivité. Veuillez patienter..."
        
    await parler(message_attente)

    # 2. Construction du prompt approprié
    if demand_backend:
        prompt = (
            f"Tu es un Développeur Full Stack Principal et Architecte Logiciel Senior d'élite.\n"
            f"Conçois le code source complet d'une application web à l'aspect premium, moderne et extrêmement professionnel avec son BACKEND et sa BASE DE DONNÉES sur le sujet : {desc}.\n\n"
            "STRUCTURE DU PROJET (SEPARATION DES PREOCCUPATIONS) :\n"
            "Tu dois concevoir et structurer le projet en plusieurs fichiers bien séparés. "
            "Rédige le code complet de chaque fichier dans le format de démarcation suivant (sans guillemets d'échappement, écris le code source brut directement, un fichier après l'autre) :\n\n"
            "==== FILE: frontend/index.html ====\n"
            "<!-- Code HTML de l'interface client ici. Charge le CDN Tailwind CSS, FontAwesome, et crée un design premium avec styles glassmorphism et formulaires soignés. -->\n"
            "==== END FILE ====\n\n"
            "==== FILE: frontend/app.js ====\n"
            "// Logique client JavaScript pour l'interactivité et appels fetch d'API HTTP REST backend en gérant les réponses.\n"
            "==== END FILE ====\n\n"
            "==== FILE: backend/server.py ====\n"
            "# Code du serveur API Flask/FastAPI en Python configurant CORS (avec Flask-CORS pour éviter les blocages Cross-Origin en local) et les routes REST.\n"
            "==== END FILE ====\n\n"
            "==== FILE: backend/database.py ====\n"
            "# Gestionnaire SQLite de la base de données (création des tables, insertion de données d'exemple, requêtes propres).\n"
            "==== END FILE ====\n\n"
            "==== FILE: requirements.txt ====\n"
            "flask\nflask-cors\n"
            "==== END FILE ====\n\n"
            "==== FILE: README.md ====\n"
            "# Guide d'utilisation\n"
            "Étapes d'installation (pip install) et lancement du backend.\n"
            "==== END FILE ====\n\n"
            "RÈGLE ABSOLUE : Rédige uniquement les fichiers dans ce format de démarcation. N'ajoute pas de texte d'introduction ou de conclusion."
        )
    else:
        prompt = (
            f"Tu es un Développeur Full Stack Senior et un Designer d'interface d'élite.\n"
            f"Conçois le code source complet d'un site web à l'aspect premium, moderne et extrêmement professionnel sur le sujet : {desc}.\n\n"
            "DIRECTIVES TECHNIQUES ET ESTHÉTIQUES :\n"
            "- Le site doit être contenu dans un fichier HTML unique en sortie (comportant le CSS Tailwind et le Javascript interactif).\n"
            "- Charge obligatoirement Tailwind CSS via CDN : <script src=\"https://cdn.tailwindcss.com\"></script>\n"
            "- Charge FontAwesome pour des icônes esthétiques : <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css\">\n"
            "- Charge des polices élégantes depuis Google Fonts (ex: Inter, Playfair Display, Montserrat, Outfit ou Roboto) et applique-les.\n"
            "- Utilise des éléments de design ultra-modernes : effets de glassmorphism (backdrop-filter), dégradés lisses et harmonieux, ombres subtiles, et micotransitions interactives.\n"
            "- Utilise des images réelles provenant d'Unsplash en libre de droits.\n"
            "- Le site doit comporter au moins ces sections : Navigation, Hero, Galerie/Services, À propos, Contact modernisé, Footer.\n"
            "- IMPORTANT : Pas de Lorem Ipsum. Rédige de vrais textes convaincantes rédigés en français, adaptés spécialement au sujet.\n"
            "- Gère l'interactivité principale (ex: menu mobile, formulaires) directement avec du Vanilla Javascript propre en bas du fichier.\n\n"
            "FORMAT DE RÉPONSE ATTENDU :\n"
            "Renvoie uniquement le code HTML complet enveloppé dans un bloc de code markdown identifié ```html\n"
            "N'ajoute aucune explication textuelle avant ou après le bloc. Rédige directement le code dans le bloc."
        )

    rep = None
    
    # ── 3. Appel de l'IA sélectionnée ──
    try:
        # Config de génération Gemini pour éviter la troncature
        config_gemini = genai_types.GenerateContentConfig(
            max_output_tokens=8192,
            temperature=0.7
        )

        if ia_choisie == "gemini":
            for model in MODELS_LIST:
                try:
                    response = await asyncio.to_thread(
                        gemini_client.models.generate_content,
                        model=model,
                        contents=[prompt],
                        config=config_gemini
                    )
                    rep = response.text
                    if rep:
                        break
                except Exception as e:
                    print(f"[SITE GENERATION] Échec Gemini {model} : {e}")
                    
        elif ia_choisie == "grok" and grok_client:
            try:
                completion = await asyncio.to_thread(
                    grok_client.chat.completions.create,
                    model="grok-3",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=8192
                )
                rep = completion.choices[0].message.content
            except Exception as e:
                print(f"[SITE GENERATION] Échec Grok : {e}")
                
        elif ia_choisie == "groq" and groq_client:
            try:
                completion = await asyncio.to_thread(
                    groq_client.chat.completions.create,
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=8192
                )
                rep = completion.choices[0].message.content
            except Exception as e:
                print(f"[SITE GENERATION] Échec Groq : {e}")
                
        elif ia_choisie == "ollama":
            for model in OLLAMA_MODELS:
                try:
                    resp = await asyncio.to_thread(
                        requests.post,
                        f"{OLLAMA_URL}/api/chat",
                        json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False},
                        timeout=120
                    )
                    if resp.status_code == 200:
                        rep = resp.json().get("message", {}).get("content", "")
                        if rep:
                            break
                except Exception as e:
                    print(f"[SITE GENERATION] Échec Ollama {model} : {e}")
        
        # ── 4. Fallback si l'IA choisie a échoué ──
        if not rep:
            print("[SITE GENERATION] L'IA spécifiée a échoué. Tentative globale via modèle Gemini standard...")
            for model in MODELS_LIST:
                try:
                    response = await asyncio.to_thread(
                        gemini_client.models.generate_content,
                        model=model,
                        contents=[prompt],
                        config=config_gemini
                    )
                    rep = response.text
                    if rep:
                        break
                except Exception:
                    pass

        if not rep:
            await parler("Je suis désolé Syndou, mes serveurs de génération sont surchargés et je n'ai pas pu concevoir le projet. Veuillez réessayer dans quelques instants.")
            return

        # ── 5. Traitement si format Projet Multi-fichiers avec Backend ──
        if demand_backend:
            # Essayer d'abord d'extraire via le format de démarcation
            files = extraire_fichiers_demarcation(rep)
            
            # Si vide, essayer de parser au format JSON (ancien format/fallback)
            if not files:
                print("[SITE GENERATION] Aucun fichier trouvé via démarcation. Tentative via parser JSON...")
                json_code = ""
                for tag in ["json", ""]:
                    if tag:
                        match = re.search(fr"```{tag}(.*?)```", rep, re.DOTALL | re.IGNORECASE)
                    else:
                        match = re.search(r"```(.*?)```", rep, re.DOTALL)
                    if match:
                        json_code = match.group(1).strip()
                        break
                if not json_code:
                    json_code = rep.strip()
                try:
                    project_data = json.loads(json_code)
                    files = project_data.get("files", [])
                except Exception as e_json:
                    print(f"[SITE GENERATION] Le parser JSON a échoué : {e_json}")

            # Écriture des fichiers extraits
            if files:
                words = [w for w in re.split(r'\W+', desc) if w]
                nom_site_clean = "_".join(words[:4]).lower() if words else "app_generee"
                
                sites_dir = r"C:\VISION\sites"
                site_path = os.path.join(sites_dir, nom_site_clean)
                os.makedirs(site_path, exist_ok=True)
                
                readme_path = None
                frontend_index_path = None
                
                for f_entry in files:
                    rel_path = f_entry.get("path")
                    content = f_entry.get("content", "")
                    if rel_path:
                        abs_file_path = os.path.join(site_path, rel_path)
                        # Créer les dossiers parents s'ils n'existent pas
                        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
                        with open(abs_file_path, "w", encoding="utf-8") as f_out:
                            f_out.write(content)
                        print(f"[SITE GENERATION] Fichier créé : {abs_file_path}")
                        if "index.html" in rel_path.lower():
                            frontend_index_path = abs_file_path
                        if "readme.md" in rel_path.lower():
                            readme_path = abs_file_path
                
                # Ouvrir le fichier principal et le dossier du projet
                if readme_path:
                    ouvrir_navigateur(abs_file_path if not frontend_index_path else frontend_index_path)
                elif frontend_index_path:
                    ouvrir_navigateur(frontend_index_path)
                else:
                    try:
                        os.startfile(site_path)
                    except Exception:
                        pass

                await parler(
                    f"Voilà Syndou, j'ai terminé de concevoir l'architecture de l'application '{desc}' avec son backend Python et sa base de données SQLite. "
                    f"Tous les fichiers ont été générés dans le dossier sites/{nom_site_clean}. "
                    f"J'ouvre l'application dans votre navigateur et un fichier README.md vous expliquant comment lancer le serveur."
                )
                return
            else:
                print("[SITE GENERATION] Aucun fichier structuré trouvé. Sauvegarde brute dans index.html en mode fallback...")

        # ── 6. Fallback / Single Page HTML ──
        html_code = ""
        match = re.search(r"```html(.*?)```", rep, re.DOTALL | re.IGNORECASE)
        if match:
            html_code = match.group(1).strip()
        else:
            match_any = re.search(r"```(.*?)```", rep, re.DOTALL)
            if match_any:
                html_code = match_any.group(1).strip()
            else:
                html_code = rep.strip()

        if not html_code.startswith("<!DOCTYPE html>") and "<html" not in html_code[:100]:
            start_idx = html_code.find("<!DOCTYPE")
            if start_idx != -1:
                html_code = html_code[start_idx:]
            else:
                start_html = html_code.find("<html")
                if start_html != -1:
                    html_code = html_code[start_html:]

        # Enregistrement en local
        words = [w for w in re.split(r'\W+', desc) if w]
        nom_site_clean = "_".join(words[:4]).lower() if words else "site_genere"
        
        sites_dir = r"C:\VISION\sites"
        site_path = os.path.join(sites_dir, nom_site_clean)
        os.makedirs(site_path, exist_ok=True)
        
        filepath = os.path.join(site_path, "index.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_code)
            
        print(f"[SITE GENERATION] Code écrit avec succès dans : {filepath}")
        
        ouvrir_navigateur(filepath)
        await parler(f"Voilà Syndou, j'ai terminé de concevoir et d'architecturer le site pour {desc}. Je l'ouvre immédiatement dans votre dev-environnement.")

    except Exception as e:
        print(f"[SITE GENERATION ERROR] {e}")
        await parler(f"Navré Syndou, une erreur interne est survenue lors de la création du site : {e}")
