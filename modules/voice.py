"""
VISION — Synthèse Vocale & Écoute
TTS prioritaire : ElevenLabs (si clé disponible), sinon edge_tts.
"""

import os
import time
import math
import json
import random
import base64
import asyncio

import pygame
import edge_tts

from modules import state
from modules.config import genai_types
from modules.websocket_server import send_web_state, send_web_volume, send_web_text

# ── ElevenLabs TTS ─────────────────────────────────────────────────
_elevenlabs_client = None
ELEVENLABS_VOICE_VISION = "onwK4e9ZLuTAKqWW03F9"  # Daniel — Steady Broadcaster (accent britannique formel, parfait pour JARVIS)
ELEVENLABS_VOICE_ADJOUA = "cgSgspJ2msm6clMCkdW9"  # Jessica — Playful, Bright, Warm (voix féminine chaleureuse)

def get_elevenlabs_client():
    global _elevenlabs_client
    if _elevenlabs_client is not None:
        return _elevenlabs_client

    key = os.getenv("ELEVENLABS_API_KEY", "")
    if not key and os.path.exists("env"):
        from dotenv import load_dotenv
        load_dotenv("env")
        key = os.getenv("ELEVENLABS_API_KEY", "")

    if key:
        try:
            from elevenlabs import ElevenLabs
            _elevenlabs_client = ElevenLabs(api_key=key)
            print("[TTS] ElevenLabs activé — voix HD disponible.")
            return _elevenlabs_client
        except Exception as _e:
            print(f"[TTS] ElevenLabs non disponible : {_e}")
    return None


def parler_elevenlabs(texte: str, output_file: str = "vision_tts.mp3") -> bool:
    """Génère l'audio via ElevenLabs et sauvegarde dans output_file."""
    client = get_elevenlabs_client()
    if not client:
        return False
    try:
        voice_id = ELEVENLABS_VOICE_ADJOUA if state.PROFIL_ACTIF == "adjoua" else ELEVENLABS_VOICE_VISION
        profil_nom = "ADJOUA" if state.PROFIL_ACTIF == "adjoua" else "VISION"
        print(f"[ElevenLabs] Génération vocal HD pour {profil_nom} (voix ID: {voice_id})")
        audio_gen = client.text_to_speech.convert(
            voice_id=voice_id,
            text=texte,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        with open(output_file, "wb") as f:
            for chunk in audio_gen:
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"[ElevenLabs] Erreur TTS : {e}")
        return False


import queue
import threading

speech_queue = queue.Queue()


def init_mixer():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception as e:
        print(f"[MIXER] Echec initialisation mixer pygame: {e}")


def nettoyer_tts_startup():
    """Supprime les restes de fichiers audio TTS lors du démarrage de VISION."""
    for file in os.listdir("."):
        if file.startswith("vision_tts") and file.endswith(".mp3"):
            try:
                os.remove(file)
                print(f"[TTS] Fichier résiduel nettoyé : {file}")
            except Exception:
                pass


