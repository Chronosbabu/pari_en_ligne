# app.py
# Serveur Flask avec SocketIO
# Écoute les commandes du client et les diffuse à tous les clients connectés.

from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # Clé secrète pour la sécurité

# Initialiser SocketIO avec mode 'threading' (plus compatible avec Render et Flutter)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')

# Route de base pour vérifier que le serveur fonctionne
@app.route('/')
def index():
    return "Serveur SocketIO en ligne"

# Événement SocketIO pour recevoir une commande
@socketio.on('command')
def handle_command(data):
    action = data.get('action')
    if action in ['allumer', 'eteindre']:
        print(f"Commande reçue: {action}")
        # Diffuser la commande à tous les clients connectés via SocketIO
        emit('command', {'action': action}, broadcast=True)
    else:
        print("Commande invalide")

# Lancer le serveur si exécuté directement (tests locaux)
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

