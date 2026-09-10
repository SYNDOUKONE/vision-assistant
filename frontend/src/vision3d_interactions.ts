/**
 * VISION — Modules 3D de Manipulation par Vision
 *
 * ═══════════════════════════════════════════════════════════
 *  MODULE 1 : Orbe Magnétique (Interaction bi-manuelle)
 *  MODULE 2 : Globe Terrestre 3D (Navigation géospatiale)
 *  MODULE 3 : Menu HUD Spatial Flottant (Laser + Air-Click)
 *  MODULE 4 : Cyber Data Cube 3D (Analyse données)
 * ═══════════════════════════════════════════════════════════
 *
 * Architecture :
 * - Chaque module expose init(), show(), hide(), update(landmarks)
 * - Les mains sont trackées via MediaPipe (2 mains max)
 * - Rendu WebGL via Three.js (scènes séparées superposées)
 * - Communication backend via WebSocket pour les actions (show/hide module, etc.)
 */

import * as THREE from "three";
import { Hands, Results, NormalizedLandmarkList } from "@mediapipe/hands";
import { Camera } from "@mediapipe/camera_utils";

// ─── Types partagés ───────────────────────────────────────────────────────────

export type ModuleId = "orbe_magnetique" | "globe3d" | "hud_menu" | "data_cube" | "galerie_holographique" | "light_painting" | "drone_pilot" | "mesh_sculpting";

export interface HandPoint {
  x: number; // 0-1 (normalisé caméra)
  y: number;
  z: number; // profondeur relative
}

export interface HandData {
  left:  HandPoint[] | null; // 21 landmarks
  right: HandPoint[] | null;
}

// ─── Gestionnaire principal ───────────────────────────────────────────────────

class Vision3DManager {
  private activeModule: ModuleId | null = null;
  private handData: HandData = { left: null, right: null };
  private modules: Map<ModuleId, Vision3DModule> = new Map();
  private overlayCanvas: HTMLCanvasElement | null = null;
  private overlayRenderer: THREE.WebGLRenderer | null = null;
  private overlayScene: THREE.Scene | null = null;
  private overlayCamera: THREE.PerspectiveCamera | null = null;
  private animFrameId: number | null = null;
  private hands: Hands | null = null;
  private mpCamera: Camera | null = null;
  private videoEl: HTMLVideoElement | null = null;
  private isTracking = false;
  private wsSender: ((data: any) => void) | null = null;

  init(wsSender: (data: any) => void): void {
    this.wsSender = wsSender;
    this.createOverlayCanvas();
    this.initModules();
    this.injectHUDControls();
  }

