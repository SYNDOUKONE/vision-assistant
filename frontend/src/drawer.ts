/**
 * VISION — Menu Rétractable (Sidebar Drawer Hub)
 * 
 * Regroupe toutes les fonctionnalités dans un tiroir latéral élégant
 * en glassmorphism afin de libérer l'espace visuel autour de l'Orbe 3D.
 */

import { enableScreenCapture } from "./screen_capture";
import { enableWebcam } from "./webcam";
import { startGestureControl, stopGestureControl } from "./gesture_control";
import { openRadioModal } from "./radio";
import { openWallpaperPanel } from "./wallpaper";

let isDrawerOpen = false;

export function openDrawer(): void {
  const drawer = document.getElementById("drawer-menu");
  const overlay = document.getElementById("drawer-overlay");
  const toggleBtn = document.getElementById("drawer-toggle-btn");
  isDrawerOpen = true;
  drawer?.classList.add("drawer-open");
  overlay?.classList.add("overlay-visible");
  toggleBtn?.classList.add("is-active");
}

export function closeDrawer(): void {
  const drawer = document.getElementById("drawer-menu");
  const overlay = document.getElementById("drawer-overlay");
  const toggleBtn = document.getElementById("drawer-toggle-btn");
  isDrawerOpen = false;
  drawer?.classList.remove("drawer-open");
  overlay?.classList.remove("overlay-visible");
  toggleBtn?.classList.remove("is-active");
}

export function toggleDrawer(): void {
  if (isDrawerOpen) {
    closeDrawer();
  } else {
    openDrawer();
  }
}

export function updateMuteStateInDrawer(): void {
  const mainMuteBtn = document.getElementById("mute-button");
  const drawerMuteStatus = document.getElementById("drawer-mute-status");
  if (mainMuteBtn && drawerMuteStatus) {
    const isMuted = mainMuteBtn.classList.contains("is-muted");
    drawerMuteStatus.textContent = isMuted ? "Micro coupé" : "Micro actif";
    drawerMuteStatus.className = `drawer-status-badge ${isMuted ? "badge-error" : "badge-success"}`;
  }
}

export function initDrawer(): void {
  const toggleBtn = document.getElementById("drawer-toggle-btn");
  const closeBtn = document.getElementById("drawer-close-btn");
  const overlay = document.getElementById("drawer-overlay");
  const drawer = document.getElementById("drawer-menu");

  if (!toggleBtn || !drawer) return;

  toggleBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleDrawer();
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", closeDrawer);
  }

  if (overlay) {
    overlay.addEventListener("click", closeDrawer);
  }

  // Fermer avec Échap
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isDrawerOpen) {
      closeDrawer();
    }
  });

  // ── Liaison des boutons du menu aux actions ──────────────────────────────────

  // 1. Assistant / Profil
  const switchProfileDrawerBtn = document.getElementById("drawer-btn-profile");
  if (switchProfileDrawerBtn) {
    switchProfileDrawerBtn.addEventListener("click", () => {
      closeDrawer();
      if ((window as any).showProfileScreen) {
        (window as any).showProfileScreen();
      }
    });
  }

  // 2. Micro (Mute / Unmute)
  const muteDrawerBtn = document.getElementById("drawer-btn-mute");
  const mainMuteBtn = document.getElementById("mute-button");
  if (muteDrawerBtn) {
    muteDrawerBtn.addEventListener("click", () => {
      if (mainMuteBtn) mainMuteBtn.click();
      updateMuteStateInDrawer();
    });
  }

  // 3. Panneau Texte
  const textDrawerBtn = document.getElementById("drawer-btn-text");
  const textToggleBtn = document.getElementById("text-toggle-button");
  if (textDrawerBtn) {
    textDrawerBtn.addEventListener("click", () => {
      closeDrawer();
      if (textToggleBtn) textToggleBtn.click();
    });
  }

  // 4. Historique
  const historyDrawerBtn = document.getElementById("drawer-btn-history");
  if (historyDrawerBtn) {
    historyDrawerBtn.addEventListener("click", () => {
      closeDrawer();
      if ((window as any).requestHistory) {
        (window as any).requestHistory();
      }
    });
  }

  // 5. Radio FM 3D
  const radioDrawerBtn = document.getElementById("drawer-btn-radio");
  if (radioDrawerBtn) {
    radioDrawerBtn.addEventListener("click", () => {
      closeDrawer();
      openRadioModal();
    });
  }

  // 6. Capture d'écran / Vision
  const visionDrawerBtn = document.getElementById("drawer-btn-vision");
  if (visionDrawerBtn) {
    visionDrawerBtn.addEventListener("click", async () => {
      const ok = await enableScreenCapture();
      const statusSpan = visionDrawerBtn.querySelector(".drawer-status-badge");
      if (statusSpan) {
        statusSpan.textContent = ok ? "Actif" : "Refusé";
        statusSpan.className = `drawer-status-badge ${ok ? "badge-success" : "badge-error"}`;
      }
    });
  }

  // 7. WebCam
  const webcamDrawerBtn = document.getElementById("drawer-btn-webcam");
  if (webcamDrawerBtn) {
    webcamDrawerBtn.addEventListener("click", async () => {
      const ok = await enableWebcam();
      const statusSpan = webcamDrawerBtn.querySelector(".drawer-status-badge");
      if (statusSpan) {
        statusSpan.textContent = ok ? "Actif" : "Refusé";
        statusSpan.className = `drawer-status-badge ${ok ? "badge-success" : "badge-error"}`;
      }
    });
  }

  // 8. Contrôle Gestuel
  const gestureDrawerBtn = document.getElementById("drawer-btn-gesture");
  let gestureActive = false;
  if (gestureDrawerBtn) {
    gestureDrawerBtn.addEventListener("click", async () => {
      const statusSpan = gestureDrawerBtn.querySelector(".drawer-status-badge");
      if (!gestureActive) {
        gestureActive = true;
        if (statusSpan) {
          statusSpan.textContent = "Actif";
          statusSpan.className = "drawer-status-badge badge-success";
        }
      } else {
        gestureActive = false;
        stopGestureControl();
        if (statusSpan) {
          statusSpan.textContent = "Inactif";
          statusSpan.className = "drawer-status-badge";
        }
      }
    });
  }

  // 9. Wallpaper
  const wallpaperDrawerBtn = document.getElementById("drawer-btn-wallpaper");
  if (wallpaperDrawerBtn) {
    wallpaperDrawerBtn.addEventListener("click", () => {
      closeDrawer();
      openWallpaperPanel();
    });
  }
}
