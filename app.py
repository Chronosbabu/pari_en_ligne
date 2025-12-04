# app.py - FICHIER COMPLET 100% FONCTIONNEL
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
TEMPLATES_DIR = 'templates'

# Créer le dossier templates s'il n'existe pas
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

# Mapping pour noms de fichiers safe
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
    template_map = {
        "Électronique": "electronique_template.html",
        "Vêtements": "vetements.html",
        "Maison": "maison.html",
        "Cuisine": "cuisine.html"
    }
    template_path = os.path.join(os.getcwd(), template_map.get(main_cat, ""))
    if not os.path.exists(template_path):
        print(f"ERREUR : Template manquant → {template_path}")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    safe_name = custom_safe.get(sub_cat, sub_cat.lower().replace(" ", "_").replace("&", "et"))
    filename = f"{safe_name}.html"
    filepath = os.path.join(TEMPLATES_DIR, filename)

    # Remplacements nécessaires
    content = content.replace("Vêtements - Mon E-Shop", f"{sub_cat} - Mon E-Shop")
    content = content.replace("Électronique - Mon E-Shop", f"{sub_cat} - Mon E-Shop")
    content = content.replace(">Vêtements<", f">{sub_cat}<")
    content = content.replace(">Électronique<", f">{sub_cat}<")
    content = content.replace('let currentSubcat = null;', f'let currentSubcat = "{sub_cat}";')
    content = content.replace('loadSubcategories();', '')
    content = content.replace('<div class="d-flex flex-wrap justify-content-center mb-5" id="subcategories"></div>', '')
    content = content.replace('function loadAll() { currentSubcat = null; loadProducts(); }', '')
    content = content.replace('function filterSubcat(sub) { currentSubcat = sub; loadProducts(); }', '')

    # Filtre strict sur catégorie + sous-catégorie
    pattern = rf"p\.category\s*===?\s*[\'\"]{re.escape(main_cat)}[\'\"]"
    replacement = f"p.category === '{main_cat}' && p.subcategory === '{sub_cat}'"
    content = re.sub(pattern, replacement, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Page générée avec succès → {filepath}")

# === CRÉATION FORCÉE DES SOUS-CATÉGORIES AU DÉMARRAGE ===
predefined = {
    "Électronique": ["Ordinateurs", "Téléphones", "Montres et Accessoires"],
    "Vêtements": ["Hommes", "Femmes", "Enfants"],
    "Maison": [],
    "Cuisine": ["Nourritures préparées", "Nourritures à préparer"]
}

for main_cat, subs in predefined.items():
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

# Routes directes pour les sous-catégories vêtements (les plus utilisées)
@app.route('/homme')
def homme():
    path = os.path.join(TEMPLATES_DIR, "homme.html")
    if os.path.exists(path):
        return send_file(path)
    return "Page homme non trouvée", 404

@app.route('/femme')
def femme():
    path = os.path.join(TEMPLATES_DIR, "femme.html")
    if os.path.exists(path):
        return send_file(path)
    return "Page femme non trouvée", 404

@app.route('/enfant')
def enfant():
    path = os.path.join(TEMPLATES_DIR, "enfant.html")
    if os.path.exists(path):
        return send_file(path)
    return "Page enfant non trouvée", 404

# Route générique pour toutes les autres sous-catégories
@app.route('/<page>')
def dynamic_page(page):
    if page in ["homme", "femme", "enfant", "ordinateur", "telephone", "manger", "preparer", "montre_et_autres"]:
        filepath = os.path.join(TEMPLATES_DIR, f"{page}.html")
    else:
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
            return jsonify({'error': 'Catégorie principale invalide'}), 400
        if sub_cat in subcategories[main_cat]:
            return jsonify({'error': 'Sous-catégorie existe déjà'}), 400

        if username not in users:
            users[username] = {'phone': phone}
        elif users[username].get('phone') != phone:
            return jsonify({'error': 'Numéro WhatsApp incorrect'}), 401

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
            return jsonify({'error': 'Tous les champs obligatoires'}), 400

        if username not in users:
            users[username] = {'phone': phone}
        elif users[username].get('phone') != phone:
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
            'subcategory': subcategory,
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
    print("Démarrage du serveur E-Shop...")
    print("Pages sous-catégories générées : homme.html, femme.html, enfant.html, etc.")
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
