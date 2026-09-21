/**
 * VISION — Gestionnaire de Fond d'Écran
 *
 * - Panneau de sélection de fond d'écran avec images pré-proposées + upload custom
 * - Contrôle de l'opacité et persistance du fond d'écran pour l'Orbe
 */

// ── Types ─────────────────────────────────────────────────────────────────────
export type WallpaperState = { src: string | null; opacity: number };

// ── Wallpapers pré-définis ────────────────────────────────────────────────────
const PRESETS: Array<{ id: string; label: string; src: string; thumb: string }> = [
  {
    id: "vision_pedestal",
    label: "VISION Command Center",
    src: "/wallpapers/vision_pedestal.jpg",
    thumb: "/wallpapers/vision_pedestal.jpg",
  },
  {
    id: "cybercity",
    label: "Cyberpunk City",
    src: "/wallpapers/cybercity.jpg",
    thumb: "/wallpapers/cybercity.jpg",
  },
  {
    id: "space_nebula",
    label: "Nébuleuse Spatiale",
    src: "/wallpapers/space_nebula.jpg",
    thumb: "/wallpapers/space_nebula.jpg",
  },
  {
    id: "matrix_datastream",
    label: "Matrix DataStream",
    src: "/wallpapers/matrix_datastream.jpg",
    thumb: "/wallpapers/matrix_datastream.jpg",
  },
  {
    id: "none",
    label: "Aucun (Défaut)",
    src: "",
    thumb: "",
  },
];

// ── State ─────────────────────────────────────────────────────────────────────
let currentWallpaper: string | null = null;
let wallpaperOpacity = 0.45;

// ── DOM ───────────────────────────────────────────────────────────────────────
let wallpaperOverlayEl: HTMLDivElement | null = null;
let wallpaperPanelEl: HTMLDivElement | null = null;

// ── Init ─────────────────────────────────────────────────────────────────────
export function initWallpaperSystem(): void {
  // Créer l'overlay de fond d'écran (derrière l'orbe)
  wallpaperOverlayEl = document.createElement("div");
  wallpaperOverlayEl.id = "wallpaper-overlay";
  document.body.insertBefore(wallpaperOverlayEl, document.body.firstChild);

  // Créer le bouton d'ouverture du panneau wallpaper (top-right HUD)
  const wallpaperBtn = document.createElement("button");
  wallpaperBtn.id = "wallpaper-open-btn";
  wallpaperBtn.title = "Changer le fond d'écran";
  wallpaperBtn.className = "hud-btn";
  wallpaperBtn.innerHTML = "🖼️ <span>FOND</span>";

  const rightGroup = document.querySelector("#top-hud-bar .hud-right");
  if (rightGroup) {
    rightGroup.insertBefore(wallpaperBtn, rightGroup.firstChild);
  } else {
    document.body.appendChild(wallpaperBtn);
  }
  wallpaperBtn.addEventListener("click", openWallpaperPanel);

  // Créer le panneau de sélection
  wallpaperPanelEl = document.createElement("div");
  wallpaperPanelEl.id = "wallpaper-panel";
  wallpaperPanelEl.classList.add("wallpaper-panel-hidden");
  wallpaperPanelEl.innerHTML = buildPanelHTML();
  document.body.appendChild(wallpaperPanelEl);

  // Listeners internes au panneau
  bindPanelListeners();

  // Restaurer depuis localStorage
  const saved = localStorage.getItem("vision_wallpaper");
  if (saved) applyWallpaper(saved);

  const savedOpacity = localStorage.getItem("vision_wallpaper_opacity");
  if (savedOpacity) {
    wallpaperOpacity = parseFloat(savedOpacity);
    updateWallpaperOpacity(wallpaperOpacity);
  }
}

