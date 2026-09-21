/**
 * VISION — Scanner Biométrique & Reconnaissance Faciale (FaceMesh HUD)
 *
 * Affiche une fenêtre HUD cybernétique avec le flux vidéo webcam,
 * le traçage temps-réel des 468 points du visage (landmarks / mesh)
 * et le nom de la personne reconnue au-dessus de la cible.
 * Permet d'ajouter et d'effacer des profils utilisateurs.
 */

import { FaceMesh, type Results } from "@mediapipe/face_mesh";
import { Camera } from "@mediapipe/camera_utils";

export interface FaceProfile {
  nom: string;
  slug: string;
  fichier?: string;
  relation?: string;
  notes?: string;
  date_enregistrement?: string;
  derniere_vue?: string;
  photo_b64?: string;
}

let faceMesh: FaceMesh | null = null;
let camera: Camera | null = null;
let videoEl: HTMLVideoElement | null = null;
let canvasEl: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;
let modalEl: HTMLDivElement | null = null;
let wsSendCallback: ((data: any) => void) | null = null;

let isOpen = false;
let isScanning = false;
let knownFaces: FaceProfile[] = [];
let identifiedPerson: { name: string; confidence: number; relation?: string } | null = null;
let lastAutoScanTime = 0;
let currentTab: "scanner" | "manager" = "scanner";

// ── Initialisation du DOM ────────────────────────────────────────────────────
export function initFaceScanner(sendWsMsg: (data: any) => void): void {
  wsSendCallback = sendWsMsg;
  createModalHTML();
  initDragWindow();
}

function createModalHTML(): void {
  if (document.getElementById("face-scanner-modal")) return;

  modalEl = document.createElement("div");
  modalEl.id = "face-scanner-modal";
  modalEl.className = "face-modal-hidden";
  modalEl.innerHTML = `
    <div class="face-modal-window">
      <!-- HUD Header -->
      <div class="face-modal-header" id="face-modal-drag-handle">
        <div class="face-header-title">
          <span class="face-hud-pulse"></span>
          <span class="face-title-text">SCANNER BIOMÉTRIQUE // FACE ID</span>
        </div>
        <div class="face-header-controls">
          <button id="face-tab-scan-btn" class="face-tab-btn active" type="button" title="Vue Caméra & Points">👁️ Live</button>
          <button id="face-tab-manage-btn" class="face-tab-btn" type="button" title="Gérer les profils">👥 Profils (<span id="face-count-badge">0</span>)</button>
          <button id="face-close-btn" class="face-close-btn" type="button" title="Fermer le scanner">✕</button>
        </div>
      </div>

      <!-- Persistent Camera Viewport (Always active & visible) -->
      <div class="face-viewport-container">
        <div class="face-viewport-wrapper">
          <video id="face-webcam-video" playsinline muted autoplay></video>
          <canvas id="face-mesh-canvas"></canvas>
          <div id="face-hud-overlay" class="face-hud-overlay">
            <div class="face-hud-crosshair tl"></div>
            <div class="face-hud-crosshair tr"></div>
            <div class="face-hud-crosshair bl"></div>
            <div class="face-hud-crosshair br"></div>
            <div id="face-status-badge" class="face-status-badge">RECHERCHE DE VISAGE...</div>
            <div id="face-tag-label" class="face-tag-label"></div>
          </div>
        </div>
      </div>

      <!-- Main Body Container with Tabs -->
      <div class="face-modal-body">
        <!-- TAB 1: Live Controls -->
        <div id="face-tab-scanner" class="face-tab-content active">
          <div class="face-scanner-actions">
            <button id="face-scan-now-btn" class="face-btn face-btn-primary" type="button">
              🔍 Identifier la personne
            </button>
            <button id="face-quick-add-btn" class="face-btn face-btn-secondary" type="button">
              ➕ Mémoriser ce visage
            </button>
          </div>
        </div>

        <!-- TAB 2: Face Manager (Ajouter & Supprimer) -->
        <div id="face-tab-manager" class="face-tab-content">
          <!-- Add Form Section -->
          <div class="face-add-section">
            <div class="face-section-title">Ajouter une nouvelle personne</div>
            <div class="face-add-form">
              <div class="face-preview-box">
                <img id="face-capture-preview" src="" alt="Capture" />
                <button id="face-recapture-btn" type="button" class="face-btn-mini">📸 Capturer</button>
              </div>
              <div class="face-inputs-col">
                <input id="face-input-name" type="text" placeholder="Prénom / Nom (ex: Syndou, Sarah...)" autocomplete="off" />
                <input id="face-input-relation" type="text" placeholder="Relation (ex: Ami, Famille, Collègue...)" autocomplete="off" />
                <button id="face-save-btn" type="button" class="face-btn face-btn-primary">
                  💾 Enregistrer ce profil
                </button>
              </div>
            </div>
          </div>

          <!-- Gallery List Section -->
          <div class="face-list-section">
            <div class="face-section-title">Profils mémorisés (<span id="face-list-total">0</span>)</div>
            <div id="face-cards-gallery" class="face-cards-gallery">
              <!-- Dynamically populated cards -->
            </div>
          </div>
        </div>
      </div>

      <!-- Toast Notification -->
      <div id="face-toast" class="face-toast"></div>
    </div>
  `;

  document.body.appendChild(modalEl);
  bindEvents();
}

