# V.I.S.I.O.N

Assistant IA personnel modulaire (voix, domotique, vision, interface web 3D).

## Prérequis

- Python 3.11+
- Node.js 20+
- Microphone (PyAudio)
- Fichier `.env` (voir `.env.example`)

## Installation

```bat
install.bat
```

Ou manuellement :

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
cd frontend && npm install
```

Copiez `.env.example` vers `.env` et renseignez vos clés API.

## Lancement

```bat
DEMARRER_VISION.bat
```

Ou :

```bash
venv\Scripts\python.exe main_v2.py
```

- Interface web : http://localhost:5173
- WebSocket : `ws://localhost:8765`
- Mobile : http://&lt;IP_LAN&gt;:8080

## Structure

- `main_v2.py` — point d'entrée (architecture modulaire)
- `modules/` — backend Python (IA, voix, domotique, etc.)
- `frontend/` — interface Vite + Three.js
- `mobile/` — interface mobile légère