// ── HTML du panneau wallpaper ─────────────────────────────────────────────────
function buildPanelHTML(): string {
  const presetsHTML = PRESETS.map(p => {
    if (p.id === "none") {
      return `
        <div class="wp-preset-card wp-preset-none" data-src="" data-id="none" role="button" tabindex="0">
          <div class="wp-none-icon">✕</div>
          <div class="wp-preset-label">${p.label}</div>
        </div>`;
    }
    return `
      <div class="wp-preset-card" data-src="${p.src}" data-id="${p.id}" role="button" tabindex="0">
        <img src="${p.thumb}" alt="${p.label}" loading="lazy" />
        <div class="wp-preset-label">${p.label}</div>
        <div class="wp-preset-check">✓</div>
      </div>`;
  }).join("");

  return `
    <div class="wp-panel-inner">
      <div class="wp-panel-header">
        <div class="wp-panel-title">
          <span class="wp-panel-icon">🖼️</span>
          <span>FOND D'ÉCRAN</span>
        </div>
        <button class="wp-close-btn" id="wp-close-btn">✕</button>
      </div>

      <div class="wp-section-label">Préréglages VISION</div>
      <div class="wp-presets-grid" id="wp-presets-grid">
        ${presetsHTML}
      </div>

      <div class="wp-section-label">Ajouter une image personnalisée</div>
      <div class="wp-upload-zone" id="wp-upload-zone">
        <input type="file" id="wp-file-input" accept="image/*" style="display:none" />
        <div class="wp-upload-content">
          <div class="wp-upload-icon">⬆️</div>
          <div class="wp-upload-text">Glisser-déposer ou cliquer pour choisir</div>
          <div class="wp-upload-hint">JPG, PNG, WEBP, GIF</div>
        </div>
        <div class="wp-custom-preview" id="wp-custom-preview" style="display:none">
          <img id="wp-custom-img" src="" alt="Aperçu" />
          <button class="wp-custom-remove" id="wp-custom-remove">✕</button>
        </div>
      </div>

      <div class="wp-section-label">Opacité du fond <span id="wp-opacity-value">${Math.round(wallpaperOpacity * 100)}%</span></div>
      <input type="range" id="wp-opacity-slider" class="wp-opacity-slider" min="10" max="95" value="${Math.round(wallpaperOpacity * 100)}" />
    </div>
  `;
}

// ── Listeners du panneau ──────────────────────────────────────────────────────
function bindPanelListeners(): void {
  if (!wallpaperPanelEl) return;

  // Fermer
  wallpaperPanelEl.querySelector("#wp-close-btn")?.addEventListener("click", closeWallpaperPanel);

  // Clic hors du panneau
  document.addEventListener("click", (e) => {
    const panel = wallpaperPanelEl;
    const openBtn = document.getElementById("wallpaper-open-btn");
    if (panel && !panel.contains(e.target as Node) && e.target !== openBtn) {
      if (!panel.classList.contains("wallpaper-panel-hidden")) {
        closeWallpaperPanel();
      }
    }
  });

  // Presets
  wallpaperPanelEl.querySelectorAll(".wp-preset-card").forEach(card => {
    card.addEventListener("click", () => {
      const src = (card as HTMLElement).dataset.src || "";
      applyWallpaper(src);
      updatePresetsUI(src);
      localStorage.setItem("vision_wallpaper", src);
    });
  });

  // Upload zone
  const uploadZone = wallpaperPanelEl.querySelector("#wp-upload-zone") as HTMLDivElement;
  const fileInput = wallpaperPanelEl.querySelector("#wp-file-input") as HTMLInputElement;

  uploadZone?.addEventListener("click", (e) => {
    if ((e.target as HTMLElement).closest("#wp-custom-remove")) return;
    fileInput?.click();
  });

  uploadZone?.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.classList.add("wp-drag-over");
  });

  uploadZone?.addEventListener("dragleave", () => uploadZone.classList.remove("wp-drag-over"));

  uploadZone?.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("wp-drag-over");
    const file = e.dataTransfer?.files[0];
    if (file) handleCustomImage(file);
  });

  fileInput?.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (file) handleCustomImage(file);
  });

  // Supprimer image custom
  wallpaperPanelEl.querySelector("#wp-custom-remove")?.addEventListener("click", (e) => {
    e.stopPropagation();
    clearCustomWallpaper();
  });

  // Slider opacité
  const slider = wallpaperPanelEl.querySelector("#wp-opacity-slider") as HTMLInputElement;
  slider?.addEventListener("input", () => {
    const val = parseInt(slider.value) / 100;
    wallpaperOpacity = val;
    updateWallpaperOpacity(val);
    const opacityLabel = wallpaperPanelEl?.querySelector("#wp-opacity-value");
    if (opacityLabel) opacityLabel.textContent = `${Math.round(val * 100)}%`;
    localStorage.setItem("vision_wallpaper_opacity", String(val));
  });
}

