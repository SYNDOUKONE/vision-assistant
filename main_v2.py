"""
V.I.S.I.O.N — Point d'Entrée Principal
Assistant IA personnel de Syndou.

Architecture modulaire :
  modules/config.py          → Configuration, constantes, clients API
  modules/state.py           → État mutable global
  modules/websocket_server.py → WebSocket (communication frontend)
  modules/voice.py           → Synthèse vocale (TTS) et nettoyage
  modules/ai_brain.py        → Orchestration LLM (Gemini, Grok, Groq, Ollama)
  modules/action_handler.py  → Exécution des commandes JSON
  modules/home_assistant.py  → Domotique Home Assistant
  modules/file_manager.py    → Gestion fichiers/dossiers
  modules/data_science.py    → Analyse de données (pandas, matplotlib)
  modules/google_services.py → Google Docs, Sheets, Gmail, Calendar
  modules/weather_sports.py  → Météo & sport
  modules/music.py           → Spotify & YouTube
  modules/vision_screen.py   → Vision par ordinateur
  modules/web_search.py      → Recherche web (SerpAPI)
  modules/local_solvers.py   → Calculs locaux offline
  modules/memory.py          → Mémoire persistante
"""

import os
import sys
import time
import math
import threading
import asyncio
import subprocess
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

default_print = print
def print(*args, **kwargs):
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        default_print(f"[{ts}]", *args, **kwargs)
    except Exception:
        safe_args = [str(arg).encode('utf-8', errors='replace').decode('utf-8', errors='replace') for arg in args]
        default_print(f"[{ts}]", *safe_args, **kwargs)

import pygame
import pyautogui
import speech_recognition as sr
import websockets

# ── Imports modules VISION ────────────────────────────────────────────────────
from modules import state
from modules.config import (
    LOCAL_IP, CLAP_THRESHOLD, WAKE_WORD, SESSION_TIMEOUT,
    PIECES_LUMIERES,
)
from modules.websocket_server import ws_handler, send_web_state, send_web_text
from modules.voice import parler, nettoyer_commande, nettoyer_tts_startup
from modules.action_handler import traiter_commande_entiere, executer_action_pc
from modules.home_assistant import ha_lumiere, ha_get_etat
from modules.file_manager import ouvrir_navigateur
from modules.memory import enregistrer_resume_session_actuelle


# ══════════════════════════════════════════════════════════════════════════════
# ÉCOUTE VOCALE
# ══════════════════════════════════════════════════════════════════════════════

