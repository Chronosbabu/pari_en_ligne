# app.py - VERSION CORRIGÉE ET OPTIMISÉE 100% FONCTIONNELLE
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_socketio import SocketIO
import datetime
from base64 import b64encode
import json
import os
import uuid
import re

app = Flask(__name__, static_folder=None)  # Important pour send_file correct
socketio = SocketIO(app, cors_allowed_origins="*")

DATA_FILE = 'data.json'
TEMPLATES_DIR = 'templates'
os.makedirs(TEMPLATES_DIR, exist_ok=True)

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
            "Vêtements": ["Hommes", "Femmes", "Enfants"],
            "Maison": [],
            "Cuisine": []
        })
else:
    users = {}
    products = []
    messages = []
    orders = []
    subcategories = {
        "Électronique": ["Ordinateurs", "Téléphones", "Montres et Accessoires"],
        "Vêtements": ["Hommes", "Femmes", "Enfants"],
        "Maison": [],
        "Cuisine": ["Nourritures préparées", "Nourritures à préparer"]
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

# Mapping pour URLs propres
custom_safe = {
    "Ordinateurs": "ordinateurs",
    "Téléphones": "telephones",
    "Montres et Accessoires": "montres",
    "Hommes": "homme",
    "Femmes": "femme",
    "Enfants": "enfant",
    "Nourritures préparées": "manger",
    "Nourritures à préparer": "preparer",
}

def create_subcategory_page(main_cat, sub_cat):
    template_map = {
        "Électronique": "electronique_template.html",
        "Vêtements": "vetements_template.html",
        "Maison": "maison_template.html",
        "Cuisine": "cuisine_template.html"
    }
    template_name = template_map.get(main_cat)
    if not template_name:
        print(f"Template non trouvé pour {main_cat}")
        return
    template_path = os.path.join(os.getcwd(), template_name)
    if not os.path.exists(template_path):
        print(f"ERREUR : Template manquant → {template_path}")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    safe_name = custom_safe.get(sub_cat, sub_cat.lower().replace(" ", "_").replace("&", "et"))
    filename = f"{safe_name}.html"
    filepath = os.path.join(TEMPLATES_DIR, filename)

    # Remplacements dynamiques
    content = content.replace("{{PAGE_TITLE}}", f"{sub_cat} - Mon E-Shop")
    content = content.replace("{{MAIN_CATEGORY}}", main_cat)
    content = content.replace("{{SUBCATEGORY}}", sub_cat)
    content = content.replace("{{BACK_LINK}}", "/vetements" if main_cat == "Vêtements" else f"/{main_cat.lower()}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Page générée → {filepath}")

# Générer toutes les sous-catégories au démarrage
for main_cat, subs in [
    ("Électronique", ["Ordinateurs", "Téléphones", "Montres et Accessoires"]),
    ("Vêtements", ["Hommes", "Femmes", "Enfants"]),
    ("Cuisine", ["Nourritures préparées", "Nourritures à préparer"])
]:
    for sub in subs:
        if sub not in subcategories.get(main_cat, []):
            subcategories[main_cat].append(sub)
        create_subcategory_page(main_cat, sub)

save_data()

# ====================== ROUTES ======================
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

# Routes directes pour sous-catégories populaires
@app.route('/homme')
def homme():
    return send_from_directory(TEMPLATES_DIR, 'homme.html')

@app.route('/femme')
def femme():
    return send_from_directory(TEMPLATES_DIR, 'femme.html')

@app.route('/enfant')
def enfant():
    return send_from_directory(TEMPLATES_DIR, 'enfant.html')

# Route générique pour toutes les sous-catégories
@app.route('/<path:page>')
def dynamic_page(page):
    filepath = os.path.join(TEMPLATES_DIR, f"{page}.html")
    if os.path.exists(filepath):
        return send_file(filepath)
    return f"Page /{page} non trouvée", 404

# ====================== API ======================
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

        if not all([main_cat, sub_cat, username, phone]):
            return jsonify({'error': 'Données manquantes'}), 400
        if main_cat not in subcategories:
            return jsonify({'error': 'Catégorie invalide'}), 400
        if sub_cat in subcategories[main_cat]:
            return jsonify({'error': 'Existe déjà'}), 400

        if username not in users:
            users[username] = {'phone': phone}
        elif users[username].get('phone') != phone:
            return jsonify({'error': 'Numéro incorrect'}), 401

        subcategories[main_cat].append(sub_cat)
        save_data()
        create_subcategory_page(main_cat, sub_cat)
        safe = custom_safe.get(sub_cat, sub_cat.lower().replace(" ", "_"))
        return jsonify({'success': True, 'url': f'/{safe}'})
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
            return jsonify({'error': 'Champs manquants'}), 400

        if username not in users:
            users[username] = {'phone': phone}
        elif users[username].get('phone') != phone:
            return jsonify({'error': 'Numéro incorrect'}), 401

        image_data = image.read()
        b64 = b64encode(image_data).decode()
        image_base64 = f"data:{image.mimetype};base64,{b64}"

        product = {
            'id': str(uuid.uuid4()),
            'username': username,
            'phone': phone.replace("+", "").replace(" ", ""),
            'title': title,
            'price': float(price),
            'shipping_price': float(shipping_price),
            'category': category,
            'subcategory': subcategory or "Autres",
            'stock': int(stock),
            'desc': desc,
            'image_base64': image_base64,
            'time': datetime.datetime.now().isoformat()
        }
        products.append(product)
        save_data()
        return jsonify({'success': True, 'message': 'Publié !'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Serveur E-Shop démarré → http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