  private createOverlayCanvas(): void {
    this.overlayCanvas = document.createElement("canvas");
    this.overlayCanvas.id = "vision3d-overlay";
    this.overlayCanvas.style.cssText = `
      position: fixed;
      top: 0; left: 0;
      width: 100vw; height: 100vh;
      pointer-events: none;
      z-index: 500;
    `;
    document.body.appendChild(this.overlayCanvas);

    this.overlayRenderer = new THREE.WebGLRenderer({
      canvas: this.overlayCanvas,
      antialias: true,
      alpha: true,
    });
    this.overlayRenderer.setPixelRatio(window.devicePixelRatio);
    this.overlayRenderer.setSize(window.innerWidth, window.innerHeight);
    this.overlayRenderer.setClearColor(0x000000, 0);
    this.overlayRenderer.autoClear = false;

    this.overlayScene = new THREE.Scene();
    this.overlayCamera = new THREE.PerspectiveCamera(
      50,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    this.overlayCamera.position.set(0, 0, 5);

    window.addEventListener("resize", () => {
      if (!this.overlayRenderer || !this.overlayCamera) return;
      this.overlayRenderer.setSize(window.innerWidth, window.innerHeight);
      this.overlayCamera.aspect = window.innerWidth / window.innerHeight;
      this.overlayCamera.updateProjectionMatrix();
    });

    this.startRenderLoop();
  }

  private initModules(): void {
    if (!this.overlayScene || !this.overlayCamera) return;
    this.modules.set("orbe_magnetique", new OrbeMagnetiqueModule(this.overlayScene, this.overlayCamera));
    this.modules.set("globe3d", new Globe3DModule(this.overlayScene, this.overlayCamera));
    this.modules.set("hud_menu", new HUDMenuModule(this.overlayScene, this.overlayCamera, (action) => this.onHUDAction(action)));
    this.modules.set("data_cube", new DataCubeModule(this.overlayScene, this.overlayCamera));
    this.modules.set("galerie_holographique", new GalerieModule(this.overlayScene, this.overlayCamera, (track) => {
      if (this.wsSender) {
        this.wsSender({ action: "jouer_musique", nom: track, plateforme: "youtube" });
        showV3DNotification("▶ Musique : " + track);
      }
    }));
    this.modules.set("light_painting", new LightPaintingModule(this.overlayScene, this.overlayCamera));
    this.modules.set("drone_pilot", new DronePilotModule(this.overlayScene, this.overlayCamera));
    this.modules.set("mesh_sculpting", new MeshSculptingModule(this.overlayScene, this.overlayCamera));
  }

  private startRenderLoop(): void {
    const animate = () => {
      this.animFrameId = requestAnimationFrame(animate);
      if (!this.overlayRenderer || !this.overlayScene || !this.overlayCamera) return;
      this.overlayRenderer.clear();

      const active = this.activeModule ? this.modules.get(this.activeModule) : null;
      if (active) {
        active.update(this.handData);
      }
      this.overlayRenderer.render(this.overlayScene, this.overlayCamera);
    };
    animate();
  }

  async startTracking(): Promise<boolean> {
    if (this.isTracking) return true;
    try {
      if (!this.videoEl) {
        this.videoEl = document.createElement("video");
        this.videoEl.style.display = "none";
        document.body.appendChild(this.videoEl);
      }

      this.hands = new Hands({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
      });
      this.hands.setOptions({
        maxNumHands: 2,
        modelComplexity: 1,
        minDetectionConfidence: 0.65,
        minTrackingConfidence: 0.6,
      });
      this.hands.onResults((r) => this.onHandResults(r));

      this.mpCamera = new Camera(this.videoEl, {
        onFrame: async () => {
          if (this.videoEl && this.hands && this.isTracking) {
            await this.hands.send({ image: this.videoEl });
          }
        },
        width: 640,
        height: 480,
      });
      await this.mpCamera.start();
      this.isTracking = true;
      return true;
    } catch (e) {
      console.error("[VISION3D] Erreur tracking:", e);
      return false;
    }
  }

  stopTracking(): void {
    this.isTracking = false;
    this.mpCamera?.stop();
    this.mpCamera = null;
    this.hands?.close();
    this.hands = null;
  }

  private onHandResults(results: Results): void {
    this.handData = { left: null, right: null };
    if (!results.multiHandLandmarks) return;
    results.multiHandLandmarks.forEach((landmarks, i) => {
      const hand = results.multiHandedness?.[i]?.label?.toLowerCase();
      // MediaPipe flips left/right for mirrored camera
      const side = hand === "left" ? "right" : "left";
      this.handData[side] = landmarks as HandPoint[];
    });
  }

  showModule(id: ModuleId): void {
    // Cacher le module actif
    if (this.activeModule && this.activeModule !== id) {
      this.modules.get(this.activeModule)?.hide();
    }
    this.activeModule = id;
    this.modules.get(id)?.show();
    showV3DNotification(`▶ MODULE ACTIVÉ : ${MODULE_LABELS[id]}`);
  }

  hideCurrentModule(): void {
    if (this.activeModule) {
      this.modules.get(this.activeModule)?.hide();
      this.activeModule = null;
    }
    showV3DNotification("⬛ Module 3D fermé");
  }

  private onHUDAction(action: string): void {
    const moduleMap: Record<string, ModuleId> = {
      "orbe": "orbe_magnetique",
      "globe": "globe3d",
      "cube": "data_cube",
    };
    if (action === "fermer") {
      this.hideCurrentModule();
    } else if (moduleMap[action]) {
      this.showModule(moduleMap[action]);
    }
  }

  private injectHUDControls(): void {
    const container = document.createElement("div");
    container.id = "vision3d-controls";
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9998;
    `;

    const select = document.createElement("select");
    select.style.cssText = `
      padding: 10px 15px;
      background: rgba(10, 15, 30, 0.85);
      color: #fff;
      border: 1px solid rgba(100,150,255,0.5);
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      font-family: 'Space Grotesk', sans-serif;
      backdrop-filter: blur(10px);
      outline: none;
      box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    `;

    const modules = [
      { id: "none", label: "👁️ Aucun module (Désactivé)" },
      { id: "orbe_magnetique", label: "🔮 Orbe Magnétique" },
      { id: "globe3d",         label: "🌍 Globe 3D" },
      { id: "hud_menu",        label: "🎯 Menu HUD" },
      { id: "data_cube",       label: "📊 Data Cube" },
      { id: "galerie_holographique", label: "🖼️ Galerie Sonore" },
      { id: "light_painting",  label: "🎨 Pinceau 3D" },
      { id: "drone_pilot",     label: "🚀 Vaisseau" },
      { id: "mesh_sculpting",  label: "🌀 Sculpture 3D" }
    ];

    modules.forEach(({ id, label }) => {
      const opt = document.createElement("option");
      opt.value = id;
      opt.textContent = label;
      select.appendChild(opt);
    });

    select.addEventListener("change", async (e) => {
      const val = (e.target as HTMLSelectElement).value;
      if (!this.isTracking && val !== "none") {
        showV3DNotification("⏳ Activation du tracking...");
        await this.startTracking();
      }
      if (val === "none") {
        this.hideCurrentModule();
      } else {
        this.showModule(val as ModuleId);
      }
    });

    container.appendChild(select);
    document.body.appendChild(container);
  }

  destroy(): void {
    this.stopTracking();
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    this.overlayRenderer?.dispose();
    this.overlayCanvas?.remove();
  }
}

// ─── Labels HUD ───────────────────────────────────────────────────────────────

const MODULE_LABELS: Record<ModuleId, string> = {
  orbe_magnetique: "ORBE MAGNÉTIQUE",
  globe3d:         "GLOBE 3D",
  hud_menu:        "MENU SPATIAL HUD",
  data_cube:       "CYBER DATA CUBE",
  galerie_holographique: "GALERIE HOLOGRAPHIQUE",
  light_painting:  "PINCEAU DE LUMIÈRE 3D",
  drone_pilot:     "VAISSEAU VIRTUEL",
  mesh_sculpting:  "SCULPTURE 3D",
};

// ─── Interface de base pour les modules ──────────────────────────────────────

abstract class Vision3DModule {
  protected scene: THREE.Scene;
  protected camera: THREE.PerspectiveCamera;
  protected group: THREE.Group;
  protected visible = false;
  protected clock = new THREE.Clock();

  constructor(scene: THREE.Scene, camera: THREE.PerspectiveCamera) {
    this.scene = scene;
    this.camera = camera;
    this.group = new THREE.Group();
    this.group.visible = false;
    scene.add(this.group);
  }

  show(): void {
    this.visible = true;
    this.group.visible = true;
    this.onShow();
  }

  hide(): void {
    this.visible = false;
    this.group.visible = false;
    this.onHide();
  }

  abstract update(hands: HandData): void;
  protected onShow(): void {}
  protected onHide(): void {}

  /** Convertit un landmark normalisé (0-1) en coordonnée Three.js */
  protected lmToWorld(lm: HandPoint, scaleX = 6, scaleY = 4): THREE.Vector3 {
    return new THREE.Vector3(
      (0.5 - lm.x) * scaleX,
      (0.5 - lm.y) * scaleY,
      0
    );
  }

  /** Distance entre deux landmarks (world space) */
  protected handDistance(a: HandPoint, b: HandPoint): number {
    return new THREE.Vector3(a.x - b.x, a.y - b.y, a.z - b.z).length();
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 1 — ORBE MAGNÉTIQUE
// ═══════════════════════════════════════════════════════════════════════════════

class OrbeMagnetiqueModule extends Vision3DModule {
  private particles: THREE.Points | null = null;
  private N = 1800;
  private positions!: Float32Array;
  private basePositions!: Float32Array;
  private velocities!: Float32Array;
  private coreGlow: THREE.Mesh | null = null;
  private ringLeft: THREE.Mesh | null = null;
  private ringRight: THREE.Mesh | null = null;
  private shockwaveMesh: THREE.Mesh | null = null;
  private shockwaveActive = false;
  private shockwaveAge = 0;

  protected onShow(): void {
    if (!this.particles) this.build();
  }

  private build(): void {
    // ── Particules principales
    const geo = new THREE.BufferGeometry();
    this.positions = new Float32Array(this.N * 3);
    this.basePositions = new Float32Array(this.N * 3);
    this.velocities = new Float32Array(this.N * 3);

    for (let i = 0; i < this.N; i++) {
      const r = 0.4 + Math.random() * 1.6;
      const theta = Math.random() * Math.PI * 2;
      const phi   = Math.acos(2 * Math.random() - 1);
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);
      this.basePositions[i*3] = x;
      this.basePositions[i*3+1] = y;
      this.basePositions[i*3+2] = z;
      this.positions[i*3] = x;
      this.positions[i*3+1] = y;
      this.positions[i*3+2] = z;
      this.velocities[i*3]   = (Math.random()-0.5)*0.01;
      this.velocities[i*3+1] = (Math.random()-0.5)*0.01;
      this.velocities[i*3+2] = (Math.random()-0.5)*0.01;
    }
    geo.setAttribute("position", new THREE.BufferAttribute(this.positions, 3));

    const mat = new THREE.PointsMaterial({
      color: 0x00d4ff,
      size: 0.04,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    this.particles = new THREE.Points(geo, mat);
    this.group.add(this.particles);

    // ── Cœur lumineux central
    const coreGeo = new THREE.SphereGeometry(0.25, 32, 32);
    const coreMat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.6 });
    this.coreGlow = new THREE.Mesh(coreGeo, coreMat);
    this.group.add(this.coreGlow);

    // ── Anneaux de main (indicateurs de position)
    const ringGeo = new THREE.TorusGeometry(0.12, 0.015, 8, 32);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xffd700, transparent: true, opacity: 0.7 });
    this.ringLeft  = new THREE.Mesh(ringGeo, ringMat.clone());
    this.ringRight = new THREE.Mesh(ringGeo, ringMat.clone());
    this.ringLeft.visible = false;
    this.ringRight.visible = false;
    this.group.add(this.ringLeft, this.ringRight);

    // ── Shockwave
    const swGeo = new THREE.RingGeometry(0, 0.1, 48);
    const swMat = new THREE.MeshBasicMaterial({ color: 0xff6600, transparent: true, opacity: 0.9, side: THREE.DoubleSide });
    this.shockwaveMesh = new THREE.Mesh(swGeo, swMat);
    this.shockwaveMesh.visible = false;
    this.group.add(this.shockwaveMesh);
  }

  update(hands: HandData): void {
    if (!this.visible || !this.particles) return;
    const t = this.clock.getElapsedTime();
    const posArr = (this.particles.geometry.attributes.position as THREE.BufferAttribute).array as Float32Array;

    // ── Position main gauche
    let lPos: THREE.Vector3 | null = null;
    let rPos: THREE.Vector3 | null = null;

    if (hands.left) {
      lPos = this.lmToWorld(hands.left[9], 4, 3); // milieu de la main
      if (this.ringLeft) {
        this.ringLeft.visible = true;
        this.ringLeft.position.copy(lPos);
        this.ringLeft.rotation.y = t * 2;
      }
    } else {
      if (this.ringLeft) this.ringLeft.visible = false;
    }

    if (hands.right) {
      rPos = this.lmToWorld(hands.right[9], 4, 3);
      if (this.ringRight) {
        this.ringRight.visible = true;
        this.ringRight.position.copy(rPos);
        this.ringRight.rotation.y = -t * 2;
      }
    } else {
      if (this.ringRight) this.ringRight.visible = false;
    }

    // ── Comportement particules selon gestes
    let grabbing = false;
    let scaleFactor = 1.0;
    let shockwaveTriggered = false;

    if (lPos && rPos) {
      const dist = lPos.distanceTo(rPos);
      scaleFactor = Math.max(0.3, Math.min(2.5, dist * 0.8));

      // Pince (mains très proches) → shockwave
      if (dist < 0.5 && !this.shockwaveActive) {
        shockwaveTriggered = true;
        this.shockwaveActive = true;
        this.shockwaveAge = 0;
      }

      grabbing = true;
      const center = new THREE.Vector3().addVectors(lPos, rPos).multiplyScalar(0.5);
      this.group.position.lerp(center, 0.05);
    } else if (lPos || rPos) {
      // Une seule main : attirer l'orbe
      const hand = lPos || rPos!;
      this.group.position.lerp(hand, 0.04);
    } else {
      this.group.position.lerp(new THREE.Vector3(0, 0, 0), 0.03);
    }

    // ── Update particules
    for (let i = 0; i < this.N; i++) {
      const bx = this.basePositions[i*3]   * scaleFactor;
      const by = this.basePositions[i*3+1] * scaleFactor;
      const bz = this.basePositions[i*3+2] * scaleFactor;

      // Rotation orbitale
      const angle = t * 0.4 + (i / this.N) * Math.PI * 2;
      const rx = bx * Math.cos(angle * 0.1) - bz * Math.sin(angle * 0.1);
      const rz = bx * Math.sin(angle * 0.1) + bz * Math.cos(angle * 0.1);

      posArr[i*3]   += (rx - posArr[i*3])   * 0.04;
      posArr[i*3+1] += (by - posArr[i*3+1]) * 0.04;
      posArr[i*3+2] += (rz - posArr[i*3+2]) * 0.04;
    }
    (this.particles.geometry.attributes.position as THREE.BufferAttribute).needsUpdate = true;

    // ── Cœur pulsation
    if (this.coreGlow) {
      const pulse = 0.9 + Math.sin(t * 3) * 0.2;
      const s = scaleFactor * pulse * (grabbing ? 1.5 : 1.0);
      this.coreGlow.scale.setScalar(s);
      (this.coreGlow.material as THREE.MeshBasicMaterial).color.setHSL(
        0.55 + Math.sin(t * 0.5) * 0.1, 1, 0.6
      );
    }

    // ── Shockwave animation
    if (this.shockwaveMesh && this.shockwaveActive) {
      this.shockwaveAge += 0.04;
      const r = this.shockwaveAge * 2.5;
      this.shockwaveMesh.visible = true;
      const geo = new THREE.RingGeometry(r * 0.8, r, 48);
      this.shockwaveMesh.geometry.dispose();
      this.shockwaveMesh.geometry = geo;
      (this.shockwaveMesh.material as THREE.MeshBasicMaterial).opacity = Math.max(0, 0.9 - this.shockwaveAge * 0.6);

      if (this.shockwaveAge > 1.5) {
        this.shockwaveActive = false;
        this.shockwaveMesh.visible = false;
      }
    }

    this.group.rotation.y = t * 0.15;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 2 — GLOBE TERRESTRE 3D
// ═══════════════════════════════════════════════════════════════════════════════

class Globe3DModule extends Vision3DModule {
  private globe: THREE.Mesh | null = null;
  private wireframe: THREE.LineSegments | null = null;
  private atmosphere: THREE.Mesh | null = null;
  private markerGroup: THREE.Group = new THREE.Group();
  private lastHandPos: THREE.Vector3 | null = null;
  private rotationSpeed = new THREE.Vector2(0, 0);
  private zoomLevel = 1.0;
  private pinchStartDist = 0;
  private isPinching = false;
  private laserLine: THREE.Line | null = null;

  protected onShow(): void {
    if (!this.globe) this.build();
  }

  private build(): void {
    // ── Globe principal (shader géo)
    const geo = new THREE.SphereGeometry(1.2, 64, 64);

    const mat = new THREE.MeshPhongMaterial({
      color: 0x0a3060,
      emissive: 0x001540,
      shininess: 80,
      transparent: true,
      opacity: 0.92,
      wireframe: false,
    });
    this.globe = new THREE.Mesh(geo, mat);
    this.group.add(this.globe);

    // ── Wireframe réseau
    const wfGeo = new THREE.IcosahedronGeometry(1.22, 4);
    const wfMat = new THREE.LineBasicMaterial({ color: 0x0088ff, opacity: 0.2, transparent: true });
    this.wireframe = new THREE.LineSegments(new THREE.EdgesGeometry(wfGeo), wfMat);
    this.group.add(this.wireframe);

    // ── Atmosphère
    const atmGeo = new THREE.SphereGeometry(1.35, 32, 32);
    const atmMat = new THREE.MeshBasicMaterial({
      color: 0x0055cc,
      transparent: true,
      opacity: 0.08,
      side: THREE.BackSide,
    });
    this.atmosphere = new THREE.Mesh(atmGeo, atmMat);
    this.group.add(this.atmosphere);

    // ── Éclairage
    const ambient = new THREE.AmbientLight(0x223366, 0.8);
    const sun = new THREE.DirectionalLight(0x88ccff, 1.5);
    sun.position.set(5, 3, 5);
    this.group.add(ambient, sun);

    // ── Points chauds (capitales)
    const capitals = [
      { lat: 48.86,  lon: 2.35,    name: "Paris",    color: 0xffd700 },
      { lat: 40.71, lon: -74.00,   name: "New York",  color: 0x00d4ff },
      { lat: 35.68,  lon: 139.69,  name: "Tokyo",    color: 0xff3366 },
      { lat: -33.87, lon: 151.21,  name: "Sydney",   color: 0x66ff66 },
      { lat: 51.51, lon: -0.13,    name: "London",   color: 0xff9900 },
      { lat: 5.35,  lon: -4.02,    name: "Abidjan",  color: 0xff6600 },
      { lat: 12.36,  lon: -1.53,   name: "Ouagadougou", color: 0xffcc00 },
      { lat: 25.20,  lon: 55.27,   name: "Dubai",    color: 0x44ffdd },
    ];

    this.markerGroup = new THREE.Group();
    capitals.forEach(({ lat, lon, name, color }) => {
      const pos = this.latLonToXYZ(lat, lon, 1.24);
      const dotGeo = new THREE.SphereGeometry(0.025, 8, 8);
      const dotMat = new THREE.MeshBasicMaterial({ color });
      const dot = new THREE.Mesh(dotGeo, dotMat);
      dot.position.copy(pos);
      dot.userData = { name, lat, lon };
      this.markerGroup.add(dot);

      // Anneau pulsant
      const ringGeo = new THREE.RingGeometry(0.03, 0.055, 16);
      const ringMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.6, side: THREE.DoubleSide });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.copy(pos);
      ring.lookAt(new THREE.Vector3(0, 0, 0));
      this.markerGroup.add(ring);
    });
    this.globe.add(this.markerGroup);

    // ── Rayon laser (pointeur)
    const laserGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0, 0, -4),
    ]);
    const laserMat = new THREE.LineBasicMaterial({ color: 0xff2266, transparent: true, opacity: 0 });
    this.laserLine = new THREE.Line(laserGeo, laserMat);
    this.group.add(this.laserLine);
  }

  private latLonToXYZ(lat: number, lon: number, r: number): THREE.Vector3 {
    const phi   = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    return new THREE.Vector3(
      -r * Math.sin(phi) * Math.cos(theta),
       r * Math.cos(phi),
       r * Math.sin(phi) * Math.sin(theta)
    );
  }

  update(hands: HandData): void {
    if (!this.visible || !this.globe) return;
    const t = this.clock.getElapsedTime();

    // ── Pulsation des anneaux de capitales
    this.markerGroup.children.forEach((child, i) => {
      if (child instanceof THREE.Mesh && child.geometry instanceof THREE.RingGeometry) {
        (child.material as THREE.MeshBasicMaterial).opacity =
          0.3 + Math.abs(Math.sin(t * 2 + i * 0.5)) * 0.5;
      }
    });

    const hand = hands.right || hands.left;

    if (hand) {
      const indexTip  = hand[8];  // Tip index
      const thumbTip  = hand[4];  // Tip pouce
      const palmBase  = hand[0];  // Base de la main

      const handWorld = this.lmToWorld(palmBase, 5, 3.5);

      // ── Rotation : suivre le mouvement de la paume
      if (this.lastHandPos) {
        const dx = handWorld.x - this.lastHandPos.x;
        const dy = handWorld.y - this.lastHandPos.y;
        this.rotationSpeed.x = dy * 1.5;
        this.rotationSpeed.y = dx * 1.5;
      }
      this.lastHandPos = handWorld.clone();

      // ── Zoom : pince (pouce-index)
      const pinchDist = this.handDistance(thumbTip, indexTip);
      if (pinchDist < 0.06) {
        if (!this.isPinching) {
          this.isPinching = true;
          this.pinchStartDist = pinchDist;
        }
        const zoomDelta = (pinchDist - this.pinchStartDist) * 3;
        this.zoomLevel = Math.max(0.5, Math.min(3.0, this.zoomLevel + zoomDelta * 0.01));
      } else {
        this.isPinching = false;
      }

      // ── Laser pointeur (index déplié)
      const middleFolded = hand[12].y > hand[10].y;
      const ringFolded   = hand[16].y > hand[14].y;
      const indexUp      = hand[8].y < hand[6].y;
      if (indexUp && middleFolded && ringFolded && this.laserLine) {
        const tipWorld = this.lmToWorld(indexTip, 5, 3.5);
        const dir = tipWorld.clone().normalize().multiplyScalar(-4);
        const pts = [new THREE.Vector3(0, 0, 0), dir];
        this.laserLine.geometry.setFromPoints(pts);
        (this.laserLine.material as THREE.LineBasicMaterial).opacity = 0.85;
        this.laserLine.position.copy(tipWorld);
      } else if (this.laserLine) {
        (this.laserLine.material as THREE.LineBasicMaterial).opacity = 0;
      }
    } else {
      this.lastHandPos = null;
      if (this.laserLine) (this.laserLine.material as THREE.LineBasicMaterial).opacity = 0;
    }

    // ── Appliquer rotation (avec inertie)
    this.group.rotation.y += this.rotationSpeed.y;
    this.group.rotation.x += this.rotationSpeed.x;
    this.rotationSpeed.multiplyScalar(0.92); // friction

    // ── Auto-rotation lente si pas de main
    if (!hand) {
      this.group.rotation.y += 0.003;
    }

    // ── Zoom
    this.group.scale.setScalar(this.zoomLevel);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 3 — MENU HUD SPATIAL FLOTTANT
// ═══════════════════════════════════════════════════════════════════════════════

class HUDMenuModule extends Vision3DModule {
  private menuItems: THREE.Mesh[] = [];
  private laserLine: THREE.Line | null = null;
  private laserDot: THREE.Mesh | null = null;
  private hoveredIndex = -1;
  private onAction: (action: string) => void;
  private lastAirClickTime = 0;
  private selectionRings: THREE.Mesh[] = [];

  private readonly ITEMS = [
    { label: "🔮 ORBE",    action: "orbe",    color: 0x00d4ff, angle: 0 },
    { label: "🌍 GLOBE",   action: "globe",   color: 0x44ff88, angle: (Math.PI * 2) / 5 },
    { label: "📊 CUBE",    action: "cube",    color: 0xff6600, angle: (Math.PI * 4) / 5 },
    { label: "✖ FERMER",   action: "fermer",  color: 0xff2244, angle: (Math.PI * 6) / 5 },
    { label: "⚙ CONFIG",   action: "config",  color: 0xaaaaaa, angle: (Math.PI * 8) / 5 },
  ];

  constructor(scene: THREE.Scene, camera: THREE.PerspectiveCamera, onAction: (action: string) => void) {
    super(scene, camera);
    this.onAction = onAction;
  }

  protected onShow(): void {
    if (this.menuItems.length === 0) this.build();
    this.animateIn();
  }

  protected onHide(): void {
    this.menuItems.forEach(m => { m.scale.setScalar(0); });
  }

  private build(): void {
    const radius = 1.4;

    this.ITEMS.forEach(({ label, color, angle, action }, i) => {
      // ── Panneau hexagonal pour chaque item
      const shape = new THREE.Shape();
      const sides = 6;
      const size  = 0.28;
      for (let j = 0; j <= sides; j++) {
        const a = (j / sides) * Math.PI * 2;
        j === 0
          ? shape.moveTo(Math.cos(a) * size, Math.sin(a) * size)
          : shape.lineTo(Math.cos(a) * size, Math.sin(a) * size);
      }
      const geo = new THREE.ShapeGeometry(shape);
      const mat = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.25,
        side: THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(
        Math.cos(angle) * radius,
        Math.sin(angle) * radius,
        0
      );
      mesh.userData = { index: i, action, label, baseColor: color };
      mesh.scale.setScalar(0);
      this.group.add(mesh);
      this.menuItems.push(mesh);

      // ── Anneau de sélection
      const rGeo = new THREE.RingGeometry(0.26, 0.3, 24);
      const rMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, side: THREE.DoubleSide });
      const ring = new THREE.Mesh(rGeo, rMat);
      ring.position.copy(mesh.position);
      this.group.add(ring);
      this.selectionRings.push(ring);
    });

    // ── Laser pointeur
    const laserGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0, 0, -5),
    ]);
    this.laserLine = new THREE.Line(
      laserGeo,
      new THREE.LineBasicMaterial({ color: 0xff2266, transparent: true, opacity: 0.8 })
    );
    this.group.add(this.laserLine);

    // ── Point de ciblage (dot)
    const dotGeo = new THREE.SphereGeometry(0.04, 8, 8);
    const dotMat = new THREE.MeshBasicMaterial({ color: 0xff2266 });
    this.laserDot = new THREE.Mesh(dotGeo, dotMat);
    this.laserDot.visible = false;
    this.group.add(this.laserDot);
  }

  private animateIn(): void {
    this.menuItems.forEach((m, i) => {
      setTimeout(() => {
        m.scale.set(0, 0, 0);
        const target = { s: 1.0 };
        const tick = () => {
          target.s = Math.min(1.0, target.s);
          m.scale.setScalar(target.s);
          if (target.s < 1.0) { target.s += 0.08; requestAnimationFrame(tick); }
        };
        requestAnimationFrame(tick);
      }, i * 80);
    });
  }

  update(hands: HandData): void {
    if (!this.visible) return;
    const t = this.clock.getElapsedTime();
    const hand = hands.right || hands.left;

    // ── Rotation lente du menu
    this.group.rotation.z = Math.sin(t * 0.3) * 0.08;

    // ── Update items (pulsation)
    this.menuItems.forEach((m, i) => {
      const pulse = 1.0 + Math.sin(t * 2 + i) * 0.05;
      if (i !== this.hoveredIndex) m.scale.setScalar(pulse);

      // Rotation douce des hexagones
      m.rotation.z = t * 0.3 + i;
    });

    if (!hand) {
      if (this.laserLine) (this.laserLine.material as THREE.LineBasicMaterial).opacity = 0;
      if (this.laserDot) this.laserDot.visible = false;
      this.hoveredIndex = -1;
      this.selectionRings.forEach(r => (r.material as THREE.MeshBasicMaterial).opacity = 0);
      return;
    }

    // ── Détection pointage (index)
    const indexUp    = hand[8].y < hand[6].y;
    const middleFold = hand[12].y > hand[10].y;
    const ringFold   = hand[16].y > hand[14].y;
    const isPointing = indexUp && middleFold && ringFold;

    if (isPointing && this.laserLine) {
      const tip = this.lmToWorld(hand[8], 5, 3.5);
      const dir = tip.clone().normalize().multiplyScalar(-6);

      this.laserLine.geometry.setFromPoints([new THREE.Vector3(0,0,0), dir]);
      this.laserLine.position.copy(tip);
      (this.laserLine.material as THREE.LineBasicMaterial).opacity = 0.9;

      // ── Tester collision avec chaque item
      let closestIdx = -1;
      let closestDist = 0.45;

      this.menuItems.forEach((m, i) => {
        const dist = tip.distanceTo(new THREE.Vector3().addVectors(this.group.position, m.position));
        if (dist < closestDist) {
          closestDist = dist;
          closestIdx = i;
        }
      });

      // ── Hover effect
      if (closestIdx !== this.hoveredIndex) {
        // Reset précédent
        if (this.hoveredIndex >= 0) {
          const prev = this.menuItems[this.hoveredIndex];
          (prev.material as THREE.MeshBasicMaterial).opacity = 0.25;
          (this.selectionRings[this.hoveredIndex].material as THREE.MeshBasicMaterial).opacity = 0;
        }
        this.hoveredIndex = closestIdx;
        if (closestIdx >= 0) {
          const cur = this.menuItems[closestIdx];
          (cur.material as THREE.MeshBasicMaterial).opacity = 0.75;
          cur.scale.setScalar(1.3);
          (this.selectionRings[closestIdx].material as THREE.MeshBasicMaterial).opacity = 0.8;
          showV3DNotification(`► ${this.ITEMS[closestIdx].label}`);
        }
      }

      // ── Air-Click : pince rapide
      const thumbTip = hand[4];
      const pinchDist = this.handDistance(hand[8], thumbTip);
      if (pinchDist < 0.05 && this.hoveredIndex >= 0) {
        const now = Date.now();
        if (now - this.lastAirClickTime > 800) {
          this.lastAirClickTime = now;
          const item = this.ITEMS[this.hoveredIndex];
          showV3DNotification(`✅ SÉLECTIONNÉ : ${item.label}`);
          this.onAction(item.action);
          // Effet de clic
          this.menuItems[this.hoveredIndex].scale.setScalar(1.6);
        }
      }

      if (this.laserDot) {
        const endPt = tip.clone().add(dir.clone().normalize().multiplyScalar(
          closestIdx >= 0 ? tip.distanceTo(new THREE.Vector3().addVectors(this.group.position, this.menuItems[closestIdx].position)) : 4
        ));
        this.laserDot.position.copy(endPt);
        this.laserDot.visible = true;
      }
    } else {
      if (this.laserLine) (this.laserLine.material as THREE.LineBasicMaterial).opacity = 0;
      if (this.laserDot) this.laserDot.visible = false;
      this.hoveredIndex = -1;
      this.selectionRings.forEach(r => (r.material as THREE.MeshBasicMaterial).opacity = 0);
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 4 — CYBER DATA CUBE 3D
// ═══════════════════════════════════════════════════════════════════════════════

class DataCubeModule extends Vision3DModule {
  private cube: THREE.Group = new THREE.Group();
  private faces: THREE.Mesh[] = [];
  private wireframeCube: THREE.LineSegments | null = null;
  private dataHUD: HTMLDivElement | null = null;
  private rotVelocity = new THREE.Euler(0, 0, 0);
  private expandedFace = -1;
  private lastGrabPos: THREE.Vector3 | null = null;
  private glowLines: THREE.Line[] = [];
  private faceData = [
    { label: "CPU",        value: "87%",   color: 0x00d4ff, icon: "💻" },
    { label: "MÉMOIRE",    value: "62%",   color: 0x44ff88, icon: "🧠" },
    { label: "RÉSEAU",     value: "1.2Gb", color: 0xff6600, icon: "🌐" },
    { label: "DISQUE",     value: "340Go", color: 0xffd700, icon: "💾" },
    { label: "PROCESSUS",  value: "124",   color: 0xff3366, icon: "⚙️" },
    { label: "UPTIME",     value: "99.9%", color: 0x9966ff, icon: "⏱️" },
  ];

  protected onShow(): void {
    if (this.faces.length === 0) this.build();
    if (!this.dataHUD) this.buildHUD();
    if (this.dataHUD) this.dataHUD.style.display = "block";
    this.startDataAnimation();
  }

  protected onHide(): void {
    if (this.dataHUD) this.dataHUD.style.display = "none";
  }

  private build(): void {
    const size = 0.85;
    const halfSize = size / 2;

    // ── 6 faces du cube
    const faceConfigs = [
      { pos: new THREE.Vector3( halfSize, 0, 0), rot: new THREE.Euler(0,  Math.PI/2, 0) },
      { pos: new THREE.Vector3(-halfSize, 0, 0), rot: new THREE.Euler(0, -Math.PI/2, 0) },
      { pos: new THREE.Vector3(0,  halfSize, 0), rot: new THREE.Euler(-Math.PI/2, 0, 0) },
      { pos: new THREE.Vector3(0, -halfSize, 0), rot: new THREE.Euler( Math.PI/2, 0, 0) },
      { pos: new THREE.Vector3(0, 0,  halfSize), rot: new THREE.Euler(0, 0, 0) },
      { pos: new THREE.Vector3(0, 0, -halfSize), rot: new THREE.Euler(0, Math.PI, 0) },
    ];

    faceConfigs.forEach(({ pos, rot }, i) => {
      const geo = new THREE.PlaneGeometry(size * 0.95, size * 0.95);
      const mat = new THREE.MeshBasicMaterial({
        color: this.faceData[i].color,
        transparent: true,
        opacity: 0.18,
        side: THREE.DoubleSide,
      });
      const face = new THREE.Mesh(geo, mat);
      face.position.copy(pos);
      face.rotation.copy(rot);
      face.userData = { index: i, baseOpacity: 0.18 };
      this.cube.add(face);
      this.faces.push(face);
    });

    // ── Wireframe brillant
    const wfGeo = new THREE.BoxGeometry(size, size, size);
    const wfMat = new THREE.LineBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.6 });
    this.wireframeCube = new THREE.LineSegments(new THREE.EdgesGeometry(wfGeo), wfMat);
    this.cube.add(this.wireframeCube);

    // ── Lignes de données animées (cyber effect)
    for (let i = 0; i < 12; i++) {
      const pts = [
        new THREE.Vector3((Math.random()-0.5)*size, (Math.random()-0.5)*size, (Math.random()-0.5)*size),
        new THREE.Vector3((Math.random()-0.5)*size, (Math.random()-0.5)*size, (Math.random()-0.5)*size),
      ];
      const lGeo = new THREE.BufferGeometry().setFromPoints(pts);
      const lMat = new THREE.LineBasicMaterial({
        color: this.faceData[i % 6].color,
        transparent: true,
        opacity: 0.3,
      });
      const line = new THREE.Line(lGeo, lMat);
      this.cube.add(line);
      this.glowLines.push(line);
    }

    this.group.add(this.cube);

    // ── Lueur centrale
    const glowGeo = new THREE.OctahedronGeometry(0.25, 2);
    const glowMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.15 });
    const glowMesh = new THREE.Mesh(glowGeo, glowMat);
    this.cube.add(glowMesh);
  }

  private buildHUD(): void {
    this.dataHUD = document.createElement("div");
    this.dataHUD.id = "data-cube-hud";
    this.dataHUD.style.cssText = `
      position: fixed;
      top: 50%;
      right: 20px;
      transform: translateY(-50%);
      z-index: 9000;
      display: flex;
      flex-direction: column;
      gap: 6px;
      pointer-events: none;
    `;

    this.faceData.forEach((data, i) => {
      const row = document.createElement("div");
      row.id = `data-cube-row-${i}`;
      row.style.cssText = `
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        background: rgba(5, 10, 25, 0.75);
        border: 1px solid ${this.hexToCSS(data.color)};
        border-radius: 8px;
        backdrop-filter: blur(8px);
        font-family: 'Space Grotesk', monospace;
        font-size: 11px;
        color: #fff;
        min-width: 150px;
        opacity: 0.6;
        transition: opacity 0.3s ease;
      `;
      row.innerHTML = `
        <span style="font-size:14px">${data.icon}</span>
        <span style="color:${this.hexToCSS(data.color)};font-weight:700;letter-spacing:1px">${data.label}</span>
        <span id="data-cube-val-${i}" style="margin-left:auto;color:#fff;font-weight:600">${data.value}</span>
      `;
      this.dataHUD!.appendChild(row);
    });

    document.body.appendChild(this.dataHUD);
  }

  private hexToCSS(hex: number): string {
    return `#${hex.toString(16).padStart(6, "0")}`;
  }

  private startDataAnimation(): void {
    const animate = () => {
      if (!this.visible) return;
      // Simuler des données qui changent
      this.faceData.forEach((data, i) => {
        const valEl = document.getElementById(`data-cube-val-${i}`);
        if (valEl) {
          if (data.label === "CPU")       valEl.textContent = `${(70 + Math.random() * 25).toFixed(0)}%`;
          if (data.label === "MÉMOIRE")   valEl.textContent = `${(50 + Math.random() * 30).toFixed(0)}%`;
          if (data.label === "RÉSEAU")    valEl.textContent = `${(0.5 + Math.random() * 2).toFixed(1)}Gb`;
          if (data.label === "PROCESSUS") valEl.textContent = `${(100 + Math.floor(Math.random() * 50))}`;
          if (data.label === "UPTIME")    valEl.textContent = `${(99 + Math.random() * 0.9).toFixed(1)}%`;
        }
      });
      setTimeout(animate, 1200);
    };
    animate();
  }

  update(hands: HandData): void {
    if (!this.visible) return;
    const t = this.clock.getElapsedTime();
    const hand = hands.right || hands.left;

    // ── Lignes de données animées
    this.glowLines.forEach((line, i) => {
      (line.material as THREE.LineBasicMaterial).opacity =
        0.1 + Math.abs(Math.sin(t * 1.5 + i * 0.7)) * 0.4;
    });

    // ── Faces pulsation
    this.faces.forEach((face, i) => {
      const base = face.userData.baseOpacity as number;
      const pulse = base + Math.sin(t * 2 + i) * 0.06;
      (face.material as THREE.MeshBasicMaterial).opacity = Math.max(0.05, pulse);
    });

    if (hand) {
      const fist = this.isFist(hand);
      const palmPos = this.lmToWorld(hand[9], 5, 3.5);

      if (fist) {
        // ── Attraper et tourner le cube
        if (this.lastGrabPos) {
          const dx = palmPos.x - this.lastGrabPos.x;
          const dy = palmPos.y - this.lastGrabPos.y;
          this.rotVelocity.x = dy * 2;
          this.rotVelocity.y = dx * 2;
          this.cube.rotation.x += this.rotVelocity.x;
          this.cube.rotation.y += this.rotVelocity.y;
        }
        this.lastGrabPos = palmPos.clone();

        // Indication visuelle "grab"
        if (this.wireframeCube) {
          (this.wireframeCube.material as THREE.LineBasicMaterial).color.setHex(0xffd700);
          (this.wireframeCube.material as THREE.LineBasicMaterial).opacity = 1.0;
        }

        // Highlight dans le HUD
        if (this.dataHUD) {
          this.dataHUD.querySelectorAll("div").forEach((el: Element) => {
            (el as HTMLElement).style.opacity = "1";
          });
        }
      } else {
        this.lastGrabPos = null;
        if (this.wireframeCube) {
          (this.wireframeCube.material as THREE.LineBasicMaterial).color.setHex(0x00d4ff);
          (this.wireframeCube.material as THREE.LineBasicMaterial).opacity = 0.6;
        }
        if (this.dataHUD) {
          this.dataHUD.querySelectorAll("div").forEach((el: Element) => {
            (el as HTMLElement).style.opacity = "0.6";
          });
        }

        // ── Zoom avec pince
        const pinchDist = this.handDistance(hand[4], hand[8]);
        const targetScale = Math.max(0.6, Math.min(2.0, 1 + (0.05 - pinchDist) * 10));
        this.group.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);
      }

      // ── Auto-rotation vers la main
      const targetRot = new THREE.Euler(
        Math.atan2(palmPos.y, 3),
        Math.atan2(palmPos.x, 3),
        0
      );
      this.group.position.lerp(palmPos.clone().multiplyScalar(0.2), 0.05);
    } else {
      this.lastGrabPos = null;
      // Rotation inertielle
      this.cube.rotation.y += this.rotVelocity.y;
      this.cube.rotation.x += this.rotVelocity.x;
      this.rotVelocity.x *= 0.94;
      this.rotVelocity.y *= 0.94;

      // Retour au centre
      this.group.position.lerp(new THREE.Vector3(0, 0, 0), 0.03);
      this.group.scale.lerp(new THREE.Vector3(1, 1, 1), 0.05);
    }

    // ── Rotation passive
    if (!hand || !this.isFist(hand)) {
      this.cube.rotation.y += 0.005;
    }
  }

