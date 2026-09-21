"""
VISION — WebSocket Server
Gestion des clients WebSocket, envoi d'états et de données.
"""

import json
import uuid
import asyncio
from modules import state


async def ws_handler(websocket):
    """Gestionnaire principal des connexions WebSocket."""
    state.CONNECTED_CLIENTS.add(websocket)
    state.interface_deja_connectee = True
    print(f"[WEB] Interface connectee (Clients actifs: {len(state.CONNECTED_CLIENTS)})")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "")

                if msg_type == "mobile_command":
                    texte = data.get("text", "").strip()
                    if texte:
                        print(f"[MOBILE] Commande recue : {texte}")
                        # Import différé pour éviter les imports circulaires
                        from modules.action_handler import traiter_commande_entiere
                        from modules.voice import nettoyer_commande
                        commande_propre = nettoyer_commande(texte)
                        asyncio.ensure_future(traiter_commande_entiere(commande_propre, mobile_ws=websocket))

                elif msg_type == "set_profile":
                    profil = data.get("profile", "vision").lower()
                    if profil in ["vision", "adjoua"]:
                        state.PROFIL_ACTIF = profil
                        print(f"[PROFIL] Profil actif : {profil.upper()}")
                        # Annonce vocale de démarrage selon le profil
                        from modules.voice import parler
                        if profil == "adjoua":
                            asyncio.ensure_future(parler(
                                "Aye ! C'est moi Adjoua ! Je suis là pour mettre l'ambiance et te faire découvrir les meilleurs sons ! "
                                "Dis-moi ce que tu veux écouter ma chérie, je suis prête !"
                            ))
                        else:
                            asyncio.ensure_future(parler("Bonjour, très chère Syndou. VISION est à votre service."))

                elif msg_type == "stop_audio":
                    state.STOP_PARLER = True
                    print("[MOBILE] Signal STOP audio recu")
                    asyncio.ensure_future(stop_web_youtube())

                elif msg_type in ["screen_frame", "webcam_frame"]:
                    req_id = data.get("id")
                    if req_id in state.PENDING_CAPTURES:
                        fut = state.PENDING_CAPTURES.pop(req_id)
                        if "error" in data:
                            fut.set_exception(Exception(data["error"]))
                        else:
                            fut.set_result(data["data"])
                        print(f"[VISION] {data.get('type')} recue et traitee pour ID: {req_id}")
                    else:
                        # On ignore les frames pour des IDs déjà traités ou inconnus
                        pass

                elif msg_type == "get_history_ui":
                    msg = json.dumps({"action": "history_ui", "history": state.history_ui})
                    await websocket.send(msg)

                elif msg_type == "get_faces":
                    from modules.face_recognition_system import get_personnes_with_photos
                    faces = get_personnes_with_photos()
                    await websocket.send(json.dumps({"action": "faces_list", "faces": faces}))

                elif msg_type == "save_face":
                    from modules.face_recognition_system import enregistrer_visage_direct, get_personnes_with_photos
                    nom = data.get("name", "")
                    relation = data.get("relation", "ami")
                    notes = data.get("notes", "")
                    img_b64 = data.get("image_b64", "")
                    res = enregistrer_visage_direct(nom, relation, notes, img_b64)
                    faces = get_personnes_with_photos()
                    # Envoi à tous les clients connectés
                    broadcast_msg = json.dumps({"action": "faces_list", "faces": faces, "notification": res.get("message", "")})
                    await asyncio.gather(*[ws.send(broadcast_msg) for ws in state.CONNECTED_CLIENTS], return_exceptions=True)

                elif msg_type == "delete_face":
                    from modules.face_recognition_system import supprimer_visage, get_personnes_with_photos
                    nom = data.get("name", "")
                    res_msg = supprimer_visage(nom)
                    faces = get_personnes_with_photos()
                    broadcast_msg = json.dumps({"action": "faces_list", "faces": faces, "notification": res_msg})
                    await asyncio.gather(*[ws.send(broadcast_msg) for ws in state.CONNECTED_CLIENTS], return_exceptions=True)

                elif msg_type == "recognize_face_frame":
                    from modules.face_recognition_system import reconnaitre_frame_direct
                    img_b64 = data.get("image_b64", "")
                    result = await reconnaitre_frame_direct(img_b64)
                    await websocket.send(json.dumps({"action": "face_recognized", "result": result}))

            except Exception as e:
                print(f"[WEB] Erreur traitement message : {e}")
    except Exception:
        pass
    finally:
        state.CONNECTED_CLIENTS.discard(websocket)
        print(f"[WEB] Interface deconnectee (Clients actifs: {len(state.CONNECTED_CLIENTS)})")


async def send_web_state(new_state):
    """Envoie un changement d'état à tous les clients."""
    if state.CONNECTED_CLIENTS:
        message = json.dumps({"action": "set_state", "state": new_state})
        await asyncio.gather(
            *[ws.send(message) for ws in state.CONNECTED_CLIENTS],
            return_exceptions=True
        )


