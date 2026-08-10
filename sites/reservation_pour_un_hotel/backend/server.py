# Code du serveur API Flask/FastAPI en Python configurant CORS (avec Flask-CORS pour éviter les blocages Cross-Origin en local) et les routes REST.

from flask import Flask, request, jsonify
from flask_cors import CORS
import database

app = Flask(__name__)
CORS(app) # Active CORS pour toutes les routes, permettant l'accès depuis le frontend

# Initialisation de la base de données au démarrage de l'application
database.init_db()

@app.route('/')
def home():
    return "Bienvenue sur l'API de réservation d'hôtel !"

@app.route('/reservations', methods=['GET'])
def get_all_reservations():
    """
    Récupère toutes les réservations de la base de données.
    """
    reservations = database.get_all_reservations()
    return jsonify(reservations)

@app.route('/reservations', methods=['POST'])
def add_reservation():
    """
    Ajoute une nouvelle réservation à la base de données.
    """
    data = request.get_json()

    # Validation basique des données
    if not data:
        return jsonify({"error": "Données de réservation manquantes"}), 400
    
    required_fields = ['guest_name', 'email', 'room_type', 'check_in_date', 'check_out_date']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Champ '{field}' manquant ou vide"}), 400

    try:
        reservation_id = database.add_reservation(
            data['guest_name'],
            data['email'],
            data['room_type'],
            data['check_in_date'],
            data['check_out_date']
        )
        return jsonify({"message": "Réservation ajoutée avec succès", "id": reservation_id}), 201
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'ajout de la réservation: {str(e)}"}), 500

if __name__ == '__main__':
    # Lance le serveur Flask en mode debug sur le port 5000
    app.run(debug=True, port=5000)