def ecouter():
    r = sr.Recognizer()
    mic = sr.Microphone()

    r.pause_threshold = 1.2
    r.non_speaking_duration = 0.8
    r.energy_threshold = 400
    r.dynamic_energy_threshold = True

    # Timestamp de fin de parole (pour cooldown anti-écho)
    _fin_parole_time = 0
    COOLDOWN_APRES_PAROLE = 1.5  # secondes d'attente après que VISION finit de parler

    with mic as source:
        print("[VISION] Calibration du bruit ambiant (2s)...")
        r.adjust_for_ambient_noise(source, duration=2)

    print("[VISION] Microphone pret. En attente de 'Vision' uniquement.")

    while True:
        try:
            # Timeout de session
            if state.vision_actif:
                if state.is_speaking or state.is_thinking:
                    state.dernier_message = time.time()
                elif (time.time() - state.dernier_message > SESSION_TIMEOUT):
                    print("[VISION] Timeout session. Retour en veille.")
                    state.vision_actif = False
                    # Enregistrer le résumé de la session en arrière-plan
                    threading.Thread(target=lambda: asyncio.run(enregistrer_resume_session_actuelle()), daemon=True).start()

            # ── ANTI-ÉCHO : bloquer l'écoute si VISION parle ──────────────────
            if state.is_speaking:
                time.sleep(0.1)
                _fin_parole_time = time.time()  # réinitialiser le cooldown
                continue

            # ── COOLDOWN : attendre après que VISION a fini de parler ─────────
            if (time.time() - _fin_parole_time) < COOLDOWN_APRES_PAROLE:
                time.sleep(0.1)
                continue

            with mic as source:
                state.is_listening = True
                loop_ws = asyncio.new_event_loop()
                ws_state = "active" if state.vision_actif else "listening"
                loop_ws.run_until_complete(send_web_state(ws_state))
                loop_ws.close()

                audio = r.listen(source, timeout=2, phrase_time_limit=7)

                state.is_listening = False
                loop_ws = asyncio.new_event_loop()
                loop_ws.run_until_complete(send_web_state("idle"))
                loop_ws.close()

            texte = r.recognize_google(audio, language="fr-FR").lower().strip()
            print(f"[ENTENDU] {texte}")

            # Mots de sommeil
            SLEEP_WORDS = ["merci", "ce sera tout", "repos", "au revoir", "silence", "tais-toi", "tais toi"]
            if any(word in texte for word in SLEEP_WORDS):
                if state.vision_actif:
                    state.vision_actif = False
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(parler("A votre service Syndou. Je me mets en veille."))
                    loop.close()
                    # Enregistrer le résumé de la session en arrière-plan
                    threading.Thread(target=lambda: asyncio.run(enregistrer_resume_session_actuelle()), daemon=True).start()
                continue

            # Détection élargie du mot-clé
            variant_detecte = WAKE_WORD in texte or any(w in texte for w in ["hey vision", "ok vision", "dis vision"])

            if variant_detecte or state.vision_actif:
                if variant_detecte:
                    print("[VISION] Mot-clé détecté.")
                    state.vision_actif = True

                # Indicateur visuel immédiat envoyé au frontend
                loop_ws = asyncio.new_event_loop()
                loop_ws.run_until_complete(send_web_text(texte, "Je vous entends..."))
                loop_ws.close()

                state.dernier_message = time.time()
                commande = nettoyer_commande(texte)

                if commande:
                    action_pc = executer_action_pc(commande)
                    if action_pc:
                        threading.Thread(target=lambda: asyncio.run(parler(action_pc)), daemon=True).start()
                    else:
                        threading.Thread(target=lambda: asyncio.run(traiter_commande_entiere(commande)), daemon=True).start()
                else:
                    if variant_detecte:
                        threading.Thread(target=lambda: asyncio.run(parler("Oui Syndou, je vous écoute.")), daemon=True).start()

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"Erreur écoute : {e}")
            time.sleep(1)


# ══════════════════════════════════════════════════════════════════════════════
# DÉTECTION CLAPS (Mode Iron Man)
# ══════════════════════════════════════════════════════════════════════════════

def monitor_claps():
    p = None
    stream = None
    last_clap_time = 0

    print("[CLAP] Détection des doubles applaudissements prête (en attente du Mode Iron Man).")

    while True:
        try:
            if not state.MODE_IRON_MAN:
                if stream is not None:
                    print("[CLAP] Mode Iron Man désactivé. Fermeture du flux micro claps.")
                    try:
                        stream.stop_stream()
                        stream.close()
                    except Exception:
                        pass
                    stream = None
                if p is not None:
                    try:
                        p.terminate()
                    except Exception:
                        pass
                    p = None
                time.sleep(1)
                continue

            # Initialisation tardive si le mode est activé
            if p is None:
                import pyaudio
                p = pyaudio.PyAudio()
            if stream is None:
                import audioop
                print("[CLAP] Mode Iron Man activé. Ouverture du flux micro claps.")
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,
                                input=True, frames_per_buffer=1024)
                last_clap_time = 0

            import audioop
            try:
                data = stream.read(1024, exception_on_overflow=False)
                rms = audioop.rms(data, 2)
            except Exception:
                time.sleep(0.1)
                continue

            if state.is_speaking or state.is_thinking:
                last_clap_time = 0
                continue

            if rms > CLAP_THRESHOLD:
                current_time = time.time()
                diff = current_time - last_clap_time

                if 0.1 < diff < 0.8:
                    print(f"\n[CLAP] !!! DOUBLE CLAP DÉTECTÉ !!!")
                    entity_id = PIECES_LUMIERES.get("salon", "light.salon")
                    etat_actuel = ha_get_etat(entity_id)

                    if etat_actuel != "on":
                        print("[CLAP] Action : ALLUMER")
                        ha_lumiere(entity_id, "on")
                        if not state.VIDEO_LANCEE:
                            ouvrir_navigateur("https://www.youtube.com/watch?v=KU5V5WZVcVE")
                            state.VIDEO_LANCEE = True
                            def seq():
                                time.sleep(5)
                                pyautogui.press('f')
                            threading.Thread(target=seq, daemon=True).start()
                        else:
                            pyautogui.press('k')
                    else:
                        print("[CLAP] Action : ÉTEINDRE")
                        ha_lumiere(entity_id, "off")
                        if state.VIDEO_LANCEE:
                            pyautogui.press('k')

                    time.sleep(3.0)
                    last_clap_time = 0
                else:
                    last_clap_time = current_time

        except Exception as e:
            print(f"[CLAP ERROR] {e}")
            time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════════
