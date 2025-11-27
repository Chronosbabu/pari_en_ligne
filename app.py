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
TEMPLATES_DIR = 'templates'
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Chargement données
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

# Mapping pour les noms de fichiers propres
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
    templates = {
        "Électronique": "electronique.html",
        "Vêtements": "vetements.html",
        "Maison": "maison.html",
        "Cuisine": "cuisine.html"
    }
    template_path = templates.get(main_cat)
    if not template_path or not os.path.exists(template_path):
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    safe_subcat = custom_safe.get(sub_cat, "".join(c for c in sub_cat if c.isalnum() or c in " -_").replace(" ", "_").lower())
    filename = f"{safe_subcat}.html"
    filepath = os.path.join(TEMPLATES_DIR, filename)

    if os.path.exists(filepath):
        return

    content = content.replace(f"{main_cat} - Mon E-Shop", f"{sub_cat} - Mon E-Shop")
    content = content.replace(f">{main_cat}<", f">{sub_cat}<")
    if main_cat == "Cuisine":
        content = content.replace(">Cuisine & Ustensiles<", f">{sub_cat}<")

    # Fixe le filtre sur cette sous-catégorie uniquement
    content = content.replace('let currentSubcat = null;', f'let currentSubcat = "{sub_cat}";')
    content = content.replace('loadSubcategories();', '')
    content = content.replace('<div class="d-flex flex-wrap justify-content-center mb-5" id="subcategories"></div>', '')
    content = content.replace('function loadAll() { currentSubcat = null; loadProducts(); }', '')
    content = content.replace('function filterSubcat(sub) { currentSubcat = sub; loadProducts(); }', '')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Sous-catégories prédéfinies au démarrage
predefined = {
    "Électronique": ["Ordinateurs", "Téléphones", "Montres et Accessoires"],
    "Vêtements": ["Hommes", "Femmes", "Enfants"],
    "Cuisine": ["Nourritures préparées", "Nourritures à préparer"]
}
for main, subs in predefined.items():
    for sub in subs:
        if sub not in subcategories.get(main, []):
            subcategories[main].append(sub)
        create_subcategory_page(main, sub)

save_data()

# Routes pages principales
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

@app.route('/<page>')
def dynamic_page(page):
    filepath = os.path.join(TEMPLATES_DIR, f"{page}.html")
    if os.path.exists(filepath):
        return send_file(filepath)
    return "Page non trouvée", 404

# API
@app.route('/api/products')
def get_products():
    return jsonify(products)

@app.route('/api/subcategories')
def get_subcategories():
    main = request.args.get('main')
    return jsonify(subcategories.get(main, []))

@app.route('/api/add_subcategory', methods=['POST'])
def add_subcategory():
    try:
        data = request.get_json()
        main_cat = data.get('main_category')
        sub_cat = data.get('subcategory', '').strip()
        username = data.get('username')
        phone = data.get('phone')

        if main_cat not in subcategories or not sub_cat:
            return jsonify({'error': 'Données invalides'}), 400

        if sub_cat in subcategories[main_cat]:
            return jsonify({'error': 'Existe déjà'}), 400

        if username not in users:
            users[username] = {'phone': phone}
        elif users[username].get('phone') != phone:
            return jsonify({'error': 'Numéro incorrect'}), 401

        subcategories[main_cat].append(sub_cat)
        save_data()
        create_subcategory_page(main_cat, sub_cat)

        safe = custom_safe.get(sub_cat, "".join(c for c in sub_cat if c.isalnum() or c in " -_").replace(" ", "_").lower())
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
        subcategory = request.form.get('subcategory', '').strip()  # déjà vidé
        stock = request.form.get('stock')
        desc = request.form.get('desc')
        image = request.files.get('image')

        required = [username, phone, title, price, shipping_price, category, stock, desc, image]
        if not all(required):
            return jsonify({'error': 'Tous les champs sont obligatoires'}), 400

        # Vérification vendeur
        if username not in users:
            users[username] = {'phone': phone}
        elif users[username].get('phone') != phone:
            return jsonify({'error': 'Numéro WhatsApp incorrect'}), 401

        # Image en base64
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
            'subcategory': subcategory or "",   # LA CORRECTION MAGIQUE : plus jamais null !
            'stock': int(stock),
            'desc': desc,
            'image_base64': image_base64,
            'time': datetime.datetime.now().isoformat()
        }

        products.append(product)
        save_data()

        return jsonify({'success': True, 'message': 'Produit publié avec succès !'})

    except Exception as e:
        print("Erreur publish:", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
