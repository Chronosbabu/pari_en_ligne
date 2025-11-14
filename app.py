from flask import Flask, request, jsonify, send_file
import datetime
from base64 import b64encode
import json
import os

app = Flask(__name__)

DATA_FILE = 'data.json'

# Chargement des données
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        users = data.get('users', {})
        posts = data.get('posts', [])
else:
    users = {}
    posts = []

def save_data():
    data = {'users': users, 'posts': posts}
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def index():
    return send_file('style.html')

@app.route('/api/posts')
def get_posts():
    return jsonify(posts)

@app.route('/publish', methods=['POST'])
def publish():
    if 'image' not in request.files or not request.files['image'].filename:
        return jsonify({'error': 'Image requise'}), 400

    username = request.form.get('username')
    password = request.form.get('password')
    title = request.form.get('title')
    price = request.form.get('price')
    shipping_price = request.form.get('shipping_price')

    if not all([username, password, title, price, shipping_price]):
        return jsonify({'error': 'Tous les champs sont requis'}), 400

    # Inscription / connexion auto
    if username in users:
        if users[username] != password:
            return jsonify({'error': 'Mot de passe incorrect'}), 401
    else:
        users[username] = password

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
        'time': datetime.datetime.now().isoformat()
    }
    posts.append(post)
    save_data()

    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