# DÉTECTION MOUVEMENT (Mode Garde)
# ══════════════════════════════════════════════════════════════════════════════

def monitor_garde():
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("[GARDE] OpenCV (cv2) ou numpy non installé. Mode garde désactivé.")
        return

    cap = None
    fgbg = None

    while True:
        try:
            if not state.MODE_GARDE:
                if cap is not None:
                    cap.release()
                    cap = None
                time.sleep(1)
                continue

            if cap is None:
                cap = cv2.VideoCapture(0)
                fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
                print("[GARDE] Caméra activée pour la surveillance continue.")
                # Laisse à la caméra le temps de s'ajuster à la luminosité
                time.sleep(2)

            ret, frame = cap.read()
            if not ret:
                time.sleep(0.5)
                continue

            fgmask = fgbg.apply(frame)

            # Clean up mask
            kernel = np.ones((5, 5), np.uint8)
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
            
            mouvement_pixels = cv2.countNonZero(fgmask)
            
            if mouvement_pixels > 8000:
                print(f"[GARDE] ALERTE: Mouvement détecté! ({mouvement_pixels} pixels modifiés)")
                try:
                    state._skip_pc_audio = False
                    asyncio.run(parler("Alerte Syndou, je détecte un mouvement suspect.", style="dynamique"))
                except Exception:
                    pass
                # Cooldown pour éviter le spam
                time.sleep(10)
            
            time.sleep(0.1)
        except Exception as e:
            print(f"[GARDE ERROR] {e}")
            time.sleep(1.0)


# ══════════════════════════════════════════════════════════════════════════════
# PLANIFICATEUR (Tâches Répétitives)
# ══════════════════════════════════════════════════════════════════════════════

