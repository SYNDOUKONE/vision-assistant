/**
 * VISION — Module Radio 3D & Explorateur de Stations Mondiales
 * 
 * - Lecteur streaming audio HTML5 (HLS / AAC / MP3)
 * - Fenêtre modale responsive au design rétro-moderne crème/rose
 * - Globe 3D interactif Three.js avec marqueurs GPS de radios
 * - Recherche & Filtrage dynamique via l'API Radio Browser
 */

import * as THREE from "three";

export interface RadioStation {
  id: string;
  name: string;
  country: string;
  countryCode: string; // ex: "CI", "FR", "US", "GB"
  flag: string;
  tags: string[];
  url: string;
  codec: string;
  lat: number;
  lng: number;
  continent: string; // "Africa", "Europe", "N. America", "S. America", "Asia"
}

// ── Presets de Radios sélectionnées ──────────────────────────────────────────
const PRESET_STATIONS: RadioStation[] = [
  {
    id: "kiis-1027",
    name: "102.7 KIIS FM",
    country: "The United States of America",
    countryCode: "US",
    flag: "🇺🇸",
    tags: ["pop", "top 40"],
    url: "https://stream.revma.ihrhls.com/zc185",
    codec: "AAC",
    lat: 34.0522,
    lng: -118.2437,
    continent: "N. America",
  },
  {
    id: "rtl-fr",
    name: "RTL",
    country: "France",
    countryCode: "FR",
    flag: "🇫🇷",
    tags: ["généraliste", "news", "talk"],
    url: "https://icecast.rtl.fr/rtl-1-44-128?listen=webcmedia",
    codec: "MP3",
    lat: 48.8566,
    lng: 2.3522,
    continent: "Europe",
  },
  {
    id: "europe1-fr",
    name: "Europe 1",
    country: "France",
    countryCode: "FR",
    flag: "🇫🇷",
    tags: ["aac", "news", "talk"],
    url: "http://stream.europe1.fr/europe1.mp3",
    codec: "MP3",
    lat: 48.8566,
    lng: 2.3522,
    continent: "Europe",
  },
  {
    id: "rmc-fr",
    name: "RMC FR",
    country: "France",
    countryCode: "FR",
    flag: "🇫🇷",
    tags: ["france", "info", "sport"],
    url: "http://audio.bfmtv.com/rmcinfo_mp3",
    codec: "MP3",
    lat: 48.8566,
    lng: 2.3522,
    continent: "Europe",
  },
  {
    id: "rti-ci",
    name: "Radio Côte d'Ivoire",
    country: "Côte d'Ivoire",
    countryCode: "CI",
    flag: "🇨🇮",
    tags: ["généraliste", "news", "culture"],
    url: "https://stream.rti.ci/radiocotedivoire/live/playlist.m3u8",
    codec: "HLS/AAC",
    lat: 5.36,
    lng: -4.008,
    continent: "Africa",
  },
  {
    id: "nostalgie-ci",
    name: "Nostalgie Abidjan",
    country: "Côte d'Ivoire",
    countryCode: "CI",
    flag: "🇨🇮",
    tags: ["zouglou", "pop", "retro"],
    url: "https://nostalgie.ice.infomaniak.ch/nostalgie-128.mp3",
    codec: "MP3",
    lat: 5.36,
    lng: -4.008,
    continent: "Africa",
  },
  {
    id: "trace-ci",
    name: "Trace FM Abidjan",
    country: "Côte d'Ivoire",
    countryCode: "CI",
    flag: "🇨🇮",
    tags: ["coupe-decale", "afrobeats", "rap"],
    url: "https://tracefm-ci.ice.infomaniak.ch/tracefm-ci-128.mp3",
    codec: "MP3",
    lat: 5.36,
    lng: -4.008,
    continent: "Africa",
  },
  {
    id: "jam-ci",
    name: "Radio Jam Abidjan",
    country: "Côte d'Ivoire",
    countryCode: "CI",
    flag: "🇨🇮",
    tags: ["ambiance", "nouchi", "music"],
    url: "https://radiojam.ice.infomaniak.ch/radiojam-128.mp3",
    codec: "MP3",
    lat: 5.36,
    lng: -4.008,
    continent: "Africa",
  },
  {
    id: "albayane-ci",
    name: "Radio Al-Bayane",
    country: "Côte d'Ivoire",
    countryCode: "CI",
    flag: "🇨🇮",
    tags: ["religion", "culture", "talk"],
    url: "https://albayane.ice.infomaniak.ch/albayane-128.mp3",
    codec: "MP3",
    lat: 5.36,
    lng: -4.008,
    continent: "Africa",
  },
  {
    id: "rfi-monde",
    name: "RFI Monde",
    country: "International",
    countryCode: "FR",
    flag: "🌍",
    tags: ["news", "afrique", "monde"],
    url: "http://stream.rfi.fr/rfimonde/all/rfimonde-64k.mp3",
    codec: "MP3",
    lat: 48.8566,
    lng: 2.3522,
    continent: "Europe",
  },
  {
    id: "bbc-world",
    name: "BBC World Service",
    country: "United Kingdom",
    countryCode: "GB",
    flag: "🇬🇧",
    tags: ["news", "world", "english"],
    url: "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service",
    codec: "MP3",
    lat: 51.5074,
    lng: -0.1278,
    continent: "Europe",
  },
  {
    id: "capital-london",
    name: "Capital FM London",
    country: "United Kingdom",
    countryCode: "GB",
    flag: "🇬🇧",
    tags: ["pop", "chart", "hits"],
    url: "https://stream-capital.musicradio.com/capitalmp3",
    codec: "MP3",
    lat: 51.5074,
    lng: -0.1278,
    continent: "Europe",
  },
  {
    id: "rts-senegal",
    name: "RTS Radio Senegal",
    country: "Senegal",
    countryCode: "SN",
    flag: "🇸🇳",
    tags: ["mbalax", "news", "culture"],
    url: "https://stream.zeno.fm/g6tqqu0m6zztv",
    codec: "MP3",
    lat: 14.7167,
    lng: -17.4677,
    continent: "Africa",
  },
  {
    id: "hot97-ny",
    name: "Hot 97 New York",
    country: "The United States of America",
    countryCode: "US",
    flag: "🇺🇸",
    tags: ["hiphop", "rnb", "urban"],
    url: "https://stream.revma.ihrhls.com/zc7465",
    codec: "AAC",
    lat: 40.7128,
    lng: -74.0060,
    continent: "N. America",
  },
  {
    id: "kexp-seattle",
    name: "KEXP 90.3 Seattle",
    country: "The United States of America",
    countryCode: "US",
    flag: "🇺🇸",
    tags: ["indie", "rock", "eclectic"],
    url: "https://kexp-mp3-128.streamguys1.com/kexp128.mp3",
    codec: "MP3",
    lat: 47.6062,
    lng: -122.3321,
    continent: "N. America",
  },
  {
    id: "bossa-rio",
    name: "Bossa Nova Brazil",
    country: "Brazil",
    countryCode: "BR",
    flag: "🇧🇷",
    tags: ["bossa nova", "latin", "jazz"],
    url: "https://stream.zeno.fm/f3wvbb75zp8uv",
    codec: "MP3",
    lat: -22.9068,
    lng: -43.1729,
    continent: "S. America",
  },
  {
    id: "tokyo-fm",
    name: "Tokyo FM 80.0",
    country: "Japan",
    countryCode: "JP",
    flag: "🇯🇵",
    tags: ["jpop", "tokyo", "music"],
    url: "https://stream.zeno.fm/5cn87r0m6zztv",
    codec: "MP3",
    lat: 35.6762,
    lng: 139.6503,
    continent: "Asia",
  }
];

