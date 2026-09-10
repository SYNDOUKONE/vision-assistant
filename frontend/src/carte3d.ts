/**
 * VISION — Localisation Maps & Vrai Globe Terrestre 3D avec Contrôle Gestuel MediaPipe
 * 
 * - Vrai Globe Terrestre 3D photoréaliste (textures continents, océans, nuages animés, atmosphère).
 * - Contrôle gestuel par caméra via MediaPipe Hands (rotation, pinch zoom, blocage poing, recentrage V, bascule pouce).
 * - Mini-fenêtre centrale avec bascule Google Maps / Globe 3D.
 */

import * as THREE from "three";
import { Hands, type Results, HAND_CONNECTIONS } from "@mediapipe/hands";
import { Camera } from "@mediapipe/camera_utils";

// ── Three.js & Globe Variables ────────────────────────────────────────────────
let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let earthGroup: THREE.Group | null = null;
let earthMesh: THREE.Mesh | null = null;
let cloudsMesh: THREE.Mesh | null = null;
let atmosphereMesh: THREE.Mesh | null = null;
let pinGroup: THREE.Group | null = null;
let animFrameId: number | null = null;
let isVisible = false;
let currentView: "maps" | "globe" = "maps";

// ── Coordonnées & Géolocalisation ─────────────────────────────────────────────
let userLat = 48.8566; // Paris par défaut
let userLon = 2.3522;
let userAddress = "Localisation en cours...";

// ── Inertie & Contrôles Rotation / Zoom ────────────────────────────────────────
let targetRotationX = 0;
let targetRotationY = 0;
let currentRotationX = 0;
let currentRotationY = 0;
let targetCameraDist = 4.2;
let currentCameraDist = 4.2;
let isLocked = false;
let isInteracting = false;

// ── MediaPipe Hands & Caméra ─────────────────────────────────────────────────
let handsDetector: Hands | null = null;
let cameraUtils: Camera | null = null;
let videoEl: HTMLVideoElement | null = null;
let handCanvasEl: HTMLCanvasElement | null = null;
let handCanvasCtx: CanvasRenderingContext2D | null = null;
let isGestureControlActive = false;
let currentGestureName = "En attente d'une main...";
let lastPinchDist: number | null = null;
let prevHandPos: { x: number; y: number } | null = null;
let gestureBadgeEl: HTMLDivElement | null = null;

// ── DOM Elements ─────────────────────────────────────────────────────────────
let modalOverlay: HTMLDivElement | null = null;
let mapIframe: HTMLIFrameElement | null = null;
let globeCanvasContainer: HTMLDivElement | null = null;
let coordsSpan: HTMLSpanElement | null = null;
let addressSpan: HTMLSpanElement | null = null;
let externalLink: HTMLAnchorElement | null = null;
let btnMaps: HTMLButtonElement | null = null;
let btnGlobe: HTMLButtonElement | null = null;
let btnToggleCamera: HTMLButtonElement | null = null;

