/**
 * V.I.S.I.O.N — Interface Mobile
 *
 * Se connecte au backend Python via WebSocket dynamiquement (même IP que le serveur HTTP).
 * Utilise Web Speech API pour STT (voix → texte) et SpeechSynthesis pour TTS (texte → voix).
 *
 * États: "idle" | "listening" | "thinking" | "speaking"
 */

// ── Config ─────────────────────────────────────────────────────────────────
const WS_URL = `ws://${window.location.hostname}:8765`;
const RECONNECT_DELAY_MS = 2500;
const SPEECH_LANG = "fr-FR";

// ── DOM Refs ────────────────────────────────────────────────────────────────
const badgeEl      = document.getElementById("connection-badge");
const badgeLabelEl = document.getElementById("connection-label");
const statusEl     = document.getElementById("status-text");
const userTextEl   = document.getElementById("user-text");
const jarvisTextEl = document.getElementById("jarvis-text");
const micBtn       = document.getElementById("mic-btn");
const micIcon      = micBtn.querySelector(".mic-icon");
const stopIcon     = micBtn.querySelector(".stop-icon");
const micLabelEl   = document.getElementById("mic-label");
const stopJarvisBtn= document.getElementById("stop-jarvis-btn");

// ── ORB 3D ──────────────────────────────────────────────────────────────────
let orb = null;
if (typeof createOrb === "function") {
  const canvas = document.getElementById("orb-canvas");
  if (canvas) {
    orb = createOrb(canvas);
  }
}



// ── HTTPS Warning ───────────────────────────────────────────────────────────
if (window.location.protocol !== "https:" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
  const warning = document.getElementById("https-warning");
  if (warning) {
    warning.style.display = "block";
    const closeBtn = document.getElementById("close-warning-btn");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        warning.style.display = "none";
      });
    }
  }
}

// ── État de l'application ───────────────────────────────────────────────────
let currentState = "idle";
let ws           = null;
let isListening  = false;
let reconnectTimer = null;

// ── Gestion des états ───────────────────────────────────────────────────────
const STATE_LABELS = {
  idle:      "en attente",
  listening: "je vous écoute...",
  thinking:  "en réflexion...",
  speaking:  "vision répond...",
};

function applyState(state) {
  // Retirer l'ancien état du body
  document.body.classList.remove(
    "state-idle", "state-listening", "state-thinking", "state-speaking"
  );
  document.body.classList.add(`state-${state}`);
  currentState = state;
  statusEl.textContent = STATE_LABELS[state] || state;

  // Affichage du bouton Stop global seulement si ca parle
  if (state === "speaking") {
    stopJarvisBtn.style.display = "flex";
  } else {
    stopJarvisBtn.style.display = "none";
  }

  // Icône microphone
  if (state === "listening") {
    micIcon.style.display = "none";
    stopIcon.style.display = "block";
    micLabelEl.textContent = "APPUYER POUR ARRÊTER";
  } else {
    micIcon.style.display = "block";
    stopIcon.style.display = "none";
    micLabelEl.textContent = "APPUYER POUR PARLER";
  }

  // Mettre à jour l'état de l'orbe 3D
  if (orb) {
    orb.setState(state);
  }
}

applyState("idle");

let currentAudio = null;
let fakeVolumeInterval = null;

// Écouteur pour le bouton stop VISION
stopJarvisBtn.addEventListener("click", () => {
  window.speechSynthesis.cancel(); // Stoppe l'audio mobile (fallback)
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "stop_audio" })); // Stoppe l'audio PC
  }
  applyState("idle");
});

// ── Badge de connexion ──────────────────────────────────────────────────────
function setConnected(ok) {
  badgeEl.classList.toggle("connected", ok);
  badgeEl.classList.toggle("disconnected", !ok);
  badgeLabelEl.textContent = ok ? "connecté" : "reconnexion...";
}
setConnected(false);

