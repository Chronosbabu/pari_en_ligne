from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")  # pour autoriser les clients à se connecter

# stockage en mémoire
utilisateurs = {}
matchs = []

# fichier pour stocker les paris
PARIS_FILE = "paris.json"

# créer le fichier paris.json si n'existe pas
if not os.path.exists(PARIS_FILE):
    with open(PARIS_FILE, "w") as f:
        json.dump([], f)

# Routes HTTP pour gérer comptes et matchs
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    nom = data.get("nom")
    francs = data.get("francs", 0)
    dollars = data.get("dollars", 0)
    
    utilisateurs[nom] = {"francs": francs, "dollars": dollars}
    return jsonify({"message": f"Utilisateur {nom} enregistré", "compte": utilisateurs[nom]})


@app.route("/list_matchs", methods=["GET"])
def list_matchs():
    return jsonify(matchs)


@app.route("/compte/<nom>", methods=["GET"])
def compte(nom):
    user = utilisateurs.get(nom)
    if user:
        return jsonify(user)
    else:
        return jsonify({"error": "Utilisateur inconnu"}), 404

@app.route("/parier", methods=["POST"])
def parier():
    data = request.json
    nom = data.get("nom")
    match = data.get("match")
    choix = data.get("choix")  # equipe1, equipe2, nul
    
    if nom not in utilisateurs:
        return jsonify({"error": "Utilisateur inconnu"}), 404
    
    # Vérifie si l'utilisateur a de l'argent
    if utilisateurs[nom]["francs"] == 0 and utilisateurs[nom]["dollars"] == 0:
        return jsonify({"error": "Pas d'argent sur le compte"})
    
    # Sauvegarde du pari dans le JSON
    with open(PARIS_FILE, "r") as f:
        paris = json.load(f)
    
    paris.append({
        "nom": nom,
        "match": match,
        "choix": choix
    })
    
    with open(PARIS_FILE, "w") as f:
        json.dump(paris, f, indent=4)
    
    return jsonify({"message": f"{nom} a parié sur {choix}", "paris": paris})


# Socket.IO pour publier les matchs en temps réel
@socketio.on("publier_match")
def handle_publier_match(data):
    match = {"equipe1": data.get("equipe1"), "equipe2": data.get("equipe2")}
    matchs.append(match)
    emit("nouveau_match", match, broadcast=True)  # envoie à tous les clients connectés

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)

