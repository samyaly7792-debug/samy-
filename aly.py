from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# كلمة السر الخاصة بك
OWNER_PASS = "samy779h"

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    username = data['username']
    password = data.get('password', '')
    
    # التحقق من أنك المالك
    is_owner = (username == "المهندس" and password == OWNER_PASS)
    
    join_room("main_chat")
    message = f"دخل {username} إلى الدردشة"
    if is_owner:
        message = "👑 دخل المالك المهندس إلى الدردشة 👑"
        
    emit('status', {'msg': message, 'is_owner': is_owner}, room="main_chat")

@socketio.on('message')
def handle_message(data):
    emit('message', data, room="main_chat")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
