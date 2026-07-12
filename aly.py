from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'samy_king_final_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# قاعدة بيانات المستخدمين
active_users = {}

# بيانات المالك
ADMIN_NAME = "المهندس"
ADMIN_PASS = "Samy779h"

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    name = data.get('name', 'زائر')
    password = data.get('pass', '')
    
    # التحقق من المالك
    is_admin = (name == ADMIN_NAME and password == ADMIN_PASS)
    
    # إضافة المستخدم
    active_users[request.sid] = {
        'name': name,
        'is_admin': is_admin,
        'role': 'مالك' if is_admin else 'عضو'
    }
    
    # رسالة ترحيب ذكية
    welcome_msg = f"دخل المالك {name}" if is_admin else f"دخل {name} بإشراف المهندس"
    emit('status', {'msg': welcome_msg}, broadcast=True)
    emit('user_list', active_users, broadcast=True)

@socketio.on('kick_user')
def on_kick(data):
    target_sid = data.get('target_sid')
    # التحقق من صلاحية المالك فقط قبل الطرد
    if active_users.get(request.sid, {}).get('is_admin'):
        if target_sid in active_users:
            emit('kicked', {'msg': 'تم طردك من قبل المالك'}, room=target_sid)
            socketio.emit('status', {'msg': f'تم طرد {active_users[target_sid]["name"]}'}, broadcast=True)
            disconnect(sid=target_sid)

@socketio.on('text')
def on_text(data):
    user = active_users.get(request.sid)
    if user:
        emit('message', {
            'sender': user['name'],
            'is_admin': user['is_admin'],
            'msg': data['msg']
        }, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_users:
        name = active_users[request.sid]['name']
        del active_users[request.sid]
        emit('status', {'msg': f'غادر {name} الشات.'}, broadcast=True)
        emit('user_list', active_users, broadcast=True)
        if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
    
