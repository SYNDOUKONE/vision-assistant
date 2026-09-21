"""
VISION — Gestionnaire d'Actions
Traitement de toutes les commandes JSON retournées par l'IA.
"""

import os
import re
import json
import time
import asyncio
import pyautogui
import subprocess
import shutil

from datetime import datetime

from modules import state
from modules.config import (
    grok_client, genai_types, LOCAL_IP,
    PIECES_LUMIERES, PIECES_PRISES, PIECES_CAPTEURS, PIECES_HUMIDITE,
    APPAREILS_BATTERIE, APPAREILS_ENERGIE, COULEURS_MAP, HA_TARIFS,
    HA_URL, HA_HEADERS,
)
from modules.ai_music import generer_musique, rechercher_musique_ai
from modules.voice import parler, nettoyer_commande
from modules.home_assistant import (
    ha_appeler_service, ha_get_etat, ha_get_calendrier,
    ha_lumiere, ha_interrupteur, ha_thermostat, ha_scene,
)
from modules.file_manager import (
    ouvrir_dossier, ouvrir_fichier, lister_dossier,
    trier_par_type, trier_par_date, trier_par_type_puis_date,
    creer_sous_dossier, renommer_fichier, deplacer_fichier, chercher_fichier,
    ouvrir_navigateur,
)
from modules.data_science import data_charger, data_nettoyer, data_analyser, data_visualiser, data_rapport_html
from modules.google_services import (
    creer_google_doc, modifier_google_doc, lire_emails, envoyer_email,
    lister_evenements_calendar, creer_google_sheet,
)
from modules.weather_sports import (
    get_meteo_actuelle, get_alertes_meteo,
    get_resultats_football, get_classement_football, get_resultats_sport_gemini,
)
from modules.music import chercher_youtube, chercher_youtube_id, jouer_musique_spotify
from modules.vision_screen import (
    vision_cliquer, vision_ecrire, vision_selectionner,
    vision_decrire, vision_voir_utilisateur,
    vision_reconnaitre_personne, vision_analyser_objet, navigation_autonome
)
from modules.face_recognition_system import (
    enregistrer_visage, reconnaitre_personne,
    lister_personnes_connues, supprimer_visage
)
from modules.assistant import (
    ajouter_tache, lister_taches, finir_tache, 
    ajouter_objectif, lister_objectifs, planifier_tache
)
from modules.games import lancer_jeu, raconter_histoire
from modules.web_search import (
    recherche_web_serpapi, recherche_tavily, recherche_newsapi,
    recherche_arxiv, info_pays, traduire_deepl, recherche_web_globale
)
from modules.memory import charger_memoire, ajouter_memoire, supprimer_memoire
from modules.websocket_server import (
    send_web_state, request_screen_capture, send_web_text, send_web_carte,
    send_web_youtube, stop_web_youtube, send_web_audio
)
from modules.ai_brain import demander_ia, demander_ia_vision, demander_grok
from modules.local_solvers import (
    resoudre_math_localement, resoudre_francais_localement,
    resoudre_conversion_localement, resoudre_traduction_localement,
)
import requests


def executer_action_pc(commande):
    cmd = commande.lower()
    user_profile = os.environ.get('USERPROFILE', '')

    if "radio" in cmd:
        return None

    if "met de la musique" in cmd or "mets de la musique" in cmd:
        url = "https://www.youtube.com/watch?v=7CGKeID7nRc&list=PL4fGSI1pDJn50iCQRUVmgUjOrCggCQ9nR"
        ouvrir_navigateur(url)
        time.sleep(6)
        pyautogui.press('f')
        return "C'est parti Syndou, je mets votre playlist en plein écran."

    if "youtube" in cmd:
        recherche = cmd
        for mot in ["mets", "joue", "lance", "la video", "sur youtube", "youtube", "vision"]:
            recherche = recherche.replace(mot, "")
        recherche = recherche.strip()
        if recherche:
            url = chercher_youtube(recherche)
            if url:
                ouvrir_navigateur(url)
                time.sleep(5)
                pyautogui.press('f')
                return f"Je lance {recherche} sur YouTube."
        return "Video introuvable."

    if "ouvre" in cmd or "lance" in cmd:
        if "chrome" in cmd:
            subprocess.Popen(["chrome.exe"])
            return "Chrome ouvert."
        if "notepad" in cmd or "bloc-notes" in cmd:
            subprocess.Popen(["notepad.exe"])
            return "Bloc-notes ouvert."
        if "explorateur" in cmd:
            subprocess.Popen(["explorer.exe"])
            return "Explorateur ouvert."

    if "volume" in cmd:
        if "monte" in cmd or "augmente" in cmd:
            for _ in range(5):
                pyautogui.press('volumeup')
            return "Volume augmente."
        if "baisse" in cmd:
            for _ in range(5):
                pyautogui.press('volumedown')
            return "Volume baisse."
        if "coupe" in cmd:
            pyautogui.press('volumemute')
            return "Son coupe."

    if "screenshot" in cmd or "capture" in cmd:
        path = os.path.join(user_profile, "Desktop", "screenshot.png")
        pyautogui.screenshot(path)
        return "Screenshot sauvegarde."

    if "eteins" in cmd or "shutdown" in cmd:
        os.system("shutdown /s /t 5")
        return "Extinction dans 5 secondes."

    return None


