from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import datetime

app = Flask(__name__)

DB_NAME = 'unilu.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    matricule TEXT UNIQUE NOT NULL,
                    nom TEXT NOT NULL,
                    post_nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    promotion TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    matricule TEXT NOT NULL,
                    course TEXT NOT NULL,
                    result_type TEXT NOT NULL 
                        CHECK(result_type IN ('td', 'tp', 'application', 'interrogation', 'examen')),
                    cote REAL NOT NULL,
                    ponderation INTEGER NOT NULL,
                    publication_date TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return send_from_directory('page', 'style.html')

@app.route('/perso.html')
def perso():
    return send_from_directory('page', 'perso.html')

# Debug : voir tous les résultats
@app.route('/api/all_results', methods=['GET'])
def all_results():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM results ORDER BY course, result_type, publication_date DESC")
    rows = c.fetchall()
    conn.close()
    data = [{
        "id": r[0], "matricule": r[1], "course": r[2], "type": r[3],
        "cote": r[4], "ponderation": r[5], "date": r[6]
    } for r in rows]
    print("=== DEBUG : Résultats dans la base ===", data)
    return jsonify(data)

@app.route('/api/register_student', methods=['POST'])
def register_student():
    data = request.json
    nom = data['nom'].strip().upper()
    post_nom = data['post_nom'].strip().upper()
    prenom = data['prenom'].strip().upper()
    promotion = data['promotion']

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM students")
    max_id = c.fetchone()[0] or 0
    new_id = max_id + 1
    year = datetime.datetime.now().year % 100
    matricule = f"UNILU{year}{promotion}{new_id:04d}"

    try:
        c.execute("""INSERT INTO students (matricule, nom, post_nom, prenom, promotion)
                     VALUES (?, ?, ?, ?, ?)""", (matricule, nom, post_nom, prenom, promotion))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'matricule': matricule})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Étudiant déjà enregistré'}), 400

@app.route('/api/students', methods=['GET'])
def get_students():
    promotion = request.args.get('promotion')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if promotion:
        c.execute("SELECT matricule, nom, post_nom, prenom FROM students WHERE promotion=? ORDER BY nom", (promotion,))
    else:
        c.execute("SELECT matricule, nom, post_nom, prenom FROM students ORDER BY promotion, nom")
    students = [{'matricule': row[0], 'nom': row[1], 'post_nom': row[2], 'prenom': row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(students)

@app.route('/api/validate_matricule', methods=['POST'])
def validate_matricule():
    data = request.json
    matricule = data.get('matricule')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nom, post_nom, prenom FROM students WHERE matricule=?", (matricule,))
    student = c.fetchone()
    conn.close()
    if student:
        return jsonify({'success': True, 'nom_complet': f"{student[2]} {student[0]} {student[1]}"})
    return jsonify({'success': False}), 404

@app.route('/api/publish_result', methods=['POST'])
def publish_result():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    date_pub = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("""INSERT INTO results (matricule, course, result_type, cote, ponderation, publication_date)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (data['matricule'], data['course'], data['result_type'], data['cote'],
               data['ponderation'], date_pub))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/get_results', methods=['GET'])
def get_results():
    matricule = request.args.get('matricule')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT course, result_type, cote, ponderation, publication_date
                 FROM results WHERE matricule=? ORDER BY course, result_type, publication_date DESC""", (matricule,))
    rows = c.fetchall()
    conn.close()
    results = [{
        'course': r[0],
        'type': r[1],
        'cote': r[2],
        'ponderation': r[3],
        'date': r[4],
        'status': 'ÉCHEC' if r[2] < r[3]/2 else 'RÉUSSITE'
    } for r in rows]
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
