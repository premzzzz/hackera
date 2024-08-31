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
import logging  # Add this line

# Set up logging


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
    if 'username' not in session:
        flash('You are not logged in!')
        return redirect(url_for('register'))

    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT user_scores, ai_scores, created_at, plot_json
                    FROM debate_scores 
                    WHERE username = %s 
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (username,))
                latest_score = cursor.fetchone()

                if latest_score:
                    user_scores, ai_scores, created_at, plot_json = latest_score
                    
                    # Handle potential None values
                    user_scores = user_scores if user_scores is not None else []
                    ai_scores = ai_scores if ai_scores is not None else []
                    
                    # Calculate average scores
                    avg_user_score = sum(user_scores) / len(user_scores) if user_scores else 0
                    avg_ai_score = sum(ai_scores) / len(ai_scores) if ai_scores else 0
                    
                    # Calculate win rate (assuming a score > 5 is a win)
                    user_wins = sum(1 for score in user_scores if score > 5)
                    win_rate = (user_wins / len(user_scores)) * 100 if user_scores else 0

                    return render_template('dashboard.html', 
                                           username=username,
                                           avg_user_score=avg_user_score,
                                           avg_ai_score=avg_ai_score,
                                           win_rate=win_rate,
                                           plot_json=plot_json,
                                           debate_date=created_at)
                else:
                    flash('No debate data available yet.')
                    return render_template('dashboard.html', username=username)

    except psycopg2.Error as e:
        flash(f"An error occurred while fetching debate scores: {e.pgerror}")
        return render_template('dashboard.html', username=username)

    
@app.route('/delete_account', methods=['POST'])
def delete_account():
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
    session.pop('username', None)
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

        # Generate AI response
        ai_response = debate_chain.invoke(
            input={
                "topic": session['debate_topic'],
                "debate_history": "\n".join([f"{speaker}: {text}" for speaker, text in debate_history]),
                "user_input": user_input
            }
        )['text'].strip()

        debate_history.append(("AI", ai_response))
        session['debate_history'] = debate_history

        return jsonify({'ai_response': ai_response})

    return render_template('debate.html', username=session['username'], topic=session['debate_topic'], debate_history=session.get('debate_history', []))

@app.route('/end_debate', methods=['POST'])
def end_debate():
    if 'username' not in session or 'debate_topic' not in session:
        flash('No active debate session.')
        return redirect(url_for('single_user'))

    debate_history = session.get('debate_history', [])
    
    # Simulate evaluation (replace with actual evaluation logic)
    user_scores = [float(np.random.uniform(0, 10)) for _ in range(len(debate_history) // 2)]
    ai_scores = [float(np.random.uniform(0, 10)) for _ in range(len(debate_history) // 2)]
    
    logging.debug(f"Generated user_scores: {user_scores}")
    logging.debug(f"Generated ai_scores: {ai_scores}")
    
    # Generate scatter plot
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
        marker=dict(size=10, color='red', symbol='diamond')
    ))
    
    fig.update_layout(
        title='Debate Scores: User vs AI',
        xaxis_title='Turn',
        yaxis_title='Score',
        yaxis=dict(range=[0, 10])
    )
    
    plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Store scores in the database
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO debate_scores (username, user_scores, ai_scores, plot_json) VALUES (%s, %s, %s, %s)",
                    (session['username'], user_scores, ai_scores, plot_json)
                )
                conn.commit()
        logging.debug("Debate scores successfully saved to database")
    except psycopg2.Error as e:
        logging.error(f"Database error while saving scores: {e.pgerror}")
        flash(f"An error occurred while saving debate scores: {e.pgerror}")

    # Clear session data
    session.pop('debate_topic', None)
    session.pop('debate_history', None)

    # Redirect to dashboard
    return redirect(url_for('dashboard'))

@app.route('/multi_user')
def multi_user():
    if 'username' in session:
        return render_template('multi_user.html', username=session['username'])
    else:
        flash('You need to log in to access this page.')
        return redirect(url_for('register'))

if __name__ == '__main__':
    app.run(debug=True)