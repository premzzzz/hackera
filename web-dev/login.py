from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# =======================
# Configuration Settings
# =======================

# It's recommended to set these environment variables securely in your deployment environment
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key')  # Replace with a strong secret key

# Database connection details from environment variables for security
db_config = {
    'user': os.environ.get('DB_USER'),
    'host': os.environ.get('DB_HOST'),
    'database': os.environ.get('DB_NAME'),
    'password': os.environ.get('DB_PASSWORD'),
    'port': os.environ.get('DB_PORT')
}

# =======================
# Database Connection
# =======================

def get_db_connection():
    """
    Establishes a new database connection.
    """
    return psycopg2.connect(**db_config)

# =======================
# Routes
# =======================

@app.route('/')
def index():
    """
    Home page route.
    """
    return render_template('index.html')

@app.route('/register', methods=['GET'])
def register():
    """
    Registration and Login page route.
    """
    return render_template('register.html')

@app.route('/signup', methods=['POST'])
def signup():
    """
    Handles user signup.
    """
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill out both username and password fields.')
        return redirect(url_for('register'))

    hashed_password = generate_password_hash(password)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM users WHERE username = %s",
                    (username,)
                )
                if cursor.fetchone():
                    flash('Username already exists. Please choose a different one.')
                    return redirect(url_for('register'))

                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, hashed_password)
                )
                conn.commit()
                flash('Signup successful! Please log in.')
                return redirect(url_for('register'))
    except psycopg2.Error as e:
        flash(f"An error occurred during signup: {e.pgerror}")
        return redirect(url_for('register'))

@app.route('/login', methods=['POST'])
def login():
    """
    Handles user login.
    """
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please enter both username and password.')
        return redirect(url_for('register'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT password FROM users WHERE username = %s",
                    (username,)
                )
                user = cursor.fetchone()

                if user and check_password_hash(user[0], password):
                    session['username'] = username
                    flash('Login successful!')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password.')
                    return redirect(url_for('register'))
    except psycopg2.Error as e:
        flash(f"An error occurred during login: {e.pgerror}")
        return redirect(url_for('register'))

@app.route('/dashboard')
def dashboard():
    """
    User dashboard route. Accessible only to logged-in users.
    """
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        flash('You are not logged in!')
        return redirect(url_for('register'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    """
    Handles account deletion.
    """
    if 'username' in session:
        username = session['username']
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM users WHERE username = %s", (username,))
                    conn.commit()
                    session.pop('username', None)
                    flash('Your account has been deleted.')
                    return redirect(url_for('index'))
        except psycopg2.Error as e:
            flash(f"An error occurred while deleting your account: {e.pgerror}")
            return redirect(url_for('dashboard'))
    else:
        flash('You are not logged in!')
        return redirect(url_for('register'))

@app.route('/logout')
def logout():
    """
    Logs the user out.
    """
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/single_user')
def single_user():
    """
    Single-user debate route. Accessible only to logged-in users.
    """
    if 'username' in session:
        return render_template('single_user.html', username=session['username'])
    else:
        flash('You need to log in to access this page.')
        return redirect(url_for('register'))

@app.route('/multi_user')
def multi_user():
    """
    Multi-user debate route. Accessible only to logged-in users.
    """
    if 'username' in session:
        return render_template('multi_user.html', username=session['username'])
    else:
        flash('You need to log in to access this page.')
        return redirect(url_for('register'))

# =======================
# Run the Application
# =======================

if __name__ == '__main__':
    # It's recommended to set debug=False in production
    app.run(debug=True)
