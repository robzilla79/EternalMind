from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
csrf = CSRFProtect(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

socketio = SocketIO(app, cors_allowed_origins="*")

# Database setup
def get_db():
    conn = sqlite3.connect('dashboard.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('submit_request')
def handle_submit_request(data):
    conn = get_db()
    conn.execute("INSERT INTO requests (content) VALUES (?)", (data['content'],))
    conn.commit()
    conn.close()
    emit('update_requests', get_requests(), broadcast=True)

@socketio.on('approve_request')
def handle_approve_request(data):
    conn = get_db()
    conn.execute("UPDATE requests SET status = 'approved' WHERE id = ?", (data['id'],))
    conn.commit()
    conn.close()
    emit('update_requests', get_requests(), broadcast=True)

@socketio.on('deny_request')
def handle_deny_request(data):
    conn = get_db()
    conn.execute("UPDATE requests SET status = 'denied' WHERE id = ?", (data['id'],))
    conn.commit()
    conn.close()
    emit('update_requests', get_requests(), broadcast=True)

def get_requests():
    conn = get_db()
    rows = conn.execute("SELECT * FROM requests").fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == '__main__':
    socketio.run(app, debug=True)
