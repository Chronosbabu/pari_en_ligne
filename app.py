# Fichier du serveur central pour le vente en ligne
from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO, join_room, emit
import datetime
from base64 import b64encode
import json
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DATA_FILE = 'data.json'
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        users = data.get('users', {})
        posts = data.get('posts', [])
        messages = data.get('messages', [])
else:
    users = {}
    posts = []
    messages = []

connected_users = {}  # Add this to map SID to username

def save_data():
    data = {'users': users, 'posts': posts, 'messages': messages}
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False)

@app.route('/')
def index():
    return send_file('style.html')

@app.route('/chat')
def chat():
    return send_file('chat.html')

@app.route('/conversations')
def conversations_page():
    return send_file('conversations.html')

@app.route('/api/posts')
def get_posts():
    return jsonify(posts)

@app.route('/register', methods=['POST'])
def user_register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Champs requis'}), 400
    if username in users:
        return jsonify({'error': "Nom d'utilisateur déjà pris"}), 409
    users[username] = {'password': password, 'avatar': None}
    save_data()
    return jsonify({'success': True})

@app.route('/login', methods=['POST'])
def user_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Champs requis'}), 400
    if username not in users:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    if users[username]['password'] != password:
        return jsonify({'error': 'Mot de passe incorrect'}), 401
    return jsonify({'success': True})

@app.route('/publish', methods=['POST'])
def publish():
    if 'image' not in request.files or not request.files['image'].filename:
        return jsonify({'error': 'Image requise'}), 400
    username = request.form.get('username')
    password = request.form.get('password')
    title = request.form.get('title')
    price = request.form.get('price')
    shipping_price = request.form.get('shipping_price')
    avatar = request.form.get('avatar')
    if not all([username, password, title, price, shipping_price]):
        return jsonify({'error': 'Tous les champs sont requis'}), 400
    if username not in users or users[username]['password'] != password:
        return jsonify({'error': 'Authentification requise'}), 401
    if avatar:
        users[username]['avatar'] = avatar
    image_file = request.files['image']
    image_data = image_file.read()
    mimetype = image_file.mimetype or 'image/jpeg'
    b64 = b64encode(image_data).decode('utf-8')
    image_base64 = f"data:{mimetype};base64,{b64}"
    post = {
        'username': username,
        'title': title,
        'price': price,
        'shipping_price': shipping_price,
        'image_base64': image_base64,
        'time': datetime.datetime.now().isoformat(),
        'avatar': users[username].get('avatar')
    }
    posts.append(post)
    save_data()
    return jsonify({'success': True})

@app.route('/api/messages')
def api_messages():
    with_u = request.args.get('with')
    username = request.args.get('username')
    pwd = request.args.get('password')
    if not all([with_u, username]):
        return jsonify({'error': 'Auth requise'}), 401
    if username not in users:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    if pwd:
        if users[username]['password'] != pwd:
            return jsonify({'error': 'Auth requise'}), 401
    else:
        if users[username]['password'] is not None:
            return jsonify({'error': 'Auth requise'}), 401
    conv_msgs = [m for m in messages if set([m['from'], m['to']]) == set([username, with_u])]
    conv_msgs.sort(key=lambda m: m['time'])
    return jsonify(conv_msgs)

@app.route('/api/conversations')
def api_conversations():
    username = request.args.get('username')
    pwd = request.args.get('password')
    if not username:
        return jsonify({'error': 'Auth requise'}), 401
    if username not in users:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    if pwd:
        if users[username]['password'] != pwd:
            return jsonify({'error': 'Auth requise'}), 401
    else:
        if users[username]['password'] is not None:
            return jsonify({'error': 'Auth requise'}), 401
    conv = set()
    last_times = {}
    last_texts = {}
    for m in messages:
        if m['from'] == username:
            other = m['to']
        elif m['to'] == username:
            other = m['from']
        else:
            continue
        conv.add(other)
        if m['time'] > last_times.get(other, '0'):
            last_times[other] = m['time']
            last_texts[other] = m['text']
    conv_list = sorted(list(conv), key=lambda u: last_times.get(u, '0'), reverse=True)
    return jsonify([{'user': u, 'last_time': last_times.get(u), 'last_text': last_texts.get(u)} for u in conv_list])

@socketio.on('connect')
def handle_connect(auth):
    if not auth:
        return False
    username = auth.get('username')
    password = auth.get('password')
    if not username:
        return False
    if username not in users:
        users[username] = {'password': None, 'avatar': None}
        save_data()
    user = users[username]
    if password:
        if user['password'] is None or user['password'] != password:
            return False
    else:
        if user['password'] is not None:
            return False
    connected_users[request.sid] = username
    join_room(username)
    print(f"[SOCKET] {username} connecté")

@socketio.on('disconnect')
def handle_disconnect():
    connected_users.pop(request.sid, None)

@socketio.on('send_message')
def handle_send(data):
    text = data.get('text', '').strip()
    to = data.get('to')
    if not text or not to:
        return
    username = connected_users.get(request.sid)
    if not username:
        return
    msg = {
        'from': username,
        'to': to,
        'text': text,
        'time': datetime.datetime.now().isoformat()
    }
    messages.append(msg)
    save_data()
    emit('new_message', msg, room=to)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
