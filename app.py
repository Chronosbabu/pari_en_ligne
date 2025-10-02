# app.py
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)

# stockage en mémoire simple : dict client_id -> list de messages
messages = {}
lock = threading.Lock()

@app.route("/")
def index():
    return "Présence server OK", 200

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json(force=True)
    if not data or "target" not in data or "message" not in data:
        return jsonify({"error":"target and message required"}), 400
    target = str(data["target"])
    msg = {"message": data["message"]}
    with lock:
        messages.setdefault(target, []).append(msg)
    return jsonify({"status":"queued", "target":target}), 200

@app.route("/receive/<client_id>", methods=["GET"])
def receive(client_id):
    client_id = str(client_id)
    with lock:
        queue = messages.get(client_id, [])
        if not queue:
            return ("", 204)
        # renvoyer le premier message (FIFO)
        msg = queue.pop(0)
        # si file vide, on peut supprimer la clé
        if not queue:
            messages.pop(client_id, None)
    return jsonify(msg), 200

@app.route("/peek/<client_id>", methods=["GET"])
def peek(client_id):
    client_id = str(client_id)
    with lock:
        queue = messages.get(client_id, [])
        return jsonify({"pending": len(queue)}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
