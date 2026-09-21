/**
 * VISION — Contrôle Gestuel Caméra & MediaPipe Hands
 * 
 * Gestes pris en charge :
 * 1. 🤫 Index sur la Bouche (Shh) OU Poing Fermé (Fist) -> Interrompt la parole & coupe l'audio immédiatement.
 * 2. Affichage d'un badge HUD futuriste lors de la détection.
 */

import { Hands, Results, NormalizedLandmarkList } from "@mediapipe/hands";
import { Camera } from "@mediapipe/camera_utils";

let hands: Hands | null = null;
let camera: Camera | null = null;
let videoEl: HTMLVideoElement | null = null;
let isGestureActive = false;
let sendWebSocketMsg: ((data: any) => void) | null = null;
let hudBadgeEl: HTMLDivElement | null = null;

let lastStopTriggerTime = 0;
const DEBOUNCE_MS = 1200;

export function initGestureControl(wsSender: (data: any) => void): void {
  sendWebSocketMsg = wsSender;
  createHUDElement();
}

export async function startGestureControl(): Promise<boolean> {
  if (isGestureActive) return true;

  try {
    // 1. Element vidéo caché pour MediaPipe
    if (!videoEl) {
      videoEl = document.createElement("video");
      videoEl.style.display = "none";
      document.body.appendChild(videoEl);
    }

    // 2. Initialiser MediaPipe Hands
    hands = new Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
    });

    hands.setOptions({
      maxNumHands: 1,
      modelComplexity: 1,
      minDetectionConfidence: 0.65,
      minTrackingConfidence: 0.65,
    });

    hands.onResults(handleHandResults);

    // 3. Demarrer la caméra via CameraUtils
    camera = new Camera(videoEl, {
      onFrame: async () => {
        if (videoEl && hands && isGestureActive) {
          await hands.send({ image: videoEl });
        }
      },
      width: 640,
      height: 480,
    });

    await camera.start();
    isGestureActive = true;
    showHUD("📷 DÉTECTION DE GESTES ACTIVE (INDEX SUR BOUCHE / POING)");
    return true;
  } catch (err) {
    console.error("[GESTURE] Échec initialisation MediaPipe:", err);
    showHUD("❌ ÉCHEC CAMÉRA / GESTES", true);
    return false;
  }
}

export function stopGestureControl(): void {
  isGestureActive = false;
  if (camera) {
    camera.stop();
    camera = null;
  }
  if (hands) {
    hands.close();
    hands = null;
  }
  hideHUD();
}

export function isGestureControlRunning(): boolean {
  return isGestureActive;
}

// ── Analyse des résultats des mains ──────────────────────────────────────────
function handleHandResults(results: Results): void {
  if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
    return;
  }

  const landmarks = results.multiHandLandmarks[0];

  // 1. Tester Geste : Poing Fermé (Fist)
  const isFist = checkClosedFist(landmarks);

  // 2. Tester Geste : Index sur la bouche (Shh gesture)
  const isShhIndex = checkIndexOnMouth(landmarks);

  if (isFist || isShhIndex) {
    const now = Date.now();
    if (now - lastStopTriggerTime > DEBOUNCE_MS) {
      lastStopTriggerTime = now;
      const gestureName = isShhIndex ? "🤫 INDEX SUR LA BOUCHE (SHH)" : "✊ POING FERMÉ (STOP)";
      triggerStopAudio(gestureName);
    }
  }
}

// ── Règle 1 : Poing Fermé (Fist) ─────────────────────────────────────────────
function checkClosedFist(lm: NormalizedLandmarkList): boolean {
  // Les extrémités des 4 doigts principaux (8, 12, 16, 20) doivent être repliées vers le bas (sous les articulations 6, 10, 14, 18)
  const indexFolded = lm[8].y > lm[6].y;
  const middleFolded = lm[12].y > lm[10].y;
  const ringFolded = lm[16].y > lm[14].y;
  const pinkyFolded = lm[20].y > lm[18].y;

  return indexFolded && middleFolded && ringFolded && pinkyFolded;
}