def parler_offline_sync(texte, rate_speed=160):
    """Méthode synchrone de secours (TTS Windows pyttsx3) sans internet."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        # Taper sur une voix française
        for voice in voices:
            try:
                if "FR" in voice.id.upper() or "FRENCH" in voice.name.upper() or (hasattr(voice, 'languages') and any("fr" in str(lang).lower() for lang in voice.languages)):
                    engine.setProperty('voice', voice.id)
                    break
            except Exception:
                pass
        engine.setProperty('rate', rate_speed)
        engine.say(texte)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"[OFFLINE TTS] Erreur critique pyttsx3 : {e}")
        return False


def nettoyer_commande(texte):
    t = texte.lower().strip()
    variantes = [
        "hey vision,", "hey vision", "ok vision,", "ok vision",
        "dis vision,", "dis vision", "vision,", "vision", "vision:", "vision :"
    ]
    for variante in variantes:
        if t.startswith(variante):
            t = t[len(variante):].strip()
    t = t.lstrip(",.;:! ")
    return t


def safe_send_web_state(new_state):
    """Envoie de manière asynchrone et thread-safe le statut en ligne de VISION au loop principal."""
    if hasattr(state, "main_loop") and state.main_loop:
        try:
            asyncio.run_coroutine_threadsafe(send_web_state(new_state), state.main_loop)
        except Exception:
            pass


def safe_send_web_volume(volume):
    """Envoie la valeur de l'animation de volume à l'interface de façon thread-safe."""
    if hasattr(state, "main_loop") and state.main_loop:
        try:
            asyncio.run_coroutine_threadsafe(send_web_volume(volume), state.main_loop)
        except Exception:
            pass


def parler_sync_internal(texte_tts, style, skip_pc):
    """Moteur interne synchrone du TTS s'exécutant dans le thread de la queue."""
    tmp = "vision_tts.mp3"
    
    # Voix edge_tts de secours selon le profil actif
    if state.PROFIL_ACTIF == "adjoua":
        voix_edge = "fr-FR-DeniseNeural"
    else:
        voix_edge = "fr-FR-HenriNeural" if style == "doux" else "fr-FR-DeniseNeural"
    
    state.is_speaking = True
    safe_send_web_state("speaking")
    state.speak_volume = 0.0
    utilisé_fallback = False
    
    try:
        # 1. Essayer ElevenLabs en priorité
        if not parler_elevenlabs(texte_tts, tmp):
            # Fallback edge_tts
            async def do_save():
                communicate = edge_tts.Communicate(texte_tts, voice=voix_edge, rate=state.tts_rate)
                await communicate.save(tmp)
                
            loop = asyncio.new_event_loop()
            loop.run_until_complete(do_save())
            loop.close()
        
        # 2. Lecture
        if skip_pc:
            try:
                with open(tmp, "rb") as f:
                    audio_b64 = base64.b64encode(f.read()).decode('utf-8')
                message = json.dumps({"action": "vision_audio", "text": texte_tts, "audio_b64": audio_b64})
                
                if state.main_loop:
                    async def send_to_all():
                        if state.CONNECTED_CLIENTS:
                            await asyncio.gather(
                                *[ws.send(message) for ws in state.CONNECTED_CLIENTS],
                                return_exceptions=True
                            )
                    asyncio.run_coroutine_threadsafe(send_to_all(), state.main_loop)
            except Exception as e:
                print(f"[MOBILE] Erreur envoi: {e}")
        else:
            init_mixer()
            if not pygame.mixer.get_init():
                raise Exception("Mixer pygame indisponible")
            
            pygame.mixer.music.load(tmp)
            pygame.mixer.music.set_volume(state.tts_volume)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                if state.STOP_PARLER:
                    pygame.mixer.music.stop()
                    break
                t_audio = time.time() * 20
                base_vol = 0.4 + 0.3 * math.sin(t_audio) + 0.2 * math.sin(t_audio * 0.5)
                state.speak_volume = max(0.1, min(1.0, (base_vol + random.uniform(-0.1, 0.1)) * state.tts_volume))
                safe_send_web_volume(state.speak_volume)
                time.sleep(0.05)
                
    except Exception as e:
        print(f"[TTS ONLINE FAILED] Erreur TTS : {e}. Fallback vers synthèse locale pyttsx3.")
        utilisé_fallback = True
        parler_offline_sync(texte_tts, state.tts_speed)
    finally:
        state.speak_volume = 0.0
        state.is_speaking = False
        state.STOP_PARLER = False
        
        if not utilisé_fallback:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.unload()
            except Exception:
                pass
        time.sleep(0.1)
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        safe_send_web_state("idle")


def speech_worker():
    """Consomme en continu les ordres de parole de la queue séquentiellement."""
    while True:
        try:
            item = speech_queue.get()
            if item is None:
                break
            texte_tts, style, skip_pc = item
            parler_sync_internal(texte_tts, style, skip_pc)
            speech_queue.task_done()
        except Exception as e:
            print(f"[SPEECH WORKER] Erreur execution : {e}")
            time.sleep(0.1)


# Lancement automatique du thread de parole
threading.Thread(target=speech_worker, daemon=True).start()


async def parler(texte, style="doux"):
    """Ajoute une phrase à la file d'attente de parole (avec gestion d'historique et envoi écran)."""
    # Nettoyage Markdown pour le TTS
    texte_tts = texte.replace("**", "").replace("*", "").replace("#", "").replace("`", "").strip()

    # Enregistrer dans l'historique IA
    if state.historique and len(state.historique) > 0:
        dernier = state.historique[-1].parts[0].text
        if dernier != texte:
            state.ajouter_historique(genai_types.Content(
                role="model",
                parts=[genai_types.Part(text=f"[Information retournée par l'action et énoncée à voix haute]: {texte}")]
            ))

    # ── Envoyer le texte au frontend pour affichage ──
    await send_web_text("", texte_tts)

    # ── Affichage Overlay HUD Flottant ──
    try:
        from modules.overlay import afficher_texte_hud
        afficher_texte_hud(texte_tts)
    except Exception:
        pass

    # Placer la parole dans la queue thread-safe
    speech_queue.put((texte_tts, style, state._skip_pc_audio))

