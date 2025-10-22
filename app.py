# Fichier 1: serveur.py (Serveur central en Python avec Flask et Flask-SocketIO)
# À déployer sur Render. Assurez-vous d'installer les dépendances : flask, flask-socketio, eventlet
# requirements.txt : flask==3.0.3, flask-socketio==5.3.6, eventlet==0.36.1
# Exécutez avec : python serveur.py

from flask import Flask
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Autoriser toutes les origines pour simplicité

@socketio.on('connect')
def handle_connect():
    print('Un client s\'est connecté')

@socketio.on('disconnect')
def handle_disconnect():
    print('Un client s\'est déconnecté')

@socketio.on('obstacle_detected')
def handle_obstacle(data):
    print('Information reçue du local py:', data)
    emit('new_message', {'message': 'Information reçue: Obstacle détecté à 5cm'}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render utilise la variable d'environnement PORT
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