function latLonToXYZ(lat: number, lon: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// 🌍 CHARGEMENT DES VRAIES TEXTURES NASA PHOTOGRAPHIQUES
// ══════════════════════════════════════════════════════════════════════════════

const _texLoader = new THREE.TextureLoader();

/**
 * Charge une texture depuis /textures/ avec chargement asynchrone.
 * Les fichiers sont dans frontend/public/textures/ → servis à /textures/
 */
function loadNasaTexture(filename: string, anisotropy = 8): THREE.Texture {
  const tex = _texLoader.load(
    `/textures/${filename}`,
    (t) => { t.needsUpdate = true; },
    undefined,
    (err) => console.warn(`[VISION Globe] Texture non chargée: ${filename}`, err)
  );
  tex.anisotropy = anisotropy;
  return tex;
}

// ══════════════════════════════════════════════════════════════════════════════
// 🪐 CRÉATION DU GLOBE TERRESTRE 3D (THREE.JS)
// ══════════════════════════════════════════════════════════════════════════════

function createRealEarth(): THREE.Group {
  const group = new THREE.Group();
  const radius = 1.8;

  // ── 1. Surface Terre : Texture photographique NASA (photo satellite réelle) ──
  const earthGeo = new THREE.SphereGeometry(radius, 96, 96);
  const earthMat = new THREE.MeshPhongMaterial({
    map:          loadNasaTexture("earth_atmos_2048.jpg"),      // Photo satellite NASA
    specularMap:  loadNasaTexture("earth_specular_2048.jpg"),   // Reflets océaniques
    normalMap:    loadNasaTexture("earth_normal_2048.jpg"),      // Relief / bump normal
    normalScale:  new THREE.Vector2(0.8, 0.8),
    specular:     new THREE.Color(0x336699),
    shininess:    28,
  });
  earthMesh = new THREE.Mesh(earthGeo, earthMat);
  group.add(earthMesh);

  // ── 2. Couche de Nuages Photographiques NASA ──────────────────────────────
  const cloudsGeo = new THREE.SphereGeometry(radius + 0.022, 64, 64);
  const cloudsMat = new THREE.MeshStandardMaterial({
    alphaMap:    loadNasaTexture("earth_clouds_1024.png"),       // Masque alpha nuages réels
    transparent: true,
    opacity:     1.0,
    color:       0xffffff,
    blending:    THREE.NormalBlending,
    depthWrite:  false,
  });
  cloudsMesh = new THREE.Mesh(cloudsGeo, cloudsMat);
  group.add(cloudsMesh);

  // ── 3. Halo d'Atmosphère Bleu Cyan (côté nuit / limbe) ────────────────────
  const atmoGeo = new THREE.SphereGeometry(radius + 0.14, 64, 64);
  const atmoMat = new THREE.MeshBasicMaterial({
    color:       0x1a9fff,
    transparent: true,
    opacity:     0.14,
    side:        THREE.BackSide,
    blending:    THREE.AdditiveBlending,
    depthWrite:  false,
  });
  atmosphereMesh = new THREE.Mesh(atmoGeo, atmoMat);
  group.add(atmosphereMesh);

  // ── 4. Halo interne doux (glow de bord) ───────────────────────────────────
  const glowGeo = new THREE.SphereGeometry(radius + 0.06, 64, 64);
  const glowMat = new THREE.MeshBasicMaterial({
    color:       0x0099ff,
    transparent: true,
    opacity:     0.06,
    side:        THREE.FrontSide,
    blending:    THREE.AdditiveBlending,
    depthWrite:  false,
  });
  group.add(new THREE.Mesh(glowGeo, glowMat));

  // ── 5. Balise GPS 3D Laser ────────────────────────────────────────────────
  pinGroup = createRealPin(userLat, userLon, radius);
  group.add(pinGroup);

  return group;
}

function createRealPin(lat: number, lon: number, radius: number): THREE.Group {
  const group = new THREE.Group();
  const pos = latLonToXYZ(lat, lon, radius);

  // Point d'ancrage doré
  const dot = new THREE.Mesh(
    new THREE.SphereGeometry(0.045, 16, 16),
    new THREE.MeshStandardMaterial({
      color: 0x00f3ff,
      emissive: 0x00bfff,
      emissiveIntensity: 1.2,
      roughness: 0.2,
    })
  );
  dot.position.copy(pos);
  group.add(dot);

  // Faisceau lumineux vertical (laser beacon)
  const normal = pos.clone().normalize();
  const beamHeight = 0.5;
  const beamGeo = new THREE.CylinderGeometry(0.008, 0.02, beamHeight, 16);
  const beamMat = new THREE.MeshBasicMaterial({
    color: 0x00eeff,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending,
  });
  const beam = new THREE.Mesh(beamGeo, beamMat);
  beam.position.copy(pos.clone().addScaledVector(normal, beamHeight / 2));
  beam.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);
  group.add(beam);

  // Anneaux de pulsation radar
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.08, 0.12, 32),
    new THREE.MeshBasicMaterial({
      color: 0x00ddff,
      transparent: true,
      opacity: 0.9,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  );
  ring.position.copy(pos);
  ring.lookAt(new THREE.Vector3(0, 0, 0));
  ring.userData = { type: "pulse_ring" };
  group.add(ring);

  return group;
}

