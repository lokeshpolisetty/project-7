from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import google.generativeai as genai
from werkzeug.utils import secure_filename
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configure Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        os.getenv('DATABASE_URL', 'postgresql://localhost/smarttutor'),
        cursor_factory=RealDictCursor
    )
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'tutor')),
            avatar VARCHAR(255),
            bio TEXT,
            hourly_rate DECIMAL(10,2),
            subjects TEXT[],
            rating DECIMAL(3,2) DEFAULT 0,
            total_sessions INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create sessions table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tutoring_sessions (
            id SERIAL PRIMARY KEY,
            tutor_id INTEGER REFERENCES users(id),
            student_id INTEGER REFERENCES users(id),
            subject VARCHAR(255) NOT NULL,
            scheduled_at TIMESTAMP NOT NULL,
            duration INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
            price DECIMAL(10,2) NOT NULL,
            notes TEXT,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            review TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create AI conversations table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ai_conversations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            subject VARCHAR(255),
            question TEXT NOT NULL,
            response TEXT NOT NULL,
            conversation_type VARCHAR(50) DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

# AI Helper Functions
def generate_ai_response(question, subject=None, conversation_type='general'):
    """Generate AI response using Gemini"""
    try:
        # Create context-aware prompt based on conversation type
        if conversation_type == 'explanation':
            prompt = f"""You are an expert tutor. Provide a clear, step-by-step explanation for this {subject or 'academic'} question. 
            Break down complex concepts into simple terms and include examples where helpful.
            
            Question: {question}
            
            Please provide a comprehensive but easy-to-understand explanation."""
            
        elif conversation_type == 'practice':
            prompt = f"""You are an expert tutor. Generate 3-5 practice problems related to this {subject or 'academic'} topic: {question}

For each problem:
1. Provide the problem statement (the question)
2. Give only the final answer (no step-by-step solution)
3. Give a helpful hint (but do not provide the full solution)

Format each problem as:
Question: ...
Answer: ...
Hint: ...

Do NOT include the full solution or step-by-step working. Only provide the question, answer, and hint.
"""
            
        elif conversation_type == 'quiz':
            prompt = f"""Create an interactive quiz about {subject or 'the topic'}: {question}

Create exactly 5 multiple-choice questions in this EXACT format:

Q1: [Question text here]
A) [Option A]
B) [Option B] 
C) [Option C]
D) [Option D]
Correct Answer: [A/B/C/D]
Explanation: [Brief explanation of why this is correct]

Q2: [Question text here]
A) [Option A]
B) [Option B]
C) [Option C] 
D) [Option D]
Correct Answer: [A/B/C/D]
Explanation: [Brief explanation of why this is correct]

[Continue for Q3, Q4, Q5...]

Make sure each question tests understanding of key concepts. Keep explanations brief but informative.
"""
            
        elif conversation_type == 'study_notes':
            prompt = f"""Create comprehensive study notes for {subject or 'the topic'}: {question}
            
            Include:
            1. Key concepts and definitions
            2. Important formulas or principles
            3. Common examples
            4. Tips for remembering the material
            5. Common mistakes to avoid
            
            Format as clear, organized notes suitable for review."""
            
        else:  # general
            prompt = f"""You are a helpful tutor assistant. Answer this {subject or 'academic'} question clearly and helpfully: {question}
            
            Provide accurate information and explain concepts in an easy-to-understand way."""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"I apologize, but I'm having trouble generating a response right now. Please try again later. Error: {str(e)}"

def generate_quiz_questions(subject, topic, difficulty='intermediate', question_count=5):
    """Generate quiz questions using AI"""
    try:
        prompt = f"""Create an interactive quiz about {topic} in {subject} at {difficulty} level.

Create exactly {question_count} multiple-choice questions in this EXACT format:

Q1: [Question text here]
A) [Option A]
B) [Option B] 
C) [Option C]
D) [Option D]
Correct Answer: [A/B/C/D]
Explanation: [Brief explanation of why this is correct]

Q2: [Question text here]
A) [Option A]
B) [Option B]
C) [Option C] 
D) [Option D]
Correct Answer: [A/B/C/D]
Explanation: [Brief explanation of why this is correct]

[Continue for all {question_count} questions...]

Make sure each question tests understanding of key concepts related to {topic}. 
Difficulty level: {difficulty}
Keep explanations brief but informative.
"""
        
        response = model.generate_content(prompt)
        return parse_quiz_response(response.text)
        
    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
        return []

def parse_quiz_response(response):
    """Parse AI response into structured quiz data"""
    quiz = []
    regex = r'Q(\d+):\s*(.*?)\nA\)\s*(.*?)\nB\)\s*(.*?)\nC\)\s*(.*?)\nD\)\s*(.*?)\nCorrect Answer:\s*([A-D])\nExplanation:\s*(.*?)(?=\n\nQ\d+:|$)'
    
    matches = re.finditer(regex, response, re.DOTALL)
    
    for match in matches:
        quiz.append({
            'questionNumber': int(match.group(1)),
            'question': match.group(2).strip(),
            'options': [
                {'label': 'A', 'text': match.group(3).strip()},
                {'label': 'B', 'text': match.group(4).strip()},
                {'label': 'C', 'text': match.group(5).strip()},
                {'label': 'D', 'text': match.group(6).strip()}
            ],
            'answer': match.group(7).strip(),
            'explanation': match.group(8).strip()
        })
    
    return quiz

# Configure file uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash('Welcome back! Login successful.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'student')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cur.fetchone():
            flash('Email already registered. Please use a different email.', 'error')
            cur.close()
            conn.close()
            return render_template('register.html')
        
        # Create user
        password_hash = generate_password_hash(password)
        cur.execute('''
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
        ''', (name, email, password_hash, role))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Account created successfully! Please login to continue.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/tutors')
def tutors():
    conn = get_db_connection()
    cur = conn.cursor()
    
    search = request.args.get('search', '')
    subject = request.args.get('subject', '')
    
    query = '''
        SELECT id, name, bio, hourly_rate, subjects, rating, total_sessions, avatar
        FROM users 
        WHERE role = 'tutor'
    '''
    params = []
    
    if search:
        query += ' AND (name ILIKE %s OR bio ILIKE %s)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    if subject:
        query += ' AND %s = ANY(subjects)'
        params.append(subject)
    
    query += ' ORDER BY rating DESC, total_sessions DESC'
    
    cur.execute(query, params)
    tutors_list = cur.fetchall()
    
    # Get unique subjects
    cur.execute('SELECT DISTINCT unnest(subjects) as subject FROM users WHERE role = \'tutor\' ORDER BY subject')
    subjects = [row['subject'] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return render_template('tutors.html', tutors=tutors_list, subjects=subjects)

@app.route('/book/<int:tutor_id>', methods=['GET', 'POST'])
def book_session(tutor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['user_role'] != 'student':
        flash('Only students can book sessions', 'error')
        return redirect(url_for('tutors'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get tutor info
    cur.execute('SELECT * FROM users WHERE id = %s AND role = \'tutor\'', (tutor_id,))
    tutor = cur.fetchone()
    
    if not tutor:
        flash('Tutor not found', 'error')
        return redirect(url_for('tutors'))
    
    if request.method == 'POST':
        subject = request.form['subject']
        date = request.form['date']
        time = request.form['time']
        duration = int(request.form['duration'])
        notes = request.form.get('notes', '')
        
        scheduled_at = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        price = float(tutor['hourly_rate']) * (duration / 60)
        
        cur.execute('''
            INSERT INTO tutoring_sessions (tutor_id, student_id, subject, scheduled_at, duration, price, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (tutor_id, session['user_id'], subject, scheduled_at, duration, price, notes))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Session booked successfully!', 'success')
        return redirect(url_for('chat'))
    
    cur.close()
    conn.close()
    return render_template('book_session.html', tutor=tutor)

@app.route('/ai-tutor')
def ai_tutor():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get recent conversations
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM ai_conversations 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', (session['user_id'],))
    recent_conversations = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('ai_tutor.html', conversations=recent_conversations)

@app.route('/ai-chat', methods=['POST'])
def ai_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Verify user exists first
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        
        if not user:
            cur.close()
            conn.close()
            session.clear()
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        question = data.get('question', '').strip()
        subject = data.get('subject', '')
        conversation_type = data.get('type', 'general')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Generate AI response
        response = generate_ai_response(question, subject, conversation_type)
        
        # Save conversation
        cur.execute('''
            INSERT INTO ai_conversations (user_id, subject, question, response, conversation_type)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at
        ''', (session['user_id'], subject, question, response, conversation_type))
        
        result = cur.fetchone()
        conn.commit()
        
        return jsonify({
            'response': response,
            'id': result['id'],
            'timestamp': result['created_at'].isoformat(),
            'type': conversation_type
        })
        
    except Exception as e:
        print(f"Error in ai_chat: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'}), 500
        
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

# Quiz Routes
@app.route('/quiz/setup')
def quiz_setup():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('quiz_setup.html')

@app.route('/quiz/generate', methods=['POST'])
def quiz_generate():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get form data
    subject = request.form.get('subject')
    topic = request.form.get('topic')
    difficulty = request.form.get('difficulty', 'intermediate')
    question_count = int(request.form.get('questionCount', 5))
    time_limit = int(request.form.get('timeLimit', 30))
    
    # Store quiz data in session
    quiz_data = {
        'subject': subject,
        'topic': topic,
        'difficulty': difficulty,
        'question_count': question_count,
        'time_limit': time_limit
    }
    session['quiz_data'] = quiz_data
    
    # Generate questions
    questions = generate_quiz_questions(subject, topic, difficulty, question_count)
    session['quiz_questions'] = questions
    
    return render_template('quiz_loading.html', quiz_data=quiz_data)

@app.route('/quiz/take')
def quiz_take():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    quiz_data = session.get('quiz_data')
    quiz_questions = session.get('quiz_questions')
    
    if not quiz_data or not quiz_questions:
        flash('No quiz data found. Please create a new quiz.', 'error')
        return redirect(url_for('quiz_setup'))
    
    return render_template('quiz_take.html', 
                         quiz_data=quiz_data, 
                         quiz_questions=quiz_questions)

@app.route('/quiz/results')
def quiz_results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('quiz_results.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = cur.fetchone()
    # Get conversation stats if needed
    cur.execute('SELECT COUNT(*) as total_conversations FROM ai_conversations WHERE user_id = %s', (session['user_id'],))
    stats = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('profile.html', user=user, stats=stats, datetime=datetime)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = cur.fetchone()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        avatar = request.form.get('avatar', '').strip()
        password = request.form.get('password', '').strip()
        file = request.files.get('avatar_file')

        # Handle image upload
        if file and allowed_file(file.filename):
            filename = secure_filename(f"user_{session['user_id']}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            avatar = url_for('static', filename=f'uploads/{filename}')
        
        # Basic validation
        if not name or not email:
            flash('Name and email are required.', 'error')
            return render_template('edit_profile.html', user=user)
        
        # Check for email conflict
        cur.execute('SELECT id FROM users WHERE email = %s AND id != %s', (email, session['user_id']))
        if cur.fetchone():
            flash('Email already in use by another account.', 'error')
            return render_template('edit_profile.html', user=user)
        
        # Update user
        if password:
            password_hash = generate_password_hash(password)
            cur.execute('''
                UPDATE users SET name=%s, email=%s, avatar=%s, password_hash=%s WHERE id=%s
            ''', (name, email, avatar, password_hash, session['user_id']))
        else:
            cur.execute('''
                UPDATE users SET name=%s, email=%s, avatar=%s WHERE id=%s
            ''', (name, email, avatar, session['user_id']))
        
        conn.commit()
        session['user_name'] = name
        flash('Profile updated successfully.', 'success')
        cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return redirect(url_for('profile'))
    
    cur.close()
    conn.close()
    return render_template('edit_profile.html', user=user)

@app.route('/profile/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = cur.fetchone()

    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not current_password or not new_password or not confirm_password:
            flash('All fields are required.', 'error')
            return render_template('change_password.html', user=user)

        if not check_password_hash(user['password_hash'], current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('change_password.html', user=user)

        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('change_password.html', user=user)

        if len(new_password) < 6:
            flash('New password must be at least 6 characters.', 'error')
            return render_template('change_password.html', user=user)

        password_hash = generate_password_hash(new_password)
        cur.execute('UPDATE users SET password_hash=%s WHERE id=%s', (password_hash, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('profile'))

    cur.close()
    conn.close()
    return render_template('change_password.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get recent conversations
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM ai_conversations 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', (session['user_id'],))
    recent_conversations = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('chat.html', conversations=recent_conversations)

@app.route('/chat/explanation')
def chat_explanation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM ai_conversations 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', (session['user_id'],))
    recent_conversations = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('chat_explanation.html', conversations=recent_conversations)

@app.route('/chat/practice')
def chat_practice():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM ai_conversations 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', (session['user_id'],))
    recent_conversations = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('chat_practice.html', conversations=recent_conversations)

@app.route('/chat/quiz')
def chat_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('quiz_setup'))

@app.route('/chat/study-notes')
def chat_study_notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    # Fetch only study_notes conversations
    cur.execute('''
        SELECT * FROM ai_conversations 
        WHERE user_id = %s AND conversation_type = 'study_notes'
        ORDER BY created_at DESC 
        LIMIT 20
    ''', (session['user_id'],))
    study_notes_conversations = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('chat_study_notes.html', conversations=study_notes_conversations)

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get all conversations with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM ai_conversations 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT %s OFFSET %s
    ''', (session['user_id'], per_page, offset))
    conversations = cur.fetchall()
    
    # Get total count for pagination
    cur.execute('SELECT COUNT(*) FROM ai_conversations WHERE user_id = %s', (session['user_id'],))
    total = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    
    return render_template('history.html', conversations=conversations, 
                         page=page, per_page=per_page, total=total)

@app.route('/history/delete', methods=['POST'])
def delete_history():
    if 'user_id' not in session:
        abort(401)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM ai_conversations WHERE user_id = %s', (session['user_id'],))
    conn.commit()
    cur.close()
    conn.close()
    flash('All chat history deleted successfully.', 'success')
    return redirect(url_for('history'))

@app.route('/history/delete/<int:conv_id>', methods=['POST'])
def delete_conversation(conv_id):
    if 'user_id' not in session:
        abort(401)
    conn = get_db_connection()
    cur = conn.cursor()
    # Only allow deleting user's own conversation
    cur.execute('DELETE FROM ai_conversations WHERE id = %s AND user_id = %s', (conv_id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    flash('Conversation deleted successfully.', 'success')
    return redirect(url_for('history'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Add JSON filter for templates
@app.template_filter('tojsonfilter')
def to_json_filter(obj):
    return json.dumps(obj)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)