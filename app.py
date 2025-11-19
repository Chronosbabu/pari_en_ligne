from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO, join_room, emit
import datetime
from base64 import b64encode
import json
import os
import uuid
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
DATA_FILE = 'data.json'
# Chargement des données
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        users = data.get('users', {})
        products = data.get('products', [])
        messages = data.get('messages', [])
        orders = data.get('orders', [])
else:
    users = {}
    products = []
    messages = []
    orders = []
connected_users = {} # sid → username
def save_data():
    data = {'users': users, 'products': products, 'messages': messages, 'orders': orders}
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
@app.route('/')
def index():
    return send_file('style.html')
@app.route('/chat')
def chat():
    return send_file('chat.html')
@app.route('/conversations')
def conversations_page():
    return send_file('conversations.html')
@app.route('/electronique')
def electronique():
    return send_file('electronique.html')
@app.route('/vetements')
def vetements():
    return send_file('vetements.html')
@app.route('/maison')
def maison():
    return send_file('maison.html')
@app.route('/cuisine')
def cuisine():
    return send_file('cuisine.html')
@app.route('/api/products')
def get_products():
    return jsonify(products)
@app.route('/api/my_products')
def get_my_products():
    username = request.args.get('username')
    pwd = request.args.get('password')
    if not username or not pwd or username not in users or users[username]['password'] != pwd:
        return jsonify({'error': 'Auth requise'}), 401
    my = [p for p in products if p['username'] == username]
    return jsonify(my)
@app.route('/api/my_orders')
def get_my_orders():
    username = request.args.get('username')
    pwd = request.args.get('password')
    if not username or not pwd or username not in users or users[username]['password'] != pwd:
        return jsonify({'error': 'Auth requise'}), 401
    my = [o for o in orders if o.get('username') == username]
    return jsonify(my)
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
# ==================== ENDPOINT PUBLISH MODIFIÉ POUR AUTO-CRÉATION UTILISATEUR ====================
@app.route('/publish', methods=['POST'])
def publish():
    if 'image' not in request.files or not request.files['image'].filename:
        return jsonify({'error': 'Image requise'}), 400
    username = request.form.get('username')
    password = request.form.get('password')
    title = request.form.get('title')
    price = request.form.get('price')
    shipping_price = request.form.get('shipping_price')
    category = request.form.get('category')
    stock = request.form.get('stock')
    desc = request.form.get('desc')
    if not all([username, password, title, price, shipping_price, category, stock, desc]):
        return jsonify({'error': 'Tous les champs sont requis'}), 400
    # === NOUVELLE FONCTIONNALITÉ : Crée l'utilisateur automatiquement s'il n'existe pas ===
    if username not in users:
        print(f"[AUTO-REGISTER] Création automatique de l'utilisateur : {username}")
        users[username] = {'password': password, 'avatar': None}
    # Vérifie maintenant le mot de passe (même si nouvel utilisateur, il est bon)
    if users[username]['password'] != password:
        return jsonify({'error': 'Mot de passe incorrect'}), 401
    # Tout est bon → on publie le produit
    image_file = request.files['image']
    image_data = image_file.read()
    mimetype = image_file.mimetype or 'image/jpeg'
    b64 = b64encode(image_data).decode('utf-8')
    image_base64 = f"data:{mimetype};base64,{b64}"
    product = {
        'id': str(uuid.uuid4()),
        'username': username,
        'title': title,
        'price': float(price),
        'shipping_price': float(shipping_price),
        'category': category,
        'stock': int(stock),
        'desc': desc,
        'image_base64': image_base64,
        'time': datetime.datetime.now().isoformat(),
        'avatar': users[username].get('avatar')
    }
    products.append(product)
    save_data()
    print(f"[PUBLISH] Produit publié par {username} : {title}")
    return jsonify({'success': True})
# Le reste du code reste 100% identique
@app.route('/delete_product', methods=['POST'])
def delete_product():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    product_id = data.get('product_id')
    if not username or not password or not product_id:
        return jsonify({'error': 'Champs requis'}), 400
    if username not in users or users[username]['password'] != password:
        return jsonify({'error': 'Authentification requise'}), 401
    global products
    products = [p for p in products if not (p['id'] == product_id and p['username'] == username)]
    save_data()
    return jsonify({'success': True})
@app.route('/edit_product', methods=['POST'])
def edit_product():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    product_id = data.get('product_id')
    updates = data.get('updates')
    if not username or not password or not product_id or not updates:
        return jsonify({'error': 'Champs requis'}), 400
    if username not in users or users[username]['password'] != password:
        return jsonify({'error': 'Authentification requise'}), 401
    for p in products:
        if p['id'] == product_id and p['username'] == username:
            for key, value in updates.items():
                if key in ['price', 'shipping_price']:
                    value = float(value)
                elif key == 'stock':
                    value = int(value)
                p[key] = value
            save_data()
            return jsonify({'success': True})
    return jsonify({'error': 'Produit non trouvé'}), 404
@app.route('/submit_order', methods=['POST'])
def submit_order():
    data = request.get_json()
    if not data.get('items') or not data.get('total'):
        return jsonify({'error': 'Données invalides'}), 400
    data['time'] = datetime.datetime.now().isoformat()
    orders.append(data)
    save_data()
    return jsonify({'success': True})
@app.route('/api/messages')
def api_messages():
    with_u = request.args.get('with')
    username = request.args.get('username')
    pwd = request.args.get('password')
    if not all([with_u, username, pwd]):
        return jsonify({'error': 'Auth requise'}), 401
    if username not in users or users[username]['password'] != pwd:
        return jsonify({'error': 'Auth requise'}), 401
    conv_msgs = [m for m in messages if set([m['from'], m['to']]) == set([username, with_u])]
    conv_msgs.sort(key=lambda m: m['time'])
    return jsonify(conv_msgs)
@app.route('/api/conversations')
def api_conversations():
    username = request.args.get('username')
    pwd = request.args.get('password')
    if not username or not pwd:
        return jsonify({'error': 'Auth requise'}), 401
    if username not in users or users[username]['password'] != pwd:
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
    if not username or username not in users or users[username]['password'] != password:
        return False
    connected_users[request.sid] = username
    join_room(username)
    print(f"[SOCKET] {username} connecté (sid {request.sid})")
    return True
@socketio.on('disconnect')
def handle_disconnect():
    connected_users.pop(request.sid, None)
    print(f"[SOCKET] Déconnexion {request.sid}")
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
    emit('new_message', msg, room=username)
    if to != username:
        emit('new_message', msg, room=to)
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
