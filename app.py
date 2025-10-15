from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

@app.route('/')
def index():
    return "Serveur SocketIO en ligne"

@socketio.on('command')
def handle_command(data):
    action = data.get('action')
    print(f"Commande reçue: {action}")
    emit('command', {'action': action}, broadcast=True)

if __name__ == '__main__':
    import eventlet
    import eventlet.wsgi
    socketio.run(app, host='0.0.0.0', port=5000)

