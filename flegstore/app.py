from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory
import sqlite3
import jwt
import datetime
import random
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Shadowh2501'  # CHANGE this in production!
app.config['SESSION_TYPE'] = 'filesystem'

# Rate limiter based on user session
def get_user_key():
    if 'token' in session:
        try:
            data = jwt.decode(session['token'], app.config['SECRET_KEY'], algorithms=['HS256'])
            return f"user:{data['user_id']}"
        except:
            return get_remote_address()
    return get_remote_address()

limiter = Limiter(
    app=app,
    key_func=get_user_key,
    default_limits=["200 per minute"],
    storage_uri="memory://"
)

# -------------------------------------------------------
# DATABASE UTILITIES
# -------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("database.db", isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # USERS table with hashed password
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0
        )
    """)

    # COUPONS table with redeemed flag
    c.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            redeemed INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # ITEMS table (flag.txt price = 70)
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price INTEGER NOT NULL
        )
    """)
    c.execute("INSERT OR IGNORE INTO items (name, price) VALUES (?, ?)", ("flag.txt", 70))

    # CART table
    c.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            price INTEGER NOT NULL,
            purchased INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------------------------------------------
# AUTH DECORATOR (JWT in session)
# -------------------------------------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            return redirect(url_for('login_page'))
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            flash("Session expired. Please log in again.", "warning")
            return redirect(url_for('login_page'))
        except:
            flash("Invalid session. Please log in again.", "danger")
            return redirect(url_for('login_page'))
        return f(user_id, *args, **kwargs)
    return decorated