def run_scheduler():
    import json
    from datetime import datetime
    
    schedule_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vision_schedule.json")
    
    while True:
        time.sleep(60) # Vérifie chaque minute
        try:
            if not os.path.exists(schedule_file):
                continue
            with open(schedule_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            scheds = data.get("schedules", [])
            now = datetime.now()
            jour_semaine = now.weekday() # 0 = Lundi, 4 = Vendredi
            heure = now.strftime("%H:%M")
            
            modifie = False
            for s in scheds:
                freq = s.get("frequence", "").lower()
                cmd = s.get("commande", "")
                last_run = s.get("last_run", 0)
                
                # Check simple du jour
                run_now = False
                if "vendredi" in freq and jour_semaine == 4 and "18:00" in freq and heure == "18:00":
                    run_now = True
                
                if time.time() - last_run > 3600 and run_now:
                    print(f"[SCHEDULER] Exécution de la tâche planifiée : {cmd}")
                    asyncio.run(traiter_commande_entiere(cmd))
                    s["last_run"] = time.time()
                    modifie = True
            
            if modifie:
                with open(schedule_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[SCHEDULER ERROR] {e}")


# ══════════════════════════════════════════════════════════════════════════════
# DÉMARRAGE
# ══════════════════════════════════════════════════════════════════════════════

def start_ia():
    threading.Thread(target=monitor_claps, daemon=True).start()
    threading.Thread(target=monitor_garde, daemon=True).start()
    threading.Thread(target=run_scheduler, daemon=True).start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_ws():
        state.main_loop = asyncio.get_running_loop()
        ws_port = 8765
        for port in [8765, 8766, 8767]:
            try:
                server = await websockets.serve(ws_handler, "0.0.0.0", port, extensions=None)
                ws_port = port
                print(f"[WEB] Serveur WebSocket demarre sur ws://0.0.0.0:{port}")
                print(f"[WEB] Accessible depuis le reseau : ws://{LOCAL_IP}:{port}")
                await asyncio.Future()  # tourne indéfiniment
                server.close()
                break
            except OSError:
                print(f"[WEB] Port {port} occupe, tentative sur {port+1}...")

    threading.Thread(target=lambda: asyncio.run(start_ws()), daemon=True).start()

    loop.run_until_complete(parler("Bonjour, très chère Syndou."))
    loop.close()
    ecouter()


def start_mobile_http_server():
    """Serveur HTTP minimal pour servir l'interface mobile. Essaie plusieurs ports."""
    import http.server
    mobile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobile")
    if not os.path.exists(mobile_dir):
        print("[MOBILE] Dossier mobile/ introuvable, serveur non demarre.")
        return

    class MobileHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=mobile_dir, **kwargs)
        def log_message(self, format, *args):
            pass

    ports_a_essayer = [8080, 8081, 8082, 8083, 8090]
    for port in ports_a_essayer:
        try:
            server = http.server.HTTPServer(("0.0.0.0", port), MobileHandler)
            print(f"[MOBILE] Serveur HTTP demarre sur http://{LOCAL_IP}:{port}")
            server.serve_forever()
            return
        except (PermissionError, OSError):
            print(f"[MOBILE] Port {port} bloque, essai du suivant...")
        except Exception as e:
            print(f"[MOBILE] Serveur erreur sur port {port}: {e}")
    print("[MOBILE] Aucun port disponible pour le serveur mobile (8080-8090). Acces mobile desactive.")


def main():
    print("=" * 60)
    print("   V.I.S.I.O.N — Mode Console + Interface Web")
    print("   Architecture Modulaire v2.0")
    print("=" * 60)
    print(f"  Backend   : actif")
    print(f"  IP locale : {LOCAL_IP}")
    print(f"  WebSocket : ws://localhost:8765")
    print(f"  Frontend  : http://localhost:5173")
    print(f"  Mobile    : http://{LOCAL_IP}:8080")
    print("=" * 60)

    # ── 1. Init audio ──────────────────────────────────────────────
    print("[INIT] Nettoyage fichiers TTS residuels...")
    nettoyer_tts_startup()

    print("[INIT] Initialisation PyGame audio...")
    pygame.init()
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        print("[INIT] Mixer audio OK.")
    except Exception as e:
        print(f"[INIT] Mixer audio ECHEC : {e}")

    # ── 2. Serveur Frontend (non bloquant) ─────────────────────────
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    frontend_process = None
    if os.path.exists(frontend_dir):
        print("[INIT] Lancement Vite (frontend)...")
        frontend_process = subprocess.Popen(
            "npm run dev",
            cwd=frontend_dir,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Petit délai minimal pour que Vite annonce son port
        time.sleep(1.5)
        print("[INIT] Vite demarre en arriere-plan.")

    # ── 3. Ouvrir navigateur ───────────────────────────────────────
    try:
        ouvrir_navigateur("http://localhost:5173")
    except Exception:
        pass

    # ── 4. Serveur Mobile ──────────────────────────────────────────
    print("[INIT] Lancement serveur HTTP mobile...")
    threading.Thread(target=start_mobile_http_server, daemon=True).start()

    # ── 5. Backend IA (bloque ici — boucle vocale infinie) ─────────
    print("[INIT] Demarrage du moteur IA...")
    try:
        start_ia()  # bloquant : la boucle vocale tourne ici
    except KeyboardInterrupt:
        print("\n[VISION] Arret manuel demande.")
    finally:
        if frontend_process:
            print("[VISION] Arret du serveur Web...")
            try:
                if os.name == 'nt':
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                else:
                    frontend_process.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    main()