// ── Règle 2 : Index sur la Bouche (Shh) ──────────────────────────────────────
function checkIndexOnMouth(lm: NormalizedLandmarkList): boolean {
  // Index déplié vers le haut (Tip 8 nettement plus haut que joint 6)
  const indexExtended = lm[8].y < lm[6].y;

  // Les autres doigts (Majeur 12, Annulaire 16, Auriculaire 20) sont repliés
  const middleFolded = lm[12].y > lm[10].y;
  const ringFolded = lm[16].y > lm[14].y;
  const pinkyFolded = lm[20].y > lm[18].y;

  // L'index se situe dans la zone centrale supérieure (proche du visage/bouche)
  const indexNearCenter = lm[8].x > 0.3 && lm[8].x < 0.7 && lm[8].y < 0.55;

  return indexExtended && middleFolded && ringFolded && pinkyFolded && indexNearCenter;
}

// ── Action : Interrompre & Mute ──────────────────────────────────────────────
function triggerStopAudio(gestureLabel: string): void {
  console.log(`[GESTURE DETECTED] ${gestureLabel}`);

  // Envoi du signal WS au backend
  if (sendWebSocketMsg) {
    sendWebSocketMsg({ type: "stop_audio" });
  }

  // Animation HUD visuelle
  showHUD(`🛑 ${gestureLabel} : PAROLE INTERROMPUE !`, false, 2500);

  // Animation visuelle de l'UI
  const statusEl = document.getElementById("status-text");
  if (statusEl) {
    statusEl.textContent = "🤫 geste : stop audio";
    setTimeout(() => {
      if (statusEl.textContent === "🤫 geste : stop audio") {
        statusEl.textContent = "";
      }
    }, 2000);
  }
}

// ── HUD Badge Visuel ────────────────────────────────────────────────────────
function createHUDElement(): void {
  if (hudBadgeEl) return;
  hudBadgeEl = document.createElement("div");
  hudBadgeEl.id = "mediapipe-gesture-badge";
  hudBadgeEl.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%) translateY(-100%);
    z-index: 9999;
    padding: 8px 18px;
    border-radius: 20px;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 215, 0, 0.4);
    color: #ffd700;
    font-family: 'Space Grotesk', system-ui, sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 15px rgba(255, 215, 0, 0.2);
    pointer-events: none;
    opacity: 0;
    transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  `;
  document.body.appendChild(hudBadgeEl);
}

let hudHideTimer: ReturnType<typeof setTimeout> | null = null;

function showHUD(text: string, isError = false, autoHideMs = 3000): void {
  if (!hudBadgeEl) createHUDElement();
  if (!hudBadgeEl) return;

  if (hudHideTimer) clearTimeout(hudHideTimer);

  hudBadgeEl.textContent = text;
  hudBadgeEl.style.borderColor = isError ? "rgba(239, 68, 68, 0.6)" : "rgba(255, 215, 0, 0.6)";
  hudBadgeEl.style.color = isError ? "#f87171" : "#ffd700";
  hudBadgeEl.style.opacity = "1";
  hudBadgeEl.style.transform = "translateX(-50%) translateY(0)";

  if (autoHideMs > 0) {
    hudHideTimer = setTimeout(() => hideHUD(), autoHideMs);
  }
}

function hideHUD(): void {
  if (!hudBadgeEl) return;
  hudBadgeEl.style.opacity = "0";
  hudBadgeEl.style.transform = "translateX(-50%) translateY(-100%)";
}

// ── Bouton flottant d'activation des gestes ──────────────────────────────────
export function injectGestureButton(sendWsMsg: (data: any) => void) {
  initGestureControl(sendWsMsg);

  const btn = document.createElement("button");
  btn.id = "gesture-control-button";
  btn.className = "hud-dock-btn";
  btn.title = "Activer le contrôle par gestes (Index sur la bouche 🤫 ou Poing ✊ pour couper l'audio)";
  btn.innerHTML = "<span>🖐️ Gestes</span>";

  btn.onclick = async () => {
    if (isGestureControlRunning()) {
      stopGestureControl();
      btn.innerHTML = "<span>🖐️ Gestes</span>";
      btn.classList.remove("active");
    } else {
      btn.innerHTML = "<span>⏳ Démarrage...</span>";
      const ok = await startGestureControl();
      btn.innerHTML = ok ? "<span>✋ Gestes Actifs</span>" : "<span>❌ Caméra Refusée</span>";
      btn.classList.toggle("active", ok);
    }
  };

  const dock = document.getElementById("bottom-hud-dock");
  if (dock) {
    const webcamBtn = document.getElementById("webcam-button");
    if (webcamBtn && webcamBtn.nextSibling) {
      dock.insertBefore(btn, webcamBtn.nextSibling);
    } else {
      dock.appendChild(btn);
    }
  } else {
    document.body.appendChild(btn);
  }
}