async def action_whatsapp_appel(contact):
    try:
        await parler(f"J'appelle {contact} sur WhatsApp, Syndou.")
        os.system("start whatsapp://")
        time.sleep(6)
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(1)
        pyautogui.typewrite(contact)
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.hotkey('ctrl', 'shift', 'c')
        time.sleep(2)
        await vision_cliquer("clique sur le bouton 'Appel vocal' ou l icone de telephone qui vient de s afficher en haut a droite")
        return True
    except Exception as e:
        print(f"[WHATSAPP ERROR] {e}")
        await parler(f"Desole Syndou, je n'ai pas pu lancer l'appel WhatsApp. {e}")
        return False


def extraire_blocs_json(texte):
    """Extrait proprement les blocs JSON du texte en gérant l'équilibrage des accolades et nettoie la syntaxe si besoin."""
    blocs = []
    pile = []
    debut = -1
    for index, char in enumerate(texte):
        if char == '{':
            if len(pile) == 0:
                debut = index
            pile.append(char)
        elif char == '}':
            if pile:
                pile.pop()
                if len(pile) == 0:
                    blocs.append(texte[debut:index+1])
    
    blocs_valides = []
    for b in blocs:
        # Tentative 1 : JSON direct
        try:
            json.loads(b)
            blocs_valides.append(b)
            continue
        except Exception:
            pass

        # Tentative 2 : Nettoyage automatique des guillemets doubles accidentels (ex: ."" -> .")
        try:
            b_nettoye = re.sub(r'(?<=\w|[.,!?;])""+', '"', b)
            b_nettoye = re.sub(r'""+(?=\s*[:,}])', '"', b_nettoye)
            b_nettoye = re.sub(r',\s*([}\]])', r'\1', b_nettoye)
            json.loads(b_nettoye)
            blocs_valides.append(b_nettoye)
            continue
        except Exception:
            pass

    return blocs_valides