// ── State variables ──────────────────────────────────────────────────────────
let currentStationsList: RadioStation[] = [...PRESET_STATIONS];
let currentPlayingStation: RadioStation = PRESET_STATIONS[0];
let isPlaying = false;
let isAudioLoading = false;
let audioVolume = 0.8;
let favoritesList: string[] = JSON.parse(localStorage.getItem("vision_radio_favorites") || "[]");

// Filtering state
let searchQuery = "";
let selectedCountry = "All countries";
let selectedContinent = "All";
let selectedTag = "All";

// Audio Element
let audioElement: HTMLAudioElement | null = null;

// 3D Globe variables
let globeContainer: HTMLDivElement | null = null;
let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let globeMesh: THREE.Mesh | null = null;
let gridMesh: THREE.LineSegments | null = null;
let markersGroup: THREE.Group | null = null;
let dotsMesh: THREE.Points | null = null;
let animFrameId: number | null = null;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();

let isDragging = false;
let previousMousePosition = { x: 0, y: 0 };
let targetRotationX = 0.3;
let targetRotationY = 0.5;
let currentRotationX = 0.3;
let currentRotationY = 0.5;

// Hover state
let hoveredStationId: string | null = null;
let tooltipEl: HTMLDivElement | null = null;

// ── Helper: Country Code to Flag Emoji ───────────────────────────────────────
function getFlagEmoji(countryCode: string): string {
  if (!countryCode || countryCode.length !== 2) return "🌐";
  const codePoints = countryCode
    .toUpperCase()
    .split("")
    .map((char) => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

// ── Audio Player Setup & Controls ───────────────────────────────────────────
function initAudioEngine(): void {
  if (audioElement) return;
  audioElement = new Audio();
  audioElement.volume = audioVolume;

  audioElement.addEventListener("playing", () => {
    isPlaying = true;
    isAudioLoading = false;
    updatePlayerUI();
  });

  audioElement.addEventListener("pause", () => {
    isPlaying = false;
    updatePlayerUI();
  });

  audioElement.addEventListener("waiting", () => {
    isAudioLoading = true;
    updatePlayerUI();
  });

  audioElement.addEventListener("error", (e) => {
    console.warn("Erreur de flux radio:", e);
    isAudioLoading = false;
    isPlaying = false;
    showRadioToast(`Impossible de charger le flux de ${currentPlayingStation.name}`);
    updatePlayerUI();
  });
}

export function playStation(station: RadioStation): void {
  initAudioEngine();
  currentPlayingStation = station;
  if (!audioElement) return;

  isAudioLoading = true;
  updatePlayerUI();
  renderStationCards();

  audioElement.src = station.url;
  audioElement
    .play()
    .then(() => {
      isPlaying = true;
      isAudioLoading = false;
      updatePlayerUI();
      renderStationCards();
      highlightGlobeMarker(station.id);
    })
    .catch((err) => {
      console.warn("Échec lecture radio:", err);
      isPlaying = false;
      isAudioLoading = false;
      updatePlayerUI();
    });
}

export function togglePlayPause(): void {
  initAudioEngine();
  if (!audioElement) return;

  if (isPlaying) {
    audioElement.pause();
  } else {
    if (audioElement.src) {
      audioElement.play().catch(() => {});
    } else if (currentPlayingStation) {
      playStation(currentPlayingStation);
    }
  }
}

export function setRadioVolume(vol: number): void {
  audioVolume = Math.max(0, Math.min(1, vol));
  if (audioElement) {
    audioElement.volume = audioVolume;
  }
}

export function toggleFavorite(stationId: string): void {
  const index = favoritesList.indexOf(stationId);
  if (index > -1) {
    favoritesList.splice(index, 1);
  } else {
    favoritesList.push(stationId);
  }
  localStorage.setItem("vision_radio_favorites", JSON.stringify(favoritesList));
  updatePlayerUI();
  renderStationCards();
}

// ── API Radio Browser Fetcher ────────────────────────────────────────────────
async function fetchOnlineRadios(query: string = ""): Promise<void> {
  const countSpan = document.getElementById("radio-count");
  if (countSpan) countSpan.textContent = "chargement...";

  try {
    const endpoint = query
      ? `https://de1.api.radio-browser.info/json/stations/byname/${encodeURIComponent(query)}?limit=40`
      : `https://de1.api.radio-browser.info/json/stations/topclick/40`;

    const res = await fetch(endpoint);
    if (!res.ok) throw new Error("HTTP error " + res.status);
    const data = await res.json();

    const fetchedStations: RadioStation[] = data.map((item: any) => {
      const country = item.country || "World";
      const cc = item.countrycode || "XX";
      const tags = (item.tags || "")
        .split(",")
        .map((t: string) => t.trim().toLowerCase())
        .filter((t: string) => t.length > 0)
        .slice(0, 2);

      // Continent approximation
      let continent = "Europe";
      if (["US", "CA", "MX"].includes(cc)) continent = "N. America";
      else if (["BR", "AR", "CO", "CL"].includes(cc)) continent = "S. America";
      else if (["CI", "SN", "NG", "GH", "ZA", "KE", "MA", "EG"].includes(cc)) continent = "Africa";
      else if (["JP", "CN", "IN", "KR", "TH"].includes(cc)) continent = "Asia";

      return {
        id: item.stationuuid || Math.random().toString(),
        name: item.name || "Radio Station",
        country: country,
        countryCode: cc,
        flag: getFlagEmoji(cc),
        tags: tags.length ? tags : ["music"],
        url: item.url_resolved || item.url,
        codec: item.codec || "MP3",
        lat: item.geo_lat ? parseFloat(item.geo_lat) : (Math.random() * 120 - 60),
        lng: item.geo_long ? parseFloat(item.geo_long) : (Math.random() * 360 - 180),
        continent: continent,
      };
    });

    // Merge presets with fetched stations (avoiding duplicates)
    const presetIds = new Set(PRESET_STATIONS.map((s) => s.id));
    const uniqueFetched = fetchedStations.filter((s) => !presetIds.has(s.id));
    currentStationsList = [...PRESET_STATIONS, ...uniqueFetched];

    renderStationCards();
    updateGlobeMarkers();
  } catch (err) {
    console.warn("Impossible de récupérer les radios en ligne:", err);
    currentStationsList = [...PRESET_STATIONS];
    renderStationCards();
  }
}

// ── UI Rendering & Event Listeners ───────────────────────────────────────────
function filterStations(): RadioStation[] {
  return currentStationsList.filter((st) => {
    // Search input
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchName = st.name.toLowerCase().includes(q);
      const matchCountry = st.country.toLowerCase().includes(q);
      const matchTags = st.tags.some((t) => t.toLowerCase().includes(q));
      if (!matchName && !matchCountry && !matchTags) return false;
    }
    // Country dropdown
    if (selectedCountry !== "All countries") {
      if (st.country.toLowerCase() !== selectedCountry.toLowerCase()) return false;
    }
    // Continent filter
    if (selectedContinent !== "All") {
      if (st.continent !== selectedContinent) return false;
    }
    // Tag filter
    if (selectedTag !== "All") {
      const match = st.tags.some((t) => t.toLowerCase() === selectedTag.toLowerCase());
      if (!match) return false;
    }
    return true;
  });
}

function renderStationCards(): void {
  const container = document.getElementById("radio-cards-list");
  const countSpan = document.getElementById("radio-count");
  if (!container) return;

  const filtered = filterStations();
  if (countSpan) {
    countSpan.textContent = `${filtered.length} stations`;
  }

  container.innerHTML = "";
  if (filtered.length === 0) {
    container.innerHTML = `<div class="radio-no-results">Aucune station trouvée pour vos filtres.</div>`;
    return;
  }

  filtered.forEach((st) => {
    const isCurrent = currentPlayingStation && currentPlayingStation.id === st.id;
    const isPlayingThis = isCurrent && isPlaying;

    const card = document.createElement("div");
    card.className = `radio-station-card ${isCurrent ? "active" : ""}`;
    card.dataset.id = st.id;

    card.innerHTML = `
      <div class="radio-card-header">
        <span class="radio-card-flag">${st.flag}</span>
        <div class="radio-card-info">
          <div class="radio-card-title">${st.name}</div>
          <div class="radio-card-tags">
            ${st.tags.map((t) => `<span class="radio-tag-pill">${t}</span>`).join("")}
          </div>
        </div>
      </div>
      <button class="radio-play-btn ${isPlayingThis ? "playing" : ""}" type="button" aria-label="Jouer">
        ${
          isPlayingThis
            ? `<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`
            : `<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`
        }
      </button>
    `;

    card.addEventListener("click", () => {
      if (isCurrent) {
        togglePlayPause();
      } else {
        playStation(st);
      }
    });

    container.appendChild(card);
  });
}

function updatePlayerUI(): void {
  const badgeCurrent = document.getElementById("radio-header-badge");
  const favCounter = document.getElementById("radio-fav-counter");
  const playerTitle = document.getElementById("radio-player-title");
  const playerSub = document.getElementById("radio-player-sub");
  const playerFlag = document.getElementById("radio-player-flag");
  const playBtnIcon = document.getElementById("radio-bottom-play-btn");
  const heartBtn = document.getElementById("radio-heart-btn");

  if (currentPlayingStation) {
    if (badgeCurrent) badgeCurrent.textContent = `• ${currentPlayingStation.name}`;
    if (playerTitle) playerTitle.textContent = currentPlayingStation.name;
    if (playerSub) playerSub.textContent = `${currentPlayingStation.country} · ${currentPlayingStation.codec}`;
    if (playerFlag) playerFlag.textContent = currentPlayingStation.flag;
  }

  if (favCounter) {
    favCounter.textContent = `${favoritesList.length}`;
  }

  if (playBtnIcon) {
    if (isAudioLoading) {
      playBtnIcon.innerHTML = `<span class="radio-spinner"></span>`;
    } else if (isPlaying) {
      playBtnIcon.innerHTML = `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`;
    } else {
      playBtnIcon.innerHTML = `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
    }
  }

  if (heartBtn && currentPlayingStation) {
    const isFav = favoritesList.includes(currentPlayingStation.id);
    heartBtn.classList.toggle("is-fav", isFav);
    heartBtn.textContent = isFav ? "♥" : "♡";
  }
}

function showRadioToast(msg: string): void {
  const toast = document.getElementById("radio-toast");
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add("visible");
  setTimeout(() => toast.classList.remove("visible"), 3500);
}

// ── 3D Globe Visualization (Three.js) ────────────────────────────────────────
function init3DGlobe(): void {
  globeContainer = document.getElementById("radio-globe-container") as HTMLDivElement;
  if (!globeContainer) return;

  const width = globeContainer.clientWidth || 450;
  const height = globeContainer.clientHeight || 450;

  // Scene & Camera
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.z = 4.5;

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  globeContainer.innerHTML = "";
  globeContainer.appendChild(renderer.domElement);

  // Globe Base (Cream sphere)
  const globeGeo = new THREE.SphereGeometry(1.8, 64, 64);
  const globeMat = new THREE.MeshBasicMaterial({
    color: 0xEAE7DF,
    transparent: true,
    opacity: 0.9,
  });
  globeMesh = new THREE.Mesh(globeGeo, globeMat);
  scene.add(globeMesh);

  // Wireframe Latitude & Longitude grid lines
  const wireMat = new THREE.LineBasicMaterial({
    color: 0xCCCCCC,
    linewidth: 1,
    transparent: true,
    opacity: 0.5,
  });
  const wireGeo = new THREE.WireframeGeometry(globeGeo);
  gridMesh = new THREE.LineSegments(wireGeo, wireMat);
  scene.add(gridMesh);

  // Outer Atmosphere Glow
  const atmosGeo = new THREE.SphereGeometry(1.84, 32, 32);
  const atmosMat = new THREE.MeshBasicMaterial({
    color: 0xFF5376,
    transparent: true,
    opacity: 0.08,
    side: THREE.BackSide,
  });
  const atmosMesh = new THREE.Mesh(atmosGeo, atmosMat);
  scene.add(atmosMesh);

  // Earth Dotted Surface (Simulated landmass dots)
  createEarthDotCloud();

  // Markers Group
  markersGroup = new THREE.Group();
  scene.add(markersGroup);

  updateGlobeMarkers();

  // Mouse interaction
  const dom = renderer.domElement;
  dom.addEventListener("mousedown", (e) => {
    isDragging = true;
    previousMousePosition = { x: e.clientX, y: e.clientY };
  });

  window.addEventListener("mouseup", () => {
    isDragging = false;
  });

  dom.addEventListener("mousemove", (e) => {
    const rect = dom.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    if (isDragging) {
      const deltaX = e.clientX - previousMousePosition.x;
      const deltaY = e.clientY - previousMousePosition.y;

      targetRotationY += deltaX * 0.006;
      targetRotationX += deltaY * 0.006;
      targetRotationX = Math.max(-1.2, Math.min(1.2, targetRotationX));

      previousMousePosition = { x: e.clientX, y: e.clientY };
    } else {
      checkRaycastHover();
    }
  });

  dom.addEventListener("click", () => {
    if (hoveredStationId) {
      const st = currentStationsList.find((s) => s.id === hoveredStationId);
      if (st) playStation(st);
    }
  });

  // Resize handler
  window.addEventListener("resize", onGlobeResize);

  // Tooltip DOM element
  tooltipEl = document.createElement("div");
  tooltipEl.className = "radio-globe-tooltip";
  globeContainer.appendChild(tooltipEl);

  // Animation Loop
  animateGlobe();
}

function createEarthDotCloud(): void {
  if (!scene) return;
  const count = 1200;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);

  const radius = 1.81;
  for (let i = 0; i < count; i++) {
    const phi = Math.acos(-1 + (2 * i) / count);
    const theta = Math.sqrt(count * Math.PI) * phi;

    positions[i * 3] = radius * Math.cos(theta) * Math.sin(phi);
    positions[i * 3 + 1] = radius * Math.sin(theta) * Math.sin(phi);
    positions[i * 3 + 2] = radius * Math.cos(phi);
  }

  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({
    color: 0x999999,
    size: 0.02,
    transparent: true,
    opacity: 0.6,
  });

  dotsMesh = new THREE.Points(geometry, material);
  scene.add(dotsMesh);
}

function latLngToVector3(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);

  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);

  return new THREE.Vector3(x, y, z);
}

function updateGlobeMarkers(): void {
  if (!markersGroup) return;

  // Clear previous markers
  while (markersGroup.children.length > 0) {
    const child = markersGroup.children[0];
    markersGroup.remove(child);
  }

  const radius = 1.83;

  currentStationsList.forEach((st) => {
    const pos = latLngToVector3(st.lat, st.lng, radius);

    // Marker Mesh (Glowing Orange/Pink Sphere)
    const isCurrent = currentPlayingStation && currentPlayingStation.id === st.id;
    const markerGeo = new THREE.SphereGeometry(isCurrent ? 0.055 : 0.04, 16, 16);
    const markerMat = new THREE.MeshBasicMaterial({
      color: isCurrent ? 0xFF5376 : 0xFFA500,
    });

    const markerMesh = new THREE.Mesh(markerGeo, markerMat);
    markerMesh.position.copy(pos);
    markerMesh.userData = { stationId: st.id, stationName: st.name, country: st.country };

    markersGroup?.add(markerMesh);
  });
}

function highlightGlobeMarker(stationId: string): void {
  if (!markersGroup) return;
  markersGroup.children.forEach((child: any) => {
    if (child.userData.stationId === stationId) {
      child.material.color.setHex(0xFF5376);
      child.scale.set(1.5, 1.5, 1.5);
    } else {
      child.material.color.setHex(0xFFA500);
      child.scale.set(1, 1, 1);
    }
  });
}

function checkRaycastHover(): void {
  if (!camera || !markersGroup || !tooltipEl || !globeContainer) return;

  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(markersGroup.children);

  if (intersects.length > 0) {
    const hit = intersects[0].object;
    hoveredStationId = hit.userData.stationId;
    document.body.style.cursor = "pointer";

    tooltipEl.textContent = `${hit.userData.stationName} (${hit.userData.country})`;
    tooltipEl.style.display = "block";
    tooltipEl.style.left = `${(mouse.x + 1) * (globeContainer.clientWidth / 2) + 10}px`;
    tooltipEl.style.top = `${(-mouse.y + 1) * (globeContainer.clientHeight / 2) - 30}px`;
  } else {
    hoveredStationId = null;
    document.body.style.cursor = "default";
    if (tooltipEl) tooltipEl.style.display = "none";
  }
}

function animateGlobe(): void {
  animFrameId = requestAnimationFrame(animateGlobe);

  // Smooth rotation damping
  currentRotationX += (targetRotationX - currentRotationX) * 0.08;
  currentRotationY += (targetRotationY - currentRotationY) * 0.08;

  if (!isDragging) {
    targetRotationY += 0.0015; // Slow auto rotation
  }

  if (globeMesh) globeMesh.rotation.y = currentRotationY;
  if (globeMesh) globeMesh.rotation.x = currentRotationX;

  if (gridMesh) {
    gridMesh.rotation.y = currentRotationY;
    gridMesh.rotation.x = currentRotationX;
  }

  if (dotsMesh) {
    dotsMesh.rotation.y = currentRotationY;
    dotsMesh.rotation.x = currentRotationX;
  }

  if (markersGroup) {
    markersGroup.rotation.y = currentRotationY;
    markersGroup.rotation.x = currentRotationX;
  }

  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
}

function onGlobeResize(): void {
  if (!globeContainer || !renderer || !camera) return;
  const w = globeContainer.clientWidth;
  const h = globeContainer.clientHeight;
  if (w === 0 || h === 0) return;

  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}

// ── Public Module Init & Window Toggles ──────────────────────────────────────
export function initRadioModule(): void {
  const modal = document.getElementById("radio-modal");
  if (!modal) return;

  // Search Input Listener
  const searchInput = document.getElementById("radio-search-input") as HTMLInputElement;
  if (searchInput) {
    let timer: any = null;
    searchInput.addEventListener("input", (e) => {
      searchQuery = (e.target as HTMLInputElement).value;
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        if (searchQuery.length > 2) {
          fetchOnlineRadios(searchQuery);
        } else {
          renderStationCards();
        }
      }, 400);
    });
  }

  // Country Selector Listener
  const countrySelect = document.getElementById("radio-country-select") as HTMLSelectElement;
  if (countrySelect) {
    countrySelect.addEventListener("change", (e) => {
      selectedCountry = (e.target as HTMLSelectElement).value;
      renderStationCards();
    });
  }

  // Continent Filter Pills
  const continentContainer = document.getElementById("radio-continent-filters");
  if (continentContainer) {
    continentContainer.querySelectorAll(".radio-filter-pill").forEach((pill) => {
      pill.addEventListener("click", (e) => {
        continentContainer.querySelectorAll(".radio-filter-pill").forEach((p) => p.classList.remove("active"));
        const target = e.currentTarget as HTMLElement;
        target.classList.add("active");
        selectedContinent = target.dataset.val || "All";
        renderStationCards();
      });
    });
  }

  // Tag Filter Pills
  const tagContainer = document.getElementById("radio-tag-filters");
  if (tagContainer) {
    tagContainer.querySelectorAll(".radio-filter-pill").forEach((pill) => {
      pill.addEventListener("click", (e) => {
        tagContainer.querySelectorAll(".radio-filter-pill").forEach((p) => p.classList.remove("active"));
        const target = e.currentTarget as HTMLElement;
        target.classList.add("active");
        selectedTag = target.dataset.val || "All";
        renderStationCards();
      });
    });
  }

  // Bottom Bar Controls
  const bottomPlayBtn = document.getElementById("radio-bottom-play-btn");
  if (bottomPlayBtn) {
    bottomPlayBtn.addEventListener("click", togglePlayPause);
  }

  const volumeSlider = document.getElementById("radio-volume-slider") as HTMLInputElement;
  if (volumeSlider) {
    volumeSlider.value = String(audioVolume * 100);
    volumeSlider.addEventListener("input", (e) => {
      const val = parseFloat((e.target as HTMLInputElement).value) / 100;
      setRadioVolume(val);
    });
  }

  const heartBtn = document.getElementById("radio-heart-btn");
  if (heartBtn) {
    heartBtn.addEventListener("click", () => {
      if (currentPlayingStation) toggleFavorite(currentPlayingStation.id);
    });
  }

  const closeBtn = document.getElementById("radio-close-btn");
  if (closeBtn) {
    closeBtn.addEventListener("click", closeRadioModal);
  }

  // Initial render
  renderStationCards();
  updatePlayerUI();
}

export function openRadioModal(): void {
  const modal = document.getElementById("radio-modal");
  if (!modal) return;

  modal.classList.remove("radio-hidden");
  modal.classList.add("radio-visible");

  // Init 3D Globe on first open
  setTimeout(() => {
    if (!renderer) {
      init3DGlobe();
    } else {
      onGlobeResize();
    }
  }, 100);

  // Play default station if none playing
  if (!isPlaying && currentPlayingStation) {
    playStation(currentPlayingStation);
  }
}

export function closeRadioModal(): void {
  const modal = document.getElementById("radio-modal");
  if (!modal) return;
  modal.classList.remove("radio-visible");
  modal.classList.add("radio-hidden");
}

export function playStationByName(name: string): void {
  openRadioModal();
  const q = name.toLowerCase();
  const found = currentStationsList.find(
    (s) => s.name.toLowerCase().includes(q) || s.tags.some((t) => t.toLowerCase().includes(q))
  );
  if (found) {
    playStation(found);
  } else {
    fetchOnlineRadios(name).then(() => {
      const retry = currentStationsList.find((s) => s.name.toLowerCase().includes(q));
      if (retry) playStation(retry);
    });
  }
}
