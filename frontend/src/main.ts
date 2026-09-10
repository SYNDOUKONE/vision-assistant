/**
 * VISION — Interface Web avec Orbe Three.js
 *
 * Se connecte au backend Python via WebSocket (ws://localhost:8765),
 * recoit les changements d'etat et pilote l'orbe en consequence.
 *
 * Etats: "idle" | "listening" | "thinking" | "speaking"
 */

import { createOrb, type OrbState, type OrbPalette, PALETTE_VISION, PALETTE_ADJOUA } from "./orb";
import { injectVisionButton, captureFrame } from "./screen_capture";
import { injectWebcamButton, captureWebcamFrame } from "./webcam";
import { injectGestureButton } from "./gesture_control";
import { showCarte, hideCarte } from "./carte3d";
import { initWallpaperSystem } from "./wallpaper";
import { vision3D } from "./vision3d_interactions";
import "./style.css";

// ── Config ────────────────────────────────────────────────────────────────────
const WS_URL = `ws://${window.location.hostname}:8765`;
const RECONNECT_INTERVAL_MS = 2_000;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const canvas = document.getElementById("orb-canvas") as HTMLCanvasElement;
const statusEl = document.getElementById("status-text") as HTMLDivElement;
const errorEl = document.getElementById("error-text") as HTMLDivElement;
const badgeEl = document.getElementById("connection-badge") as HTMLDivElement;
const badgeLabelEl = document.getElementById(
  "connection-label"
) as HTMLSpanElement;
const muteButtonEl = document.getElementById("mute-button") as HTMLButtonElement;
const textToggleBtnEl = document.getElementById("text-toggle-button") as HTMLButtonElement;
const textPanelEl = document.getElementById("text-panel") as HTMLDivElement;
const textInputEl = document.getElementById("text-input") as HTMLTextAreaElement;
const textSendBtnEl = document.getElementById("text-send-button") as HTMLButtonElement;
const responsePanelEl = document.getElementById("response-panel") as HTMLDivElement;
const responseUserEl = document.getElementById("response-user") as HTMLDivElement;
const responseTextEl = document.getElementById("response-text") as HTMLDivElement;

// ── Music player DOM refs ───────────────────────────────────────────────────
const musicPlayerHudEl = document.getElementById("music-player-hud") as HTMLDivElement;
const musicIframeEl = document.getElementById("music-iframe") as HTMLIFrameElement;
const musicTrackTitleEl = document.getElementById("music-track-title") as HTMLDivElement;
const musicCollapseBtnEl = document.getElementById("music-collapse-btn") as HTMLButtonElement;
const musicCloseBtnEl = document.getElementById("music-close-btn") as HTMLButtonElement;

// ── Orb — created after profile selection ───────────────────────────────
let orb: ReturnType<typeof createOrb> | null = null;

// ── Active profile ────────────────────────────────────────────────────────
let activeProfile: "vision" | "adjoua" = "vision";

// ── State labels (French) ────────────────────────────────────────────────────
const STATE_LABELS: Record<OrbState, string> = {
  idle: "",
  listening: "ecoute...",
  thinking: "reflexion...",
  speaking: "",
};

function applyState(state: OrbState): void {
  if (orb) orb.setState(state);
  statusEl.textContent = STATE_LABELS[state];
}

function setMuted(muted: boolean): void {
  muteButtonEl.classList.toggle("is-muted", muted);
  muteButtonEl.setAttribute("aria-pressed", String(muted));
  muteButtonEl.textContent = muted ? "unmute" : "mute";
}

// ── Error toast ───────────────────────────────────────────────────────────────
let errorTimer: ReturnType<typeof setTimeout> | null = null;

function showError(msg: string): void {
  errorEl.textContent = msg;
  errorEl.style.opacity = "1";
  if (errorTimer) clearTimeout(errorTimer);
  errorTimer = setTimeout(() => {
    errorEl.style.opacity = "0";
  }, 4_000);
}

// ── Response panel (VISION text display) ─────────────────────────────────────
let responseHideTimer: ReturnType<typeof setTimeout> | null = null;

function showResponse(userText: string, visionText: string): void {
  // Clear auto-hide timer
  if (responseHideTimer) {
    clearTimeout(responseHideTimer);
    responseHideTimer = null;
  }

  // Update user message if provided
  if (userText) {
    responseUserEl.textContent = `syndou : ${userText}`;
  }

  // Show the panel only when there's vision text
  if (visionText) {
    responseTextEl.textContent = visionText;
    responseTextEl.classList.remove("typing");
    responsePanelEl.classList.remove("response-hidden");
    responsePanelEl.classList.add("response-visible");

    // Auto-hide after 15 seconds
    responseHideTimer = setTimeout(() => {
      responsePanelEl.classList.remove("response-visible");
      responsePanelEl.classList.add("response-hidden");
    }, 15_000);
  } else if (userText) {
    // User message received, show typing state
    responseTextEl.textContent = "";
    responseTextEl.classList.add("typing");
    responsePanelEl.classList.remove("response-hidden");
    responsePanelEl.classList.add("response-visible");
  }
}

