#!/bin/bash
# V.I.S.I.O.N — Lancement Backend & Frontend sur macOS / Linux

cd "$(dirname "$0")"

echo "============================================================"
echo "   V.I.S.I.O.N — Démarrage du système..."
echo "============================================================"
echo ""

# Tuer toute ancienne instance de Vite pour libérer le port 5173
pkill -f vite 2>/dev/null || true

# Vérifier si venv existe
if [ ! -d "venv" ]; then
    echo "[!] Environnement virtuel venv non trouvé. Création..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Lancer le backend Python (qui gère aussi Vite)
echo "[+] Démarrage du backend Python et de l'interface..."
./venv/bin/python -u main_v2.py