function bindEvents(): void {
  const closeBtn = document.getElementById("face-close-btn");
  if (closeBtn) closeBtn.addEventListener("click", closeFaceScanner);

  const tabScanBtn = document.getElementById("face-tab-scan-btn");
  const tabManageBtn = document.getElementById("face-tab-manage-btn");
  if (tabScanBtn && tabManageBtn) {
    tabScanBtn.addEventListener("click", () => switchTab("scanner"));
    tabManageBtn.addEventListener("click", () => switchTab("manager"));
  }

  const scanNowBtn = document.getElementById("face-scan-now-btn");
  if (scanNowBtn) {
    scanNowBtn.addEventListener("click", () => triggerFaceIdentification(false));
  }

  const quickAddBtn = document.getElementById("face-quick-add-btn");
  if (quickAddBtn) {
    quickAddBtn.addEventListener("click", () => {
      switchTab("manager");
      captureCurrentSnapshot();
    });
  }

  const recaptureBtn = document.getElementById("face-recapture-btn");
  if (recaptureBtn) {
    recaptureBtn.addEventListener("click", captureCurrentSnapshot);
  }

  const saveBtn = document.getElementById("face-save-btn");
  if (saveBtn) {
    saveBtn.addEventListener("click", handleSaveFace);
  }
}

function switchTab(tab: "scanner" | "manager"): void {
  currentTab = tab;
  const tabScan = document.getElementById("face-tab-scanner");
  const tabManage = document.getElementById("face-tab-manager");
  const tabScanBtn = document.getElementById("face-tab-scan-btn");
  const tabManageBtn = document.getElementById("face-tab-manage-btn");

  if (tabScan && tabManage && tabScanBtn && tabManageBtn) {
    if (tab === "scanner") {
      tabScan.classList.add("active");
      tabManage.classList.remove("active");
      tabScanBtn.classList.add("active");
      tabManageBtn.classList.remove("active");
    } else {
      tabScan.classList.remove("active");
      tabManage.classList.add("active");
      tabScanBtn.classList.remove("active");
      tabManageBtn.classList.add("active");
      requestFacesList();
      captureCurrentSnapshot();
    }
  }
}

// ── Ouvrir & Fermer le scanner ───────────────────────────────────────────────
export async function openFaceScanner(): Promise<void> {
  if (isOpen) return;
  isOpen = true;

  if (!modalEl) createModalHTML();
  modalEl?.classList.remove("face-modal-hidden");

  await startFaceMesh();
  requestFacesList();
}