// ── Embedded Music Player Logic ──────────────────────────────────────────────
function playEmbeddedMusic(videoId: string, title?: string): void {
  if (!musicPlayerHudEl) return;
  if (title && musicTrackTitleEl) {
    musicTrackTitleEl.textContent = title;
  }

  const body = document.getElementById("music-player-body");
  if (body) {
    body.innerHTML = "";

    const iframe = document.createElement("iframe");
    iframe.id = "music-iframe";
    iframe.title = "VISION Music Player";
    iframe.allow = "autoplay; encrypted-media; picture-in-picture";
    iframe.allowFullscreen = true;
    iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&enablejsapi=1`;
    iframe.style.cssText = "width: 100%; height: 100%; border: none; display: block;";

    // Bouton secours si YouTube restreint l'intégration dans l'iframe
    const fallbackLink = document.createElement("a");
    fallbackLink.href = `https://www.youtube.com/watch?v=${videoId}`;
    fallbackLink.target = "_blank";
    fallbackLink.rel = "noopener noreferrer";
    fallbackLink.textContent = "↗ Ouvrir sur YouTube";
    fallbackLink.style.cssText = `
      position: absolute;
      bottom: 8px;
      right: 8px;
      background: rgba(0,0,0,0.75);
      color: #ff4444;
      font-size: 10px;
      padding: 4px 8px;
      border-radius: 4px;
      text-decoration: none;
      border: 1px solid rgba(255,68,68,0.4);
      z-index: 10;
    `;

    body.appendChild(iframe);
    body.appendChild(fallbackLink);
  }

  musicPlayerHudEl.classList.remove("music-player-hidden");
  musicPlayerHudEl.classList.remove("music-player-minimized");
}

function playEmbeddedAudio(url: string, title?: string): void {
  if (!musicPlayerHudEl) return;
  if (title && musicTrackTitleEl) {
    musicTrackTitleEl.textContent = title;
  }

  const body = document.getElementById("music-player-body");
  if (body) {
    body.innerHTML = "";
    const audio = document.createElement("audio");
    audio.src = url;
    audio.autoplay = true;
    audio.controls = true;
    audio.style.cssText = "width: 90%; margin: 30px auto; display: block; outline: none;";
    body.appendChild(audio);
  }

  musicPlayerHudEl.classList.remove("music-player-hidden");
  musicPlayerHudEl.classList.remove("music-player-minimized");
}

function stopEmbeddedMusic(): void {
  if (!musicPlayerHudEl) return;
  const body = document.getElementById("music-player-body");
  if (body) body.innerHTML = "";
  musicPlayerHudEl.classList.add("music-player-hidden");
}

if (musicCloseBtnEl) {
  musicCloseBtnEl.addEventListener("click", stopEmbeddedMusic);
}

if (musicCollapseBtnEl) {
  musicCollapseBtnEl.addEventListener("click", () => {
    if (musicPlayerHudEl) {
      musicPlayerHudEl.classList.toggle("music-player-minimized");
    }
  });
}

// ── Connection badge ──────────────────────────────────────────────────────────
function setConnected(ok: boolean): void {
  badgeEl.classList.toggle("connected", ok);
  badgeEl.classList.toggle("disconnected", !ok);
  badgeLabelEl.textContent = ok ? "connecte" : "reconnexion";
  muteButtonEl.disabled = !ok;
}

// ── WebSocket with auto-reconnect ─────────────────────────────────────────────
let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

