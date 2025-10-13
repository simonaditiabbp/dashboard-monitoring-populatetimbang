from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from dotenv import load_dotenv
import mysql.connector
import os
from datetime import datetime, timedelta

load_dotenv()
app = Flask(__name__)

# ====== Load konfigurasi dari .env ======
MYSQL_CONN = {
    'host': os.getenv("MYSQL_HOST"),
    'user': os.getenv("MYSQL_USER"),
    'password': os.getenv("MYSQL_PASS"),
    'database': os.getenv("MYSQL_DB"),
}

app.secret_key = os.getenv("FLASK_SECRET", "defaultsecret")
LOGIN_USER = os.getenv("LOGIN_USER", "admin")
LOGIN_PASS = os.getenv("LOGIN_PASS", "12345")

heartbeats = {}  

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))
    
    if request.method == 'POST':
        user = request.form.get("username")
        password = request.form.get("password")
        if user == LOGIN_USER and password == LOGIN_PASS:
            session["logged_in"] = True
            session["username"] = user
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Username atau password salah.")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/logs')
def get_logs():
    conn = mysql.connector.connect(**MYSQL_CONN)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT NOURUT1, PLANT_ID, AKSI, LOG_TIME, MESSAGE, STATUS FROM tb_timbang2_log ORDER BY LOG_TIME DESC")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'data': result})  # ✅ penting: bungkus di 'data'


@app.route('/api/status')
def get_status():
    now = datetime.now()
    # result = {
    #     'timbang1': 'OFFLINE',
    #     'timbang2': 'OFFLINE'
    # }
    
    result = {}
    for pc, last_beat in heartbeats.items():
        if (now - last_beat) < timedelta(seconds=20):
            status = 'ONLINE'
        else:
            status = 'OFFLINE'
            
        result[pc] = {
            "status": status,
            "last_seen": last_beat.strftime("%Y-%m-%d %H:%M:%S"),
            "ago_seconds": int((now - last_beat).total_seconds())
        }

    return jsonify(result)

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    name = data.get('pc_name')
    name = name.lower() if name else None
    if name:
        heartbeats[name] = datetime.now()
        print(f"💓 Heartbeat diterima dari {name} pada {datetime.now().strftime('%H:%M:%S')}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "pc_name missing"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)