# server.py
import os
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# utiliser eventlet (Render + gunicorn -k eventlet fonctionne bien)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')


@app.route('/')
def index():
    return "Serveur SocketIO ready."

# Quand un client envoie une commande ("on" / "off")
@socketio.on('command')
def handle_command(data):
    # data attendu: {"action": "on"} ou {"action": "off"}
    print("Reçu du sender:", data)
    # renvoyer/broadcaster à tous les receivers (ou tous clients connectés)
    socketio.emit('command', data, broadcast=True)

# optionnel: log de connexion
@socketio.on('connect')
def on_connect():
    print("Client connecté.")

@socketio.on('disconnect')
def on_disconnect():
    print("Client déconnecté.")

# Expose app pour gunicorn: "gunicorn server:app --worker-class eventlet ..."
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)

