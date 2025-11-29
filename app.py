from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_socketio import SocketIO
import datetime
from base64 import b64encode
import json
import os
import uuid
import shutil
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
DATA_FILE = 'data.json'
TEMPLATES_DIR = 'templates' # Dossier où seront générés les fichiers HTML
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
# Dictionnaire pour safe custom afin de matcher tes noms de fichiers
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
# === Création des pages HTML pour chaque sous-catégorie ===
def create_subcategory_page(main_cat, sub_cat):
    # Choisir le template en fonction de la catégorie principale
    if main_cat == "Électronique":
        template_path = "electronique.html"
    elif main_cat == "Vêtements":
        template_path = "vetements.html"
    elif main_cat == "Maison":
        template_path = "maison.html"
    elif main_cat == "Cuisine":
        template_path = "cuisine.html"
    else:
        return
    if not os.path.exists(template_path):
        print(f"Modèle manquant : {template_path}")
        return
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Safe avec custom si disponible
    safe_subcat = custom_safe.get(sub_cat, "".join(c for c in sub_cat if c.isalnum() or c in " -*").replace(" ", "*").lower())
    filename = f"{safe_subcat}.html"
    filepath = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(filepath):
        return # Déjà existe
    # Remplacements pour adapter à la sous-catégorie
    content = content.replace(f"{main_cat} - Mon E-Shop", f"{sub_cat} - Mon E-Shop")
    content = content.replace(f">{main_cat}<", f">{sub_cat}<") # Pour h2, approx
    if main_cat == "Cuisine":
        content = content.replace(">Cuisine & Ustensiles<", f">{sub_cat}<")
    content = content.replace(f"main={main_cat}", f"main={main_cat}") # Déjà ok
    content = content.replace(f"p.category === '{main_cat}'", f"p.category === '{main_cat}'") # Déjà ok
    # Pour page de sous-catégorie : fixer le filtre, supprimer boutons
    content = content.replace('let currentSubcat = null;', f'let currentSubcat = "{sub_cat}";')
    content = content.replace('loadSubcategories();', '')
    content = content.replace('<div class="d-flex flex-wrap justify-content-center mb-5" id="subcategories"></div>', '')
    content = content.replace('function loadAll() { currentSubcat = null; loadProducts(); }', '')
    content = content.replace('function filterSubcat(sub) { currentSubcat = sub; loadProducts(); }', '')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Page créée : {filename}")
# Ajout des sous-catégories prédéfinies au démarrage
predefined_subcats = {
    "Électronique": ["Ordinateurs", "Téléphones", "Montres et Accessoires"],
    "Vêtements": ["Hommes", "Femmes", "Enfants"],
    "Maison": [],
    "Cuisine": ["Nourritures préparées", "Nourritures à préparer"]
}
for main, subs in predefined_subcats.items():
    for sub in subs:
        if sub not in subcategories.get(main, []):
            subcategories[main].append(sub)
        create_subcategory_page(main, sub)
save_data()
# === Pages statiques principales ===
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
# === Route dynamique pour les sous-catégories créées ===
@app.route('/<subcat_page>')
def dynamic_subcategory_page(subcat_page):
    filepath = os.path.join(TEMPLATES_DIR, f"{subcat_page}.html")
    if os.path.exists(filepath):
        return send_file(filepath)
    return "Page non trouvée", 404
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
        # Vérification vendeur
        if username not in users:
            users[username] = {'phone': phone}
        if users[username].get('phone') != phone:
            return jsonify({'error': 'Numéro WhatsApp incorrect'}), 401
        # Ajouter la sous-catégorie
        subcategories[main_cat].append(sub_cat)
        save_data()
        # Créer la page HTML réelle automatiquement
        create_subcategory_page(main_cat, sub_cat)
        safe_subcat = custom_safe.get(sub_cat, "".join(c for c in sub_cat if c.isalnum() or c in " -*").replace(" ", "*").lower())
        return jsonify({
            'success': True,
            'message': f'Sous-catégorie "{sub_cat}" ajoutée !',
            'url': f'/{safe_subcat}'
        })
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
        return jsonify({'success': True, 'message': 'Produit publié avec succès !'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
