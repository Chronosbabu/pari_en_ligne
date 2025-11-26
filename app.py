from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO
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
        subcategories = data.get('subcategories', {
            "Électronique": [],
            "Vêtements": [],
            "Maison": [],
            "Cuisine": []
        })
else:
    users = {}
    products = []
    messages = []
    orders = []
    subcategories = {
        "Électronique": [],
        "Vêtements": [],
        "Maison": [],
        "Cuisine": []
    }
def save_data():
    data = {
        'users': users,
        'products': products,
        'messages': messages,
        'orders': orders,
        'subcategories': subcategories
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
# === Pages HTML ===
@app.route('/')
def index():
    return send_file('style.html')
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
# === API ===
@app.route('/api/products')
def get_products():
    return jsonify(products)
@app.route('/api/subcategories')
def get_subcategories():
    main = request.args.get('main')
    if main in subcategories:
        return jsonify(subcategories[main])
    return jsonify([])
@app.route('/api/add_subcategory', methods=['POST'])
def add_subcategory():
    try:
        data = request.get_json()
        main_cat = data.get('main_category')
        sub_cat = data.get('subcategory', '').strip()
        username = data.get('username')
        phone = data.get('phone')
        if not main_cat or main_cat not in subcategories:
            return jsonify({'error': 'Catégorie principale invalide'}), 400
        if not sub_cat:
            return jsonify({'error': 'Nom de sous-catégorie requis'}), 400
        if sub_cat in subcategories[main_cat]:
            return jsonify({'error': 'Cette sous-catégorie existe déjà'}), 400
        # Création auto de l'utilisateur s'il n'existe pas
        if username not in users:
            users[username] = {'phone': phone}
        if users[username]['phone'] != phone:
            return jsonify({'error': 'Numéro WhatsApp incorrect'}), 401
        subcategories[main_cat].append(sub_cat)
        save_data()
        return jsonify({'success': True, 'message': f'Sous-catégorie "{sub_cat}" ajoutée !'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/publish', methods=['POST'])
def publish():
    try:
        username = request.form.get('username')
        phone = request.form.get('phone')
        title = request.form.get('title')
        price = request.form.get('price')
        shipping_price = request.form.get('shipping_price')
        category = request.form.get('category')
        subcategory = request.form.get('subcategory', '').strip()
        stock = request.form.get('stock')
        desc = request.form.get('desc')
        image = request.files.get('image')
        if not all([username, phone, title, price, shipping_price, category, stock, desc, image]):
            return jsonify({'error': 'Tous les champs sont obligatoires'}), 400
        # Auto-création utilisateur
        if username not in users:
            users[username] = {'phone': phone}
        if users[username]['phone'] != phone:
            return jsonify({'error': 'Numéro WhatsApp incorrect'}), 401
        # Traitement image
        image_data = image.read()
        b64 = b64encode(image_data).decode()
        image_base64 = f"data:{image.mimetype};base64,{b64}"
        product = {
            'id': str(uuid.uuid4()),
            'username': username,
            'phone': phone,
            'title': title,
            'price': float(price),
            'shipping_price': float(shipping_price),
            'category': category,
            'subcategory': subcategory if subcategory else None,
            'stock': int(stock),
            'desc': desc,
            'image_base64': image_base64,
            'time': datetime.datetime.now().isoformat()
        }
        products.append(product)
        save_data()
        return jsonify({'success': True, 'message': 'Produit publié avec succès !'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
