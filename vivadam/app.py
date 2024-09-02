from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash, check_password_hash
import os
from langchain.chains import LLMChain
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
import json
import plotly
import plotly.graph_objs as go
import numpy as np
import logging
import requests


# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Configuration Settings
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key')

db_config = {
    'user': os.environ.get('DB_USER'),
    'host': os.environ.get('DB_HOST'),
    'database': os.environ.get('DB_NAME'),
    'password': os.environ.get('DB_PASSWORD'),
    'port': os.environ.get('DB_PORT')
}


# Database Connection
def get_db_connection():
    return psycopg2.connect(**db_config)


# Ollama Model Setup
llm = Ollama(model="llama3.1")

debate_prompt = PromptTemplate(
    input_variables=["topic", "debate_history", "user_input"],
    template="""
You are an AI debate bot engaged in a debate on the topic of {topic}.
Previous debate history:
{debate_history}
The user's latest argument is: {user_input}
Provide a concise counter-argument or supporting point, depending on the context of the debate.
Limit your response to 1-2 sentences.
Your response:
"""
)

debate_chain = LLMChain(llm=llm, prompt=debate_prompt)


def initialize_database():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(150) UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )
                """)
                print("Users table is ready.")

                # Create debate_scores table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS debate_scores (
                        id SERIAL PRIMARY KEY,
                        user_id INT REFERENCES users(id) ON DELETE CASCADE,
                        average_fact_score REAL NOT NULL CHECK (average_fact_score BETWEEN 0 AND 10),
                        average_argument_score REAL NOT NULL CHECK (average_argument_score BETWEEN 0 AND 10),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        plot_json JSONB,
                        user_scores REAL[],
                        ai_scores REAL[]
                    )
                """)
                print("Debate scores table is ready.")

                conn.commit()
                print("Database tables and columns have been created or verified.")
    except psycopg2.Error as e:
        print(f"An error occurred while initializing the database: {e.pgerror}")



def generate_response_with_ngrok(prompt, model="llama3.1"):
    url = "https://3714-34-168-163-150.ngrok-free.app/api/generate"  # Replace with your ngrok URL
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": prompt
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        # Combine all the 'response' parts from the JSON response
        responses = [json.loads(line)['response'] for line in response.text.strip().splitlines()]
        return "".join(responses)
    else:
        raise Exception(f"Failed to generate response: {response.status_code} - {response.text}")


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')


