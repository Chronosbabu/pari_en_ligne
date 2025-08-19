from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import json
import os

app = Flask(__name__, static_folder="frontend")
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

utilisateurs = {}
matchs = []

PARIS_FILE = "paris.json"

if not os.path.exists(PARIS_FILE):
    with open(PARIS_FILE, "w") as f:
        json.dump([], f)

# Route principale
@app.route("/")
def home():
    return send_from_directory("frontend", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("frontend", path)

# API pour enregistrer un utilisateur
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    nom = data.get("nom")
    francs = data.get("francs", 0)
    dollars = data.get("dollars", 0)
    utilisateurs[nom] = {"francs": francs, "dollars": dollars}
    return jsonify({"message": f"Utilisateur {nom} enregistré", "compte": utilisateurs[nom]})

# Liste des matchs
@app.route("/list_matchs", methods=["GET"])
def list_matchs():
    return jsonify(matchs)

# Détails d'un compte
@app.route("/compte/<nom>", methods=["GET"])
def compte(nom):
    user = utilisateurs.get(nom)
    if user:
        return jsonify(user)
    return jsonify({"error": "Utilisateur inconnu"}), 404

# Placer un pari
@app.route("/parier", methods=["POST"])
def parier():
    data = request.json
    nom = data.get("nom")
    match = data.get("match")
    choix = data.get("choix")

    if nom not in utilisateurs:
        return jsonify({"error": "Utilisateur inconnu"}), 404
    if utilisateurs[nom]["francs"] == 0 and utilisateurs[nom]["dollars"] == 0:
        return jsonify({"error": "Pas d'argent sur le compte"})

    with open(PARIS_FILE, "r") as f:
        paris = json.load(f)
    paris.append({"nom": nom, "match": match, "choix": choix})
    with open(PARIS_FILE, "w") as f:
        json.dump(paris, f, indent=4)
    return jsonify({"message": f"{nom} a parié sur {choix}", "paris": paris})

# Socket.IO pour publier les matchs en temps réel
@socketio.on("publier_match")
def handle_publier_match(data):
    match = {"equipe1": data.get("equipe1"), "equipe2": data.get("equipe2")}
    matchs.append(match)
    emit("nouveau_match", match, broadcast=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)

