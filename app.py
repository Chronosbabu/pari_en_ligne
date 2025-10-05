import os
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# ⚡ Utiliser gevent
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

@app.route('/')
def index():
    return "Serveur SocketIO ready."

@socketio.on('command')
def handle_command(data):
    print("Reçu du sender:", data)
    socketio.emit('command', data, broadcast=True)

@socketio.on('connect')
def on_connect():
    print("Client connecté.")

@socketio.on('disconnect')
def on_disconnect():
    print("Client déconnecté.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)