@app.route('/signup', methods=['POST'])
def signup():
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
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please enter both username and password.')
        return redirect(url_for('register'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user and check_password_hash(user[1], password):
                    session['username'] = username
                    session['user_id'] = user[0]  # Store user_id in session
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
    if 'username' not in session:
        flash('You are not logged in!')
        return redirect(url_for('register'))

    username = session['username']

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Fetch the latest debate scores for the user
                cursor.execute("""
                    SELECT user_scores, ai_scores, plot_json
                    FROM debate_scores
                    WHERE username = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (username,))

                result = cursor.fetchone()

                if result:
                    user_scores = result[0] or []
                    ai_scores = result[1] or []
                    plot_json = result[2] or json.dumps({})  # Fallback to empty JSON if plot_json is None
                else:
                    user_scores = []
                    ai_scores = []
                    plot_json = json.dumps({})

                # Calculate average scores
                avg_user_score = sum(user_scores) / len(user_scores) if user_scores else 0
                avg_ai_score = sum(ai_scores) / len(ai_scores) if ai_scores else 0

                # Calculate win rate (assuming a score > 5 is a win)
                user_wins = sum(1 for score in user_scores if score > 5)
                win_rate = (user_wins / len(user_scores)) * 100 if user_scores else 0

    except psycopg2.Error as e:
        flash(f"An error occurred while fetching dashboard data: {e.pgerror}")
        return redirect(url_for('index'))

    return render_template('dashboard.html',
                           username=username,
                           avg_user_score=avg_user_score,
                           avg_ai_score=avg_ai_score,
                           win_rate=win_rate,
                           plot_json=plot_json)



@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'username' in session:
        user_id = session['user_id']
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    conn.commit()
                    session.pop('username', None)
                    session.pop('user_id', None)
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
    session.pop('username', None)
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route('/single_user', methods=['GET', 'POST'])
def single_user():
    if 'username' not in session:
        flash('You need to log in to access this page.')
        return redirect(url_for('register'))

    if request.method == 'POST':
        topic = request.form.get('topic')
        session['debate_topic'] = topic
        session['debate_history'] = []
        return redirect(url_for('debate'))

    return render_template('single_user.html', username=session['username'])


@app.route('/debate', methods=['GET', 'POST'])
def debate():
    if 'username' not in session or 'debate_topic' not in session:
        flash('You need to start a debate first.')
        return redirect(url_for('single_user'))

    if request.method == 'POST':
        user_input = request.form.get('user_input')
        debate_history = session.get('debate_history', [])
        debate_history.append(("User", user_input))

        # Generate AI response using the ngrok API
        try:
            ai_response = generate_response_with_ngrok(
                prompt=f"Topic: {session['debate_topic']}\nDebate History:\n{''.join([f'{speaker}: {text}\n' for speaker, text in debate_history])}\nUser: {user_input}"
            )
        except Exception as e:
            flash(f"An error occurred while generating a response: {str(e)}")
            return redirect(url_for('index'))

        debate_history.append(("AI", ai_response))
        session['debate_history'] = debate_history

        return jsonify({'ai_response': ai_response})

    return render_template('debate.html', username=session['username'], topic=session['debate_topic'],
                           debate_history=session.get('debate_history', []))



@app.route('/end_debate', methods=['POST'])
def end_debate():
    if 'username' not in session or 'debate_topic' not in session:
        flash('No active debate session.')
        return redirect(url_for('single_user'))

    debate_history = session.get('debate_history', [])

    user_scores = [float(np.random.uniform(0, 10)) for _ in range(len(debate_history) // 2)]
    ai_scores = [float(np.random.uniform(0, 10)) for _ in range(len(debate_history) // 2)]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(range(1, len(user_scores) + 1)),
        y=user_scores,
        mode='markers',
        name='User Scores',
        marker=dict(size=10, color='blue', symbol='circle')
    ))

    fig.add_trace(go.Scatter(
        x=list(range(1, len(ai_scores) + 1)),
        y=ai_scores,
        mode='markers',
        name='AI Scores',
        marker=dict(size=10, color='red', symbol='x')
    ))

    fig.update_layout(
        title='User vs AI Debate Scores',
        xaxis_title='Turn',
        yaxis_title='Score',
        xaxis=dict(tickmode='linear'),
        yaxis=dict(range=[0, 10])
    )

    plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO debate_scores (username, average_fact_score, average_argument_score, plot_json, user_scores, ai_scores) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        session['username'],  # Use username here
                        sum(user_scores) / len(user_scores),
                        sum(ai_scores) / len(ai_scores),
                        plot_json,
                        user_scores,
                        ai_scores
                    )
                )
                conn.commit()
    except psycopg2.Error as e:
        logging.error(f"An error occurred while saving debate scores: {e.pgerror}")
        flash('An error occurred while saving your debate scores.')
        return redirect(url_for('index'))

    session.pop('debate_topic', None)
    session.pop('debate_history', None)

    return redirect(url_for('dashboard'))



@app.route('/multi_user')
def multi_user():
    if 'username' in session:
        return render_template('multi_user.html', username=session['username'])
    else:
        flash('You need to log in to access this page.')
        return redirect(url_for('register'))


@app.route('/evaluate_debate', methods=['POST'])
def evaluate_debate():
    if 'username' not in session:
        return jsonify({'error': 'You need to be logged in to participate in debates.'}), 401

    data = request.json
    topic = data.get('topic')
    debate_history = data.get('history')

    if not topic or not debate_history:
        return jsonify({'error': 'Missing topic or debate history'}), 400

    # Create a formatted debate history string
    formatted_history = "\n".join([f"{entry['user']}: {entry['message']}" for entry in debate_history])

    # Create a prompt for the AI to evaluate the debate
    evaluation_prompt = PromptTemplate(
        input_variables=["topic", "debate_history"],
        template="""Evaluate the following debate on the topic "{topic}":
{debate_history}

Provide a score for both participants and a brief commentary on their performance.
"""
    )
    evaluation_chain = LLMChain(llm=ollama, prompt=evaluation_prompt)

    result = evaluation_chain.invoke(input={"topic": topic, "debate_history": formatted_history})

    return jsonify({'evaluation': result['text'].strip()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