function createStarField(): THREE.Points {
  const count = 800;
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);

  for (let i = 0; i < count; i++) {
    const u = Math.random();
    const v = Math.random();
    const theta = u * 2.0 * Math.PI;
    const phi = Math.acos(2.0 * v - 1.0);
    const r = Math.cbrt(Math.random()) * 40 + 15;

    const x = r * Math.sin(phi) * Math.cos(theta);
    const y = r * Math.sin(phi) * Math.sin(theta);
    const z = r * Math.cos(phi);

    positions[i * 3] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;

    colors[i * 3] = 0.8 + Math.random() * 0.2;
    colors[i * 3 + 1] = 0.85 + Math.random() * 0.15;
    colors[i * 3 + 2] = 1.0;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const mat = new THREE.PointsMaterial({
    size: 0.25,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
  });

  return new THREE.Points(geo, mat);
}

// ══════════════════════════════════════════════════════════════════════════════
// 🖐️ MODULE MEDIAPIPE HANDS (DÉTECTION DE GESTES PAR CAMÉRA)
// ══════════════════════════════════════════════════════════════════════════════

function initMediaPipe(): void {
  if (handsDetector) return;

  videoEl = document.getElementById("mediapipe-video") as HTMLVideoElement;
  handCanvasEl = document.getElementById("mediapipe-canvas") as HTMLCanvasElement;
  if (!videoEl || !handCanvasEl) return;
  handCanvasCtx = handCanvasEl.getContext("2d");

  handsDetector = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
  });

  handsDetector.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.65,
    minTrackingConfidence: 0.6,
  });

  handsDetector.onResults(handleHandResults);

  cameraUtils = new Camera(videoEl, {
    onFrame: async () => {
      if (isGestureControlActive && videoEl && handsDetector) {
        await handsDetector.send({ image: videoEl });
      }
    },
    width: 320,
    height: 240,
  });
}

function handleHandResults(results: Results): void {
  if (!handCanvasCtx || !handCanvasEl || !isGestureControlActive) return;

  handCanvasCtx.save();
  handCanvasCtx.clearRect(0, 0, handCanvasEl.width, handCanvasEl.height);

  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    const landmarks = results.multiHandLandmarks[0];

    // 1. Dessin du squelette de la main dans le mini HUD caméra
    handCanvasCtx.strokeStyle = "#00f3ff";
    handCanvasCtx.lineWidth = 2;
    for (const [startIdx, endIdx] of HAND_CONNECTIONS) {
      const p1 = landmarks[startIdx];
      const p2 = landmarks[endIdx];
      handCanvasCtx.beginPath();
      handCanvasCtx.moveTo(p1.x * handCanvasEl.width, p1.y * handCanvasEl.height);
      handCanvasCtx.lineTo(p2.x * handCanvasEl.width, p2.y * handCanvasEl.height);
      handCanvasCtx.stroke();
    }

    for (const p of landmarks) {
      handCanvasCtx.fillStyle = "#ffffff";
      handCanvasCtx.beginPath();
      handCanvasCtx.arc(p.x * handCanvasEl.width, p.y * handCanvasEl.height, 3, 0, Math.PI * 2);
      handCanvasCtx.fill();
    }

    // 2. Reconnaissance des Gestes
    processGesture(landmarks);
  } else {
    currentGestureName = "Main non détectée";
    updateGestureBadge("👁️ Présentez votre main devant la caméra");
    prevHandPos = null;
    lastPinchDist = null;
  }

  handCanvasCtx.restore();
}

