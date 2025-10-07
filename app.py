# app.py (anciennement server.py, adapté à votre nommage)
# Ce fichier est le serveur Flask avec SocketIO.
# Il écoute les commandes du client émetteur et les diffuse à tous les clients connectés (y compris le récepteur).

import gevent.monkey  # Ajout pour monkey patching gevent (doit être en premier)
gevent.monkey.patch_all()  # Patch pour compatibilité asynchrone

from flask import Flask
from flask_socketio import SocketIO, emit
import os
import json
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # Clé secrète pour la sécurité

# Initialiser SocketIO avec mode 'gevent'
socketio = SocketIO(app, async_mode='gevent')

# Initialiser Firebase
cred_json = os.environ.get('FIREBASE_CREDENTIALS')
if cred_json:
    cred_dict = json.loads(cred_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
else:
    print("Aucune credential Firebase trouvée dans l'environnement.")

# Stockage des tokens FCM
tokens = set()

# Route de base pour vérifier que le serveur fonctionne (optionnelle, mais utile pour Render)
@app.route('/')
def index():
    return "Serveur SocketIO en ligne"

# Événement pour enregistrer le token FCM
@socketio.on('registerToken')
def register_token(data):
    token = data.get('token')
    if token:
        tokens.add(token)
        print(f"Token FCM enregistré: {token}")

# Événement SocketIO pour recevoir une commande
@socketio.on('command')
def handle_command(data):
    action = data.get('action')
    if action in ['allumer', 'eteindre']:
        print(f"Commande reçue: {action}")
        # Diffuser la commande à tous les clients connectés via SocketIO
        emit('command', {'action': action}, broadcast=True)
        
        # Envoyer la notification push via FCM à tous les tokens enregistrés
        if tokens:
            message = messaging.MulticastMessage(
                data={'action': action},
                tokens=list(tokens)
            )
            try:
                response = messaging.send_multicast(message)
                print(f"Notifications envoyées: {response.success_count} succès, {response.failure_count} échecs")
            except Exception as e:
                print(f"Erreur lors de l'envoi FCM: {e}")
    else:
        print("Commande invalide")

# Lancer le serveur si exécuté directement (pour tests locaux)
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)  # Retiré debug=True pour production
