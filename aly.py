from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random
import os

app = Flask(__name__)
# الإعدادات لضمان تحديث الواجهة فوراً
app.config['SECRET_KEY'] = 'samy_king_final_2026'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
socketio = SocketIO(app, cors_allowed_origins="*")

# قاعدة بيانات المستخدمين النشطين
active_sessions = {}

# بيانات الدخول الخاصة بالمهندس
ADMIN_NAME = "المهندس"
ADMIN_PASS = "Samy779h"

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('check_join')
def on_check_join(data):
    nickname = data.get('name', '').strip()
    password = data.get('pass', '').strip()
    
    # التحقق من صلاحيات المهندس
    if nickname == ADMIN_NAME:
        if password != ADMIN_PASS:
            emit('login_failed', {'msg': '❌ كلمة سر المهندس غير صحيحة!'})
            return
        is_admin = True
        display_name = f"👑 {nickname}"
    else:
        is_admin = False
        display_name = nickname

    avatar_url = f"https://i.pravatar.cc/100?img={random.randint(1, 70)}"
    active_sessions[request.sid] = {"name": display_name, "avatar": avatar_url, "is_admin": is_admin}
    
    emit('status', {'msg': f'انضم {display_name} بإشراف المهندس.'}, broadcast=True)
    emit('user_list', active_sessions, broadcast=True)

@socketio.on('text')
def on_text(data):
    if request.sid in active_sessions:
        user_data = active_sessions[request.sid]
        emit('message', {
            'sender': user_data['name'], 
            'avatar': user_data['avatar'], 
            'msg': data['msg']
        }, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_sessions:
        nickname = active_sessions[request.sid]['name']
        del active_sessions[request.sid]
        emit('status', {'msg': f'غادر {nickname} الشات.'}, broadcast=True)
        emit('user_list', active_sessions, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
