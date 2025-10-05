# server.py
# Ce fichier est le serveur Flask avec SocketIO.
# Il écoute les commandes du client émetteur et les diffuse à tous les clients connectés (y compris le récepteur).

from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # Clé secrète pour la sécurité

# Initialiser SocketIO avec support asynchrone (eventlet)
socketio = SocketIO(app, async_mode='eventlet')

# Route de base pour vérifier que le serveur fonctionne (optionnelle, mais utile pour Render)
@app.route('/')
def index():
    return "Serveur SocketIO en ligne"

# Événement SocketIO pour recevoir une commande
@socketio.on('command')
def handle_command(data):
    action = data.get('action')
    if action in ['allumer', 'eteindre']:
        print(f"Commande reçue: {action}")
        # Diffuser la commande à tous les clients connectés
        emit('command', {'action': action}, broadcast=True)
    else:
        print("Commande invalide")

# Lancer le serveur si exécuté directement (pour tests locaux)
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