// ── WebSocket ───────────────────────────────────────────────────────────────
function connectWS() {
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }

  ws = new WebSocket(WS_URL);

  ws.addEventListener("open", () => {
    console.log("[WS] Connecté à", WS_URL);
    setConnected(true);
  });

  ws.addEventListener("message", async (event) => {
    try {
      const data = JSON.parse(event.data);

      // État de l'orbe (envoyé par le backend lors de ses propres actions)
      if (data.action === "set_state" && data.state) {
        if (data.state === "listening" || data.state === "active") return;
        if (data.state === "idle" && isListening) return;
        if (data.state !== "speaking") {
          applyState(data.state);
        }
      }

      // Capture Webcam Mobile
      if (data.action === "request_webcam_capture") {
        const frame = await captureWebcamFrame();
        if (frame && ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "webcam_frame", id: data.id, data: frame }));
        } else if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "webcam_frame", id: data.id, error: "no_webcam" }));
        }
        return;
      }

      // Réponse textuelle de VISION
      if (data.action === "vision_audio" && data.audio_b64) {
        afficherReponseVision(data.text);
        jouerAudioBase64(data.audio_b64);
      }
      else if (data.action === "vision_response" && data.text) {
        afficherReponseVision(data.text);
        parleSynthese(data.text);
      }
    } catch (e) {
      console.error("[WS] Erreur parsing message :", e);
    }
  });

// ── Gestion Webcam Mobile ───────────────────────────────────────────────────
const visionBtn = document.getElementById("vision-btn");
let webcamStream = null;

async function enableWebcam() {
  if (webcamStream) return true;
  try {
    webcamStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false
    });
    visionBtn.classList.add("active");
    return true;
  } catch (e) {
    console.error("[WEBCAM] Refusée:", e);
    return false;
  }
}

async function captureWebcamFrame() {
  if (!webcamStream) {
    const ok = await enableWebcam();
    if (!ok) return null;
  }
  
  const video = document.createElement("video");
  video.srcObject = webcamStream;
  await video.play();
  
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0);
  
  const frame = canvas.toDataURL("image/jpeg", 0.7).split(",")[1];
  video.pause();
  return frame;
}

visionBtn.addEventListener("click", async () => {
  const ok = await enableWebcam();
  if (ok) {
     visionBtn.style.color = "#2ecc71";
  } else {
     visionBtn.style.color = "#e74c3c";
  }
});


  ws.addEventListener("close", () => {
    console.log("[WS] Déconnecté. Reconnexion dans", RECONNECT_DELAY_MS, "ms...");
    setConnected(false);
    applyState("idle");
    scheduleReconnect();
  });

  ws.addEventListener("error", () => {
    setConnected(false);
  });
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWS();
  }, RECONNECT_DELAY_MS);
}

function sendCommand(text) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.warn("[WS] WebSocket non connecté, commande ignorée.");
    return false;
  }
  ws.send(JSON.stringify({ type: "mobile_command", text }));
  return true;
}

// ── Affichage dialogue ──────────────────────────────────────────────────────
function afficherTexteUtilisateur(text) {
  userTextEl.textContent = `"${text}"`;
  jarvisTextEl.textContent = "";
}

function afficherReponseVision(text) {
  // Nettoyer les éventuels blocs JSON de la réponse pour l'affichage
  const textePropre = text
    .replace(/\{[^}]*\}/gs, "")        // supprimer blocs JSON
    .replace(/\s{2,}/g, " ")           // normaliser espaces
    .trim();
  jarvisTextEl.textContent = textePropre || text;
}

function jouerAudioBase64(base64) {
  if (currentAudio) {
    currentAudio.pause();
  }
  window.speechSynthesis.cancel();
  
  applyState("speaking");
  
  currentAudio = new Audio("data:audio/mp3;base64," + base64);
  currentAudio.play().catch(e => console.error("[AUDIO] Erreur lecture :", e));
  
  // Fake volume for ORB
  if (fakeVolumeInterval) clearInterval(fakeVolumeInterval);
  fakeVolumeInterval = setInterval(() => {
    if (orb) {
      const t = Date.now() / 50;
      const vol = 0.4 + 0.3 * Math.sin(t) + 0.2 * Math.sin(t * 0.5);
      orb.setVolume(Math.max(0.1, Math.min(1.0, vol + (Math.random() * 0.2 - 0.1))));
    }
  }, 50);

  currentAudio.addEventListener("ended", () => {
    applyState("idle");
    if (fakeVolumeInterval) {
      clearInterval(fakeVolumeInterval);
      fakeVolumeInterval = null;
    }
    if (orb) orb.setVolume(0);
    currentAudio = null;
  });
  
  currentAudio.addEventListener("pause", () => {
    if (currentState === "speaking") {
      applyState("idle");
    }
    if (fakeVolumeInterval) {
      clearInterval(fakeVolumeInterval);
      fakeVolumeInterval = null;
    }
    if (orb) orb.setVolume(0);
  });
}

// ── TTS Web (Speech Synthesis) ──────────────────────────────────────────────
let synthVoice = null;