export function closeFaceScanner(): void {
  if (!isOpen) return;
  isOpen = false;
  modalEl?.classList.add("face-modal-hidden");
  stopFaceMesh();
}

export function toggleFaceScanner(): void {
  if (isOpen) {
    closeFaceScanner();
  } else {
    openFaceScanner();
  }
}

// ── Démarrage MediaPipe FaceMesh ─────────────────────────────────────────────
async function startFaceMesh(): Promise<void> {
  videoEl = document.getElementById("face-webcam-video") as HTMLVideoElement;
  canvasEl = document.getElementById("face-mesh-canvas") as HTMLCanvasElement;
  if (!videoEl || !canvasEl) return;

  ctx = canvasEl.getContext("2d");

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480, frameRate: 30 },
      audio: false,
    });
    videoEl.srcObject = stream;
    await videoEl.play();

    canvasEl.width = videoEl.videoWidth || 640;
    canvasEl.height = videoEl.videoHeight || 480;

    faceMesh = new FaceMesh({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
    });

    faceMesh.setOptions({
      maxNumFaces: 2,
      refineLandmarks: true,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });

    faceMesh.onResults(onFaceMeshResults);

    camera = new Camera(videoEl, {
      onFrame: async () => {
        if (faceMesh && videoEl && isOpen) {
          await faceMesh.send({ image: videoEl });
        }
      },
      width: 640,
      height: 480,
    });

    await camera.start();
    showFaceToast("✅ Scanner Biométrique connecté", "success");
    captureCurrentSnapshot();
  } catch (err) {
    console.error("[FACE SCANNER] Erreur caméra/FaceMesh:", err);
    showFaceToast("❌ Impossible d'accéder à la webcam", "error");
  }
}

function stopFaceMesh(): void {
  if (camera) {
    camera.stop();
    camera = null;
  }
  if (videoEl && videoEl.srcObject) {
    const stream = videoEl.srcObject as MediaStream;
    stream.getTracks().forEach((track) => track.stop());
    videoEl.srcObject = null;
  }
  if (ctx && canvasEl) {
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
  }
  faceMesh = null;
}

