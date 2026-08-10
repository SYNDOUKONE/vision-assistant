/**
 * VISION — Carte 3D Holographique
 * Globe de points lumineux bleus avec pin de position en temps réel.
 * Activé par la commande "active la carte".
 */

import * as THREE from "three";

let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let globe: THREE.Points | null = null;
let pinGroup: THREE.Group | null = null;
let animFrameId: number | null = null;
let container: HTMLDivElement | null = null;
let isVisible = false;

// ── Géolocalisation ─────────────────────────────────────────────────────────
let userLat = 48.8566; // Paris par défaut (France)
let userLon = 2.3522;

function latLonToXYZ(
  lat: number,
  lon: number,
  radius: number
): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

// ── Création du globe en points ──────────────────────────────────────────────
function createGlobePoints(): THREE.Points {
  const radius = 1.8;
  const positions: number[] = [];
  const colors: number[] = [];
  const N = 6000;

  // Distribution uniforme sur la sphère (méthode de Fibonacci)
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < N; i++) {
    const y = 1 - (i / (N - 1)) * 2;
    const r = Math.sqrt(1 - y * y);
    const theta = goldenAngle * i;
    const x = Math.cos(theta) * r;
    const z = Math.sin(theta) * r;

    positions.push(x * radius, y * radius, z * radius);

    // Dégradé bleu profond → cyan électrique
    const t = Math.random();
    colors.push(
      0.05 + t * 0.15,   // R
      0.4 + t * 0.4,     // G
      0.85 + t * 0.15    // B
    );
  }

  // Grille de latitude/longitude (lignes)
  for (let lat = -80; lat <= 80; lat += 20) {
    for (let lon = -180; lon <= 180; lon += 3) {
      const v = latLonToXYZ(lat, lon, radius);
      positions.push(v.x, v.y, v.z);
      const t = (lat + 90) / 180;
      colors.push(0.1, 0.45 + t * 0.2, 0.9);
    }
  }
  for (let lon = -180; lon <= 180; lon += 30) {
    for (let lat = -85; lat <= 85; lat += 2) {
      const v = latLonToXYZ(lat, lon, radius);
      positions.push(v.x, v.y, v.z);
      const t = (lon + 180) / 360;
      colors.push(0.05, 0.35 + t * 0.25, 0.85);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));

  const mat = new THREE.PointsMaterial({
    size: 0.018,
    vertexColors: true,
    transparent: true,
    opacity: 0.9,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  return new THREE.Points(geo, mat);
}

// ── Épingle de position pulsante ─────────────────────────────────────────────
function createPin(lat: number, lon: number): THREE.Group {
  const group = new THREE.Group();
  const radius = 1.8;
  const pos = latLonToXYZ(lat, lon, radius);

  // Point central (épingle)
  const dotGeo = new THREE.SphereGeometry(0.035, 16, 16);
  const dotMat = new THREE.MeshBasicMaterial({
    color: 0x00eeff,
    transparent: true,
    opacity: 1.0,
  });
  const dot = new THREE.Mesh(dotGeo, dotMat);
  dot.position.copy(pos);
  group.add(dot);

  // Halo 1 (anneau pulsant)
  const ring1 = new THREE.Mesh(
    new THREE.RingGeometry(0.06, 0.075, 32),
    new THREE.MeshBasicMaterial({
      color: 0x00ddff,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  );
  ring1.position.copy(pos);
  ring1.lookAt(new THREE.Vector3(0, 0, 0));
  ring1.userData = { type: "ring", phase: 0 };
  group.add(ring1);

  // Halo 2 (anneau pulsant décalé)
  const ring2 = new THREE.Mesh(
    new THREE.RingGeometry(0.1, 0.12, 32),
    new THREE.MeshBasicMaterial({
      color: 0x0099cc,
      transparent: true,
      opacity: 0.5,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  );
  ring2.position.copy(pos);
  ring2.lookAt(new THREE.Vector3(0, 0, 0));
  ring2.userData = { type: "ring", phase: Math.PI };
  group.add(ring2);

  // Ligne verticale depuis le centre du globe vers le pin
  const linePts = [new THREE.Vector3(0, 0, 0), pos];
  const lineGeo = new THREE.BufferGeometry().setFromPoints(linePts);
  const lineMat = new THREE.LineBasicMaterial({
    color: 0x00aadd,
    transparent: true,
    opacity: 0.3,
    blending: THREE.AdditiveBlending,
  });
  group.add(new THREE.Line(lineGeo, lineMat));

  // Label texte
  const canvas2d = document.createElement("canvas");
  canvas2d.width = 256;
  canvas2d.height = 64;
  const ctx = canvas2d.getContext("2d")!;
  ctx.fillStyle = "transparent";
  ctx.clearRect(0, 0, 256, 64);
  ctx.font = "bold 22px 'Segoe UI', sans-serif";
  ctx.fillStyle = "#00eeff";
  ctx.shadowColor = "#00aaff";
  ctx.shadowBlur = 10;
  ctx.fillText("📍 Syndou", 10, 40);

  const texture = new THREE.CanvasTexture(canvas2d);
  const labelPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(0.6, 0.15),
    new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  const labelOffset = pos.clone().normalize().multiplyScalar(2.15);
  labelPlane.position.copy(labelOffset);
  labelPlane.lookAt(new THREE.Vector3(0, 0, 0).addScaledVector(pos, -1));
  group.add(labelPlane);

  return group;
}

// ── Atmosphère lumineuse ─────────────────────────────────────────────────────
function createAtmosphere(): THREE.Mesh {
  const geo = new THREE.SphereGeometry(2.05, 64, 64);
  const mat = new THREE.MeshBasicMaterial({
    color: 0x0044aa,
    transparent: true,
    opacity: 0.06,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  return new THREE.Mesh(geo, mat);
}

// ── Init Three.js ────────────────────────────────────────────────────────────
function initThree(): void {
  container = document.createElement("div");
  container.id = "carte-3d-container";
  Object.assign(container.style, {
    position: "fixed",
    inset: "0",
    zIndex: "999",
    background: "rgba(0,0,0,0)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    opacity: "0",
    transition: "opacity 0.8s ease",
    pointerEvents: "all",
  });
  document.body.appendChild(container);

  // Close button
  const closeBtn = document.createElement("button");
  closeBtn.textContent = "✕ fermer";
  Object.assign(closeBtn.style, {
    position: "absolute",
    top: "20px",
    right: "20px",
    background: "rgba(0,40,80,0.6)",
    border: "1px solid rgba(0,200,255,0.3)",
    borderRadius: "999px",
    color: "rgba(0,220,255,0.9)",
    fontSize: "13px",
    letterSpacing: "2px",
    padding: "8px 18px",
    cursor: "pointer",
    zIndex: "1001",
    backdropFilter: "blur(12px)",
    fontFamily: "inherit",
    textTransform: "uppercase",
  });
  closeBtn.addEventListener("click", hideCarte);
  container.appendChild(closeBtn);

  // Title
  const title = document.createElement("div");
  title.textContent = "VISION — Localisation";
  Object.assign(title.style, {
    position: "absolute",
    top: "22px",
    left: "50%",
    transform: "translateX(-50%)",
    color: "rgba(0,200,255,0.6)",
    fontSize: "12px",
    letterSpacing: "5px",
    textTransform: "uppercase",
    fontFamily: "inherit",
    fontWeight: "300",
    pointerEvents: "none",
  });
  container.appendChild(title);

  // Coords display
  const coordsEl = document.createElement("div");
  coordsEl.id = "vision-coords";
  Object.assign(coordsEl.style, {
    position: "absolute",
    bottom: "30px",
    left: "50%",
    transform: "translateX(-50%)",
    color: "rgba(0,200,255,0.5)",
    fontSize: "12px",
    letterSpacing: "3px",
    fontFamily: "monospace",
    textAlign: "center",
    pointerEvents: "none",
  });
  coordsEl.textContent = `lat: ${userLat.toFixed(4)}° · lon: ${userLon.toFixed(4)}°`;
  container.appendChild(coordsEl);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(
    55,
    window.innerWidth / window.innerHeight,
    0.1,
    100
  );
  camera.position.set(0, 0, 4.5);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x000000, 0);
  Object.assign(renderer.domElement.style, {
    position: "absolute",
    inset: "0",
    width: "100%",
    height: "100%",
  });
  container.appendChild(renderer.domElement);

  // Ambient light (gives depth)
  const ambientLight = new THREE.AmbientLight(0x003366, 1.5);
  scene.add(ambientLight);

  // Globe
  globe = createGlobePoints();
  scene.add(globe);

  // Atmosphere
  scene.add(createAtmosphere());

  // Initial pin at default location (will update after geolocation)
  pinGroup = createPin(userLat, userLon);
  scene.add(pinGroup);

  // Resize handler
  window.addEventListener("resize", onResize);

  // Mouse drag rotation
  setupDrag();
}

// ── Drag rotation ────────────────────────────────────────────────────────────
let isPointerDown = false;
let prevPointer = { x: 0, y: 0 };
let rotVelocity = { x: 0, y: 0 };

function setupDrag(): void {
  const el = renderer!.domElement;
  el.addEventListener("pointerdown", (e) => {
    isPointerDown = true;
    prevPointer = { x: e.clientX, y: e.clientY };
    rotVelocity = { x: 0, y: 0 };
  });
  el.addEventListener("pointermove", (e) => {
    if (!isPointerDown || !globe) return;
    const dx = e.clientX - prevPointer.x;
    const dy = e.clientY - prevPointer.y;
    rotVelocity.y = dx * 0.008;
    rotVelocity.x = dy * 0.008;
    globe.rotation.y += rotVelocity.y;
    globe.rotation.x += rotVelocity.x;
    if (pinGroup) {
      pinGroup.rotation.y += rotVelocity.y;
      pinGroup.rotation.x += rotVelocity.x;
    }
    prevPointer = { x: e.clientX, y: e.clientY };
  });
  el.addEventListener("pointerup", () => { isPointerDown = false; });
}

let autoRotY = 0;

// ── Animation loop ───────────────────────────────────────────────────────────
function animate(): void {
  animFrameId = requestAnimationFrame(animate);
  const t = Date.now() * 0.001;

  // Globe auto-rotation
  if (!isPointerDown && globe) {
    globe.rotation.y += 0.0012;
    if (pinGroup) {
      pinGroup.rotation.y += 0.0012;
    }
  }

  // Pin rings pulsation
  if (pinGroup) {
    pinGroup.children.forEach((child) => {
      if (child.userData?.type === "ring") {
        const phase = child.userData.phase as number;
        const scale = 1 + 0.45 * Math.abs(Math.sin(t * 1.8 + phase));
        child.scale.setScalar(scale);
        (child as THREE.Mesh<any, THREE.MeshBasicMaterial>).material.opacity =
          0.9 * (1 - Math.abs(Math.sin(t * 1.8 + phase)) * 0.6);
      }
    });
  }

  // Camera gentle float
  camera!.position.y = Math.sin(t * 0.3) * 0.08;
  camera!.lookAt(0, 0, 0);

  renderer!.render(scene!, camera!);
}

function onResize(): void {
  if (!camera || !renderer) return;
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

// ── Positionnement GPS ───────────────────────────────────────────────────────
function updatePosition(lat: number, lon: number): void {
  userLat = lat;
  userLon = lon;
  if (scene && pinGroup) {
    scene.remove(pinGroup);
    pinGroup = createPin(lat, lon);
    scene.add(pinGroup);
  }
  const coordsEl = document.getElementById("vision-coords");
  if (coordsEl) {
    coordsEl.textContent = `lat: ${lat.toFixed(4)}° · lon: ${lon.toFixed(4)}°`;
  }
}

function fetchGeolocation(): void {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      updatePosition(pos.coords.latitude, pos.coords.longitude);
    },
    () => {
      console.warn("[CARTE] Géolocalisation refusée, position par défaut.");
    },
    { timeout: 8000, maximumAge: 60000 }
  );
}

// ── Show / Hide ──────────────────────────────────────────────────────────────
export function showCarte(): void {
  if (isVisible) return;
  if (!container) {
    initThree();
  }
  isVisible = true;
  container!.style.display = "flex";
  requestAnimationFrame(() => {
    container!.style.opacity = "1";
    container!.style.background =
      "radial-gradient(ellipse at center, rgba(0,10,30,0.92) 0%, rgba(0,0,8,0.97) 100%)";
  });
  fetchGeolocation();
  if (!animFrameId) animate();
}

export function hideCarte(): void {
  if (!isVisible || !container) return;
  isVisible = false;
  container.style.opacity = "0";
  container.style.background = "rgba(0,0,0,0)";
  setTimeout(() => {
    if (container) container.style.display = "none";
    if (animFrameId !== null) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
  }, 800);
}

export function toggleCarte(): void {
  isVisible ? hideCarte() : showCarte();
}
