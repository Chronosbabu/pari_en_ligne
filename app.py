# app.py  → FICHIER COMPLET ET CORRIGÉ (décembre 2025)

from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO
import datetime
from base64 import b64encode
import json
import os
import uuid
import re

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DATA_FILE = 'data.json'
TEMPLATES_DIR = 'templates'  # dossier où sont générés ordinateur.html, telephone.html, etc.

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

# Mapping noms → noms de fichiers safe
custom_safe = {
    "Ordinateurs": "ordinateur",
    "Téléphones": "telephone",
    "Montres et Accessoires": "montre_et_autres",
    "Hommes": "homme",
    "Femmes": "femme",
    "Enfants": "enfant",
    "Nourritures préparées": "manger",
    "Nourritures à préparer": "preparer",
}

def create_subcategory_page(main_cat, sub_cat):
    # Le template qui sera copié pour chaque sous-catégorie
    template_map = {
        "Électronique": "electronique_template.html",   # CE FICHIER DOIT EXISTER !
        "Vêtements": "vetements_template.html",
        "Maison": "maison_template.html",
        "Cuisine": "cuisine_template.html",
    }

    template_path = template_map.get(main_cat)
    if not template_path or not os.path.exists(template_path):
        print(f"Modèle manquant pour {main_cat} → {template_path}")
        return

    safe_name = custom_safe.get(sub_cat, re.sub(r'\W+', '_', sub_cat.lower()))
    filename = f"{safe_name}.html"
    filepath = os.path.join(TEMPLATES_DIR, filename)

    if os.path.exists(filepath):
        return  # déjà créé

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Personnalisation du titre et du filtre JS
    content = content.replace("{{SUBCATEGORY}}", sub_cat)
    content = content.replace("{{MAIN_CATEGORY}}", main_cat)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Page créée → {filename}")

# Création automatique des sous-catégories au démarrage
predefined = {
    "Électronique": ["Ordinateurs", "Téléphones", "Montres et Accessoires"],
    "Vêtements": ["Hommes", "Femmes", "Enfants"],
    "Maison": [],
    "Cuisine": ["Nourritures préparées", "Nourritures à préparer"]
}

for main_cat, subs in predefined.items():
    for sub in subs:
        if sub not in subcategories[main_cat]:
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

# Route dynamique pour ordinateur / telephone / montre_et_autres etc.
@app.route('/<page>')
def dynamic_page(page):
    # D'abord on regarde dans le dossier templates
    path = os.path.join(TEMPLATES_DIR, f"{page}.html")
    if os.path.exists(path):
        return send_file(path)
    # Sinon on laisse Flask chercher normalement (pour style.html, electronique.html, etc.)
    try:
        return send_file(page)
    except:
        return "Page non trouvée", 404

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

        if not main_cat or main_cat not in subcategories:
            return jsonify({'error': 'Catégorie invalide'}), 400
        if not sub_cat:
            return jsonify({'error': 'Nom requis'}), 400
        if sub_cat in subcategories[main_cat]:
            return jsonify({'error': 'Existe déjà'}), 400

        if username not in users:
            users[username] = {'phone': phone}
        if users[username].get('phone') != phone:
            return jsonify({'error': 'Numéro incorrect'}), 401

        subcategories[main_cat].append(sub_cat)
        create_subcategory_page(main_cat, sub_cat)
        save_data()

        safe = custom_safe.get(sub_cat, re.sub(r'\W+', '_', sub_cat.lower()))
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
            return jsonify({'error': 'Tous les champs obligatoires'}), 400

        if username not in users:
            users[username] = {'phone': phone}
        if users[username].get('phone') != phone:
            return jsonify({'error': 'Numéro WhatsApp incorrect'}), 401

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
            'subcategory': subcategory or "",
            'stock': int(stock),
            'desc': desc,
            'image_base64': image_base64,
            'time': datetime.datetime.now().isoformat()
        }
        products.append(product)
        save_data()
        return jsonify({'success': True, 'message': 'Produit publié !'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ====================== LANCEMENT ======================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