// ── Rendu des Points du Visage (Landmarks & Mesh) ────────────────────────────
function onFaceMeshResults(results: Results): void {
  if (!ctx || !canvasEl || !videoEl) return;

  ctx.save();
  ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);

  const statusBadge = document.getElementById("face-status-badge");
  const tagLabel = document.getElementById("face-tag-label");

  if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
    if (statusBadge) {
      statusBadge.textContent = "RECHERCHE DE VISAGE...";
      statusBadge.className = "face-status-badge searching";
    }
    if (tagLabel) tagLabel.style.display = "none";
    ctx.restore();
    return;
  }

  const w = canvasEl.width;
  const h = canvasEl.height;

  for (const landmarks of results.multiFaceLandmarks) {
    let minX = w, maxX = 0, minY = h, maxY = 0;
    for (const pt of landmarks) {
      const px = pt.x * w;
      const py = pt.y * h;
      if (px < minX) minX = px;
      if (px > maxX) maxX = px;
      if (py < minY) minY = py;
      if (py > maxY) maxY = py;
    }

    // 1. Dessiner les points biométriques (Landmarks)
    ctx.fillStyle = "#00f2fe";
    for (let i = 0; i < landmarks.length; i++) {
      const pt = landmarks[i];
      const px = pt.x * w;
      const py = pt.y * h;
      const isKeyPoint = i % 4 === 0 || (i >= 468);
      if (isKeyPoint) {
        ctx.beginPath();
        ctx.arc(px, py, 1.2, 0, 2 * Math.PI);
        ctx.fill();
      }
    }

    // 2. Contours des Yeux & Lèvres en néon
    const leftEyeIndices = [33, 133, 159, 145, 153, 144];
    const rightEyeIndices = [362, 263, 386, 374, 380, 373];
    const lipsIndices = [61, 291, 0, 17, 84, 314];

    drawContour(landmarks, leftEyeIndices, w, h, "#10b981", 1.5);
    drawContour(landmarks, rightEyeIndices, w, h, "#10b981", 1.5);
    drawContour(landmarks, lipsIndices, w, h, "#38bdf8", 1.5);

    // 3. Bounding Box HUD
    const pad = 16;
    const boxX = Math.max(0, minX - pad);
    const boxY = Math.max(0, minY - pad);
    const boxW = Math.min(w - boxX, maxX - minX + pad * 2);
    const boxH = Math.min(h - boxY, maxY - minY + pad * 2);

    drawHudReticle(ctx, boxX, boxY, boxW, boxH);

    // 4. Affichage du Nom au-dessus du visage
    if (tagLabel) {
      tagLabel.style.display = "block";
      tagLabel.style.left = `${boxX + boxW / 2}px`;
      tagLabel.style.top = `${Math.max(10, boxY - 28)}px`;

      if (identifiedPerson && identifiedPerson.name && identifiedPerson.name !== "Inconnu" && identifiedPerson.name !== "Visage non enregistré") {
        tagLabel.innerHTML = `👤 <strong>${identifiedPerson.name.toUpperCase()}</strong> <span class="tag-conf">${Math.round((identifiedPerson.confidence || 0.95) * 100)}%</span>`;
        tagLabel.className = "face-tag-label verified";
      } else {
        tagLabel.innerHTML = `❓ <strong>VISAGE INCONNU</strong>`;
        tagLabel.className = "face-tag-label unknown";
      }
    }

    if (statusBadge) {
      if (identifiedPerson && identifiedPerson.name && identifiedPerson.name !== "Inconnu" && identifiedPerson.name !== "Visage non enregistré") {
        statusBadge.textContent = `IDENTIFIÉ : ${identifiedPerson.name.toUpperCase()}`;
        statusBadge.className = "face-status-badge verified";
      } else {
        statusBadge.textContent = "VISAGE DÉTECTÉ";
        statusBadge.className = "face-status-badge active";
      }
    }
  }

  ctx.restore();

  const now = Date.now();
  if (now - lastAutoScanTime > 14000 && (!identifiedPerson || identifiedPerson.name === "Inconnu" || identifiedPerson.name === "Visage non enregistré")) {
    lastAutoScanTime = now;
    triggerFaceIdentification(true);
  }
}

function drawContour(landmarks: any[], indices: number[], w: number, h: number, color: string, lineWidth: number): void {
  if (!ctx || indices.length === 0) return;
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  indices.forEach((idx, i) => {
    const pt = landmarks[idx];
    if (!pt) return;
    const px = pt.x * w;
    const py = pt.y * h;
    if (i === 0) ctx!.moveTo(px, py);
    else ctx!.lineTo(px, py);
  });
  ctx.closePath();
  ctx.stroke();
}

function drawHudReticle(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number): void {
  const lineLen = Math.min(24, w * 0.2);
  ctx.strokeStyle = "#00f2fe";
  ctx.lineWidth = 2;
  ctx.shadowColor = "#00f2fe";
  ctx.shadowBlur = 8;

  // Coin Haut-Gauche
  ctx.beginPath();
  ctx.moveTo(x, y + lineLen);
  ctx.lineTo(x, y);
  ctx.lineTo(x + lineLen, y);
  ctx.stroke();

  // Coin Haut-Droite
  ctx.beginPath();
  ctx.moveTo(x + w - lineLen, y);
  ctx.lineTo(x + w, y);
  ctx.lineTo(x + w, y + lineLen);
  ctx.stroke();

  // Coin Bas-Gauche
  ctx.beginPath();
  ctx.moveTo(x, y + h - lineLen);
  ctx.lineTo(x, y + h);
  ctx.lineTo(x + lineLen, y + h);
  ctx.stroke();

  // Coin Bas-Droite
  ctx.beginPath();
  ctx.moveTo(x + w - lineLen, y + h);
  ctx.lineTo(x + w, y + h);
  ctx.lineTo(x + w, y + h - lineLen);
  ctx.stroke();

  ctx.shadowBlur = 0;
}