// ── Gestion de l'image custom ────────────────────────────────────────────────
function handleCustomImage(file: File): void {
  const reader = new FileReader();
  reader.onload = (e) => {
    const dataUrl = e.target?.result as string;
    if (!dataUrl) return;

    // Afficher aperçu
    const previewWrap = wallpaperPanelEl?.querySelector("#wp-custom-preview") as HTMLElement;
    const previewImg = wallpaperPanelEl?.querySelector("#wp-custom-img") as HTMLImageElement;
    if (previewWrap) previewWrap.style.display = "block";
    const uploadContent = wallpaperPanelEl?.querySelector(".wp-upload-content") as HTMLElement;
    if (uploadContent) uploadContent.style.display = "none";
    if (previewImg) previewImg.src = dataUrl;

    // Appliquer comme fond
    applyWallpaper(dataUrl);
    updatePresetsUI("");
    localStorage.setItem("vision_wallpaper", dataUrl);
  };
  reader.readAsDataURL(file);
}

function clearCustomWallpaper(): void {
  const previewWrap = wallpaperPanelEl?.querySelector("#wp-custom-preview") as HTMLElement;
  const previewImg = wallpaperPanelEl?.querySelector("#wp-custom-img") as HTMLImageElement;
  const uploadContent = wallpaperPanelEl?.querySelector(".wp-upload-content") as HTMLElement;
  if (previewWrap) previewWrap.style.display = "none";
  if (uploadContent) uploadContent.style.display = "flex";
  if (previewImg) previewImg.src = "";

  applyWallpaper("");
  localStorage.removeItem("vision_wallpaper");
}

// ── Appliquer un fond ─────────────────────────────────────────────────────────
function applyWallpaper(src: string): void {
  currentWallpaper = src || null;
  if (!wallpaperOverlayEl) return;

  if (!src) {
    wallpaperOverlayEl.style.backgroundImage = "none";
    wallpaperOverlayEl.style.opacity = "0";
    return;
  }
  wallpaperOverlayEl.style.backgroundImage = `url("${src}")`;
  wallpaperOverlayEl.style.backgroundSize = "cover";
  wallpaperOverlayEl.style.backgroundPosition = "center";
  wallpaperOverlayEl.style.backgroundRepeat = "no-repeat";
  wallpaperOverlayEl.style.opacity = String(wallpaperOpacity);
}

function updateWallpaperOpacity(val: number): void {
  if (!wallpaperOverlayEl) return;
  if (currentWallpaper) {
    wallpaperOverlayEl.style.opacity = String(val);
  }
}

function updatePresetsUI(activeSrc: string): void {
  wallpaperPanelEl?.querySelectorAll(".wp-preset-card").forEach(card => {
    const src = (card as HTMLElement).dataset.src || "";
    const isActive = src === activeSrc || (activeSrc === "" && src === "");
    card.classList.toggle("active", isActive);
  });
}

// ── Panneau open/close ────────────────────────────────────────────────────────
function openWallpaperPanel(): void {
  if (!wallpaperPanelEl) return;
  wallpaperPanelEl.classList.remove("wallpaper-panel-hidden");
  wallpaperPanelEl.classList.add("wallpaper-panel-visible");

  // Sync slider avec valeur actuelle
  const slider = wallpaperPanelEl.querySelector("#wp-opacity-slider") as HTMLInputElement;
  if (slider) slider.value = String(Math.round(wallpaperOpacity * 100));
  const opacityLabel = wallpaperPanelEl?.querySelector("#wp-opacity-value");
  if (opacityLabel) opacityLabel.textContent = `${Math.round(wallpaperOpacity * 100)}%`;

  // Sync presets
  updatePresetsUI(currentWallpaper ?? "");
}

function closeWallpaperPanel(): void {
  if (!wallpaperPanelEl) return;
  wallpaperPanelEl.classList.add("wallpaper-panel-hidden");
  wallpaperPanelEl.classList.remove("wallpaper-panel-visible");
}
