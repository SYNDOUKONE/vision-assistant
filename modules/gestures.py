"""
VISION — Module de Reconnaissance des Gestes (Webcam / MediaPipe)
Détection 100% locale des gestes de la main via la webcam.
Permet de piloter la musique, les lumières ou les scènes d'un geste.
"""

import time
import threading

_gestes_actifs = False
_gesture_thread = None

def initialiser_mediapipe_mains():
    """Tente d'importer et d'initialiser le détecteur de mains MediaPipe."""
    try:
        import cv2
        import mediapipe as mp
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        return cv2, mp_hands, hands
    except Exception as e:
        print(f"[GESTES] Erreur d'initialisation (OpenCV/MediaPipe requis) : {e}")
        return None, None, None


def _interpreter_geste(landmarks):
    """Interprète les coordonnées des points de la main pour identifier le geste."""
    # Landmarks clés : 4 (pouce bout), 8 (index bout), 12 (majeur bout), 16 (annulaire bout), 20 (auriculaire bout)
    # 0 (poignet), 3 (pouce base), 5 (index base), 9 (majeur base), 13 (annulaire base), 17 (auriculaire base)
    
    doigts = []
    # Index
    doigts.append(landmarks[8].y < landmarks[6].y)
    # Majeur
    doigts.append(landmarks[12].y < landmarks[10].y)
    # Annulaire
    doigts.append(landmarks[16].y < landmarks[14].y)
    # Auriculaire
    doigts.append(landmarks[20].y < landmarks[18].y)

    # Paume ouverte (4 doigts levés) -> PAUSE / MUTE
    if all(doigts):
        return "PAUME_OUVERTE"
    
    # Signe V / Paix (Index + Majeur levés) -> PISTE SUIVANTE
    if doigts[0] and doigts[1] and not doigts[2] and not doigts[3]:
        return "SIGNE_PAIX"
    
    # Pouce levé -> LUMIERE ON
    if landmarks[4].y < landmarks[3].y and not any(doigts):
        return "POUCE_LEVE"
    
    # Poing fermé -> STOP / LUMIERE OFF
    if not any(doigts):
        return "POING_FERME"

    return "INCONNU"

def _boucle_gestes_webcam():
    """Boucle de capture webcam et de traitement des gestes."""
    global _gestes_actifs
    cv2, mp_hands, hands = initialiser_mediapipe_mains()

    if not hands or not cv2:
        print("[GESTES] MediaPipe/OpenCV indisponible. Désactivation des gestes.")
        _gestes_actifs = False
        return


    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[GESTES] Impossible d'ouvrir la webcam.")
        _gestes_actifs = False
        return

    print("[GESTES] Reconnaissance gestuelle activée.")
    dernier_geste = None
    dernier_temps_geste = 0
    COOLDOWN_GESTE = 2.0  # 2 secondes entre chaque action détectée

    from modules.home_assistant import ha_lumiere

    while _gestes_actifs:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        # Inversion miroir + conversion RGB
        frame_rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                geste = _interpreter_geste(hand_landmarks.landmark)
                maintenant = time.time()

                if geste != "INCONNU" and (geste != dernier_geste or maintenant - dernier_temps_geste > COOLDOWN_GESTE):
                    print(f"[GESTES] Geste détecté : {geste}")
                    dernier_geste = geste
                    dernier_temps_geste = maintenant

                    # Exécution des actions associées
                    if geste == "PAUME_OUVERTE":
                        import pyautogui
                        pyautogui.press('space')  # Play/Pause
                    elif geste == "POUCE_LEVE":
                        ha_lumiere("allumer", "salon")
                    elif geste == "POING_FERME":
                        ha_lumiere("eteindre", "salon")
                    elif geste == "SIGNE_PAIX":
                        import pyautogui
                        pyautogui.press('nexttrack')

        time.sleep(0.05)

    cap.release()
    print("[GESTES] Boucle de reconnaissance gestuelle arrêtée.")

def activer_reconnaissance_gestes():
    """Active la détection des gestes par webcam en arrière-plan."""
    global _gestes_actifs, _gesture_thread
    if _gestes_actifs:
        return "La reconnaissance gestuelle est déjà active."
    
    _gestes_actifs = True
    _gesture_thread = threading.Thread(target=_boucle_gestes_webcam, daemon=True)
    _gesture_thread.start()
    return "Reconnaissance gestuelle activée par webcam Syndou."

def desactiver_reconnaissance_gestes():
    """Désactive la détection des gestes."""
    global _gestes_actifs
    _gestes_actifs = False
    return "Reconnaissance gestuelle désactivée."