  private isFist(lm: HandPoint[]): boolean {
    return (
      lm[8].y > lm[6].y &&
      lm[12].y > lm[10].y &&
      lm[16].y > lm[14].y &&
      lm[20].y > lm[18].y
    );
  }
}

// ─── Notification HUD partagée ────────────────────────────────────────────────

let v3dNotifEl: HTMLDivElement | null = null;
let v3dNotifTimer: ReturnType<typeof setTimeout> | null = null;

function showV3DNotification(text: string, duration = 2500): void {
  if (!v3dNotifEl) {
    v3dNotifEl = document.createElement("div");
    v3dNotifEl.id = "vision3d-notification";
    v3dNotifEl.style.cssText = `
      position: fixed;
      bottom: 120px;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      z-index: 9999;
      padding: 9px 20px;
      background: rgba(5, 10, 30, 0.88);
      border: 1px solid rgba(0, 212, 255, 0.5);
      border-radius: 18px;
      color: #00d4ff;
      font-family: 'Space Grotesk', monospace;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1.2px;
      text-transform: uppercase;
      backdrop-filter: blur(12px);
      box-shadow: 0 0 20px rgba(0,212,255,0.15);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s ease, transform 0.3s ease;
    `;
    document.body.appendChild(v3dNotifEl);
  }

  if (v3dNotifTimer) clearTimeout(v3dNotifTimer);
  v3dNotifEl.textContent = text;
  v3dNotifEl.style.opacity = "1";
  v3dNotifEl.style.transform = "translateX(-50%) translateY(0)";

  v3dNotifTimer = setTimeout(() => {
    if (v3dNotifEl) {
      v3dNotifEl.style.opacity = "0";
      v3dNotifEl.style.transform = "translateX(-50%) translateY(20px)";
    }
  }, duration);
}

