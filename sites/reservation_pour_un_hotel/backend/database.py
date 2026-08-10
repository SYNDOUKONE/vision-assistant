# Gestionnaire SQLite de la base de données (création des tables, insertion de données d'exemple, requêtes propres).

import sqlite3

DB_FILE = 'hotel_reservations.db'

def get_db_connection():
    """
    Établit une connexion à la base de données SQLite.
    Configure row_factory pour retourner les lignes comme des dictionnaires.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Permet d'accéder aux colonnes par nom
    return conn

def create_tables():
    """
    Crée la table 'reservations' si elle n'existe pas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL,
            email TEXT NOT NULL,
            room_type TEXT NOT NULL,
            check_in_date TEXT NOT NULL,
            check_out_date TEXT NOT NULL,
            status TEXT DEFAULT 'Confirmed'
        )
    ''')
    conn.commit()
    conn.close()
    print("Table 'reservations' vérifiée/créée.")

def insert_example_data():
    """
    Insère des données d'exemple si la table 'reservations' est vide.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Vérifie si la table est vide
    cursor.execute("SELECT COUNT(*) FROM reservations")
    if cursor.fetchone()[0] == 0:
        print("Insertion de données d'exemple...")
        reservations_data = [
            ("Alice Smith", "alice@example.com", "Deluxe", "2023-10-26", "2023-10-29"),
            ("Bob Johnson", "bob@example.com", "Standard", "2023-11-10", "2023-11-15"),
            ("Charlie Brown", "charlie@example.com", "Suite", "2023-12-01", "2023-12-05")
        ]
        cursor.executemany(
            "INSERT INTO reservations (guest_name, email, room_type, check_in_date, check_out_date) VALUES (?, ?, ?, ?, ?)",
            reservations_data
        )
        conn.commit()
        print("Données d'exemple insérées.")
    else:
        print("La table 'reservations' contient déjà des données. Pas d'insertion d'exemples.")
    conn.close()

def init_db():
    """
    Initialise la base de données : crée les tables et insère des données d'exemple.
    """
    create_tables()
    insert_example_data()

def get_all_reservations():
    """
    Récupère toutes les réservations de la base de données.
    Retourne une liste de dictionnaires.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservations ORDER BY check_in_date DESC")
    reservations = cursor.fetchall()
    conn.close()
    # Convertit les objets Row en dictionnaires pour une meilleure sérialisation JSON
    return [dict(row) for row in reservations]

def add_reservation(guest_name, email, room_type, check_in_date, check_out_date):
    """
    Ajoute une nouvelle réservation à la base de données.
    Retourne l'ID de la nouvelle réservation.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reservations (guest_name, email, room_type, check_in_date, check_out_date) VALUES (?, ?, ?, ?, ?)",
        (guest_name, email, room_type, check_in_date, check_out_date)
    )
    conn.commit()
    reservation_id = cursor.lastrowid
    conn.close()
    return reservation_id

# Vous pouvez ajouter d'autres fonctions CRUD (get_reservation_by_id, update_reservation, delete_reservation) ici
# pour une API plus complète si nécessaire.