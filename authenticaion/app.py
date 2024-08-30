from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection details
db_config = {
    'user': 'postgres',
    'host': 'localhost',
    'database': 'mydb',
    'password': 'turtle369',
    'port': 5432
}

def get_db_connection():
    conn = psycopg2.connect(**db_config)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
            flash('Signup successful! Please login.')
            return redirect(url_for('login'))
        except psycopg2.Error as e:
            flash(f"An error occurred: {e}")
        finally:
            cursor.close()
            conn.close()

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[0], password):
            session['username'] = username
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')

        cursor.close()
        conn.close()

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        flash('You are not logged in!')
        return redirect(url_for('login'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'username' in session:
        username = session['username']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE username = %s", (username,))
            conn.commit()
            session.pop('username', None)
            flash('Your account has been deleted.')
            return redirect(url_for('index'))
        except psycopg2.Error as e:
            flash(f"An error occurred: {e}")
        finally:
            cursor.close()
            conn.close()

    flash('You are not logged in!')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