# -------------------------------------------------------
# REGISTER / LOGIN / LOGOUT ROUTES
# -------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm  = request.form.get('confirm_password', '')

    if not username or not password or not confirm:
        flash("All fields are required.", "danger")
        return redirect(url_for('register'))
    if password != confirm:
        flash("Passwords do not match.", "danger")
        return redirect(url_for('register'))

    hashed = generate_password_hash(password)
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, balance) VALUES (?, ?, 0)",
            (username, hashed)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        flash("Username already taken.", "danger")
        return redirect(url_for('register'))
    conn.close()

    flash("Registration successful! Please log in.", "success")
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        flash("All fields are required.", "danger")
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    user = conn.execute("SELECT id, password FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        flash("Invalid credentials.", "danger")
        return redirect(url_for('login_page'))

    token = jwt.encode(
        {
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        },
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    session['token'] = token
    flash("Logged in successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/logout')
@token_required
def logout_page(user_id):
    session.pop('token', None)
    flash("Logged out.", "info")
    return redirect(url_for('login_page'))

# -------------------------------------------------------
# DASHBOARD
# -------------------------------------------------------
@app.route('/dashboard')
@token_required
def dashboard(user_id):
    conn = get_db_connection()
    balance_row = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
    coupons = conn.execute(
        "SELECT code, redeemed FROM coupons WHERE user_id = ? ORDER BY id DESC LIMIT 10",
        (user_id,)
    ).fetchall()
    conn.close()

    balance = balance_row['balance'] if balance_row else 0
    return render_template('dashboard.html', balance=balance, coupons=coupons)

# -------------------------------------------------------
# SHOP & CART
# -------------------------------------------------------
@app.route('/shop')
@token_required
def shop(user_id):
    conn = get_db_connection()
    items = conn.execute("SELECT name, price FROM items").fetchall()
    balance_row = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    balance = balance_row['balance'] if balance_row else 0
    return render_template('shop.html', items=items, balance=balance)

@app.route('/buy_flag', methods=['POST'])
@token_required
def buy_flag(user_id):
    conn = get_db_connection()
    conn.execute("INSERT INTO cart (user_id, item, price) VALUES (?, ?, ?)",
                 (user_id, "flag.txt", 70))
    conn.commit()
    conn.close()
    flash("Flag added to cart!", "success")
    return redirect(url_for('cart'))

@app.route('/cart')
@token_required
def cart(user_id):
    conn = get_db_connection()
    cart_items = conn.execute(
        "SELECT item, price, id FROM cart WHERE user_id = ? AND purchased = 0",
        (user_id,)
    ).fetchall()
    balance_row = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    balance = balance_row['balance'] if balance_row else 0
    total_cost = sum(row['price'] for row in cart_items)
    return render_template('cart.html', cart_items=cart_items, balance=balance, total_cost=total_cost)

@app.route('/checkout', methods=['POST'])
@token_required
def checkout(user_id):
    total_cost = int(request.form.get('total_cost', 0))
    conn = get_db_connection()
    balance_row = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
    if not balance_row or balance_row['balance'] < total_cost:
        conn.close()
        flash("Insufficient balance.", "danger")
        return redirect(url_for('cart'))

    conn.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (total_cost, user_id))
    conn.execute("UPDATE cart SET purchased = 1 WHERE user_id = ? AND item = 'flag.txt' AND purchased = 0", (user_id,))
    conn.commit()
    conn.close()
    flash("Purchase successful! You can now download the flag.", "success")
    return redirect(url_for('dashboard'))

# -------------------------------------------------------
# RACE‐CONDITION‐VULNERABLE COUPON GENERATION
# -------------------------------------------------------
@app.route('/generate_coupon', methods=['POST'])
@token_required
def generate_coupon(user_id):
    conn = get_db_connection()
    cnt = conn.execute(
        "SELECT COUNT(*) AS cnt FROM coupons WHERE user_id = ?",
        (user_id,)
    ).fetchone()['cnt']
    if cnt >= 5:
        conn.close()
        return jsonify({"error": "Coupon limit reached"}), 400

    coupon_code = f"COUPON{random.randint(10000, 99999)}"
    conn.execute("INSERT INTO coupons (user_id, code) VALUES (?, ?)", (user_id, coupon_code))
    conn.commit()
    conn.close()
    return jsonify({"coupon": coupon_code})

# -------------------------------------------------------
# REDEEM COUPON
# -------------------------------------------------------
@app.route('/redeem', methods=['GET', 'POST'])
@token_required
def redeem_page(user_id):
    if request.method == 'GET':
        conn = get_db_connection()
        balance_row = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
        balance = balance_row['balance'] if balance_row else 0
        conn.close()
        return render_template('redeem.html', balance=balance)

    coupon_code = request.form.get('coupon', '').strip()
    if not coupon_code:
        flash("Enter a coupon code.", "warning")
        return redirect(url_for('redeem_page'))

    conn = get_db_connection()
    coupon = conn.execute(
        "SELECT id FROM coupons WHERE user_id = ? AND code = ? AND redeemed = 0",
        (user_id, coupon_code)
    ).fetchone()

    if not coupon:
        conn.close()
        flash("Invalid or already redeemed coupon.", "danger")
        return redirect(url_for('redeem_page'))

    conn.execute("UPDATE users SET balance = balance + 10 WHERE id = ?", (user_id,))
    conn.execute("UPDATE coupons SET redeemed = 1 WHERE id = ?", (coupon['id'],))
    conn.commit()
    conn.close()

    flash("Coupon redeemed! +10 balance.", "success")
    return redirect(url_for('dashboard'))

# -------------------------------------------------------
# SERVE FLAG.TXT ONLY IF PURCHASED
# -------------------------------------------------------
@app.route('/flag.txt')
@token_required
def download_flag(user_id):
    conn = get_db_connection()
    purchased = conn.execute(
        "SELECT 1 FROM cart WHERE user_id = ? AND item = 'flag.txt' AND purchased = 1",
        (user_id,)
    ).fetchone()
    conn.close()

    if not purchased:
        flash("You must purchase the flag before downloading.", "danger")
        return redirect(url_for('shop'))

    return send_from_directory(
        directory=os.path.abspath(os.path.dirname(__file__)),
        path="flag.txt",
        as_attachment=True,
        mimetype="text/plain"
    )

# -------------------------------------------------------
# HOME REDIRECT
# -------------------------------------------------------
@app.route('/')
def home():
    if session.get('token'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

# -------------------------------------------------------
# 404 ERROR HANDLER
# -------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# -------------------------------------------------------
# RUN
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)