function processGesture(lm: Array<{ x: number; y: number; z: number }>): void {
  const thumbTip = lm[4];
  const indexTip = lm[8];
  const middleTip = lm[12];
  const ringTip = lm[16];
  const pinkyTip = lm[20];

  const indexMcp = lm[5];
  const middleMcp = lm[9];
  const ringMcp = lm[13];
  const pinkyMcp = lm[17];
  const wrist = lm[0];

  // Calcul de l'extension des doigts
  const isIndexOpen = indexTip.y < indexMcp.y;
  const isMiddleOpen = middleTip.y < middleMcp.y;
  const isRingOpen = ringTip.y < ringMcp.y;
  const isPinkyOpen = pinkyTip.y < pinkyMcp.y;
  const isThumbUp = thumbTip.y < indexMcp.y && thumbTip.y < wrist.y;

  // Distance Index-Pouce (Pinch)
  const pinchDist = Math.hypot(thumbTip.x - indexTip.x, thumbTip.y - indexTip.y);

  // Centre de la paume
  const palmCenter = {
    x: (wrist.x + middleMcp.x) / 2,
    y: (wrist.y + middleMcp.y) / 2,
  };

  // ── GESTE 1 : ✊ POING FERMÉ (Stop / Verrouillage du globe) ───────────────
  if (!isIndexOpen && !isMiddleOpen && !isRingOpen && !isPinkyOpen) {
    isLocked = true;
    currentGestureName = "✊ Globe Verrouillé";
    updateGestureBadge("✊ Poing Fermé : Rotation Bloquée");
    prevHandPos = null;
    return;
  }
  isLocked = false;

  // ── GESTE 2 : ✌️ SIGNE V / VICTOIRE (Recentrage sur Syndou) ─────────────
  if (isIndexOpen && isMiddleOpen && !isRingOpen && !isPinkyOpen) {
    currentGestureName = "✌️ Recentrage GPS";
    updateGestureBadge("✌️ Signe V : Recentrage sur votre position");
    recenterOnLocation();
    prevHandPos = null;
    return;
  }

  // ── GESTE 3 : 👍 POUCE LEVÉ (Bascule Vue Maps / 3D) ──────────────────────
  if (isThumbUp && !isIndexOpen && !isMiddleOpen && !isRingOpen && !isPinkyOpen) {
    currentGestureName = "👍 Bascule de Vue";
    updateGestureBadge("👍 Pouce Levé : Changement de vue");
    switchView(currentView === "maps" ? "globe" : "maps");
    return;
  }

  // ── GESTE 4 : 👌 PINCEMENT (Pinch Zoom) ──────────────────────────────────
  if (pinchDist < 0.08 && isMiddleOpen && isRingOpen) {
    if (lastPinchDist !== null) {
      const delta = pinchDist - lastPinchDist;
      targetCameraDist = THREE.MathUtils.clamp(targetCameraDist - delta * 12, 2.5, 7.0);
      const zoomLevel = (5.0 / targetCameraDist).toFixed(1);
      currentGestureName = `👌 Zoom ${zoomLevel}x`;
      updateGestureBadge(`👌 Pincement : Zoom ${zoomLevel}x`);
    }
    lastPinchDist = pinchDist;
    prevHandPos = null;
    return;
  }
  lastPinchDist = null;

  // ── GESTE 5 : ✋ MAIN OUVERTE / TRANSLATION (Rotation 3D intuitive) ──────
  if (isIndexOpen && isMiddleOpen && isRingOpen && isPinkyOpen) {
    if (prevHandPos) {
      const dx = palmCenter.x - prevHandPos.x;
      const dy = palmCenter.y - prevHandPos.y;

      targetRotationY -= dx * 4.5;
      targetRotationX += dy * 3.5;
      targetRotationX = THREE.MathUtils.clamp(targetRotationX, -Math.PI / 2.3, Math.PI / 2.3);

      currentGestureName = "✋ Rotation 3D";
      updateGestureBadge("✋ Paume Ouverte : Rotation Libre");
    }
    prevHandPos = palmCenter;
    return;
  }

  prevHandPos = null;
  updateGestureBadge("🖐️ Main détectée — Prête aux gestes");
}

function updateGestureBadge(text: string): void {
  if (gestureBadgeEl) {
    gestureBadgeEl.textContent = text;
  }
}

function recenterOnLocation(): void {
  const phi = (90 - userLat) * (Math.PI / 180);
  const theta = (userLon + 180) * (Math.PI / 180);

  targetRotationX = (phi - Math.PI / 2);
  targetRotationY = -theta + Math.PI / 2;
  targetCameraDist = 3.6;
}

// ══════════════════════════════════════════════════════════════════════════════
// 🖥️ INTERFACE MODALE & AFFICHAGE
// ══════════════════════════════════════════════════════════════════════════════

