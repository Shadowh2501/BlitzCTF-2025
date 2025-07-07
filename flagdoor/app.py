from flask import Flask, render_template, request, redirect, session, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
import uuid
import os
import hashlib
import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', str(uuid.uuid4()))

# Rate limiting based on cookie
def get_cookie_key():
    # Check if rate_limit_id cookie exists
    rate_limit_id = request.cookies.get('rate_limit_id')
    if not rate_limit_id:
        # Generate a new UUID for the cookie if none exists
        rate_limit_id = str(uuid.uuid4())
    # Return the cookie-based key
    return f"cookie:{rate_limit_id}"

limiter = Limiter(
    app=app,
    key_func=get_cookie_key,
    default_limits=["10000 per day", "1000 per hour"],
    storage_uri="memory://"
)

DB_PATH = os.path.join(os.getcwd(), 'users.db')
ADMIN_ID = -3
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'Shadowh2501')

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
        admin_pw_hash = hashlib.md5(ADMIN_PASS.encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users VALUES (?, 'admin', ?)", (ADMIN_ID, admin_pw_hash))
        conn.commit()
        print(f"Database initialized. Admin ID: {ADMIN_ID}")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
    finally:
        conn.close()

init_db()

@app.route('/')
def index():
    response = redirect('/login')
    # Set rate_limit_id cookie if not already set
    if not request.cookies.get('rate_limit_id'):
        response.set_cookie('rate_limit_id', str(uuid.uuid4()), max_age=86400 * 30)  # Cookie lasts 30 days
    return response

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.md5(password.encode()).hexdigest()
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            user_id = None
            for _ in range(10):
                candidate_id = random.randint(2, 100000)
                c.execute("SELECT 1 FROM users WHERE id=?", (candidate_id,))
                if not c.fetchone():
                    user_id = candidate_id
                    break
            if not user_id:
                return render_template('register.html', error="Registration failed. Try again.")
            c.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)", (user_id, username, password_hash))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists!")
        finally:
            conn.close()
    response = make_response(render_template('register.html'))
    # Set rate_limit_id cookie if not already set
    if not request.cookies.get('rate_limit_id'):
        response.set_cookie('rate_limit_id', str(uuid.uuid4()), max_age=86400 * 30)  # Cookie lasts 30 days
    return response

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.md5(password.encode()).hexdigest()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password_hash))
        user_id = c.fetchone()
        conn.close()
        if user_id:
            session['user_id'] = user_id[0]
            return redirect(f'/profile?id={user_id[0]}')
        else:
            return render_template('login.html', error="Invalid credentials!")
    response = make_response(render_template('login.html'))
    # Set rate_limit_id cookie if not already set
    if not request.cookies.get('rate_limit_id'):
        response.set_cookie('rate_limit_id', str(uuid.uuid4()), max_age=86400 * 30)  # Cookie lasts 30 days
    return response

@app.route('/profile')
@limiter.limit("30 per minute")
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = request.args.get('id')
    if not user_id:
        return "Missing user ID", 400
    try:
        user_id_int = int(user_id)
        if user_id_int < 0 and user_id_int != ADMIN_ID:
            return "User not found", 404
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (user_id_int,))
        user = c.fetchone()
        if user:
            return render_template('profile.html',
                                   username=user[1],
                                   user_id=user[0],
                                   flag="Blitz{ID0R_1s_FUN_w1TH_N3g4t1v3_IDs!?}" if user[0] == ADMIN_ID else None)
        return "User not found", 404
    except ValueError:
        return "Invalid user ID", 400
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)