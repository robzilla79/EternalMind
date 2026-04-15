<!-- Last updated: 2026-04-15 16:14 UTC -->
_socketio import SocketIO, emit
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

if __name__ == '__main__':
    socketio.run(app)
FILE_CONTENT_END

LIVE_CONTEXT_ADD: Dashboard app updated with Flask-WTF CSRF protection, Flask-Limiter rate limiting, and SQLite3 persistent storage. Ready for Rob's review and testing. Next steps: implement UI refinements and security hardening.