function initModal(): void {
  if (modalOverlay) return;

  modalOverlay = document.createElement("div");
  modalOverlay.id = "carte-modal";
  modalOverlay.className = "carte-modal-hidden";

  modalOverlay.innerHTML = `
    <div class="carte-window" id="carte-window">
      <!-- HEADER -->
      <div class="carte-header">
        <div class="carte-title-wrap">
          <span class="carte-pulse-dot"></span>
          <span class="carte-title">VISION — GLOBE 3D &amp; MAPS</span>
          <span class="carte-badge">GPS CONNECTÉ</span>
        </div>
        <div class="carte-header-actions">
          <div class="carte-view-toggle">
            <button id="btn-view-maps" type="button">🗺️ Maps</button>
            <button id="btn-view-globe" class="active" type="button">🌍 Vrai Globe 3D</button>
          </div>
          <button id="btn-toggle-camera" class="carte-cam-btn" type="button" title="Activer le contrôle gestuel par caméra">
            📹 Contrôle Gestuel
          </button>
          <button id="btn-carte-close" class="carte-close-btn" type="button" title="Fermer (Échap)">✕</button>
        </div>
      </div>

      <!-- BODY (MAPS / 3D REAL EARTH / MEDIAPIPE HUD) -->
      <div class="carte-body">
        <div id="map-frame-container" class="map-view-hidden">
          <iframe
            id="carte-iframe"
            title="Google Maps"
            src="https://maps.google.com/maps?q=${userLat},${userLon}&hl=fr&z=15&output=embed"
            allowfullscreen
            loading="lazy"
          ></iframe>
        </div>

        <div id="globe-3d-container" class="globe-view-active"></div>

        <!-- HUD FLOTTANT CONTRÔLE GESTUEL MEDIAPIPE -->
        <div id="mediapipe-hud" class="mediapipe-hud-hidden">
          <div class="mediapipe-hud-header">
            <span>📹 DÉTECTION DES MAINS</span>
            <span id="mediapipe-gesture-badge">✋ Prêt</span>
          </div>
          <div class="mediapipe-hud-view">
            <video id="mediapipe-video" playsinline muted autoplay></video>
            <canvas id="mediapipe-canvas" width="320" height="240"></canvas>
          </div>
          <div class="mediapipe-legend">
            <span>✋ Tourner</span>
            <span>👌 Zoom</span>
            <span>✊ Bloquer</span>
            <span>✌️ Recentrer</span>
          </div>
        </div>
      </div>

      <!-- FOOTER -->
      <div class="carte-footer">
        <div class="carte-info-group">
          <div class="carte-address" id="carte-address">📍 ${userAddress}</div>
          <div class="carte-coords" id="carte-coords">LAT: ${userLat.toFixed(4)}° · LON: ${userLon.toFixed(4)}°</div>
        </div>
        <div class="carte-footer-actions">
          <button id="btn-recenter-gps" class="carte-btn-secondary" type="button" title="Actualiser et recentrer sur ma position">🎯 Ma position</button>
          <a id="carte-external-link" class="carte-btn-primary" href="https://www.google.com/maps?q=${userLat},${userLon}" target="_blank" rel="noopener">Ouvrir Maps ↗</a>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modalOverlay);

  // References
  mapIframe = document.getElementById("carte-iframe") as HTMLIFrameElement;
  globeCanvasContainer = document.getElementById("globe-3d-container") as HTMLDivElement;
  coordsSpan = document.getElementById("carte-coords") as HTMLSpanElement;
  addressSpan = document.getElementById("carte-address") as HTMLDivElement;
  externalLink = document.getElementById("carte-external-link") as HTMLAnchorElement;
  btnMaps = document.getElementById("btn-view-maps") as HTMLButtonElement;
  btnGlobe = document.getElementById("btn-view-globe") as HTMLButtonElement;
  btnToggleCamera = document.getElementById("btn-toggle-camera") as HTMLButtonElement;
  gestureBadgeEl = document.getElementById("mediapipe-gesture-badge") as HTMLDivElement;

  // Listeners
  document.getElementById("btn-carte-close")?.addEventListener("click", hideCarte);

  modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) hideCarte();
  });

  btnMaps?.addEventListener("click", () => switchView("maps"));
  btnGlobe?.addEventListener("click", () => switchView("globe"));

  btnToggleCamera?.addEventListener("click", toggleGestureControl);

  document.getElementById("btn-recenter-gps")?.addEventListener("click", () => {
    fetchGeolocation(true);
    recenterOnLocation();
  });

  // Init Three.js
  initThree();

  // Init MediaPipe
  initMediaPipe();
}

function toggleGestureControl(): void {
  isGestureControlActive = !isGestureControlActive;
  const hud = document.getElementById("mediapipe-hud");

  if (isGestureControlActive) {
    btnToggleCamera?.classList.add("cam-active");
    hud?.classList.remove("mediapipe-hud-hidden");
    cameraUtils?.start();
  } else {
    btnToggleCamera?.classList.remove("cam-active");
    hud?.classList.add("mediapipe-hud-hidden");
    cameraUtils?.stop();
    prevHandPos = null;
    lastPinchDist = null;
  }
}

function switchView(view: "maps" | "globe"): void {
  currentView = view;
  const mapContainer = document.getElementById("map-frame-container");
  const globeContainer = document.getElementById("globe-3d-container");

  if (view === "maps") {
    btnMaps?.classList.add("active");
    btnGlobe?.classList.remove("active");
    mapContainer?.classList.remove("map-view-hidden");
    mapContainer?.classList.add("map-view-active");
    globeContainer?.classList.remove("globe-view-active");
    globeContainer?.classList.add("globe-view-hidden");
  } else {
    btnGlobe?.classList.add("active");
    btnMaps?.classList.remove("active");
    globeContainer?.classList.remove("globe-view-hidden");
    globeContainer?.classList.add("globe-view-active");
    mapContainer?.classList.remove("map-view-active");
    mapContainer?.classList.add("map-view-hidden");
    onResize();
  }
}

function initThree(): void {
  if (!globeCanvasContainer) return;

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, (globeCanvasContainer.clientWidth || 760) / (globeCanvasContainer.clientHeight || 420), 0.1, 100);
  camera.position.set(0, 0, currentCameraDist);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(globeCanvasContainer.clientWidth || 760, globeCanvasContainer.clientHeight || 420);
  renderer.setClearColor(0x020409, 1);

  globeCanvasContainer.appendChild(renderer.domElement);

  // Lumière du Soleil (Directionnelle)
  const sunLight = new THREE.DirectionalLight(0xffffff, 1.8);
  sunLight.position.set(5, 3, 5);
  scene.add(sunLight);

  // Lumière d'ambiance douce (côté nuit)
  const ambientLight = new THREE.AmbientLight(0x1a2e4a, 0.9);
  scene.add(ambientLight);

  // Champ d'étoiles
  scene.add(createStarField());

  // Vrai Globe Terrestre
  earthGroup = createRealEarth();
  scene.add(earthGroup);

  // Position initiale
  recenterOnLocation();

  // Contrôles souris
  setupMouseControls();
}

function setupMouseControls(): void {
  if (!renderer) return;
  const el = renderer.domElement;
  let isDown = false;
  let startX = 0;
  let startY = 0;

  el.addEventListener("pointerdown", (e) => {
    isDown = true;
    isInteracting = true;
    startX = e.clientX;
    startY = e.clientY;
  });

  el.addEventListener("pointermove", (e) => {
    if (!isDown) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    targetRotationY += dx * 0.006;
    targetRotationX += dy * 0.006;
    targetRotationX = THREE.MathUtils.clamp(targetRotationX, -Math.PI / 2.2, Math.PI / 2.2);
    startX = e.clientX;
    startY = e.clientY;
  });

  el.addEventListener("pointerup", () => {
    isDown = false;
    isInteracting = false;
  });

  el.addEventListener("wheel", (e) => {
    e.preventDefault();
    targetCameraDist = THREE.MathUtils.clamp(targetCameraDist + e.deltaY * 0.004, 2.4, 7.0);
  }, { passive: false });
}

function animate(): void {
  animFrameId = requestAnimationFrame(animate);
  const t = Date.now() * 0.001;

  if (currentView === "globe" && earthGroup && camera) {
    // 1. Rotation continue si non bloqué et pas d'interaction
    if (!isLocked && !isInteracting && !isGestureControlActive) {
      targetRotationY += 0.0015;
    }

    // 2. Interpolation fluide de la rotation (Damping)
    currentRotationX += (targetRotationX - currentRotationX) * 0.1;
    currentRotationY += (targetRotationY - currentRotationY) * 0.1;
    earthGroup.rotation.x = currentRotationX;
    earthGroup.rotation.y = currentRotationY;

    // 3. Rotation atmosphérique des nuages
    if (cloudsMesh) {
      cloudsMesh.rotation.y += 0.0006;
    }

    // 4. Interpolation fluide du zoom caméra
    currentCameraDist += (targetCameraDist - currentCameraDist) * 0.1;
    camera.position.z = currentCameraDist;

    // 5. Pulsation de l'anneau radar
    if (pinGroup) {
      pinGroup.children.forEach((c) => {
        if (c.userData?.type === "pulse_ring") {
          const s = 1 + 0.5 * Math.abs(Math.sin(t * 2.5));
          c.scale.setScalar(s);
          (c as THREE.Mesh<any, THREE.MeshBasicMaterial>).material.opacity = 1 - (s - 1);
        }
      });
    }

    if (renderer && scene) {
      renderer.render(scene, camera);
    }
  }
}

function onResize(): void {
  if (!globeCanvasContainer || !camera || !renderer) return;
  const w = globeCanvasContainer.clientWidth || 760;
  const h = globeCanvasContainer.clientHeight || 420;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}

// ══════════════════════════════════════════════════════════════════════════════
// 📍 GÉOLOCALISATION & ADRESSE
// ══════════════════════════════════════════════════════════════════════════════

async function reverseGeocode(lat: number, lon: number): Promise<void> {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`,
      { headers: { "Accept-Language": "fr" } }
    );
    if (res.ok) {
      const data = await res.json();
      const addr = data.address || {};
      const street = addr.road || addr.pedestrian || addr.suburb || "";
      const city = addr.city || addr.town || addr.village || addr.municipality || "";
      const postcode = addr.postcode || "";
      const country = addr.country || "";

      const parts = [street, city, postcode, country].filter(Boolean);
      userAddress = parts.length > 0 ? parts.join(", ") : data.display_name || "Position repérée";
      if (addressSpan) {
        addressSpan.textContent = `📍 ${userAddress}`;
      }
    }
  } catch {
    if (addressSpan) {
      addressSpan.textContent = `📍 Lat: ${lat.toFixed(4)}°, Lon: ${lon.toFixed(4)}°`;
    }
  }
}