// ── Capture Instantanée pour Enregistrement / Identification ─────────────────
export function captureCurrentFrameBase64(): string | null {
  if (!videoEl || videoEl.readyState < 2) return null;
  const offscreen = document.createElement("canvas");
  offscreen.width = videoEl.videoWidth || 640;
  offscreen.height = videoEl.videoHeight || 480;
  const offCtx = offscreen.getContext("2d");
  if (!offCtx) return null;
  offCtx.drawImage(videoEl, 0, 0, offscreen.width, offscreen.height);
  return offscreen.toDataURL("image/jpeg", 0.9);
}

function captureCurrentSnapshot(): void {
  const imgB64 = captureCurrentFrameBase64();
  if (imgB64) {
    const preview = document.getElementById("face-capture-preview") as HTMLImageElement;
    if (preview) preview.src = imgB64;
  }
}

// ── Identification via Backend (Gemini / Base de visages) ───────────────────
export async function triggerFaceIdentification(isSilent: boolean = false): Promise<void> {
  if (isScanning) return;
  const imgB64 = captureCurrentFrameBase64();
  if (!imgB64) {
    if (!isSilent) showFaceToast("Veuillez vous placer devant la caméra", "error");
    return;
  }

  isScanning = true;
  const statusBadge = document.getElementById("face-status-badge");
  if (statusBadge) {
    statusBadge.textContent = "ANALYSE BIOMÉTRIQUE EN COURS...";
    statusBadge.className = "face-status-badge analyzing";
  }

  if (wsSendCallback) {
    wsSendCallback({
      type: "recognize_face_frame",
      image_b64: imgB64,
    });
  }
}

// ── Gestion de l'Enregistrement de Visage ────────────────────────────────────
function handleSaveFace(): void {
  const nameInput = document.getElementById("face-input-name") as HTMLInputElement;
  const relationInput = document.getElementById("face-input-relation") as HTMLInputElement;
  const preview = document.getElementById("face-capture-preview") as HTMLImageElement;

  const name = nameInput?.value.trim();
  const relation = relationInput?.value.trim() || "Ami";

  if (!name) {
    showFaceToast("Veuillez saisir un nom pour cette personne", "error");
    nameInput?.focus();
    return;
  }

  // Tente de récupérer l'image de la prévisualisation ou capture en direct
  let image_b64 = preview?.src;
  if (!image_b64 || !image_b64.startsWith("data:image")) {
    image_b64 = captureCurrentFrameBase64() || "";
  }

  if (!image_b64 || !image_b64.startsWith("data:image")) {
    showFaceToast("Impossible de capturer la photo de la caméra", "error");
    return;
  }

  if (wsSendCallback) {
    wsSendCallback({
      type: "save_face",
      name: name,
      relation: relation,
      notes: "Enregistré via le scanner HUD",
      image_b64: image_b64,
    });

    nameInput.value = "";
    relationInput.value = "";
    showFaceToast(`Enregistrement de "${name}" en cours...`, "info");
  } else {
    showFaceToast("Connexion au serveur perdue", "error");
  }
}

// ── Suppression de Visage ───────────────────────────────────────────────────
export function deleteFace(name: string): void {
  if (!name) return;
  if (confirm(`Confirmez-vous la suppression du profil de "${name}" ?`)) {
    if (wsSendCallback) {
      wsSendCallback({
        type: "delete_face",
        name: name,
      });
      showFaceToast(`Suppression de ${name}...`, "info");
    }
  }
}

// ── Récupération de la liste des Visages ─────────────────────────────────────
export function requestFacesList(): void {
  if (wsSendCallback) {
    wsSendCallback({ type: "get_faces" });
  }
}

