# Guide d'utilisation : Système de Réservation d'Hôtel Premium

Ce projet est une application web full-stack pour la gestion des réservations d'hôtel, conçue avec une interface utilisateur moderne et premium (glassmorphism) et un backend Python Flask robuste.

## Technologies Utilisées

*   **Frontend:** HTML5, Tailwind CSS, FontAwesome, JavaScript (Vanilla JS pour les appels API).
*   **Backend:** Python 3, Flask (pour l'API REST), Flask-CORS (pour la gestion des requêtes cross-origin).
*   **Base de Données:** SQLite3.

## Structure du Projet

```
.
├── backend/
│   ├── database.py       # Gestionnaire SQLite (création tables, CRUD)
│   └── server.py         # Application Flask (routes API, CORS)
├── frontend/
│   ├── app.js            # Logique client (interactions, appels fetch)
│   └── index.html        # Interface utilisateur HTML, CSS (Tailwind, FontAwesome)
├── requirements.txt      # Dépendances Python
└── README.md             # Ce fichier
```

## Étapes d'Installation et Lancement

Suivez ces étapes pour mettre en place et lancer l'application.

### 1. Prérequis

Assurez-vous d'avoir Python 3 installé sur votre système.

### 2. Installation du Backend

1.  **Naviguez dans le répertoire `backend` :**
    ```bash
    cd backend
    ```

2.  **Installez les dépendances Python :**
    Il est recommandé d'utiliser un environnement virtuel.
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur macOS/Linux
    # ou `venv\Scripts\activate` sur Windows
    pip install -r ../requirements.txt
    ```
    *(Note: `../requirements.txt` car vous êtes dans le dossier `backend`)*

3.  **Lancez le serveur Flask :**
    ```bash
    python server.py
    ```
    Le serveur devrait démarrer et être accessible à `http://127.0.0.1:5000`. Vous verrez des messages dans la console indiquant la création de la base de données et l'insertion des données d'exemple.

### 3. Lancement du Frontend

1.  **Ouvrez le fichier `index.html` :**
    Le frontend est une application HTML/JavaScript statique. Vous n'avez pas besoin d'un serveur web séparé pour le frontend.
    Naviguez vers le répertoire `frontend` et ouvrez simplement le fichier `index.html` dans votre navigateur web préféré.
    ```bash
    # Depuis la racine du projet
    open frontend/index.html # Sur macOS
    # ou
    start frontend\index.html # Sur Windows
    # ou ouvrez-le manuellement via l'explorateur de fichiers
    ```

### 4. Utilisation de l'Application

*   Une fois le frontend ouvert, vous verrez le formulaire de réservation et une liste des réservations existantes (initialement remplie avec des données d'exemple par le backend).
*   Remplissez le formulaire et cliquez sur "Réserver maintenant" pour ajouter une nouvelle réservation.
*   La liste des réservations se mettra à jour automatiquement après chaque ajout.

### Notes Importantes

*   Le fichier de base de données SQLite (`hotel_reservations.db`) sera créé dans le répertoire `backend/` lors du premier lancement du serveur.
*   Si vous rencontrez des problèmes CORS, assurez-vous que `flask-cors` est correctement installé et que le serveur Flask est en cours d'exécution.
*   Pour arrêter le backend, appuyez sur `Ctrl+C` dans la console où le serveur Flask est lancé.