function updateLocation(lat: number, lon: number): void {
  userLat = lat;
  userLon = lon;

  if (mapIframe) {
    mapIframe.src = `https://maps.google.com/maps?q=${lat},${lon}&hl=fr&z=15&output=embed`;
  }
  if (coordsSpan) {
    coordsSpan.textContent = `LAT: ${lat.toFixed(4)}° · LON: ${lon.toFixed(4)}°`;
  }
  if (externalLink) {
    externalLink.href = `https://www.google.com/maps?q=${lat},${lon}`;
  }

  if (earthGroup && pinGroup) {
    earthGroup.remove(pinGroup);
    pinGroup = createRealPin(lat, lon, 1.8);
    earthGroup.add(pinGroup);
  }

  reverseGeocode(lat, lon);
}

function fetchGeolocation(forceRecenter = false): void {
  if (!navigator.geolocation) {
    updateLocation(userLat, userLon);
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      updateLocation(pos.coords.latitude, pos.coords.longitude);
      if (forceRecenter) recenterOnLocation();
    },
    async () => {
      try {
        const r = await fetch("https://ipapi.co/json/");
        if (r.ok) {
          const d = await r.json();
          if (d.latitude && d.longitude) {
            updateLocation(d.latitude, d.longitude);
            if (forceRecenter) recenterOnLocation();
            return;
          }
        }
      } catch {}
      updateLocation(userLat, userLon);
    },
    { enableHighAccuracy: true, timeout: 7000, maximumAge: forceRecenter ? 0 : 60000 }
  );
}

// ── Export Show / Hide ────────────────────────────────────────────────────────
export function showCarte(): void {
  if (isVisible) return;
  initModal();
  isVisible = true;

  if (modalOverlay) {
    modalOverlay.classList.remove("carte-modal-hidden");
    modalOverlay.classList.add("carte-modal-visible");
  }

  switchView("globe");
  fetchGeolocation();

  if (!animFrameId) {
    animate();
  }
}

export function hideCarte(): void {
  if (!isVisible || !modalOverlay) return;
  isVisible = false;
  modalOverlay.classList.remove("carte-modal-visible");
  modalOverlay.classList.add("carte-modal-hidden");

  if (isGestureControlActive) {
    toggleGestureControl();
  }

  if (animFrameId !== null) {
    cancelAnimationFrame(animFrameId);
    animFrameId = null;
  }
}

export function toggleCarte(): void {
  isVisible ? hideCarte() : showCarte();
}