// ─── Export singleton ─────────────────────────────────────────────────────────

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 5 — GALERIE HOLOGRAPHIQUE SONORE
// ═══════════════════════════════════════════════════════════════════════════════

class GalerieModule extends Vision3DModule {
  private panels: THREE.Mesh[] = [];
  private carouselRot = 0;
  private targetRot = 0;
  private lastHandX = 0;
  private isGrabbing = false;
  private isPinching = false;
  private activePanel: THREE.Mesh | null = null;
  private onPlaySound: (track: string) => void;

  constructor(scene: THREE.Scene, camera: THREE.PerspectiveCamera, onPlaySound: (track: string) => void) {
    super(scene, camera);
    this.onPlaySound = onPlaySound;
  }

  protected onShow(): void {
    if (this.panels.length === 0) this.build();
    this.targetRot = 0;
    this.carouselRot = 0;
  }

  private build(): void {
    const tracks = ["Cyberpunk OST", "Synthwave Mix", "Epic Orchestral", "Lofi Chill", "Space Ambient", "Hans Zimmer", "86 OST", "Valkyrie Apocalypse"];
    const numPanels = tracks.length;
    const radius = 2.2;
    for (let i = 0; i < numPanels; i++) {
      const canvas = document.createElement("canvas");
      canvas.width = 512;
      canvas.height = 256;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = `hsl(${(i / numPanels) * 360}, 80%, 15%)`;
      ctx.fillRect(0, 0, 512, 256);
      ctx.fillStyle = "white";
      ctx.font = "bold 40px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(tracks[i], 256, 128);
      ctx.strokeStyle = "rgba(255,255,255,0.5)";
      ctx.lineWidth = 10;
      ctx.strokeRect(0, 0, 512, 256);

      const tex = new THREE.CanvasTexture(canvas);
      const geo = new THREE.PlaneGeometry(1.2, 0.6);
      const mat = new THREE.MeshBasicMaterial({
        map: tex,
        transparent: true,
        opacity: 0.7,
        side: THREE.DoubleSide
      });
      const panel = new THREE.Mesh(geo, mat);
      const angle = (i / numPanels) * Math.PI * 2;
      panel.position.set(Math.sin(angle) * radius, 0, Math.cos(angle) * radius);
      panel.lookAt(0, 0, 0);
      panel.userData = { angle, basePos: panel.position.clone(), trackName: tracks[i] };
      this.panels.push(panel);
      this.group.add(panel);
    }
    this.group.position.set(0, 0, -2);
  }