async def send_web_volume(volume):
    """Envoie le volume audio pour animer l'orbe."""
    if state.CONNECTED_CLIENTS:
        message = json.dumps({"action": "set_volume", "volume": round(volume, 3)})
        await asyncio.gather(
            *[ws.send(message) for ws in state.CONNECTED_CLIENTS],
            return_exceptions=True
        )


async def send_web_text(user_text, vision_text):
    """Envoie la réponse textuelle de VISION à tous les clients pour affichage."""
    if user_text:
        state.ajouter_histoire_ui("user", user_text)
    if vision_text:
        state.ajouter_histoire_ui("vision", vision_text)
        
    if state.CONNECTED_CLIENTS:
        message = json.dumps({
            "action": "vision_text",
            "user": user_text,
            "text": vision_text,
        })
        await asyncio.gather(
            *[ws.send(message) for ws in state.CONNECTED_CLIENTS],
            return_exceptions=True
        )


async def send_web_carte(show: bool):
    """Affiche ou cache la carte 3D holographique dans le frontend."""
    if state.CONNECTED_CLIENTS:
        message = json.dumps({"action": "show_carte" if show else "hide_carte"})
        await asyncio.gather(
            *[ws.send(message) for ws in state.CONNECTED_CLIENTS],
            return_exceptions=True
        )


async def send_web_youtube(video_id: str, title: str = ""):
    """Envoie une vidéo / musique à jouer directement dans l'interface web (embed)."""
    if state.CONNECTED_CLIENTS:
        message = json.dumps({
            "action": "play_youtube",
            "videoId": video_id,
            "title": title
        })
        await asyncio.gather(
            *[ws.send(message) for ws in state.CONNECTED_CLIENTS],
            return_exceptions=True
        )


async def send_web_radio(action: str = "open_radio", station: str = ""):
    """Ouvre, ferme ou lance une station radio sur le frontend."""
    if state.CONNECTED_CLIENTS:
        message = json.dumps({
            "action": action,
            "station": station
        })
        await asyncio.gather(
            *[ws.send(message) for ws in state.CONNECTED_CLIENTS],
            return_exceptions=True
        )


async def stop_web_youtube():
    """Arrête la lecture de la musique dans l'interface web."""
    if state.CONNECTED_CLIENTS:
        message = json.dumps({"action": "stop_youtube"})
        await asyncio.gather(
            *[ws.send(message) for ws in state.CONNECTED_CLIENTS],
            return_exceptions=True
        )


async def send_web_audio(audio_url: str, title: str = ""):
    """Envoie un fichier audio à jouer directement dans l'interface web."""
    if state.CONNECTED_CLIENTS:
        message = json.dumps({
            "action": "play_audio",
            "url": audio_url,
            "title": title
        })
        await asyncio.gather(
            *[ws.send(message) for ws in state.CONNECTED_CLIENTS],
            return_exceptions=True
        )


async def request_screen_capture():
    """Demande une capture d'écran au frontend via WebSocket."""
    if not state.CONNECTED_CLIENTS:
        return None
    req_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    state.PENDING_CAPTURES[req_id] = fut

    msg = json.dumps({"action": "request_screen_capture", "id": req_id})
    for ws in state.CONNECTED_CLIENTS:
        await ws.send(msg)
    try:
        return await asyncio.wait_for(fut, timeout=5.0)
    except Exception:
        state.PENDING_CAPTURES.pop(req_id, None)
        return None


import base64


def capture_local_webcam_frame_b64():
    """Capture une image via la caméra USB locale du PC (OpenCV) en secours."""
    try:
        import cv2
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[WEBCAM LOCAL] Caméra USB locale du PC introuvable.")
            return None
        
        # Réchauffement capteur
        for _ in range(3):
            ret, frame = cap.read()
            
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            print("[WEBCAM LOCAL] Frame capturée avec succès via la webcam du PC !")
            return base64.b64encode(buffer).decode('utf-8')
        return None
    except Exception as e:
        print(f"[WEBCAM LOCAL ERROR] {e}")
        return None


async def request_webcam_capture():
    """Demande une capture webcam au frontend via WebSocket, ou bascule sur la webcam locale si nécessaire."""
    if state.CONNECTED_CLIENTS:
        req_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        state.PENDING_CAPTURES[req_id] = fut

        msg = json.dumps({"action": "request_webcam_capture", "id": req_id})
        for ws in state.CONNECTED_CLIENTS:
            try:
                await ws.send(msg)
            except Exception:
                pass
        try:
            img_b64 = await asyncio.wait_for(fut, timeout=4.0)
            if img_b64 and img_b64 != "no_webcam":
                return img_b64
        except Exception:
            state.PENDING_CAPTURES.pop(req_id, None)

    # Bascule automatique sur la caméra physique du PC (OpenCV)
    print("[VISION] Bascule sur la webcam locale du serveur PC...")
    return await asyncio.to_thread(capture_local_webcam_frame_b64)