async def traiter_commande_entiere(texte_utilisateur, mobile_ws=None):
    """Point d'entrée principal : résout localement ou via IA, puis exécute les actions."""
    state._skip_pc_audio = bool(mobile_ws)

    # Envoyer le texte utilisateur au frontend
    await send_web_text(texte_utilisateur, "")

    # Tentative de résolution locale
    reponse = resoudre_math_localement(texte_utilisateur)
    if not reponse:
        reponse = resoudre_francais_localement(texte_utilisateur)
    if not reponse:
        reponse = resoudre_conversion_localement(texte_utilisateur)
    # Interception rapide des commandes Radio
    t_lower = texte_utilisateur.lower()
    if "radio" in t_lower:
        from modules.websocket_server import send_web_radio
        if any(kw in t_lower for kw in ["ferme", "stop", "arrête", "quitte"]):
            await send_web_radio("close_radio")
            reponse_txt = "J'ai fermé la radio Syndou."
            await parler(reponse_txt)
            await send_web_text(texte_utilisateur, reponse_txt)
            return
        elif any(kw in t_lower for kw in ["ouvre", "lance", "affiche", "mets", "écouter", "écoute"]):
            station = ""
            for s_name in ["rtl", "kiis", "europe 1", "rmc", "trace", "nostalgie", "jam", "rfi", "bbc", "al-bayane", "albayane", "senegal", "hot 97", "kexp"]:
                if s_name in t_lower:
                    station = s_name
                    break
            await send_web_radio("play_radio" if station else "open_radio", station)
            msg_station = f"station {station.upper()}" if station else "3D"
            reponse_txt = f"Je lance la radio {msg_station} pour vous Syndou."
            await parler(reponse_txt)
            await send_web_text(texte_utilisateur, reponse_txt)
            return

    # Vision écran
    if not reponse:
        t = texte_utilisateur.lower()
        if any(kw in t for kw in ["regarde mon écran", "analyse mon écran", "vois-tu mon écran", "qu'est-ce qu'il y a sur mon écran"]):
            await parler("Bien sûr Syndou, laissez-moi jeter un œil...")
            img_b64 = await request_screen_capture()
            if img_b64:
                reponse = await demander_ia_vision(texte_utilisateur, img_b64)
            else:
                reponse = "Je n'ai pas pu accéder à votre écran Syndou. Assurez-vous d'avoir cliqué sur l'icône de l'œil (👁️) en bas à gauche de mon interface Web pour m'autoriser à voir."


    if not reponse:
        reponse = await demander_ia(texte_utilisateur)

    print(f"[VISION] {reponse}")

    # Extraction des blocs JSON de manière robuste
    json_blocks = extraire_blocs_json(reponse)

    if not json_blocks:
        await parler(reponse)
        state._skip_pc_audio = False
        return

    for block in json_blocks:
        try:
            data = json.loads(block)
            action = data.get("action", "")
            print(f"[VISION] Execution de l'action : {action}")

            # ── FONCTIONNALITÉS JARVIS ENRICHIES ─────────────────────────────
            if action == "reconnaître_musique":
                from modules.music import reconnaître_musique_actuelle
                msg = await reconnaître_musique_actuelle(duree_sec=5)
                await parler(msg)

            elif action == "eteindre_pc":
                from modules.power import eteindre_pc_securise
                msg = eteindre_pc_securise(delai_secondes=30)
                await parler(msg)

            elif action == "annuler_extinction":
                from modules.power import annuler_extinction_pc
                msg = annuler_extinction_pc()
                await parler(msg)

            elif action == "wake_on_lan":
                mac = data.get("mac", "")
                from modules.power import wake_on_lan
                msg = wake_on_lan(mac)
                await parler(msg)

            elif action == "activer_gestes":
                from modules.gestures import activer_reconnaissance_gestes
                msg = activer_reconnaissance_gestes()
                await parler(msg)

            elif action == "desactiver_gestes":
                from modules.gestures import desactiver_reconnaissance_gestes
                msg = desactiver_reconnaissance_gestes()
                await parler(msg)

            elif action in ["open_radio", "play_radio"]:
                from modules.websocket_server import send_web_radio
                station = data.get("station", "")
                await send_web_radio("play_radio" if station else "open_radio", station)
                msg_txt = f"Radio {station.upper()} lancée !" if station else "Radio 3D ouverte pour vous Syndou."
                await parler(msg_txt)

            elif action == "close_radio":
                from modules.websocket_server import send_web_radio
                await send_web_radio("close_radio")
                await parler("Radio fermée Syndou.")

            # ── MODES ────────────────────────────────────────────────────
            elif action == "mode_iron_man":

                etat = data.get("etat", "off")
                state.MODE_IRON_MAN = (etat == "on")
                msg = "Protocoles Iron Man activés, Monsieur. Je reste à l'écoute de vos signaux d'urgence." if state.MODE_IRON_MAN else "Protocoles Iron Man désactivés. Je repasse en veille standard, Monsieur."
                await parler(msg)

            elif action == "mode_analyse":
                etat = data.get("etat", "off")
                state.MODE_ANALYSE = (etat == "on")
                if state.MODE_ANALYSE:
                    await send_web_state("thinking")
                    msg = "Mode Analyse activé. Je dédie tous mes processeurs à vos données, Syndou. Quel fichier étudions-nous ?"
                else:
                    await send_web_state("idle")
                    msg = "Mode Analyse désactivé. Je reviens à mes fonctions d'assistance générale."
                await parler(msg)

            elif action == "mode_garde":
                etat = data.get("etat", "off")
                if etat == "on":
                    state.MODE_GARDE = True
                    msg = "Mode Garde activé, Monsieur. Les systèmes de surveillance visuelle sont en ligne."
                else:
                    state.MODE_GARDE = False
                    msg = "Mode Garde désactivé. Fin de la surveillance, Monsieur."
                await parler(msg)

            elif action == "mode_sentinelle":
                etat = data.get("etat", "off")
                if etat == "on":
                    state.MODE_SENTINELLE = True
                    msg = "Mode Sentinelle Cyber activé, Monsieur. Déploiement des protocoles de surveillance réseau et système. Votre pare-feu numérique est en ligne."
                else:
                    state.MODE_SENTINELLE = False
                    msg = "Mode Sentinelle Cyber désactivé, Monsieur. Les boucliers de surveillance sont en veille."
                await parler(msg)

            elif action == "mode_lecteur":
                etat = data.get("etat", "off")
                if etat == "on":
                    state.MODE_LECTEUR = True
                    msg = "Mode Lecteur activé, Monsieur. Je vais me concentrer sur la lecture et la synthèse de longs textes, sans interruption."
                else:
                    state.MODE_LECTEUR = False
                    msg = "Mode Lecteur désactivé."
                await parler(msg)

            elif action == "lire_document":
                fichier = data.get("fichier", "")
                if fichier:
                    from modules.lecteur import demarrer_lecture
                    demarrer_lecture(fichier)
                else:
                    await parler("Veuillez préciser le nom du fichier à lire, Monsieur.")

            # ── MÉMOIRE ──────────────────────────────────────────────────
            elif action == "memoriser":
                cle = data.get("cle", "info")
                valeur = data.get("valeur", "")
                categorie = data.get("categorie", "general")
                ajouter_memoire(cle, valeur, categorie)
                await parler(f"C'est noté Syndou, je me souviendrai que {valeur}.")

            elif action == "oublier":
                cle = data.get("cle", "")
                if supprimer_memoire(cle):
                    await parler("Information oubliée, Syndou.")
                else:
                    await parler("Je n'avais pas cette information en mémoire.")

            elif action == "lister_memoire":
                memoire = charger_memoire()
                facts = memoire.get("facts", {})
                if not facts:
                    await parler("Aucune information personnalisée en mémoire, Syndou.")
                else:
                    lignes = ["Voici ce que je sais sur vous Syndou."]
                    for cle, data_m in facts.items():
                        cat = data_m.get("categorie", "general")
                        lignes.append(f"Dans la catégorie {cat}, je sais que {cle} est {data_m['valeur']}.")
                    await parler(" ".join(lignes))

            # ── FICHIERS ─────────────────────────────────────────────────
            elif action == "ouvrir_dossier":
                chemin = data.get("chemin", "bureau")
                ok, resultat = ouvrir_dossier(chemin)
                await parler("Dossier ouvert, Syndou." if ok else f"Je n ai pas trouve ce dossier. {resultat}")

            elif action == "ouvrir_fichier":
                chemin = data.get("chemin", "")
                ok, resultat = ouvrir_fichier(chemin)
                await parler("Fichier ouvert, Syndou." if ok else f"Je n ai pas pu ouvrir ce fichier. {resultat}")

            elif action == "lister_dossier":
                contenu, err = lister_dossier()
                if err:
                    await parler(err)
                else:
                    await parler(f"Le dossier contient {len(contenu['fichiers'])} fichiers et {len(contenu['dossiers'])} sous-dossiers, Syndou.")

            elif action == "trier_par_type":
                await parler("Je trie vos fichiers par type, Syndou.")
                ok, msg = trier_par_type()
                await parler(msg if ok else f"Probleme : {msg}")

            elif action == "trier_par_date":
                await parler("Je trie vos fichiers par date, Syndou.")
                ok, msg = trier_par_date()
                await parler(msg if ok else f"Probleme : {msg}")

            elif action == "trier_complet":
                await parler("Je trie vos fichiers par type puis par date, Syndou.")
                ok, msg = trier_par_type_puis_date()
                await parler(msg if ok else f"Probleme : {msg}")

            elif action == "creer_dossier":
                nom = data.get("nom", "Nouveau Dossier")
                ok, msg = creer_sous_dossier(nom)
                await parler(msg if ok else f"Erreur : {msg}")

            elif action == "renommer_fichier":
                ok, msg = renommer_fichier(data.get("ancien", ""), data.get("nouveau", ""))
                await parler(msg if ok else f"Erreur : {msg}")

            elif action == "deplacer_fichier":
                ok, msg = deplacer_fichier(data.get("fichier", ""), data.get("destination", ""))
                await parler(msg if ok else f"Erreur : {msg}")

            elif action == "chercher_fichier":
                nom = data.get("nom", "")
                resultats, err = chercher_fichier(nom)
                if err:
                    await parler(err)
                elif not resultats:
                    await parler(f"Aucun fichier contenant {nom} n a ete trouve.")
                else:
                    noms = [os.path.basename(r) for r in resultats[:5]]
                    await parler(f"J ai trouve {len(resultats)} fichier(s). Par exemple : {', '.join(noms)}.")

            # ── HOME ASSISTANT ───────────────────────────────────────────
            elif action == "ha_lumiere":
                piece = data.get("piece", "salon")
                etat = data.get("etat", "on")
                couleur = data.get("couleur", None)
                luminosite = data.get("luminosite", None)
                entity_id = PIECES_LUMIERES.get(piece, f"light.{piece}")
                rgb = COULEURS_MAP.get(couleur) if couleur else None
                ha_lumiere(entity_id, etat, luminosite, rgb)
                if etat == "off":
                    msg = f"J'éteins {piece}."
                else:
                    details = []
                    if couleur:
                        details.append(f"en {couleur}")
                    if luminosite is not None:
                        pourcent = int((int(luminosite) / 255) * 100)
                        details.append(f"à {pourcent}%")
                    msg = f"C'est fait, {piece} est réglé{' '.join(details)}." if details else f"Lumière {piece} allumée."
                await parler(msg)

            elif action == "ha_prise":
                piece = data.get("piece", "bureau")
                etat = data.get("etat", "on")
                entity_id = PIECES_PRISES.get(piece, f"switch.prise_{piece}")
                ha_interrupteur(entity_id, etat)
                await parler(f"Prise {piece} {'activée' if etat == 'on' else 'désactivée'}.")

            elif action == "ha_temperature":
                piece = data.get("piece", "salon")
                entity_id = PIECES_CAPTEURS.get(piece)
                if entity_id:
                    temp = ha_get_etat(entity_id)
                    await parler(f"La température dans le {piece} est de {temp} degrés.")
                else:
                    await parler(f"Désolé, je n'ai pas de capteur configuré pour le {piece}.")

            elif action == "ha_humidite":
                piece = data.get("piece", "bureau")
                entity_id = PIECES_HUMIDITE.get(piece)
                if entity_id:
                    humi = ha_get_etat(entity_id)
                    await parler(f"Le taux d'humidité dans le {piece} est de {humi}%.")
                else:
                    await parler(f"Je n'ai pas de capteur d'humidité pour le {piece}.")

            elif action == "ha_batterie":
                appareil = data.get("appareil", "").lower()
                entity_id = APPAREILS_BATTERIE.get(appareil)
                if entity_id:
                    batt = ha_get_etat(entity_id)
                    if batt == "unknown":
                        await parler(f"Je n'arrive pas à récupérer l'état de la batterie pour {appareil}.")
                    else:
                        if "telephone" in appareil or "papa" in appareil or "Syndou" in appareil:
                            suff = "Ton téléphone est à "
                        elif "julie" in appareil or "maman" in appareil:
                            suff = "Le téléphone de Julie est à "
                        else:
                            suff = f"La batterie de {appareil} est à "
                        await parler(f"{suff}{batt}%.")
                else:
                    await parler(f"Je n'ai pas l'appareil {appareil} dans ma liste de batterie.")

            elif action == "ha_thermostat":
                temp = data.get("temperature", 20)
                ha_thermostat("climate.thermostat", temp)
                await parler(f"Thermostat réglé à {temp} degrés.")

            elif action == "ha_scene":
                nom = data.get("nom", "")
                ha_scene(f"scene.{nom}")
                await parler(f"Ambiance {nom} activée.")

            elif action == "ha_alarme":
                etat = data.get("etat", "on")
                if etat == "on":
                    ha_appeler_service("alarm_control_panel", "alarm_arm_away", "alarm_control_panel.home_base_2")
                    await parler("Alarme activée.")
                else:
                    ha_appeler_service("alarm_control_panel", "alarm_disarm", "alarm_control_panel.home_base_2")
                    await parler("Alarme désactivée.")

            elif action == "ha_simulation":
                etat = data.get("etat", "on")
                ha_interrupteur("switch.simulation", etat)
                await parler("Simulation de présence activée." if etat == "on" else "Simulation de présence désactivée.")

            elif action == "ha_anniversaires":
                events = ha_get_calendrier("calendar.anniversaires")
                if not events:
                    await parler("Rien de prévu aujourd'hui.")
                else:
                    noms = [e.get("summary", "Anniversaire sans nom") for e in events]
                    if len(noms) == 1:
                        await parler(f"Aujourd'hui, nous fêtons l'anniversaire de {noms[0]}.")
                    else:
                        liste = ", ".join(noms[:-1]) + " et " + noms[-1]
                        await parler(f"Aujourd'hui, il y a plusieurs anniversaires : {liste}.")

            elif action == "ha_consommation":
                entity_id = PIECES_CAPTEURS.get("consommation")
                puissance = ha_get_etat(entity_id)
                if puissance in ["unknown", "inconnu"]:
                    await parler("Je n'arrive pas à lire la consommation électrique pour le moment.")
                else:
                    await parler(f"La consommation actuelle de la maison est de {puissance} Volt-Ampères.")

            elif action == "ha_tiktok":
                entity_id = PIECES_CAPTEURS.get("tiktok")
                followers = ha_get_etat(entity_id)
                await parler(f"Tu as actuellement {followers} abonnés sur ton compte TikTok TechEnClair, Syndou.")

            elif action == "ha_oeufs":
                entity_id = PIECES_CAPTEURS.get("oeufs")
                try:
                    r = requests.get(f"{HA_URL}/api/states/{entity_id}", headers=HA_HEADERS, timeout=5)
                    d = r.json()
                    last_changed = d.get("last_changed", "")
                    if last_changed:
                        dt = datetime.fromisoformat(last_changed.replace("Z", "+00:00"))
                        phrase = dt.strftime("le %d %B à %Hh%M")
                        await parler(f"Le dernier ramassage des œufs a été enregistré {phrase}.")
                    else:
                        await parler("Je n'ai pas d'historique pour le ramassage des œufs.")
                except Exception:
                    await parler("Je n'arrive pas à accéder aux informations sur les œufs.")

            elif action == "ha_energie":
                periode = data.get("periode", "mois")
                appareil = data.get("appareil", "")
                if appareil:
                    entite = APPAREILS_ENERGIE.get(appareil.lower())
                    if entite:
                        val = ha_get_etat(entite)
                        if val not in ["inconnu", "unknown"]:
                            kwh = float(val)
                            await parler(f"La consommation de {appareil} pour ce mois est de {kwh:.1f} kWh.")
                        else:
                            await parler(f"Je n'ai pas de données de consommation pour {appareil}.")
                    else:
                        await parler(f"Je n'ai pas d'appareil nommé {appareil} dans mon suivi.")
                elif periode == "hier":
                    total_kwh = total_cost = 0.0
                    try:
                        for i in range(1, 7):
                            val = ha_get_etat(f"sensor.lixee_zlinky_tic_zlinky_p{i}_daily", attribut="last_period")
                            if val not in ["inconnu", "unknown"]:
                                k = float(val)
                                total_kwh += k
                                total_cost += k * HA_TARIFS.get(f"p{i}", 0.16)
                        await parler(f"Hier, la maison a consommé {total_kwh:.1f} kWh, pour {total_cost:.2f} euros.")
                    except Exception:
                        await parler("J'ai eu un problème pour calculer la consommation d'hier.")
                else:
                    total_kwh = total_cost = 0.0
                    try:
                        for i in range(1, 7):
                            val = ha_get_etat(f"sensor.lixee_zlinky_tic_zlinky_p{i}_mensuel")
                            if val not in ["inconnu", "unknown"]:
                                k = float(val)
                                total_kwh += k
                                total_cost += k * HA_TARIFS.get(f"p{i}", 0.16)
                        await parler(f"Ce mois-ci, la consommation totale est de {total_kwh:.1f} kWh, pour {total_cost:.2f} euros.")
                    except Exception:
                        await parler("Je n'ai pas pu calculer la consommation mensuelle.")

            elif action == "ha_aspirateur":
                commande = data.get("commande", "start")
                cmds = {"start": ("vacuum", "start", "C'est parti, Bob lance le nettoyage."),
                         "stop": ("vacuum", "stop", "J'ai arrêté l'aspirateur."),
                         "pause": ("vacuum", "pause", "Bob est en pause."),
                         "base": ("vacuum", "return_to_base", "Bob retourne à sa base.")}
                svc, act, msg = cmds.get(commande, cmds["start"])
                ha_appeler_service(svc, act, "vacuum.bob")
                await parler(msg)

            # ── GOOGLE ───────────────────────────────────────────────────
            elif action == "create_doc":
                result = creer_google_doc(data.get("title", "Document VISION"), data.get("content", ""))
                await parler(result)
            elif action == "write_doc":
                result = modifier_google_doc(data.get("content", ""))
                await parler(result)
            elif action == "create_sheet":
                result = creer_google_sheet(data.get("title", "Feuille VISION"))
                await parler(result)
            elif action == "read_emails":
                result = lire_emails()
                await parler(f"Voici vos derniers emails Syndou. {result}")
            elif action == "envoyer_email":
                destinataire = data.get("destinataire", "")
                sujet = data.get("sujet", "")
                corps = data.get("corps", "")
                result = envoyer_email(destinataire, sujet, corps)
                await parler(result)
            elif action == "read_calendar":
                result = lister_evenements_calendar()
                await parler(f"Voici vos prochains evenements Syndou. {result}")

            # ── MÉTÉO & RECHERCHE ────────────────────────────────────────
            elif action == "meteo":
                ville = data.get("ville") or None
                await parler("Je consulte la meteo, un instant Syndou.")
                res = await asyncio.to_thread(get_meteo_actuelle, ville)
                await parler(res)
            elif action == "alerte_meteo":
                res = await asyncio.to_thread(get_alertes_meteo, data.get("ville") or None)
                await parler(res)
            elif action == "recherche_web":
                query = data.get("query", "")
                await parler(f"Je lance une recherche sur internet pour {query}.")
                res = await asyncio.to_thread(recherche_web_globale, query)
                await parler(res)

            elif action == "recherche_tavily":
                query = data.get("query", "")
                await parler(f"Je lance une recherche Tavily pour {query}.")
                res = await asyncio.to_thread(recherche_tavily, query)
                if not res:
                    res = await asyncio.to_thread(recherche_web_globale, query)
                await parler(res)

            elif action == "recherche_news":
                query = data.get("query", "top-headlines")
                await parler("Je consulte les dernières actualités.")
                res = await asyncio.to_thread(recherche_newsapi, query)
                if not res:
                    res = await asyncio.to_thread(recherche_web_globale, query)
                await parler(res)

            elif action == "recherche_arxiv":
                query = data.get("query", "")
                await parler(f"Je recherche les publications scientifiques pour {query}.")
                res = await asyncio.to_thread(recherche_arxiv, query)
                await parler(res or "Aucun résultat trouvé sur ArXiv.")

            elif action == "info_pays":
                pays = data.get("pays", "")
                await parler(f"Je recherche les informations pour le pays {pays}.")
                res = await asyncio.to_thread(info_pays, pays)
                await parler(res or f"Impossible de récupérer les informations pour {pays}.")

            elif action == "traduire":
                texte = data.get("texte", "")
                langue = data.get("langue", "FR")
                await parler("Je traduis le texte pour vous.")
                res = await asyncio.to_thread(traduire_deepl, texte, langue)
                await parler(res or f"La traduction n'a pas pu être effectuée.")

            # ── SPORT ────────────────────────────────────────────────────
            elif action == "sport_resultats":
                equipe = data.get("equipe") or None
                ligue = data.get("ligue") or None
                await parler(f"Je cherche les informations pour {equipe or ligue}.")
                result = await asyncio.to_thread(get_resultats_football, equipe=equipe, ligue=ligue)
                if ("pas trouvé" in result or "Impossible" in result) and grok_client:
                    res_grok = await demander_grok(f"Syndou veut savoir : {texte_utilisateur}")
                    if res_grok:
                        result = res_grok
                await parler(result)
            elif action == "sport_classement":
                ligue = data.get("ligue", "Ligue 1")
                await parler(f"Je recupere le classement {ligue}.")
                res = await asyncio.to_thread(get_classement_football, ligue=ligue)
                await parler(res)
            elif action == "sport_live":
                question = data.get("question", "derniers resultats sportifs 2026")
                await parler("Je recherche les derniers resultats en direct.")
                res = await asyncio.to_thread(get_resultats_sport_gemini, question)
                await parler(res)

            # ── VISION ÉCRAN ─────────────────────────────────────────────
            elif action == "voir_ecran":
                await parler(await vision_cliquer(data.get("instruction", "")))
            elif action == "vision_ecrire":
                await parler(await vision_ecrire(data.get("instruction", ""), data.get("texte", "")))
            elif action == "vision_selectionner":
                await parler(await vision_selectionner(data.get("instruction", "")))
            elif action == "decrire_ecran":
                await parler(await vision_decrire(data.get("question", "Que vois-tu?")))
            elif action == "voir_utilisateur":
                await parler(await vision_voir_utilisateur(data.get("question", "Que vois-tu?")))
            elif action == "reconnaitre_personne":
                await parler("Un instant Syndou, j'analyse le visage devant la caméra...")
                res = await reconnaitre_personne()
                await parler(res)
            elif action == "enregistrer_visage":
                nom = data.get("nom", "").strip()
                relation = data.get("relation", "")
                notes = data.get("notes", "")
                await parler(f"Regardez bien la caméra Syndou, j'enregistre le visage pour {nom}...")
                res = await enregistrer_visage(nom, relation=relation, notes=notes)
                await parler(res)
            elif action == "lister_personnes":
                res = lister_personnes_connues()
                await parler(res)
            elif action == "supprimer_visage":
                nom = data.get("nom", "").strip()
                res = supprimer_visage(nom)
                await parler(res)
            elif action == "analyser_objet":
                question = data.get("question", "Analyse cet objet")
                await parler("Voyons voir cet objet...")
                res = await vision_analyser_objet(question)
                await parler(res)
            elif action == "navigation_autonome":
                objectif = data.get("objectif", "")
                res = await navigation_autonome(objectif)
                await parler(res)
            elif action == "carte":
                etat = data.get("etat", "on")
                if etat == "on":
                    await send_web_carte(True)
                    await parler("Voici votre position actuelle sur Google Maps au centre de l'écran, Syndou.")
                else:
                    await send_web_carte(False)
                    await parler("Fermeture de la carte.")

            # ── ASSISTANT PERSONNEL ──────────────────────────────────────
            elif action == "ajouter_tache":
                res = ajouter_tache(data.get("tache", ""))
                await parler(res)
            elif action == "lister_taches":
                res = lister_taches()
                await parler(res)
            elif action == "finir_tache":
                res = finir_tache(data.get("index", 0))
                await parler(res)
            elif action == "ajouter_objectif":
                res = ajouter_objectif(data.get("objectif", ""))
                await parler(res)
            elif action == "lister_objectifs":
                res = lister_objectifs()
                await parler(res)
            elif action == "planifier_tache":
                res = planifier_tache(data.get("cron", ""), data.get("commande", ""))
                await parler(res)

            # ── JEUX & HISTOIRES ─────────────────────────────────────────
            elif action == "lancer_jeu":
                res = await lancer_jeu(data.get("jeu", "quiz"))
                await parler(res)
            elif action == "raconter_histoire":
                res = await raconter_histoire(data.get("theme", "aventure"))
                await parler(res)

            # ── MUSIQUE & AUDIO (Directement sur l'interface) ────────────
            elif action == "jouer_musique":
                nom = data.get("nom", "")
                if nom:
                    await parler(f"Très bien Syndou, je lance {nom} sur votre interface.")
                    vid = chercher_youtube_id(nom)
                    if vid and state.CONNECTED_CLIENTS:
                        await send_web_youtube(vid, nom)
                    else:
                        url = chercher_youtube(nom)
                        if url:
                            ouvrir_navigateur(url)
                        else:
                            ouvrir_navigateur(f"https://www.youtube.com/results?search_query={nom.replace(' ', '+')}")
                else:
                    await parler("Quelle musique souhaitez-vous écouter ?")

            elif action == "chanter":
                sujet = data.get("sujet", data.get("nom", "chanson"))
                if "anniversaire" in sujet.lower():
                    await parler("Joyeux anniversaire Syndou ! Je vous joue la chanson directement sur l'interface.")
                    recherche = "Joyeux Anniversaire chanson"
                elif not sujet or sujet.lower() in ["vision", "une chanson joyeuse", "quelque chose", "un truc", "chanson"]:
                    await parler("C'est parti Syndou, je vous joue un bon morceau en direct.")
                    recherche = "chanson française du moment"
                else:
                    await parler(f"C'est parti Syndou, je vous joue {sujet} sur votre interface.")
                    recherche = sujet

                vid = chercher_youtube_id(recherche)
                if vid and state.CONNECTED_CLIENTS:
                    await send_web_youtube(vid, recherche)
                else:
                    url = chercher_youtube(recherche)
                    if url:
                        ouvrir_navigateur(url)
                    else:
                        ouvrir_navigateur(f"https://www.youtube.com/results?search_query={recherche.replace(' ', '+')}")

            elif action == "generer_musique":
                prompt = data.get("prompt", "")
                style = data.get("style", "moderne")
                await parler(f"Je génère une musique {style} pour vous, Syndou. Ça peut prendre une à deux minutes, je vous préviens dès que c'est prêt.")

                # Lancer la génération en tâche de fond avec messages d'avancement
                async def _generer_avec_progression():
                    import time as _time
                    t0 = _time.time()
                    fut = asyncio.get_event_loop().run_in_executor(None, generer_musique, prompt, style)

                    # Messages de patienter toutes les 35 secondes
                    messages_attente = [
                        "La musique est en cours de création... encore un peu de patience.",
                        "Je finalise votre création musicale, presque prêt Syndou !",
                    ]
                    idx = 0
                    while not fut.done():
                        try:
                            await asyncio.wait_for(asyncio.shield(fut), timeout=35)
                            break
                        except asyncio.TimeoutError:
                            if not fut.done() and idx < len(messages_attente):
                                await parler(messages_attente[idx])
                                idx += 1

                    ok, result = await fut
                    elapsed = round(_time.time() - t0)
                    print(f"[AI MUSIC] Génération terminée en {elapsed}s → {str(result)[:80]}")

                    if ok:
                        await parler("C'est prêt ! Je lance votre création musicale sur l'interface.")
                        try:
                            mobile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mobile")
                            os.makedirs(mobile_dir, exist_ok=True)
                            dest_path = os.path.join(mobile_dir, "generated_music.wav")

                            # Si result est un chemin local, on copie. Si c'est une URL, on l'envoie directement.
                            if result.startswith("http"):
                                audio_url = result
                            else:
                                shutil.copy2(result, dest_path)
                                audio_url = f"http://{LOCAL_IP}:8080/generated_music.wav"

                            await send_web_audio(audio_url, f"Musique {style} — {prompt[:30]}")
                        except Exception as e:
                            print(f"[MUSIC WEB ERROR] {e}")
                            ouvrir_navigateur(result)
                    else:
                        await parler(f"Désolé Syndou, la génération a échoué. {result}")

                asyncio.ensure_future(_generer_avec_progression())


            elif action == "recherche_musique_ai":
                query = data.get("query", "")
                await parler(f"Je recherche une musique correspondant à : {query}...")
                result, err = await asyncio.to_thread(rechercher_musique_ai, query)
                if err:
                    await parler(f"Je n'ai pas pu effectuer la recherche. {err}")
                else:
                    res_text = str(result)[:500]
                    await parler(f"Voici ce que j'ai trouvé pour votre recherche : {res_text}")

            # ── WHATSAPP ─────────────────────────────────────────────────
            elif action == "whatsapp_appel":
                await action_whatsapp_appel(data.get("contact", ""))

            # ── DATA SCIENCE ─────────────────────────────────────────────
            elif action == "data_charger":
                chemin = data.get("chemin", "")
                await parler("Chargement des données en cours, Syndou.")
                ok, msg = data_charger(chemin)
                if ok:
                    await parler(f"Données chargées. {msg}")
                else:
                    await parler(f"Je n'ai pas trouvé le fichier '{chemin}'.")
                    # Suggestion de fichiers existants
                    res, _ = lister_dossier()
                    if res and res.get("fichiers"):
                        csv_files = [f for f in res["fichiers"] if f.lower().endswith((".csv", ".xlsx", ".json"))]
                        if csv_files:
                            await parler(f"Dans ce dossier, je vois par exemple : {', '.join(csv_files[:3])}.")
                        else:
                            await parler("Vérifiez le nom ou l'emplacement du fichier.")


            elif action == "data_nettoyer":
                await parler("Je nettoie vos données, Syndou.")
                ok, msg = data_nettoyer()
                await parler(msg if ok else f"Erreur : {msg}")

            elif action == "data_analyser":
                await parler("J'analyse vos données en profondeur, Syndou.")
                ok, msg = data_analyser(data.get("question", ""))
                if ok:
                    await parler(msg)
                    try:
                        interp = await demander_ia(f"Interprète ces statistiques en 2-3 phrases : {msg}")
                        if interp and len(interp) < 600:
                            await parler(f"Mon interprétation : {interp}")
                    except Exception:
                        pass
                else:
                    await parler(f"Erreur analyse : {msg}")

            elif action == "data_visualiser":
                type_viz = data.get("type", "histogramme")
                await parler(f"Je génère un graphique {type_viz}, Syndou.")
                ok, resultat = data_visualiser(type_viz, data.get("col_x"), data.get("col_y"), data.get("titre", ""))
                await parler(f"Graphique {type_viz} généré." if ok else f"Erreur : {resultat}")

            elif action == "data_rapport":
                await parler("Je génère le rapport complet, Syndou.")
                ok, resultat = data_rapport_html()
                await parler("Rapport HTML généré et ouvert." if ok else f"Erreur : {resultat}")

        except Exception as e:
            print(f"[ACTION ERROR] Block failed: {block} | Error: {e}")
            if grok_client:
                res_grok = await demander_grok(f"Syndou m'a demandé : {texte_utilisateur}. J'ai eu une erreur ({e}). Peux-tu répondre ?")
                if res_grok:
                    await parler(res_grok)
            continue

    state._skip_pc_audio = False