  update(hands: HandData): void {
    if (!this.visible) return;
    const hand = hands.right || hands.left;

    if (hand) {
      const palmPos = this.lmToWorld(hand[9], 5, 3.5);
      const isFist = (hand[8].y > hand[6].y && hand[12].y > hand[10].y);

      if (isFist) {
        if (!this.isGrabbing) {
          this.isGrabbing = true;
          this.lastHandX = palmPos.x;
        } else {
          const dx = palmPos.x - this.lastHandX;
          this.targetRot += dx * 0.5;
          this.lastHandX = palmPos.x;
        }
      } else {
        this.isGrabbing = false;
        
        // Sélection avec l'Index Pointé (index seul levé)
        const isIndexUp = this.handDistance(hand[8], hand[5]) > 0.08 && this.handDistance(hand[12], hand[9]) < 0.08;
        if (isIndexUp) {
          if (!this.isPinching && this.activePanel) {
            this.isPinching = true;
            this.onPlaySound(this.activePanel.userData.trackName);
            // Animation flash vert
            (this.activePanel.material as THREE.MeshBasicMaterial).color.setHex(0x55ff55);
            setTimeout(() => {
              if (this.activePanel) (this.activePanel.material as THREE.MeshBasicMaterial).color.setHex(0xffffff);
            }, 300);
          }
        } else {
          this.isPinching = false;
        }
      }
    } else {
      this.isGrabbing = false;
      this.isPinching = false;
    }

    this.carouselRot += (this.targetRot - this.carouselRot) * 0.1;
    this.group.rotation.y = this.carouselRot;

    // Highlight center panel
    this.activePanel = null;
    this.panels.forEach(p => {
      const worldPos = new THREE.Vector3();
      p.getWorldPosition(worldPos);
      if (worldPos.z > 0 && Math.abs(worldPos.x) < 0.5) {
        this.activePanel = p;
        p.scale.lerp(new THREE.Vector3(1.3, 1.3, 1.3), 0.1);
        (p.material as THREE.MeshBasicMaterial).opacity = 1;
      } else {
        p.scale.lerp(new THREE.Vector3(1, 1, 1), 0.1);
        (p.material as THREE.MeshBasicMaterial).opacity = 0.4;
      }
    });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 6 — PINCEAU DE LUMIÈRE 3D (LIGHT PAINTING)
// ═══════════════════════════════════════════════════════════════════════════════

class LightPaintingModule extends Vision3DModule {
  private particles: THREE.Mesh[] = [];
  private currentColor = 0x00d4ff;
  private particleGeo = new THREE.SphereGeometry(0.04, 8, 8);

  protected onShow(): void {
    this.currentColor = 0x00d4ff;
  }

  protected onHide(): void {
    this.clearLines();
  }

  private clearLines() {
    this.particles.forEach(p => {
      this.group.remove(p);
      (p.material as THREE.Material).dispose();
    });
    this.particles = [];
  }

  update(hands: HandData): void {
    if (!this.visible) return;
    const hand = hands.right || hands.left;

    if (hand) {
      // Effacer tout si main grande ouverte (distance bout des doigts > 0.15)
      const isHandOpen = this.handDistance(hand[4], hand[20]) > 0.15 && this.handDistance(hand[8], hand[0]) > 0.15;
      
      if (isHandOpen) {
        this.clearLines();
      } else {
        // Index levé
        const isIndexUp = this.handDistance(hand[8], hand[5]) > 0.08 && this.handDistance(hand[12], hand[9]) < 0.08;
        if (isIndexUp) {
          const tip = this.lmToWorld(hand[8], 8, 5);
          const mat = new THREE.MeshBasicMaterial({ color: this.currentColor, transparent: true, opacity: 0.9 });
          const p = new THREE.Mesh(this.particleGeo, mat);
          p.position.copy(tip);
          this.group.add(p);
          this.particles.push(p);

          if (this.particles.length > 300) {
            const old = this.particles.shift();
            if (old) {
              this.group.remove(old);
              (old.material as THREE.Material).dispose();
            }
          }
        }
        
        // Changement de couleur avec pouce+majeur
        if (this.handDistance(hand[4], hand[12]) < 0.04) this.currentColor = 0xff3366;
        if (this.handDistance(hand[4], hand[16]) < 0.04) this.currentColor = 0x44ff88;
      }
    }

    // Rotation douce de l'ensemble de l'œuvre
    this.group.rotation.y += 0.002;
    // Fade out
    this.particles.forEach(p => {
       const m = p.material as THREE.MeshBasicMaterial;
       m.opacity *= 0.995;
    });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 7 — PILOTE DE VAISSEAU
// ═══════════════════════════════════════════════════════════════════════════════

class DronePilotModule extends Vision3DModule {
  private ship: THREE.Group = new THREE.Group();
  private thrusters: THREE.Points | null = null;
  private tData = { pos: new Float32Array(300), vel: new Float32Array(300) };

  protected onShow(): void {
    if (this.ship.children.length === 0) this.build();
  }

  private build(): void {
    // Vaisseau style Wireframe
    const bodyGeo = new THREE.ConeGeometry(0.3, 1, 4);
    bodyGeo.rotateX(Math.PI / 2);
    const bodyMat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, wireframe: true });
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    this.ship.add(body);

    const wingGeo = new THREE.BoxGeometry(1.2, 0.05, 0.4);
    const wing = new THREE.Mesh(wingGeo, bodyMat);
    wing.position.set(0, 0, -0.2);
    this.ship.add(wing);

    this.group.add(this.ship);

    // Réacteurs (Particules)
    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute("position", new THREE.BufferAttribute(this.tData.pos, 3));
    const pMat = new THREE.PointsMaterial({ color: 0xff6600, size: 0.05, transparent: true, blending: THREE.AdditiveBlending });
    this.thrusters = new THREE.Points(pGeo, pMat);
    this.thrusters.position.set(0, 0, -0.6);
    this.ship.add(this.thrusters);
  }

  update(hands: HandData): void {
    if (!this.visible) return;
    const hand = hands.right || hands.left;
    let boost = false;

    if (hand) {
      // Inclinaison de la paume (Index base vs Pinky base, et poignet vs milieu)
      const dx = hand[17].x - hand[5].x; // Roll
      const dy = hand[9].y - hand[0].y;  // Pitch

      this.ship.rotation.z = -dx * 5;
      this.ship.rotation.x = -dy * 3;

      // Poing fermé = Boost
      const isFist = hand[8].y > hand[6].y && hand[12].y > hand[10].y;
      if (isFist) boost = true;
    } else {
      this.ship.rotation.set(0, 0, 0);
    }

    // Animation Particules
    if (this.thrusters) {
      const pos = this.thrusters.geometry.attributes.position.array as Float32Array;
      for (let i = 0; i < 100; i++) {
        if (pos[i*3+2] < -1.5 || (pos[i*3] === 0 && pos[i*3+2] === 0)) {
          pos[i*3] = (Math.random() - 0.5) * 0.2;
          pos[i*3+1] = (Math.random() - 0.5) * 0.2;
          pos[i*3+2] = 0;
          this.tData.vel[i*3+2] = -0.05 - Math.random() * (boost ? 0.2 : 0.05);
        }
        pos[i*3+2] += this.tData.vel[i*3+2];
      }
      this.thrusters.geometry.attributes.position.needsUpdate = true;
      (this.thrusters.material as THREE.PointsMaterial).color.setHex(boost ? 0x00d4ff : 0xff6600);
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 8 — SCULPTURE 3D
// ═══════════════════════════════════════════════════════════════════════════════

class MeshSculptingModule extends Vision3DModule {
  private sphere: THREE.Mesh | null = null;
  private origVertices: Float32Array | null = null;

  protected onShow(): void {
    if (!this.sphere) this.build();
  }

  private build(): void {
    const geo = new THREE.SphereGeometry(1.2, 64, 64);
    this.origVertices = new Float32Array(geo.attributes.position.array);
    const mat = new THREE.MeshPhongMaterial({
      color: 0xaa22ff, emissive: 0x220044, shininess: 100, wireframe: true, transparent: true, opacity: 0.8
    });
    this.sphere = new THREE.Mesh(geo, mat);
    this.group.add(this.sphere);
    
    const ambient = new THREE.AmbientLight(0x404040);
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(2, 2, 5);
    this.group.add(ambient, light);
  }

  update(hands: HandData): void {
    if (!this.visible || !this.sphere || !this.origVertices) return;
    
    const geo = this.sphere.geometry as THREE.BufferGeometry;
    const pos = geo.attributes.position;
    const hand = hands.right || hands.left;

    // Retour progressif à la forme d'origine (effet élastique)
    for (let i = 0; i < pos.count; i++) {
      pos.setX(i, pos.getX(i) + (this.origVertices[i*3] - pos.getX(i)) * 0.05);
      pos.setY(i, pos.getY(i) + (this.origVertices[i*3+1] - pos.getY(i)) * 0.05);
      pos.setZ(i, pos.getZ(i) + (this.origVertices[i*3+2] - pos.getZ(i)) * 0.05);
    }

    if (hand) {
      const palmWorld = this.lmToWorld(hand[9], 4, 3);
      
      // Raycasting manuel basique depuis la main
      for (let i = 0; i < pos.count; i++) {
        const vx = pos.getX(i);
        const vy = pos.getY(i);
        const vz = pos.getZ(i);
        const dist = Math.sqrt((vx - palmWorld.x)**2 + (vy - palmWorld.y)**2 + (vz - palmWorld.z)**2);
        
        if (dist < 0.6) {
          const force = (0.6 - dist) * 0.2;
          pos.setX(i, vx - (palmWorld.x - vx) * force);
          pos.setY(i, vy - (palmWorld.y - vy) * force);
          pos.setZ(i, vz - (palmWorld.z - vz) * force);
        }
      }
    }

    pos.needsUpdate = true;
    this.sphere.rotation.y += 0.005;
  }
}

export const vision3D = new Vision3DManager();
export { showV3DNotification };