function chargerVoix() {
  const voices = window.speechSynthesis.getVoices();
  // Chercher une voix française de bonne qualité
  synthVoice =
    voices.find(v => v.lang === "fr-FR" && v.name.includes("Google")) ||
    voices.find(v => v.lang === "fr-FR") ||
    voices.find(v => v.lang.startsWith("fr")) ||
    null;
  console.log("[TTS] Voix sélectionnée :", synthVoice?.name || "par défaut");
}

window.speechSynthesis.addEventListener("voiceschanged", chargerVoix);
chargerVoix();

function parleSynthese(texte) {
  // Annuler toute synthèse en cours
  window.speechSynthesis.cancel();

  // Nettoyer le texte (enlever JSON pour ne lire que la partie conversationnelle)
  const textePropre = texte
    .replace(/\{[^}]*\}/gs, "")
    .replace(/\s{2,}/g, " ")
    .trim();

  if (!textePropre) return;

  applyState("speaking");

  const utterance = new SpeechSynthesisUtterance(textePropre);
  utterance.lang = SPEECH_LANG;
  utterance.rate = 0.95;
  utterance.pitch = 0.9;
  utterance.volume = 1.0;

  if (synthVoice) {
    utterance.voice = synthVoice;
  }

  utterance.addEventListener("end", () => {
    applyState("idle");
  });

  utterance.addEventListener("error", (e) => {
    console.warn("[TTS] Erreur synthèse :", e.error);
    applyState("idle");
  });

  window.speechSynthesis.speak(utterance);
}

// ── STT Web Speech API ──────────────────────────────────────────────────────
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

let recognition = null;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang           = SPEECH_LANG;
  recognition.continuous     = false;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  recognition.addEventListener("start", () => {
    isListening = true;
    applyState("listening");
    userTextEl.textContent  = "";
    jarvisTextEl.textContent = "";
    console.log("[STT] Écoute démarrée.");
  });

  recognition.addEventListener("result", (event) => {
    let interim   = "";
    let final_txt = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        final_txt += transcript;
      } else {
        interim += transcript;
      }
    }

    // Affichage en temps réel des résultats intermédiaires
    userTextEl.textContent = `"${final_txt || interim}"`;

    if (final_txt) {
      console.log("[STT] Résultat final :", final_txt);
    }
  });

  recognition.addEventListener("end", () => {
    isListening = false;
    const texteCapture = userTextEl.textContent.replace(/^"|"$/g, "").trim();
    console.log("[STT] Fin écoute. Texte :", texteCapture);

    if (texteCapture) {
      applyState("thinking");
      const envoyé = sendCommand(texteCapture);
      if (!envoyé) {
        applyState("idle");
        userTextEl.textContent = "⚠ Non connecté à VISION";
      }
    } else {
      applyState("idle");
    }
  });

  recognition.addEventListener("error", (event) => {
    console.warn("[STT] Erreur :", event.error);
    isListening = false;
    applyState("idle");

    if (event.error === "not-allowed") {
      userTextEl.textContent =
        "⚠ Micro non autorisé. Activez le dans chrome://flags";
    } else if (event.error === "no-speech") {
      userTextEl.textContent = "";
    } else {
      userTextEl.textContent = `⚠ Erreur micro : ${event.error}`;
    }
  });

} else {
  // SpeechRecognition non supporté
  micBtn.disabled = true;
  statusEl.textContent = "micro non supporté sur ce navigateur";
  console.error("[STT] SpeechRecognition non disponible.");
}

// ── Audio Context Unlock (pour mobile) ──────────────────────────────────────
function unlockAudio() {
  const audio = new Audio();
  audio.play().then(() => audio.pause()).catch(() => {});
  // On peut aussi déclencher une synthèse silencieuse
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance("");
  window.speechSynthesis.speak(u);
}

// ── Bouton microphone ───────────────────────────────────────────────────────
micBtn.addEventListener("click", () => {
  if (!recognition) return;

  // Débloquer l'audio au premier clic pour les navigateurs mobiles
  unlockAudio();

  // Bloquer si VISION pense ou parle
  if (currentState === "thinking" || currentState === "speaking") return;

  if (isListening) {
    // Arrêter l'écoute
    recognition.stop();
  } else {
    // Annuler TTS en cours si nécessaire
    window.speechSynthesis.cancel();
    try {
      recognition.start();
    } catch (e) {
      console.warn("[STT] Impossible de démarrer :", e);
    }
  }
});

// ── Démarrage ───────────────────────────────────────────────────────────────
connectWS();
console.log("[VISION MOBILE] Interface initialisée. WebSocket :", WS_URL);
