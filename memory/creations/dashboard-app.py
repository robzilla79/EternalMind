from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
csrf = CSRFProtect(app)

# Rate limiting setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# SQLite setup
def init_db():
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_request', methods=['POST'])
@limiter.limit("10 per minute")
def submit_request():
    content = request.form['content']
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    c.execute("INSERT INTO requests (content, status) VALUES (?, 'pending')", (content,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@socketio.on('chat_message')
def handle_chat_message(data):
    user = data['user']
    message = data['message']
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    c.execute("INSERT INTO chat (user, message) VALUES (?, ?)", (user, message))
    conn.commit()
    conn.close()
    emit('chat_message', {'user': user, 'message': message}, broadcast=True)

@socketio.on('get_requests')
def handle_get_requests():
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    c.execute("SELECT * FROM requests WHERE status = 'pending'")
    requests = c.fetchall()
    conn.close()
    emit('update_requests', [dict(id=row[0], content=row[1], status=row[2]) for row in requests])

@socketio.on('approve_request')
def handle_approve_request(data):
    req_id = data['id']
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    c.execute("UPDATE requests SET status = 'approved' WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()
    emit('update_requests', data, broadcast=True)

@socketio.on('deny_request')
def handle_deny_request(data):
    req_id = data['id']
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    c.execute("UPDATE requests SET status = 'denied' WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()
    emit('update_requests', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app)