function connect(): void {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  ws = new WebSocket(WS_URL);
  (window as any).ws = ws;

  ws.addEventListener("open", () => {
    setConnected(true);
  });

  ws.addEventListener("message", async (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data as string) as {
        state?: string;
        action?: string;
        muted?: boolean;
        volume?: number;
        id?: string;
      };

      if (data.action === "request_screen_capture") {
        const frame = await captureFrame();
        if (frame && ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: "screen_frame",
            id: data.id,
            data: frame,
          }));
        } else if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: "screen_frame",
            id: data.id,
            error: "no_stream",
          }));
        }
        return;
      }

      if (data.action === "request_webcam_capture") {
        const frame = await captureWebcamFrame();
        if (frame && ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: "webcam_frame",
            id: data.id,
            data: frame,
          }));
        } else if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: "webcam_frame",
            id: data.id,
            error: "no_webcam",
          }));
        }
        return;
      }

      if (data.action === "show_carte") {
        showCarte();
        return;
      }
      if (data.action === "hide_carte") {
        hideCarte();
        return;
      }
      if (data.action === "play_youtube") {
        const vid = (data as any).videoId;
        const title = (data as any).title;
        if (vid) {
          playEmbeddedMusic(vid, title);
        }
        return;
      }
      if (data.action === "stop_youtube") {
        stopEmbeddedMusic();
        return;
      }
      if (data.action === "play_audio") {
        const url = (data as any).url;
        const title = (data as any).title;
        if (url) {
          playEmbeddedAudio(url, title);
        }
        return;
      }
      if (data.action === "demo") {
        if (orb) orb.triggerDemo();
        return;
      }
      if (data.action === "set_volume" && typeof data.volume === "number") {
        if (orb) orb.setVolume(data.volume);
        return;
      }
      if (data.action === "vision_text") {
        showResponse(
          (data as any).user || "",
          (data as any).text || ""
        );
        return;
      }
      if (data.action === "show_orbe_magnetique") {
        vision3D.showModule("orbe_magnetique");
        return;
      }
      if (data.action === "show_globe3d") {
        vision3D.showModule("globe3d");
        return;
      }
      if (data.action === "show_hud_menu") {
        vision3D.showModule("hud_menu");
        return;
      }
      if (data.action === "show_data_cube") {
        vision3D.showModule("data_cube");
        return;
      }
      if (data.action === "hide_vision3d") {
        vision3D.hideCurrentModule();
        return;
      }
      if (data.action === "history_ui") {
        const listEl = document.getElementById("history-list");
        if (listEl) {
          listEl.innerHTML = "";
          const history = (data as any).history || [];
          for (const item of history) {
            const div = document.createElement("div");
            div.className = item.role === "vision" ? "history-item-vision" : "history-item-user";
            div.textContent = (item.role === "vision" ? "VISION : " : "Vous : ") + item.text;
            listEl.appendChild(div);
          }
          listEl.scrollTop = listEl.scrollHeight;
        }
        return;
      }
      if (data.state) {
        applyState(data.state as OrbState);
      }
      if (typeof data.volume === "number") {
        if (orb) orb.setVolume(data.volume);
      }
      if (typeof data.muted === "boolean") {
        setMuted(data.muted);
      }
    } catch {
      // ignore malformed messages
    }
  });

  ws.addEventListener("close", () => {
    setConnected(false);
    applyState("idle");
    scheduleReconnect();
  });

  ws.addEventListener("error", () => {
    setConnected(false);
  });
}

function scheduleReconnect(): void {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, RECONNECT_INTERVAL_MS);
}

// ── Events ──────────────────────────────────────────────────────────────────
muteButtonEl.addEventListener("click", () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;

  // Envoi du signal stop au backend
  ws.send(JSON.stringify({ type: "stop_audio" }));

  // Feedback immédiat sur l'orbe
  applyState("idle");
});

// ── Text panel logic ─────────────────────────────────────────────────────────
let textPanelOpen = false;

function toggleTextPanel(): void {
  textPanelOpen = !textPanelOpen;
  textPanelEl.classList.toggle("text-panel-visible", textPanelOpen);
  textPanelEl.classList.toggle("text-panel-hidden", !textPanelOpen);
  textToggleBtnEl.classList.toggle("is-open", textPanelOpen);
  if (textPanelOpen) {
    // Petit délai pour que l'animation soit visible avant le focus
    setTimeout(() => textInputEl.focus(), 60);
  }
}

function sendTextPrompt(): void {
  const text = textInputEl.value.trim();
  if (!text) return;
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showError("Non connecté au backend");
    return;
  }
  ws.send(JSON.stringify({ type: "mobile_command", text }));
  textInputEl.value = "";
  autoResizeTextarea();
  // Feedback visuel : l'orbe passe en "thinking"
  applyState("thinking");
  // Fermer le panneau après envoi
  toggleTextPanel();
}

function autoResizeTextarea(): void {
  textInputEl.style.height = "auto";
  textInputEl.style.height = Math.min(textInputEl.scrollHeight, 140) + "px";
}

textToggleBtnEl.addEventListener("click", toggleTextPanel);

textSendBtnEl.addEventListener("click", sendTextPrompt);

textInputEl.addEventListener("input", autoResizeTextarea);

textInputEl.addEventListener("keydown", (e: KeyboardEvent) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendTextPrompt();
  }
});

// ── Boot ──────────────────────────────────────────────────────────────────────
setConnected(false);
applyState("idle");
setMuted(false);
injectVisionButton();
injectWebcamButton();
injectGestureButton((data) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
});
initWallpaperSystem();
vision3D.init((data: any) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
});

// Listen for profile selection (from the profile screen HTML/JS)
window.addEventListener("profileSelected", (e: Event) => {
  const evt = e as CustomEvent<{ profile: string }>;
  activeProfile = evt.detail.profile as "vision" | "adjoua";

  // Create the orb with the right palette
  const palette: OrbPalette = activeProfile === "adjoua" ? PALETTE_ADJOUA : PALETTE_VISION;
  if (orb) orb.destroy();
  orb = createOrb(canvas, palette);

  // Update assistant label
  const label = document.getElementById("assistant-label");
  if (label) label.textContent = activeProfile === "adjoua" ? "ADJOUA" : "VISION";

  // Start WebSocket (connect to backend)
  connect();

  // Notify backend of profile choice once connected
  setTimeout(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "set_profile", profile: activeProfile }));
    }
  }, 800);
});

// Escape ferme la carte
window.addEventListener("keydown", (e: KeyboardEvent) => {
  if (e.key === "Escape") hideCarte();
});

// Silence unused-import warning for showError
void showError;
void hideCarte;
