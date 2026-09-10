# V.I.S.I.O.N

Assistant IA personnel modulaire (voix, domotique, vision, interface web 3D).

## Prérequis

- Python 3.11+
- Node.js 20+
- Microphone (PyAudio)
- Fichier `.env` (voir `.env.example`)

## Installation

**Sous macOS / Linux :**
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cd frontend && npm install
```

**Sous Windows :**
```bat
install.bat
```

Copiez `.env.example` vers `.env` et renseignez vos clés API.

## Lancement

**Sous macOS / Linux :**
```bash
./demarrer_vision.sh
# Ou manuellement :
./venv/bin/python main_v2.py
```

**Sous Windows :**
```bat
DEMARRER_VISION.bat
# Ou manuellement :
venv\Scripts\python.exe main_v2.py
```

- Interface web : http://localhost:5173
- WebSocket : `ws://localhost:8765`
- Mobile : http://<IP_LAN>:8080

## Structure

- `main_v2.py` — point d'entrée (architecture modulaire)
- `modules/` — backend Python (IA, voix, domotique, etc.)
- `frontend/` — interface Vite + Three.js
- `mobile/` — interface mobile légère
