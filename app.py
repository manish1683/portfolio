# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
from dotenv import load_dotenv
import secrets
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# ---------- BASE DIRECTORY (for absolute paths) ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'messages.db')

# ---------- RESUME CONFIG ----------
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/resume')
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

init_db()

def save_message(name, email, message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)',
              (name, email, message))
    conn.commit()
    conn.close()

def get_all_messages():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute('SELECT * FROM contacts ORDER BY timestamp DESC').fetchall()
    conn.close()
    return rows

def delete_message(msg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM contacts WHERE id = ?', (msg_id,))
    conn.commit()
    conn.close()

def delete_all_messages():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM contacts')
    conn.commit()
    conn.close()

# ---------- EMAIL ----------
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')

def send_email_notification(name, email, message):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        print("Email credentials missing – skipping email.")
        return False
    subject = f"New portfolio message from {name}"
    body = f"""
    Name: {name}
    Email: {email}
    Message:
    {message}

    Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {EMAIL_RECEIVER}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ---------- AUTH DECORATOR ----------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ---------- ROUTES ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact', methods=['POST'])
def contact():
    try:
        # Parse JSON data
        data = request.get_json()
        if data is None:
            print("ERROR: No JSON data received or invalid Content-Type.")
            return jsonify({'status': 'error', 'message': 'Invalid JSON or missing Content-Type'}), 400

        name = data.get('name')
        email = data.get('email')
        message = data.get('message')

        if not name or not email or not message:
            print(f"ERROR: Missing fields – name={name}, email={email}, message={message}")
            return jsonify({'status': 'error', 'message': 'All fields required.'}), 400

        # Save to database
        save_message(name, email, message)
        print(f"Message saved from {name} ({email})")

        # Send email (catch errors separately)
        try:
            send_email_notification(name, email, message)
        except Exception as e:
            print(f"Email error (but message saved): {e}")

        return jsonify({'status': 'success', 'message': 'Message saved! We\'ll get back to you.'})

    except Exception as e:
        print(f"ERROR in /contact: {e}")
        import traceback
        traceback.print_exc()   # full stack trace in logs
        return jsonify({'status': 'error', 'message': 'Server error. Please try again.'}), 500

# ---------- ADMIN LOGIN ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin_user = os.getenv('ADMIN_USERNAME', 'admin')
        admin_pass = os.getenv('ADMIN_PASSWORD', 'password')
        if username == admin_user and password == admin_pass:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid username or password'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

# ---------- ADMIN DASHBOARD ----------
@app.route('/admin')
@login_required
def admin_dashboard():
    messages = get_all_messages()
    return render_template('admin_dashboard.html', messages=messages)

# ---------- DELETE ROUTES ----------
@app.route('/admin/delete/<int:msg_id>', methods=['POST'])
@login_required
def admin_delete(msg_id):
    delete_message(msg_id)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-all')
@login_required
def admin_delete_all():
    delete_all_messages()
    return redirect(url_for('admin_dashboard'))

# ---------- RESUME MANAGEMENT ----------
@app.route('/admin/resume', methods=['GET', 'POST'])
@login_required
def admin_resume():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return 'No file part', 400
        file = request.files['resume']
        if file.filename == '':
            return 'No selected file', 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'resume.pdf')
            file.save(filepath)
            return 'Resume uploaded successfully! <a href="/admin/resume">Upload another</a>'
        else:
            return 'Only PDF files are allowed', 400

    resume_exists = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'resume.pdf'))
    return render_template('resume_upload.html', resume_exists=resume_exists)

@app.route('/admin/resume/delete', methods=['POST'])
@login_required
def admin_resume_delete():
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'resume.pdf')
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('admin_resume'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)