"""
VISION — Mémoire Long Terme (SQLite)
Persiste les faits, préférences et informations apprises entre sessions.
Inspiré de jarvis_memory.db et jarvis_knowledge.db de Jarvis AI.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/VISION/data/vision_memoire.db")


def _connexion():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialiser():
    """Crée les tables si elles n'existent pas."""
    with _connexion() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS faits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categorie TEXT NOT NULL,
                cle TEXT NOT NULL,
                valeur TEXT NOT NULL,
                confiance REAL DEFAULT 1.0,
                date_appris TEXT NOT NULL,
                date_modifie TEXT,
                UNIQUE(categorie, cle)
            );

            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT UNIQUE NOT NULL,
                valeur TEXT NOT NULL,
                date_modifie TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sujets_frequents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sujet TEXT UNIQUE NOT NULL,
                compteur INTEGER DEFAULT 1,
                derniere_mention TEXT NOT NULL
            );
        """)


def apprendre_fait(categorie: str, cle: str, valeur: str, confiance: float = 1.0):
    """Enregistre un fait appris."""
    now = datetime.now().isoformat()
    with _connexion() as conn:
        conn.execute("""
            INSERT INTO faits (categorie, cle, valeur, confiance, date_appris, date_modifie)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(categorie, cle) DO UPDATE SET
                valeur=excluded.valeur,
                confiance=excluded.confiance,
                date_modifie=excluded.date_modifie
        """, (categorie, cle, valeur, confiance, now, now))


def rappeler_fait(categorie: str, cle: str) -> str | None:
    """Récupère un fait par catégorie et clé."""
    with _connexion() as conn:
        row = conn.execute(
            "SELECT valeur FROM faits WHERE categorie=? AND cle=?",
            (categorie, cle)
        ).fetchone()
        return row["valeur"] if row else None


def lister_faits(categorie: str = None) -> list:
    """Liste tous les faits (optionnellement par catégorie)."""
    with _connexion() as conn:
        if categorie:
            rows = conn.execute(
                "SELECT * FROM faits WHERE categorie=? ORDER BY date_modifie DESC",
                (categorie,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM faits ORDER BY date_modifie DESC LIMIT 50"
            ).fetchall()
        return [dict(r) for r in rows]


def sauvegarder_preference(nom: str, valeur: str):
    """Sauvegarde une préférence utilisateur."""
    with _connexion() as conn:
        conn.execute("""
            INSERT INTO preferences (nom, valeur, date_modifie)
            VALUES (?, ?, ?)
            ON CONFLICT(nom) DO UPDATE SET
                valeur=excluded.valeur,
                date_modifie=excluded.date_modifie
        """, (nom, valeur, datetime.now().isoformat()))


def obtenir_preference(nom: str) -> str | None:
    """Récupère une préférence."""
    with _connexion() as conn:
        row = conn.execute(
            "SELECT valeur FROM preferences WHERE nom=?", (nom,)
        ).fetchone()
        return row["valeur"] if row else None


def noter_sujet_frequent(sujet: str):
    """Incrémente le compteur d'un sujet fréquemment mentionné."""
    with _connexion() as conn:
        conn.execute("""
            INSERT INTO sujets_frequents (sujet, compteur, derniere_mention)
            VALUES (?, 1, ?)
            ON CONFLICT(sujet) DO UPDATE SET
                compteur=compteur+1,
                derniere_mention=excluded.derniere_mention
        """, (sujet, datetime.now().isoformat()))


def sujets_populaires(n: int = 5) -> list:
    """Retourne les n sujets les plus fréquents."""
    with _connexion() as conn:
        rows = conn.execute(
            "SELECT sujet, compteur FROM sujets_frequents ORDER BY compteur DESC LIMIT ?",
            (n,)
        ).fetchall()
        return [dict(r) for r in rows]


def extraire_et_apprendre(texte: str) -> bool:
    """
    Tente d'extraire des faits du texte de l'utilisateur et les mémorise.
    Ex: "je m'appelle Syndou" → fait(utilisateur, prénom, Syndou)
    Retourne True si quelque chose a été appris.
    """
    t = texte.lower().strip()
    appris = False

    # Détecter le prénom
    for pattern in ["je m'appelle ", "mon prénom est ", "mon nom est "]:
        if pattern in t:
            nom = t.split(pattern, 1)[1].strip().split()[0].capitalize()
            apprendre_fait("utilisateur", "prénom", nom)
            appris = True

    # Détecter la ville
    for pattern in ["j'habite à ", "je vis à ", "je suis à "]:
        if pattern in t:
            ville = t.split(pattern, 1)[1].strip().split()[0].capitalize()
            apprendre_fait("utilisateur", "ville", ville)
            appris = True

    # Détecter les préférences musicales
    if "j'aime " in t and any(x in t for x in ["musique", "chanson", "artiste", "groupe"]):
        preference = t.split("j'aime ", 1)[1].strip()[:100]
        apprendre_fait("préférences", "musique", preference)
        appris = True

    return appris


def generer_contexte_personnalise() -> str:
    """Génère un contexte système enrichi avec les faits mémorisés."""
    faits = lister_faits()
    if not faits:
        return ""
    lignes = []
    for f in faits[:10]:
        lignes.append(f"- {f['categorie']}/{f['cle']}: {f['valeur']}")
    return "Faits mémorisés sur l'utilisateur:\n" + "\n".join(lignes)


def traiter_commande_memoire(texte: str) -> str | None:
    """Traite les commandes de mémorisation explicites."""
    t = texte.lower().strip()

    if "souviens-toi" in t or "mémorise" in t or "retiens que" in t:
        # "souviens-toi que j'aime le café"
        for pattern in ["souviens-toi que ", "mémorise que ", "retiens que "]:
            if pattern in t:
                info = texte.split(pattern, 1)[-1].strip()
                apprendre_fait("notes", f"note_{datetime.now().strftime('%H%M%S')}", info)
                return f"C'est noté, Monsieur. Je me souviendrai que : {info}"

    if "qu'est-ce que tu sais sur moi" in t or "que sais-tu de moi" in t:
        faits = lister_faits()
        if not faits:
            return "Je n'ai encore rien mémorisé à votre sujet, Monsieur."
        lignes = [f"• {f['categorie']}/{f['cle']}: {f['valeur']}" for f in faits[:10]]
        return "Voici ce que je sais de vous :\n" + "\n".join(lignes)

    if "oublie" in t and ("tout" in t or "tout ce que" in t):
        with _connexion() as conn:
            conn.execute("DELETE FROM faits")
            conn.execute("DELETE FROM preferences")
        return "Ma mémoire a été réinitialisée, Monsieur."

    return None


# Initialiser la DB au chargement du module
initialiser()