// ── Réception des messages WebSocket liés au Face Scanner ───────────────────
export function handleFaceWsMessage(data: any): void {
  const action = data.action;

  if (action === "faces_list") {
    knownFaces = data.faces || [];
    renderFacesGallery();
    const badge = document.getElementById("face-count-badge");
    const total = document.getElementById("face-list-total");
    if (badge) badge.textContent = String(knownFaces.length);
    if (total) total.textContent = String(knownFaces.length);
    if (data.notification) {
      showFaceToast(data.notification, "success");
    }
  } else if (action === "face_recognized") {
    isScanning = false;
    const res = data.result || {};
    if (res.identified && res.name && res.name !== "Inconnu" && res.name !== "Visage non enregistré") {
      identifiedPerson = {
        name: res.name,
        confidence: res.confidence || 0.95,
        relation: res.relation,
      };
      showFaceToast(`Identifié : ${res.name}`, "success");
    } else {
      identifiedPerson = { name: "Inconnu", confidence: 0.0 };
      showFaceToast("Visage non reconnu dans la base", "info");
    }
  }
}

function renderFacesGallery(): void {
  const gallery = document.getElementById("face-cards-gallery");
  if (!gallery) return;

  if (knownFaces.length === 0) {
    gallery.innerHTML = `
      <div class="face-empty-state">
        <span>Aucun profil mémorisé pour le moment.</span>
        <small>Utilisez le formulaire ci-dessus pour enregistrer un visage.</small>
      </div>
    `;
    return;
  }

  gallery.innerHTML = knownFaces
    .map(
      (f) => `
      <div class="face-card" data-name="${escapeHtml(f.nom)}">
        <div class="face-card-avatar">
          ${f.photo_b64 ? `<img src="${f.photo_b64}" alt="${escapeHtml(f.nom)}" />` : `<div class="face-avatar-placeholder">👤</div>`}
        </div>
        <div class="face-card-info">
          <div class="face-card-name">${escapeHtml(f.nom)}</div>
          <div class="face-card-relation">${escapeHtml(f.relation || "Ami")}</div>
          <div class="face-card-date">${f.date_enregistrement || ""}</div>
        </div>
        <button class="face-card-del-btn" title="Supprimer ce profil" onclick="window.deleteFaceProfile('${escapeHtml(f.nom)}')">
          🗑️
        </button>
      </div>
    `
    )
    .join("");
}

// ── Notifications Toast ─────────────────────────────────────────────────────
let toastTimer: ReturnType<typeof setTimeout> | null = null;
function showFaceToast(msg: string, type: "info" | "success" | "error" = "info"): void {
  const toast = document.getElementById("face-toast");
  if (!toast) return;
  toast.textContent = msg;
  toast.className = `face-toast active ${type}`;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.className = "face-toast";
  }, 3500);
}

// ── Drag & Drop de la fenêtre HUD ───────────────────────────────────────────
function initDragWindow(): void {
  const handle = document.getElementById("face-modal-drag-handle");
  const win = document.querySelector(".face-modal-window") as HTMLElement;
  if (!handle || !win) return;

  let isDragging = false;
  let startX = 0, startY = 0, initialLeft = 0, initialTop = 0;

  handle.addEventListener("mousedown", (e) => {
    if ((e.target as HTMLElement).tagName === "BUTTON") return;
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    const rect = win.getBoundingClientRect();
    initialLeft = rect.left;
    initialTop = rect.top;
    win.style.position = "fixed";
    win.style.transform = "none";
    win.style.left = `${initialLeft}px`;
    win.style.top = `${initialTop}px`;
    win.style.margin = "0";
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    win.style.left = `${Math.max(10, Math.min(window.innerWidth - win.offsetWidth - 10, initialLeft + dx))}px`;
    win.style.top = `${Math.max(10, Math.min(window.innerHeight - win.offsetHeight - 10, initialTop + dy))}px`;
  });

  window.addEventListener("mouseup", () => {
    isDragging = false;
  });
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Exposition globale pour les onclick inline
(window as any).deleteFaceProfile = (name: string) => {
  deleteFace(name);
};
(window as any).toggleFaceScanner = toggleFaceScanner;
