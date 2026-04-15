from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

pending_requests = []

@app.route('/')
def index():
    return render_template('dashboard.html', pending_requests=pending_requests)

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    emit('response', {'status': 'Message received', 'data': data}, broadcast=True)

@socketio.on('approve_request')
def approve_request(data):
    request_id = data['id']
    for req in pending_requests:
        if req['id'] == request_id:
            req['status'] = 'approved'
            break
    emit('update_requests', pending_requests, broadcast=True)

@socketio.on('deny_request')
def deny_request(data):
    request_id = data['id']
    for req in pending_requests:
        if req['id'] == request_id:
            req['status'] = 'denied'
            break
    emit('update_requests', pending_requests, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
